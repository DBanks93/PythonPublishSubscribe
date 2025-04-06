import asyncio
import json
from threading import Thread
from time import sleep
from typing import Any, Optional

from google.api_core.exceptions import InvalidArgument
from google.api_core.retry import Retry
from google.pubsub_v1 import Subscription

from python_publish_subscribe.config import Config
from python_publish_subscribe.src.Publisher import Publisher
from python_publish_subscribe.src.Subscriber import Subscriber

class PythonPublishSubscribe:
    config: Config

    def __init__(self, config=None):
        self.config = config or {}

        self.initialise()
        self.test_func_map = {}
        self.publisher = Publisher(self.config)
        self.subscriber = Subscriber(self.config)


    def initialise(self):
        self.config = Config(self.config)

    def publish(self, topic_name, timeout: int=None, retry: Retry=None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                message = func(*args, **kwargs)
                return self.publisher.publish(topic_name, message, timeout, retry)
            return wrapper
        return decorator

    def create_topic(self, topic_name: str) -> bool:
        """
        Creates a topic on the given topic.

        Errors are caught and only printed out.
        :param topic_name: Name of the topic, can either be the complete topic as required by gcp or just the topic name.
        :return: If topic was created or already exists.
        """
        return self.publisher.create_topic(topic_name)

    def create_subscription(self, subscription_name: str, topic: str, create_topic: bool=False) -> Optional[Subscription]:
        """
        Creates a subscription on the given topic.

        :param topic:
        :param subscription_name:
        :param create_topic:
        :return: Subscription if created or already exists.
        """
        if create_topic:
            has_topic_been_created = self.publisher.create_topic(topic)
            if not has_topic_been_created:
                return None
        return self.subscriber.create_subscription(subscription_name, topic)

    def subscribe(self, subscription_name: str, topic_name: str=None):
        def decorator(func):
            if topic_name is not None:
                self.subscriber.create_subscription(subscription_name, topic_name)
            self.subscriber.add_subscription(subscription_name, func)
            return func
        return decorator

    def run(self):
        self.subscriber.start_subscription_tasks()