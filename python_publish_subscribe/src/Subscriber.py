from google import pubsub_v1
from google.auth.api_key import Credentials

from python_publish_subscribe.config import Config


class Subscriber:
    def __init__(self, config: Config, credentials: Credentials=None):
        self._subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        self._config = config


    # def add_subscription(self, callback, subscription_name, topic_name):
    #
    #
    # def start_listening(self):
    #     with self._subscriber as subscriber:
