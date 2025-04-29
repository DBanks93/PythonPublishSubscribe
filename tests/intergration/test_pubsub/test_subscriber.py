import asyncio
from asyncio import wrap_future

import pytest
from google.cloud import pubsub_v1

from python_publish_subscribe.src.db.DatabaseHelper import DatabaseHelper

TOPIC_NAME = "test_subscription_topic"
SUBSCRIPTION_NAME = "test_subscription"

def test_create_subscription(app, capfd):
    # Given

    # When
    app.create_topic(TOPIC_NAME)
    subscription = app.create_subscription(SUBSCRIPTION_NAME, TOPIC_NAME)

    # Then
    assert subscription.name == f"projects/test-project/subscriptions/{SUBSCRIPTION_NAME}", "Expected subscription name to be 'projects/test-project/subscriptions/name'"
    assert capfd.readouterr().out is '', "Expected no error/warnings"

def test_subscription_annotation(app):
    mock_message = "Message"

    # Given When
    @app.subscribe(SUBSCRIPTION_NAME)
    def callback(message):
        print(message.data)

    # Then
    assert app.subscriber._subscriptions[SUBSCRIPTION_NAME]['callback'] == callback, "Expected callback to be mapped to subscription"
    assert app.subscriber._subscriptions[SUBSCRIPTION_NAME]['exactly_once_delivery'] == False, "Expected exactly_once_delivery to be set"

@pytest.mark.asyncio
async def test_subscribe_decorator_integration(app):
    publisher = pubsub_v1.PublisherClient()
    topic_id   = "int-topic"
    topic_path = publisher.topic_path(app.config.get("PROJECT_ID"), topic_id)
    publisher.create_topic(name=topic_path)

    seen = []

    @app.subscribe("int-sub", topic_name=topic_id)
    def handler(msg, session=None):
        seen.append(msg.data.decode("utf-8"))

    app.subscriber._loop = asyncio.get_event_loop()
    subscription_config = app.subscriber._subscriptions["int-sub"]
    task = asyncio.create_task(
        app.subscriber._subscribe_to_subscription("int-sub", subscription_config)
    )

    await asyncio.sleep(1)

    publish_future = publisher.publish(topic_path, b"hello world")
    await wrap_future(publish_future)  # ensure it’s sent

    for _ in range(10):
        if seen:
            break
        await asyncio.sleep(0.2)
    else:
        pytest.fail("Timed out waiting for message")

    assert seen == ["hello world"]

    task.cancel()
    # with pytest.raises(asyncio.CancelledError):
    #     await task

@pytest.mark.asyncio
async def test_subscribe_decorator_async_integration(app):
    publisher = pubsub_v1.PublisherClient()
    topic_id   = "int-topic"
    topic_path = publisher.topic_path(app.config.get("PROJECT_ID"), topic_id)

    seen = []

    @app.subscribe("int-sub")
    async def handler(msg):
        seen.append(msg.data.decode("utf-8"))

    app.subscriber._loop = asyncio.get_event_loop()
    subscription_config = app.subscriber._subscriptions["int-sub"]
    task = asyncio.create_task(
        app.subscriber._subscribe_to_subscription("int-sub", subscription_config)
    )

    await asyncio.sleep(1)

    publish_future = publisher.publish(topic_path, b"hello world")
    await wrap_future(publish_future)  # ensure it’s sent

    for _ in range(10):
        if seen:
            break
        await asyncio.sleep(0.2)
    else:
        pytest.fail("Timed out waiting for message")

    assert seen == ["hello world"]

    task.cancel()

@pytest.mark.asyncio
async def test_subscribe_decorator_async_integration(app):
    publisher = pubsub_v1.PublisherClient()
    topic_id   = "int-topic"
    topic_path = publisher.topic_path(app.config.get("PROJECT_ID"), topic_id)

    seen = []

    @app.subscribe("int-sub")
    async def handler(msg):
        seen.append(msg.data.decode("utf-8"))

    app.subscriber._loop = asyncio.get_event_loop()
    subscription_config = app.subscriber._subscriptions["int-sub"]
    task = asyncio.create_task(
        app.subscriber._subscribe_to_subscription("int-sub", subscription_config)
    )

    await asyncio.sleep(1)

    publish_future = publisher.publish(topic_path, b"hello world")
    await wrap_future(publish_future)  # ensure it’s sent

    for _ in range(10):
        if seen:
            break
        await asyncio.sleep(0.2)
    else:
        pytest.fail("Timed out waiting for message")

    assert seen == ["hello world"]

    task.cancel()

@pytest.mark.asyncio
async def test_subscribe_decorator_async_database_integration(app):
    publisher = pubsub_v1.PublisherClient()
    topic_id   = "int-topic"
    topic_path = publisher.topic_path(app.config.get("PROJECT_ID"), topic_id)

    seen = []

    @app.subscribe("int-sub")
    async def handler(msg, session):
        seen.append(msg.data.decode("utf-8"))

    app.subscriber._loop = asyncio.get_event_loop()
    subscription_config = app.subscriber._subscriptions["int-sub"]
    task = asyncio.create_task(
        app.subscriber._subscribe_to_subscription("int-sub", subscription_config)
    )

    await asyncio.sleep(1)

    publish_future = publisher.publish(topic_path, b"hello world")
    await wrap_future(publish_future)  # ensure it’s sent

    for _ in range(10):
        if seen:
            break
        await asyncio.sleep(0.2)
    else:
        pytest.fail("Timed out waiting for message")

    assert seen == ["hello world"]

    task.cancel()