from unittest.mock import patch

from python_publish_subscribe.src.helper import *

def test_checking_topic_path_is_topic():
    # Given
    topic = "projects/project_name/topics/topic_name"

    # When
    is_topic =  is_topic_topic_path(topic)

    # Then
    assert is_topic, "Expected the topic to be seen as a topic"

def test_checking_topic_path_is_not_topic():
    # Given
    fake_topic = "this is not a topic"

    # When
    is_topic = is_topic_topic_path(fake_topic)

    # Then
    assert not is_topic, "Expected the topic not to be seen as a topic"

@patch('python_publish_subscribe.src.helper.is_topic_topic_path')
def test_building_a_topic(mock_is_topic_topic_path):
    # Given
    topic_name = "test-topic"
    project_name = "test-project"

    # When
    mock_is_topic_topic_path.return_value = False
    topic, topic_name = build_topic_string(topic_name, project_name)

    # Then
    assert topic == "projects/test-project/topics/test-topic", "Expected the topic path to be built"
    assert topic_name == "test-topic", "Expected the topic name to be returned"

@patch('python_publish_subscribe.src.helper.is_topic_topic_path')
def test_building_a_topic_with_a_topic_path(mock_is_topic_topic_path):
    # Given
    topic_path = "projects/test-project/topics/test-topic"
    project_name = "test-project"

    # When
    mock_is_topic_topic_path.return_value = True
    topic, topic_name = build_topic_string(topic_path, project_name)

    # Then
    assert topic == "projects/test-project/topics/test-topic", "Expected the topic path to be returned"
    assert topic_name == "test-topic", "Expected the topic name to be returned"

@patch('python_publish_subscribe.src.helper.build_topic_string')
@patch('python_publish_subscribe.config.Config')
def test_building_and_saving_topic( mock_config, mock_build_topic_string):
    # Given
    topic_name = "test-topic"
    project_name = "test-project"

    # When
    mock_config = mock_config.return_value
    mock_build_topic_string.return_value = ("projects/test-project/topics/test-topic", topic_name)
    mock_config.add_value_to_key.return_value = {topic_name: "projects/test-project/topics/test-topic"}

    topic, topic_name = build_and_save_topic_string(topic_name, project_name, mock_config)

    # Then
    assert topic == "projects/test-project/topics/test-topic", "Expected the topic path to be returned"
    assert topic_name == "test-topic", "Expected the topic name to be returned"
