import asyncio
import inspect
import signal
import typing
from asyncio import AbstractEventLoop
from typing import Optional, Dict, Callable, Set
from concurrent.futures import ThreadPoolExecutor

from google.cloud import pubsub_v1
from google.api_core.exceptions import AlreadyExists
from google.auth.api_key import Credentials
from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1.types import message
from google.pubsub_v1 import Subscription, SubscriberClient

from python_publish_subscribe.config import Config
from python_publish_subscribe.src.helper import build_and_save_topic_string, is_subscription_subscription_path
from python_publish_subscribe.src.db.DatabaseHelper import DatabaseHelper, create_engine_from_url

_SYNC_EXECUTOR = ThreadPoolExecutor()

async def _handle_message(message, callback):
    wants_session = 'session' in inspect.signature(callback).parameters

    if inspect.iscoroutinefunction(callback):
        if wants_session and DatabaseHelper.is_setup():
            if DatabaseHelper.is_async():
                async with DatabaseHelper.create_async_session() as session:
                    try:
                        result = await callback(message, session)
                        if result is False:
                            raise ValueError("Callback returned False")
                        await session.commit()
                    except Exception:
                        await session.rollback()
                        raise
            else:
                print("Error: Async callback provided but using a synchronous database engine.")
                raise RuntimeError(
                    "Async callback provided but using a synchronous database engine "
                    "Either make the callback synchronous or configure an async database engine."
                )
        else:
            await callback(message)

    else:
        def sync_work():
            local_session = None
            if wants_session:
                local_session = DatabaseHelper.create_session()
            try:
                callback(message, local_session) if wants_session else callback(message)
                if wants_session:
                    local_session.commit()
            except Exception:
                if wants_session:
                    local_session.rollback()
                raise
            finally:
                if wants_session:
                    local_session.close()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(_SYNC_EXECUTOR, sync_work)


class Subscriber:
    def __init__(self, config: Config, credentials: Credentials=None):
        self._subscriber: SubscriberClient = pubsub_v1.SubscriberClient(credentials=credentials)
        self._config: Config = config
        self._subscriptions: Dict[str, Dict[str, Callable] | Dict[str, bool]] = {}
        self._loop = asyncio.get_event_loop()

    def get_subscription_path(self, subscription_name: str) -> str:
        """
        Gets the path of a subscription.

        :param subscription_name: name of the subscription
        :return: subscription path
        """
        if is_subscription_subscription_path(subscription_name):
            return subscription_name
        subscription_paths = self._config.get(Config.ConfigKeys.SUBSCRIPTION_TOPICS.name)
        if subscription_name in subscription_paths:
            return subscription_paths.get(subscription_name)
        return self._subscriber.subscription_path(self._config.get('PROJECT_ID'), subscription_name)

    def add_subscription(self, subscription_name: str, callback: typing.Callable, exactly_once_delivery: bool=False) -> None:
        """
        Adds a preconfigured subscription, and it's callback function to the configuration, such that
        when app.run() is called it can be subscribed too correctly.

        :param subscription_name: name of the subscription
        :param callback: callback function for the subscription when a message is received
        :param exactly_once_delivery: if the subscription should use exactly once delivery
        """
        self._subscriptions[subscription_name] = {
            'callback': callback,
            'exactly_once_delivery': exactly_once_delivery,
        }

        # self._subscriptions[subscription_name]["CALLBACK"] = callback
        # self._subscriptions[subscription_name]["EXACTLY_ONCE"] = exactly_once_delivery

    def create_subscription(self, subscription_name, topic) -> Optional[Subscription]:
        """
        Creates a new subscription in GCP Pub/Sub and returns it.

        :param topic: Name of the topic to subscribe to
        :param subscription_name: Subscription name
        :return: The subscription or None if there was an error correcting it.
        """
        path = self._subscriber.subscription_path(self._config.get('PROJECT_ID'), subscription_name)
        topic, topic_name = build_and_save_topic_string(topic, self._config.get(Config.ConfigKeys.PROJECT_ID.name), self._config)
        self._config.add_value_to_key(Config.ConfigKeys.SUBSCRIPTION_TOPICS.name, {subscription_name: path})
        try:
            subscription = self._subscriber.create_subscription(name=path, topic=topic)
            return subscription
        except AlreadyExists:
            print("Warning: Subscription {subscription} already exists".format(subscription=subscription_name))
            return self._subscriber.get_subscription({"subscription": path})
        except Exception as error:
            print("Error: Something went wrong when creating subscription {subscription}: {error}"
                  .format(subscription=path, error=error))
            return None

    def start_subscription_tasks(self) -> None:
        """
        Starts listening and handling subscriptions asynchronously.
        """
        try:
            if not self._loop.is_running():
                self._loop.create_task(self._subscribe_to_subscriptions())
                self._loop.run_forever()
        except KeyboardInterrupt:
            print("Info: Interrupted, stopping listening to subscriptions")


    async def _subscribe_to_subscription(self, subscription_name: str, subscription_config: Dict[str, Callable] | Dict[str, bool]) -> None:
        """
        Subscribes to one subscription and calls handler.
        A new asynchronous task will be created to call the handler/callback function.

        :param subscription_name: Name of the subscription to listen to
        :param handler: Callback function for the subscription when a message is received
        """
        subscription_path = self.get_subscription_path(subscription_name)

        def callback(message: Message):

            if subscription_config['exactly_once_delivery']:
                ack_future = message.ack_with_response()

                def done_callback(future):
                    exception = future.exception()
                    if exception:
                        print("Error in handler:", exception)
                        ack_future.nack()
                    else:
                        ack_future.ack()
                future = asyncio.run_coroutine_threadsafe(
                    _handle_message(message, subscription_config['callback']),
                    self._loop
                )
                future.add_done_callback(done_callback)
            else:
                def done_callback(future):
                    exception = future.exception()
                    if exception:
                        print("Error in handler:", exception)
                        message.nack()
                    else:
                        message.ack()
                future = asyncio.run_coroutine_threadsafe(
                    _handle_message(message, subscription_config['callback']),
                    self._loop
                )
                future.add_done_callback(done_callback)


        streaming_pull_future = self._subscriber.subscribe(subscription_path, callback=callback)
        print(f"Info: Listening for messages on {subscription_name}")

        try:
            await asyncio.wrap_future(streaming_pull_future)
        except asyncio.CancelledError:
            print(f"Info: Subscription {subscription_name} stopped")
            streaming_pull_future.cancel()
        except Exception as error:
            print(f"Error: Something went wrong when listening to {subscription_name}: {error}")
        finally:
            streaming_pull_future.cancel()

    async def _subscribe_to_subscriptions(self) -> None:
        """
        Listens to all subscriptions that the subscriber currently has configured.
        Each subscription will be listened to in a new asyncio task.
        """
        tasks = [self._subscribe_to_subscription(subscription, subscription_config) for subscription, subscription_config in self._subscriptions.items()]
        await asyncio.gather(*tasks)
