import json
from typing import Optional, Any, Dict, List, Tuple

from google.api_core.retry import Retry
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.publisher.futures import Future

from python_publish_subscribe.config import Config
from google.api_core.exceptions import AlreadyExists, InvalidArgument, GoogleAPICallError, RetryError
import re


TOPIC_STRING_FORMAT = 'projects/{project_id}/topics/{topic_name}'


def convert_data_to_string(data: Any) -> str:
    """
    Converts given data to string.

    Trys to use json dumps so that the string is formatted in a json way,
    so it can handle objects better.
    If json dumps fails serialisation normal string casting is used.
    :param data: Data to convert.
    :return: converted data
    """
    if isinstance(data, str):
        return data

    try:
        return json.dumps(data)
    except (TypeError, OverflowError):
        return str(data)


class Publisher:
    def __init__(self, config: Config, timout: int=None):
        self._publisher = pubsub_v1.PublisherClient()
        self._config = config
        if timout:
            self._timout = timout
        else:
            self._timout = self._config.get('DEFAULT_TIMEOUT')

    @staticmethod
    def is_topic_topic_path(topic_name: str) -> bool:
        """
        Checks if a topic is just the topic name or the whole topic url.
        :param topic_name: Topic to check
        :return: if topic is the whole topic path
        """
        return True if re.match(r"projects/[a-zA-Z0-9_-]+/topics/[a-zA-Z0-9_-]+", topic_name) else False

    def build_topic(self, topic_name: str, project_id: str=None) -> str:
        """
        Builds and saves a topic that can be published too from the topic name.
        :param topic_name: Name of the topic or complete topic url
        :param project_id: Optional project id of the project to publish too, by default this is the project id if set by the config when initialised.
        :return: Whole topic string, for GCP it should look like, 'projects/<project_id>/topics/<topic>'
        """
        project_id = project_id or self._config.get(Config.ConfigKeys.PROJECT_ID.name)
        if self.is_topic_topic_path(topic_name):
            topic, topic_name = topic_name, topic_name.split('/')[-1]
        else:
            topic = TOPIC_STRING_FORMAT.format(project_id=project_id, topic_name=topic_name)
        self._config.add_value_to_key(Config.ConfigKeys.PUBLISH_TOPICS.name, {topic_name: topic})
        return topic

    def create_topic(self, topic_name: str) -> bool:
        """
        Creates a topic on the given topic.

        Errors are caught and only printed out.
        :param topic_name: Name of the topic, can either be the complete topic as required by gcp or just the topic name.
        :return: If topic was created or already exists.
        """
        topic = self.build_topic(topic_name)

        try:
            self._publisher.create_topic(name=topic)
            return True
        except AlreadyExists:
            print("Warning: Topic {topic} already exists".format(topic=topic_name))
            return True
        except Exception as error:
            print("Error: Something when wrong when creating topic {topic}: {error}".format(topic=topic_name, error=error))
            return False

    def get_topic(self, topic_name: str):
        """
        Gets both the topic path and name from the given topic.

        :param topic_name: Topic, can either be the complete url to the topic or just the topic name
        :return: [Topic, Topic Name]
        """
        if self.is_topic_topic_path(topic_name):
            topic, topic_name = topic_name, topic_name.split('/')[-1]
        else:
            publish_topics = self._config.get(Config.ConfigKeys.PUBLISH_TOPICS.name)
            if topic_name in publish_topics:
                topic = publish_topics.get(topic_name)
            else:
                print(
                    "Warning: topic may not have been created, try building the topic or passing though the whole topic")
                topic = topic_name
        return topic, topic_name


    def publish(
            self,
            topic_name: str,
            data: Any,
            attributes: Optional[Dict]=None,
            timeout: int=None,
            retry: Retry=None,
            topic: str=None,
            asynchronous: bool=False,
    ) -> Optional[str] | Future:
        """
        Publishes a message to a given topic.

        :param topic_name: Topic to publish to, can either be the complete url to the topic or just the topic name
        :param data: Data/message to send
        :param attributes: Optional custom attributes to add to the message
        :param timeout: Timeout for the request (optional)
        :param retry: What retry approach to take if a retry fails (optional)
        :param topic: Topic path to publish to (optional).
        Currently, topic path is still the preferred way to pass the topic.
        :param asynchronous: If the function should return the future of the message publishing or
         wait till it gets a result.
        :return: Result of the publishing, if successful, otherwise None.
        """

        data = convert_data_to_string(data)

        if not topic:
            topic, topic_name = self.get_topic(topic_name)

        timeout = timeout or self._timout

        if attributes:
            published = self._publisher.publish(topic, data.encode('utf-8'), timeout=timeout, retry=retry, **attributes)
        else:
            published = self._publisher.publish(topic, data.encode('utf-8'), timeout=timeout, retry=retry)

        if not asynchronous:
            try:
                return published.result()
            except InvalidArgument as error:
                print("Error: Unable to publish to {topic}: {error}".format(topic=topic_name, error=error))
                return None
            except TimeoutError as error:
                print("Error: Message Timed out while trying to send: {error}".format(error=error))
            except Exception as error:
                print("Error: Something when wrong: {error}".format(error=error))
                return None
        else:
            return published


    def publish_batch(
            self,
            topic_name,
            messages: List[Any],
            attributes: Optional[Dict]=None,
            timeout: int=None,
            retry: Retry=None
    ) -> list[tuple[Any, str | None, Exception | None]]:
        """
        Publishes a list of messages to a topic.

        :param topic_name: Topic to publish to, can either be the complete url to the topic or just the topic name
        :param messages: List of messages/data to send.
        :param attributes: Optional custom attributes to add to the message (optional)
        :param timeout: Timeout for the request (optional)
        :param retry: What retry approach to take if a retry fails (optional)
        :return: List of results of each message
        """

        full_topic, _ = self.get_topic(topic_name)

        timeout = timeout or self._timout

        paired_futures: List[Tuple[Any, Future]] = [
            (message, self.publish(topic_name, message, attributes, timeout, retry, full_topic, True))
            for message in messages
        ]

        results: List[Tuple[Any, Optional[str], Optional[Exception]]] = []
        for message, future in paired_futures:
            try:
                message_id = future.result(timeout=timeout)
                results.append((message, message_id, None))
            except Exception as error:
                results.append((message, None, error))
                print("Error: Something went wrong when publishing a message in a batch: {error}".format(error=error))

        return results