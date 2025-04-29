import json
from unittest.mock import MagicMock, patch

import pytest
from google.api_core.exceptions import AlreadyExists, InvalidArgument
from google.cloud.pubsub_v1.futures import Future

from python_publish_subscribe.src.Publisher import Publisher
from python_publish_subscribe.src.Publisher import convert_data_to_string
from python_publish_subscribe.config import Config

TEST_TOPIC_NAME = "test-topic"
TEST_TOPIC = "projects/project_name/topics/topic_name"

def test_create_topic(app):
    assert app.create_topic(TEST_TOPIC_NAME)

def test_converting_string():
    # Given
    data = "hello"

    # When
    converted_data = convert_data_to_string(data)

    # Then
    assert converted_data == data, "Expected converted data to be equal to data"

def test_converting_json():
    # Given
    data = {
        "int": 1,
        "str": "hello",
        "list": [1, 2, 3],
    }

    # When
    converted_data = convert_data_to_string(data)

    # Then
    assert json.dumps(data) == converted_data, "Expected converted data to be converted to json"

def test_convert_data_error():
    # Given
    data = 1
    with patch('json.dumps') as mock_dumps:
        mock_dumps.side_effect = TypeError()

    # When
        converted_data = convert_data_to_string(data)

    #Then
        assert converted_data == str(data), "Expected converted data to be converted to string"


def test_checking_topic_path_is_topic(app):
    # Given
    topic = "projects/project_name/topics/topic_name"

    # When
    is_topic = Publisher.is_topic_topic_path(topic)

    # Then
    assert is_topic, "Expected the topic to be seen as a topic"

def test_checking_topic_path_is_not_topic(app):
    # Given
    fake_topic = "this is not a topic"

    # When
    is_topic = Publisher.is_topic_topic_path(fake_topic)

    # Then
    assert not is_topic, "Expected the topic not to be seen as a topic"

def test_building_a_topic_with_just_topic_name(app):
    # Given
    topic_name = "test-topic"

    # When
    topic = app.publisher.build_topic(topic_name=topic_name)

    # Then
    assert topic == "projects/test-project/topics/test-topic", "Expected the topic path to be built"
    assert topic_name in app.config._config[app.config.ConfigKeys.PUBLISH_TOPICS.name], "Expected the name of the topic to be added to the config"
    assert topic in app.config._config[Config.ConfigKeys.PUBLISH_TOPICS.name][topic_name], "Expected the whole topic path to be added to the config"

def test_building_a_topic_with_just_topic_path(app):
    # Given
    topic_name = "test-topic"
    topic = f"projects/test-project/topics/{topic_name}"

    # When
    returned_topic = app.publisher.build_topic(topic_name=topic)

    # Then
    assert returned_topic == "projects/test-project/topics/test-topic", "Expected the topic path to be the same as input"
    assert topic_name in app.config._config[app.config.ConfigKeys.PUBLISH_TOPICS.name], "Expected the name of the topic to be added to the config"
    assert topic in app.config._config[Config.ConfigKeys.PUBLISH_TOPICS.name][topic_name], "Expected the whole topic path to be added to the config"

def test_building_a_topic_with_topic_name_and_project_id(app):
    # Given
    topic_name = "test-topic"

    # When
    topic = app.publisher.build_topic(topic_name=topic_name, project_id="new-test-project")

    # Then
    assert topic == "projects/new-test-project/topics/test-topic", "Expected the topic path to be built"
    assert topic_name in app.config._config[
        app.config.ConfigKeys.PUBLISH_TOPICS.name], "Expected the name of the topic to be added to the config"
    assert topic in app.config._config[Config.ConfigKeys.PUBLISH_TOPICS.name][
        topic_name], "Expected the whole topic path to be added to the config"

def test_building_a_topic_with_topic_path_and_project_id(app):
    # Given
    topic_name = "test-topic"
    project_id = "new-test-project"
    topic = f"projects/{project_id}/topics/{topic_name}"

    # When
    returned_topic = app.publisher.build_topic(topic_name=topic, project_id=project_id)

    # Then
    assert returned_topic == f"projects/{project_id}/topics/test-topic", "Expected the topic path to be the same as input"
    assert topic_name in app.config._config[
        app.config.ConfigKeys.PUBLISH_TOPICS.name], "Expected the name of the topic to be added to the config"
    assert topic in app.config._config[Config.ConfigKeys.PUBLISH_TOPICS.name][
        topic_name], "Expected the whole topic path to be added to the config"

def test_creating_topic(app, mock_publisher_client):
    # Given
    topic_name = "test-topic"
    mock_publisher_client.create_topic.return_value = None

    # When
    is_topic_created = app.publisher.create_topic(topic_name)

    # Then
    assert is_topic_created, "Expected the topic to be created"


def test_creating_topic_that_exists(app, mock_publisher_client, capfd):
    # Given
    topic_name = "test-topic"
    mock_publisher_client.create_topic.side_effect = AlreadyExists("Topic already exists")

    # When
    is_topic_created = app.publisher.create_topic(topic_name)

    # Then
    assert f"Warning: Topic {topic_name} already exists" in capfd.readouterr().out, "Expected a warning message"
    assert is_topic_created, "Expected the topic to be shown as created"


def test_error_when_creating_topic(app, mock_publisher_client, capfd):
    # Given
    topic_name = "test-topic"
    mock_publisher_client.create_topic.side_effect = ValueError("Some Error")

    # When
    is_topic_created = app.publisher.create_topic(topic_name)

    # Then
    assert f"Error: Something when wrong when creating topic {topic_name}: Some Error" in capfd.readouterr().out, "Expected an error message"
    assert not is_topic_created, "Expected the topic not to be created"

def test_getting_topic(app):
    # Given
    topic_name = "test-topic"
    topic = "projects/test-project/topics/test-topic"

    app.config._config[Config.ConfigKeys.PUBLISH_TOPICS.name][
        topic_name] = topic

    # Then
    found_topic, found_topic_name = app.publisher.get_topic(topic_name)

    # Then
    assert topic_name == found_topic_name, "Expected the topic name to be found"
    assert topic == found_topic, "Expected the topic to be found"


def test_getting_topic_with_whole_topic_path(app):
    # Given
    topic_name = "test-topic"
    topic = "projects/test-project/topics/test-topic"

    # Then
    found_topic, found_topic_name = app.publisher.get_topic(topic)

    # Then
    assert topic_name == found_topic_name, "Expected the topic name to be returned"
    assert topic == found_topic, "Expected the topic to be returned"

def test_getting_topic_that_does_not_exist(app, capfd):
    # Given
    topic_name = "non-existent-topic"

    # Then
    found_topic, found_topic_name = app.publisher.get_topic(topic_name)

    # Then
    assert "Warning: topic may not have been created, try building the topic or passing though the whole topic" in capfd.readouterr().out, "Expected a warning message"
    assert topic_name == found_topic_name, "Expected the topic name to be returned"
    assert topic_name == found_topic, "Expected the topic to be returned"

def test_publish_success(app, mock_publisher_client):
    # Given
    topic_name = "test-topic"
    data = "test-data"

    mock_future = MagicMock(spec=Future)
    mock_future.result.return_value = 'mocked_response'
    mock_publisher_client.publish.return_value = mock_future

    # When
    result = app.publisher.publish(topic_name, data)

    # Then
    assert result == 'mocked_response', "Expected the topic to be published"

def test_publish_invalid_arg_failure(app, mock_publisher_client, mock_get_topic, capfd):
    # Given
    topic_name = "test-topic"
    data = "test-data"

    mock_future = MagicMock()
    mock_future.result.side_effect = InvalidArgument("Some Error")
    mock_publisher_client.publish.return_value = mock_future

    # When
    result = app.publisher.publish(topic_name, data)

    # Then
    assert f"Error: Unable to publish to" in capfd.readouterr().out, "Expected an error message"
    assert result is None, "Expected nothing to be returned"

def test_publish_timeout_failure(app, mock_publisher_client, mock_get_topic, capfd):
    # Given
    topic_name = "test-topic"
    data = "test-data"

    mock_future = MagicMock(spec=Future)
    mock_future.result.side_effect = TimeoutError("Timed out")
    mock_publisher_client.publish.return_value = mock_future

    # When
    result = app.publisher.publish(topic_name, data)

    # Then
    assert f"Error: Message Timed out while trying to send: Timed out" in capfd.readouterr().out, "Expected an error message"
    assert result is None, "Expected nothing to be returned"

def test_error_when_publishing(app, mock_publisher_client, mock_get_topic, capfd):
    # Given
    topic_name = "test-topic"
    data = "test-data"

    mock_future = MagicMock(spec=Future)
    mock_future.result.side_effect = Exception("Some Error")
    mock_publisher_client.publish.return_value = mock_future

    # When
    result = app.publisher.publish(topic_name, data)

    # Then
    assert f"Error: Something when wrong: Some Error" in capfd.readouterr().out, "Expected an error message"
    assert result is None, "Expected nothing to be returned"

