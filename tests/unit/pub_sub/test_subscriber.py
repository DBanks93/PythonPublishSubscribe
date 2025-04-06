import asyncio
import unittest
from google.cloud.pubsub_v1.futures import Future
from types import NoneType
from unittest import mock
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from google.api_core.exceptions import AlreadyExists
from google.cloud.pubsub_v1.subscriber.futures import StreamingPullFuture
from google.pubsub_v1 import types
from google.cloud.pubsub_v1.subscriber.message import Message



def test_getting_subscription_path(app, mock_subscriber_client):
    # Given
    subscription_name = "test_subscription"
    mock_subscriber_client.subscription_path.return_value = f"test_project/subscriptions/{subscription_name}"

    # When
    subscription_path = app.subscriber.get_subscription_path(subscription_name)

    # Then
    assert subscription_path == f"test_project/subscriptions/{subscription_name}"

def test_get_existing_subscription_path(app):
    # Given
    subscription_name = "test_subscription"
    subscription_map = {subscription_name: f"test_project/subscriptions/{subscription_name}"}
    app.subscriber._config.add_value_to_key(app.config.ConfigKeys.SUBSCRIPTION_TOPICS.name, subscription_map)

    # When
    subscription_path = app.subscriber.get_subscription_path(subscription_name)

    # Then
    assert subscription_path == f"test_project/subscriptions/{subscription_name}"

def test_get_subscription_path_with_existing_path(app):
    # Given
    subscription_path = f"projects/test_project/subscriptions/test_subscription"
    # When
    returned_subscription_path = app.subscriber.get_subscription_path(subscription_path)

    # Then
    assert returned_subscription_path == subscription_path

def test_adding_subscription(app):
    # Given
    def callback():
        return True

    subscription_name = "test_subscription"

    # When
    app.subscriber.add_subscription(subscription_name, callback)

    # Then
    assert app.subscriber._subscriptions[subscription_name] == {'callback': callback, 'exactly_once_delivery': False}
    assert app.subscriber._subscriptions[subscription_name]['callback']

def test_adding_subscription_with_exactly_once_delivery(app):
    # Given
    def callback():
        return True

    subscription_name = "test_subscription"

    # When
    app.subscriber.add_subscription(subscription_name, callback, exactly_once_delivery=True)

    # Then
    assert app.subscriber._subscriptions[subscription_name] == {'callback': callback, 'exactly_once_delivery': True}
    assert app.subscriber._subscriptions[subscription_name]['callback']

def test_create_subscription(app, mock_subscriber_client):
    # Given
    subscription_path = f"projects/test_project/subscriptions/test_subscription"
    topic = "test_topic"

    mock_subscriber_client.subscription_path.return_value = subscription_path
    mock_subscription = MagicMock(spec=types.Subscription)
    mock_subscriber_client.create_subscription.return_value = mock_subscription

    # When
    subscription = app.subscriber.create_subscription(subscription_path, topic)

    # Then
    assert subscription == mock_subscription, "Expect a subscription to be returned"
    assert mock_subscriber_client.create_subscription.call_count == 1, "Expect google's create subscription call to create a subscription"

def test_create_existing_subscription(app, mock_subscriber_client, capfd):
    # Given
    subscription_path = f"projects/test_project/subscriptions/test_subscription"
    topic = "test_topic"

    mock_subscriber_client.subscription_path.return_value = subscription_path
    mock_subscriber_client.create_subscription.side_effect = AlreadyExists("Topic already exists")
    mock_subscription = MagicMock(spec=types.Subscription)
    mock_subscriber_client.get_subscription.return_value = mock_subscription

    # When
    subscription = app.subscriber.create_subscription(subscription_path, topic)

    # Then
    assert mock_subscriber_client.create_subscription.call_count == 1, "Expect google pub/sub client to try and create a subscription"
    assert subscription == mock_subscription, "Expect a subscription to be returned"
    assert f"Warning: Subscription {subscription_path} already exists" in capfd.readouterr().out, "Expect a warning message to be printed"

def test_error_when_creating_subscription(app, mock_subscriber_client, capfd):
    # Given
    subscription_path = f"projects/test_project/subscriptions/test_subscription"
    topic = "test_topic"

    mock_subscriber_client.subscription_path.return_value = subscription_path
    mock_subscriber_client.create_subscription.side_effect = ValueError("Some Error")

    # When
    subscription = app.subscriber.create_subscription(subscription_path, topic)

    # Then
    assert mock_subscriber_client.create_subscription.call_count == 1, "Expect google pub/sub client to try and create a subscription"
    assert subscription is None, "Expect none subscription to be returned"
    assert f"Error: Something went wrong when creating subscription {subscription_path}: Some Error" in capfd.readouterr().out, "Expect an error message to be printed"

def test_message_handling(app):
    # Given
    message = "test-message"

    def callback(given_message):
        # Then
        assert True, "Expect the callback function to be called"
        assert given_message == message, f"Expect {message} to be passed through the callback"

    # When
    app.subscriber._handle_message(message, callback)

pytest_plugins = ('pytest_asyncio',)

@pytest.mark.asyncio
async def test_subscribe_to_subscriptions(app):
    # Given
    app.subscriber._subscriptions = {'subscription': {'foo': 'bar'}}

    with patch.object(app.subscriber, '_subscribe_to_subscription', return_value=None) as mock_subscribe_to_subscription:
        # When
        await app.subscriber._subscribe_to_subscriptions()

        # Then
        mock_subscribe_to_subscription.assert_called_once_with(
            "subscription",
            {'foo': 'bar'},
        )


@pytest.mark.asyncio
async def test_subscribe_to_subscription_success(app, mock_subscriber_client):
    mock_streaming_pull_future = MagicMock(spec=StreamingPullFuture)

    mock_streaming_pull_future.result.return_value = "mocked_result"
    mock_streaming_pull_future.done.return_value = True
    mock_streaming_pull_future.add_done_callback = MagicMock()

    mock_subscriber_client.return_value.subscribe.return_value = mock_streaming_pull_future

    mock_message = MagicMock(spec=Message)
    mock_message.ack = MagicMock()
    mock_message.nack = MagicMock()
    mock_message.ack_with_response = MagicMock(return_value=MagicMock())

    mock_callback = MagicMock()

    subscription_config = {
        'callback': mock_callback,
        'exactly_once_delivery': False
    }

    await app.subscriber._subscribe_to_subscription('test-subscription', subscription_config)

    mock_subscriber_client.return_value.subscribe.assert_called_with("mocked_subscription_path", callback=MagicMock())

    callback = mock_subscriber_client.return_value.subscribe.call_args[1]['callback']
    await callback(mock_message)

    mock_callback.assert_called_with(mock_message)

    mock_message.ack.assert_called_once()


@pytest.mark.asyncio
async def test_subscribe_to_subscription_cancel_error(app, mock_subscriber_client, capfd):
    # Given
    mock_callback = MagicMock()

    subscription_config = {
        'callback': mock_callback,
        'exactly_once_delivery': False
    }

    with patch('asyncio.wrap_future') as mock_asyncio_wrapper:
        mock_asyncio_wrapper.side_effect = asyncio.CancelledError("Error")

        # Then
        await app.subscriber._subscribe_to_subscription('test-subscription', subscription_config)


        assert f"Info: Subscription test-subscription stopped" in capfd.readouterr().out, "Expect an info message to be printed"


@pytest.mark.asyncio
async def test_subscribe_to_subscription_exception(app, mock_subscriber_client, capfd):
    # Given
    mock_callback = MagicMock()

    subscription_config = {
        'callback': mock_callback,
        'exactly_once_delivery': False
    }

    with patch('asyncio.wrap_future') as mock_asyncio_wrapper:
        mock_asyncio_wrapper.side_effect = Exception("Some Error")

        # Then
        await app.subscriber._subscribe_to_subscription('test-subscription', subscription_config)

        assert f"Error: Something went wrong when listening to test-subscription: Some Error" in capfd.readouterr().out, "Expect an error message to be printed"




# @pytest.mark.asyncio
# async def test_start_subscription_tasks(app):
#     # Given
#     with patch.object(app.subscriber, '_loop', autospec=True) as mock_loop:
#         with patch.object(app.subscriber, '_subscribe_to_subscriptions', new_callable=AsyncMock) as mock_subscribe_to_subscriptions:
#
#             mock_loop.is_running.return_value = False  # Simulate that the loop is not running
#
#             # When
#             app.subscriber.start_subscription_tasks()
#
#             # Then
#             mock_loop.create_task.assert_called_once_with(mock_subscribe_to_subscriptions())
#             mock_loop.run_forever.assert_called_once()

@pytest.fixture
def mock_loop():
    # Create a mock for the event loop
    mock_loop = mock.Mock()
    mock_loop.is_running.return_value = False  # Mock is_running() to return False
    return mock_loop

@pytest.mark.asyncio
async def test_start_no_running_loop(app, mock_loop):
    app.subscriber._loop = mock_loop

    # Test that the loop's task is created and run_forever() is called when the loop is not running
    await app.subscriber.start_subscription_tasks()

    # Check that create_task was called on the loop
    mock_loop.create_task.assert_called_once_with(app.subscriber._subscribe_to_subscriptions())

    # Check that run_forever was called on the loop
    mock_loop.run_forever.assert_called_once()

@pytest.mark.asyncio
async def test_start_with_running_loop(app, mock_loop):
    # Simulate the loop being already running
    mock_loop.is_running.return_value = True

    # Test that neither create_task nor run_forever is called when the loop is running
    await app.start_subscription_tasks()

    # Verify create_task and run_forever were not called
    mock_loop.create_task.assert_not_called()
    mock_loop.run_forever.assert_not_called()

@pytest.mark.asyncio
async def test_start_keyboard_interrupt_handling(your_instance, mock_loop):
    # Simulate a KeyboardInterrupt during the start method
    with mock.patch('builtins.print') as mock_print:
        # Simulate the exception being raised during start
        mock_loop.is_running.side_effect = KeyboardInterrupt
        await app.subscriber.start_subscription_tasks()

        # Ensure print is called with the expected message
        mock_print.assert_called_once_with("Info: Interrupted, stopping  listening to subscriptions")