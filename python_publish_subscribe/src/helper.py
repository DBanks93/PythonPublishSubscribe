import re

from python_publish_subscribe.config import Config

TOPIC_STRING_FORMAT = 'projects/{project_id}/topics/{topic_name}'

def is_topic_topic_path(topic_name: str) -> bool:
    """
    Checks if a topic is just the topic name or the whole topic url.
    :param topic_name: Topic to check
    :return: if topic is the whole topic path
    """
    return True if re.match(r"projects/[a-zA-Z0-9_-]+/topics/[a-zA-Z0-9_-]+", topic_name) else False

def is_subscription_subscription_path(subscription_name: str) -> bool:
    """
    Checks if a subscription is just the subscription name or the whole subscription path.
    :param subscription_name: Subscription to check
    :return: if subscription is the whole subscription path
    """
    return True if re.match(r"projects/[a-zA-Z0-9_-]+/subscriptions/[a-zA-Z0-9_-]+/", subscription_name) else False

def build_and_save_topic_string(topic_name: str, project_id: str, config: Config) -> (str, str):
    """
    Builds a topic path and saves it to the config.
    For GCP the topic should like something like 'projects/<project_id>/topics/<topic>'

    :param topic_name: Name of the topic or complete topic url
    :param project_id: project id of the topic
    :param config: the config to save it to
    :return: Tuple of the whole topic path and the topic name
    """
    topic, topic_name = build_topic_string(topic_name, project_id)
    config.add_value_to_key(Config.ConfigKeys.PUBLISH_TOPICS.name, {topic_name: topic})
    return topic, topic_name

def build_topic_string(topic_name: str, project_id: str) -> (str, str):
    """
    Builds a topic path.
    For GCP the topic should like something like 'projects/<project_id>/topics/<topic>'

    :param topic_name: Name of the topic or complete topic url
    :param project_id: project id of the topic
    :param config: the config to save it to
    :return: Tuple of the whole topic path and the topic name
    """
    if is_topic_topic_path(topic_name):
        return topic_name, topic_name.split('/')[-1]
    else:
        topic = TOPIC_STRING_FORMAT.format(project_id=project_id, topic_name=topic_name)
    return topic, topic_name