from threading import Thread
from time import sleep

from python_publish_subscribe.config import Config

class PythonPublishSubscribe:
    def __init__(self, config=None):
        self.config = config or {}
        self.initialise()

        self.test_func_map = {}


    def initialise(self):
        print("initialise")

    def run(self):
        print("run")


    def add_subscription(self, callback, topic=None):
        if not topic:
            topic = callback.__name__
        topic_dict = {
            "topic": topic,
            "callback": callback
        }
        self.config.add_value_to_key(Config.ConfigKeys.SUBSCRIPTION_TOPICS, topic_dict)


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