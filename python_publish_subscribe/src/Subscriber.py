import asyncio
import signal
import typing
from typing import Optional

from google.cloud import pubsub_v1
from google.api_core.exceptions import AlreadyExists
from google.auth.api_key import Credentials
from google.cloud.pubsub_v1.types import message
from google.pubsub_v1 import Subscription
from google.cloud.pubsub_v1.subscriber.message import Message

from python_publish_subscribe.config import Config
from python_publish_subscribe.src.Message import Message
from python_publish_subscribe.src.helper import build_and_save_topic_string, is_subscription_subscription_path

# TODO: Add support for credentials
# TODO: Add ability for other pubsub types (ONE_TIME_DELIVERY etc etc) and any other config settings
class Subscriber:
    def __init__(self, config: Config, credentials: Credentials=None):
        self._subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        self._config = config
        self._subscriptions = {}
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

    def add_subscription(self, subscription_name: str, callback: typing.Callable) -> None:
        """
        Adds a preconfigured subscription, and it's callback function to the configuration, such that
        when app.run() is called it can be subscribed too correctly.

        :param subscription_name: name of the subscription
        :param callback: callback function for the subscription when a message is received
        """
        self._subscriptions[subscription_name] = callback

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
            print("Error: Something when wrong when creating subscription {subscription}: {error}"
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

    def _handle_message(self, message, callback):
        callback(message)

    async def _subscribe_to_subscription(self, subscription_name: str, handler: typing.Callable) -> None:
        """
        Subscribes to one subscription and calls handler.
        A new asynchronous task will be created to call the handler/callback function.

        :param subscription_name: Name of the subscription to listen to
        :param handler: Callback function for the subscription when a message is received
        """
        subscription_path = self.get_subscription_path(subscription_name)

        def callback(message: Message):
            try:
                handler(message)
                message.ack()
            except Exception:
                message.nack()
            # self._handle_message(message, handler)
            # self._loop.create_task(self._handle_message(message, handler))


        streaming_pull_future = self._subscriber.subscribe(subscription_path, callback=callback)
        print(f"Info: Listening for messages on {subscription_name}")

        try:
            await asyncio.wrap_future(streaming_pull_future)
        except asyncio.CancelledError:
            print(f"Info: Subscription {subscription_name} stopped")
            streaming_pull_future.cancel()
        except Exception as error:
            print(f"Error: Something went wrong when listening to {subscription_path}: {error}")
        finally:
            streaming_pull_future.cancel()

    async def _subscribe_to_subscriptions(self) -> None:
        """
        Listens to all subscriptions that the subscriber currently has configured.
        Each subscription will be listened to in a new asyncio task.
        """
        tasks = [self._subscribe_to_subscription(subscription, handler) for subscription, handler in self._subscriptions.items()]

        await asyncio.gather(*tasks)

    # def subscribe(self, subscription_name, callback):
    #     subscription_path = self.get_subscription_path(subscription_name)
    #
    #     with self._subscriber:  # Manages the subscriber's lifecycle
    #         streaming_pull_future = self._subscriber.subscribe(subscription_path, callback=callback)
    #
    #         print(f"Info: Listening for messages on {subscription_path}")
    #
    #         try:
    #             # Block and keep the subscriber running
    #             streaming_pull_future.result()
    #         except KeyboardInterrupt:
    #             print(f"Subscription interrupted")
    #             streaming_pull_future.cancel()
    #             streaming_pull_future.result()
    #         except Exception as error:
    #             print(f"Error: Something went wrong when listing to subscriptions: {error}")
    #
    # def start_listening(self):
    #     with self._subscriber as subscriber:
