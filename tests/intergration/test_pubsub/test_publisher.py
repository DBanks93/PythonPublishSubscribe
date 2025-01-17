import pytest


def test_create_topic(app, capfd):
    # Given
    topic_name = "test-topic"

    # When
    is_topic_created = app.publisher.create_topic(topic_name)

    # Then
    assert is_topic_created
    assert capfd.readouterr().out is '', "Expected no error/warnings"


def test_creating_existing_topic(app, capfd):
    # Given
    topic_name = "test-topic"

    # When
    is_topic_created = app.publisher.create_topic(topic_name)

    # Then
    assert f"Warning: Topic {topic_name} already exists" in capfd.readouterr().out, "Expected a warning message"
    assert is_topic_created, "Expected the topic to be shown as created"


def test_publish_success(app):
    # Given
    topic_name = "test-topic"
    message = "test-data"

    # When
    app.publisher.create_topic(topic_name)

    @app.publish(topic_name)
    def publish(data):
        return data

    message_id = publish(message)

    assert app.config.ConfigKeys

    # Then
    assert message_id, "Expected the message to be published"
