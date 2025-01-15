import json
from threading import Thread
from time import sleep
from typing import Any

from google.api_core.exceptions import InvalidArgument
from google.api_core.retry import Retry

from python_publish_subscribe.config import Config
from python_publish_subscribe.src.Publisher import Publisher

class PythonPublishSubscribe:
    config: Config

    def __init__(self, config=None):
        self.config = config or {}

        self.initialise()
        self.test_func_map = {}
        self.publisher = Publisher(self.config)


    def initialise(self):
        self.config = Config(self.config)


    def add_subscription(self, callback, topic=None):
        if not topic:
            topic = callback.__name__
        topic_dict = {
            "topic": topic,
            "callback": callback
        }
        # self.config.add_value_to_key(Config.ConfigKeys.SUBSCRIPTION_TOPICS, topic_dict)

    def publish(self, topic_name, timeout: int=None, retry: Retry=None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                message = func(*args, **kwargs)
                return self.publisher.publish(topic_name, message, timeout, retry)
            return wrapper
        return decorator


    """
    Used for testing to get a hand of and practice techniques
    """

    def test_decorators(self, test_fun):
        test_fun()

    def test_decorator_with_params(self, test_message):
        def decorator(test_fun):
            def wrapper(*args, **kwargs):
                print(test_message)
                return test_fun(*args, **kwargs)
            return wrapper
        return decorator

    def test_map_function(self, map_name):
        def decorator(test_func):
            self.test_func_map[map_name] = test_func
            return test_func
        return decorator

    def test_call_function(self, map_name, *args, **kwargs):
        if map_name in self.test_func_map:
            return self.test_func_map[map_name](*args, **kwargs)

    def test_run(self):
        """
        Not effiecent way of looping
        and this is not how the final implementation will look
        just doing it to work out how to call a function in a dict
        :return:
        """
        print("run here")
        def loop():
            while True:
                for map_name, function in self.test_func_map.items():
                    self.test_call_function(map_name)
                sleep(1)
        thread = Thread(target=loop)
        thread.start()