def test_publish_with_attributes(app, mock_publisher_client):
    # Given
    topic_name = "test-topic"
    data = "test-data"
    attributes = {"test": "attributes"}

    mock_future = MagicMock(spec=Future)
    mock_future.result.return_value = 'mocked_response'
    mock_publisher_client.publish.return_value = mock_future

    # When
    result = app.publisher.publish(topic_name, data, attributes=attributes)

    # Then
    assert result == 'mocked_response', "Expected the topic to be published"

def test_publish_with_async(app, mock_publisher_client):
    # Given
    topic_name = "test-topic"
    data = "test-data"

    mock_future = MagicMock(spec=Future)
    mock_future.result.return_value = 'mocked_response'
    mock_publisher_client.publish.return_value = mock_future

    # When
    future = app.publisher.publish(topic_name, data, asynchronous=True)

    # Then
    assert future.result() == 'mocked_response', "Expected the topic to be published"

def test_subscribe_wrapper_success(app):
    # Given
    subscription_name = "test-sub"

    with patch.object(app.subscriber, "create_subscription", return_value='mocked_create_response') as mock_create_subscription:
        with patch.object(app.subscriber, "add_subscription", return_value='mocked_add_response') as mock_add_subscription:
            @app.subscribe(subscription_name)
            def subscribe(message):
                return message

        # When
        # Then
            mock_create_subscription.assert_not_called(), "A subscription was not created"
            mock_add_subscription.assert_called_once_with(subscription_name, subscribe), "Subscription should've been added"

def test_crate_subscribe_wrapper_success(app):
    # Given
    subscription_name = "test-sub"
    topic_name = "test-topic"

    with patch.object(app.subscriber, "create_subscription", return_value='mocked_create_response') as mock_create_subscription:
        with patch.object(app.subscriber, "add_subscription", return_value='mocked_add_response') as mock_add_subscription:
            @app.subscribe(subscription_name, topic_name)
            def subscribe(message):
                return message

        # When
        # Then
            mock_create_subscription.assert_called_once_with(subscription_name, topic_name), "A subscription was created"
            mock_add_subscription.assert_called_once_with(subscription_name, subscribe), "Subscription should've been added"


def test_publish_batch_success(app, mock_publisher_client, mock_get_topic):
    # Given
    topic_name = "test-topic"
    data = [f"test data {i}" for i in range(10)]
    mock_future = MagicMock(spec=Future)
    mock_future.result.return_value = 'mocked_response'

    with patch.object(app.publisher, 'publish') as mock_publish:
        mock_publish.side_effect = [mock_future for _ in range(len(data))]

        # When
        results = app.publisher.publish_batch(topic_name, data)

        # Then
        assert len(results) == len(data), "Expected the same number of results as messages"

        for i in range(len(data)):
            assert results[i][0] == data[i], "first element is the original message"
            assert results[i][1] == 'mocked_response', "second element is the returned message_id"
            assert results[i][2] is None, "no error on success"


def test_publish_batch_failure(app, mock_publisher_client, mock_get_topic, capfd):
    # Given
    topic_name = "test-topic"
    data = [f"test data {i}" for i in range(10)]
    mock_future = MagicMock(spec=Future)
    mock_future.result.side_effect = TimeoutError("Timed out")

    with patch.object(app.publisher, 'publish') as mock_publish:
        mock_publish.side_effect = [mock_future for _ in range(len(data))]

        # When
        results = app.publisher.publish_batch(topic_name, data)

        # Then
        assert len(results) == len(data), "Expected the same number of results as messages"

        captured_output = capfd.readouterr().out
        assert "Error: Something went wrong when publishing a message in a batch: Timed out" in captured_output, "Expected a warning message to be printed"

        for i in range(len(results)):
            assert results[i][0] == data[i], f"Expected message {i} to match input data"
            assert results[i][1] is None, f"Expected second result to be None for message {i}"
            assert isinstance(results[i][2], TimeoutError), f"Expected TimeoutError for message {i}"

def test_config_timeout(monkeypatch):
    import google.cloud.pubsub_v1 as pubsub
    from python_publish_subscribe.src import Publisher
    monkeypatch.setattr(pubsub,'PublisherClient', lambda *args, **kwargs: None)

    publisher = Publisher.Publisher(Config(), timout=100)

    assert publisher._timout == 100, "Timeout should've been configured"