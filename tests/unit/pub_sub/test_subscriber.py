import asyncio
import inspect
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from google.api_core.exceptions import AlreadyExists
from google.pubsub_v1.types import Subscription
from google.cloud.pubsub_v1.subscriber.message import Message

from python_publish_subscribe.src.Subscriber import Subscriber, _handle_message
from python_publish_subscribe.src.db.DatabaseHelper import DatabaseHelper
from python_publish_subscribe.config import Config

pytest_plugins = ("pytest_asyncio",)

def test_create_subscription(app):
    assert app.create_subscription("test-subscription", "test-topic")

def test_create_subscription_with_topic_not_creating(app):
    with patch.object(app.publisher, "create_topic", return_value=False) as mock_create_topic:
        assert not app.create_subscription("test-subscription", "test-topic", create_topic=True)

def test_app_run(app):
    # Given
    with patch.object(app.subscriber, "start_subscription_tasks", ) as mock_run:
        # When
        app.run()

        #Then
        mock_run.assert_called_once()

def test_get_subscription_path_full_path(app):
    full = "projects/test_project/subscriptions/foo"
    with patch("python_publish_subscribe.src.Subscriber.is_subscription_subscription_path", return_value=True):
        assert app.subscriber.get_subscription_path(full) == full


def test_get_subscription_path_from_config(app):
    key = Config.ConfigKeys.SUBSCRIPTION_TOPICS.name
    name = "my_sub"
    path = f"projects/test_project/subscriptions/{name}"
    app.config.add_value_to_key(key, {name: path})
    with patch("python_publish_subscribe.src.Subscriber.is_subscription_subscription_path", return_value=False):
        assert app.subscriber.get_subscription_path(name) == path


def test_get_subscription_path_falls_back_to_client(app, mock_subscriber_client):
    with patch("python_publish_subscribe.src.Subscriber.is_subscription_subscription_path", return_value=False):
        result = app.subscriber.get_subscription_path("new_sub")
    assert result == mock_subscriber_client.subscription_path.return_value
    mock_subscriber_client.subscription_path.assert_called_once_with(
        app.config.get("PROJECT_ID"), "new_sub"
    )


def test_add_subscription_registers_callback(app):
    def cb(msg):
        pass

    app.subscriber.add_subscription("s1", cb, exactly_once_delivery=True)
    entry = app.subscriber._subscriptions["s1"]
    assert entry["callback"] is cb
    assert entry["exactly_once_delivery"] is True


def test_create_subscription_success(app, mock_subscriber_client, monkeypatch):
    name = "sub1"
    path = f"projects/test_project/subscriptions/{name}"
    topic_in = "topic1"
    full_topic = f"projects/test_project/topics/{topic_in}"

    real_get = app.config.get
    def fake_get(key):
        if key == Config.ConfigKeys.PROJECT_ID.name:
            return "test_project"
        return real_get(key)
    monkeypatch.setattr(app.config, "get", fake_get)

    monkeypatch.setattr(
        "python_publish_subscribe.src.Subscriber.build_and_save_topic_string",
        lambda t, p, c: (full_topic, topic_in),
    )
    mock_sub = MagicMock(spec=Subscription)
    mock_subscriber_client.create_subscription.return_value = mock_sub
    mock_subscriber_client.subscription_path.return_value = path

    sub = app.subscriber.create_subscription(name, topic_in)

    assert sub is mock_sub
    mock_subscriber_client.create_subscription.assert_called_once_with(
        name=path, topic=full_topic
    )
    stored = app.config.get(Config.ConfigKeys.SUBSCRIPTION_TOPICS.name)
    assert stored == {name: path}


def test_create_subscription_already_exists(app, mock_subscriber_client, capfd, monkeypatch):
    name = "sub2"
    path = f"projects/test_project/subscriptions/{name}"
    topic_in = "topic2"
    full_topic = f"projects/test_project/topics/{topic_in}"

    real_get = app.config.get
    def fake_get(key):
        if key == Config.ConfigKeys.PROJECT_ID.name:
            return "test_project"
        return real_get(key)
    monkeypatch.setattr(app.config, "get", fake_get)

    monkeypatch.setattr(
        "python_publish_subscribe.src.Subscriber.build_and_save_topic_string",
        lambda t, p, c: (full_topic, topic_in),
    )
    mock_subscriber_client.subscription_path.return_value = path
    mock_subscriber_client.create_subscription.side_effect = AlreadyExists("exists")
    got = MagicMock(spec=Subscription)
    mock_subscriber_client.get_subscription.return_value = got

    sub = app.subscriber.create_subscription(name, topic_in)

    assert sub is got
    assert f"Warning: Subscription {name} already exists" in capfd.readouterr().out
    mock_subscriber_client.get_subscription.assert_called_once_with({"subscription": path})


def test_create_subscription_error(app, mock_subscriber_client, capfd, monkeypatch):
    name = "sub3"
    path = f"projects/test_project/subscriptions/{name}"
    topic_in = "topic3"
    full_topic = f"projects/test_project/topics/{topic_in}"

    real_get = app.config.get
    def fake_get(key):
        if key == Config.ConfigKeys.PROJECT_ID.name:
            return "test_project"
        return real_get(key)
    monkeypatch.setattr(app.config, "get", fake_get)

    monkeypatch.setattr(
        "python_publish_subscribe.src.Subscriber.build_and_save_topic_string",
        lambda t, p, c: (full_topic, topic_in),
    )
    mock_subscriber_client.subscription_path.return_value = path
    mock_subscriber_client.create_subscription.side_effect = ValueError("boom!")

    sub = app.subscriber.create_subscription(name, topic_in)
    assert sub is None
    assert f"Error: Something went wrong when creating subscription {path}: boom!" in capfd.readouterr().out


@pytest.mark.asyncio
async def test_handle_message_async_without_session(monkeypatch):
    cb = AsyncMock()
    monkeypatch.setattr(DatabaseHelper, "is_setup", lambda: False)

    msg = MagicMock()
    await _handle_message(msg, cb)
    cb.assert_awaited_once_with(msg)



@pytest.mark.asyncio
async def test_handle_message_async_with_session(monkeypatch):
    async def real_cb(message, session):
        return True

    monkeypatch.setattr(DatabaseHelper, "is_setup", lambda: True)
    monkeypatch.setattr(DatabaseHelper, "is_async", lambda: True)
    fake_sess = AsyncMock()

    class CM:
        async def __aenter__(self): return fake_sess
        async def __aexit__(self, *args): pass

    monkeypatch.setattr(DatabaseHelper, "create_async_session", lambda: CM())

    await _handle_message(MagicMock(), real_cb)
    fake_sess.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_message_async_callback_false_raises(monkeypatch):
    async def real_cb(message, session):
        return False

    monkeypatch.setattr(DatabaseHelper, "is_setup", lambda: True)
    monkeypatch.setattr(DatabaseHelper, "is_async", lambda: True)
    fake_sess = AsyncMock()

    class CM:
        async def __aenter__(self): return fake_sess
        async def __aexit__(self, *args): pass

    monkeypatch.setattr(DatabaseHelper, "create_async_session", lambda: CM())

    with pytest.raises(ValueError):
        await _handle_message(MagicMock(), real_cb)
    fake_sess.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_message_async_with_sync_db_error(monkeypatch):
    async def real_cb(message, session):
        return True

    monkeypatch.setattr(DatabaseHelper, "is_setup", lambda: True)
    monkeypatch.setattr(DatabaseHelper, "is_async", lambda: False)

    with pytest.raises(RuntimeError):
        await _handle_message(MagicMock(), real_cb)


@pytest.mark.asyncio
async def test_handle_message_sync_without_session(monkeypatch):
    calls = []
    def cb(msg):
        calls.append(msg)

    monkeypatch.setattr(DatabaseHelper, "is_setup", lambda: False)
    msg = MagicMock()
    await _handle_message(msg, cb)
    assert calls == [msg]


@pytest.mark.asyncio
async def test_handle_message_sync_with_session(monkeypatch):
    calls = []
    def cb(msg, session):
        calls.append((msg, session))

    monkeypatch.setattr(DatabaseHelper, "is_setup", lambda: True)
    monkeypatch.setattr(DatabaseHelper, "is_async", False)
    fake_sess = MagicMock()
    monkeypatch.setattr(DatabaseHelper, "create_session", lambda: fake_sess)

    msg = MagicMock()
    await _handle_message(msg, cb)
    assert calls == [(msg, fake_sess)]
    fake_sess.commit.assert_called_once()
    fake_sess.close.assert_called_once()


@pytest.mark.asyncio
async def test_handle_message_sync_rollback_on_error(monkeypatch):
    def cb(msg, session):
        raise RuntimeError("oops")

    monkeypatch.setattr(DatabaseHelper, "is_setup", lambda: True)
    monkeypatch.setattr(DatabaseHelper, "is_async", False)
    fake_sess = MagicMock()
    monkeypatch.setattr(DatabaseHelper, "create_session", lambda: fake_sess)

    with pytest.raises(RuntimeError):
        await _handle_message(MagicMock(), cb)
    fake_sess.rollback.assert_called_once()
    fake_sess.close.assert_called_once()


@pytest.mark.asyncio
async def test_subscribe_to_subscriptions_invokes_each(app):
    calls = []
    subs = {
        "a": {"callback": lambda x: x, "exactly_once_delivery": False},
        "b": {"callback": lambda x: x, "exactly_once_delivery": True},
    }
    app.subscriber._subscriptions = subs

    async def fake_subscribe(name, cfg):
        calls.append((name, cfg))

    with patch.object(app.subscriber, "_subscribe_to_subscription", new=fake_subscribe):
        await app.subscriber._subscribe_to_subscriptions()

    assert len(calls) == 2
    assert ("a", subs["a"]) in calls
    assert ("b", subs["b"]) in calls


@pytest.mark.asyncio
async def test_subscribe_to_subscription_simple_ack(app, mock_subscriber_client, monkeypatch):
    name = "mysub"
    cfg = {"callback": MagicMock(), "exactly_once_delivery": False}
    path = f"projects/test_project/subscriptions/{name}"

    monkeypatch.setattr(app.subscriber, "get_subscription_path", lambda n: path)

    monkeypatch.setattr(asyncio, "wrap_future", lambda fut: (_ for _ in ()).throw(asyncio.CancelledError()))

    def fake_run(coro, loop):
        try:
            coro.close()
        except Exception:
            pass
        class DummyFuture:
            def add_done_callback(self, cb):
                class F:
                    def exception(self): return None
                cb(F())
        return DummyFuture()
    monkeypatch.setattr(asyncio, "run_coroutine_threadsafe", fake_run)

    await app.subscriber._subscribe_to_subscription(name, cfg)

    called_args = mock_subscriber_client.subscribe.call_args
    assert called_args[0][0] == path
    cb_fn = called_args[1]["callback"]

    msg = MagicMock(spec=Message)
    msg.ack = MagicMock()
    msg.nack = MagicMock()

    cb_fn(msg)

    msg.ack.assert_called_once()
    msg.nack.assert_not_called()


@pytest.mark.asyncio
async def test_subscribe_to_subscription_cancelled(app, mock_subscriber_client, monkeypatch, capfd):
    name = "cancelled"
    cfg = {"callback": MagicMock(), "exactly_once_delivery": False}

    monkeypatch.setattr(app.subscriber, "get_subscription_path", lambda n: name)
    mock_subscriber_client.subscribe.return_value = MagicMock()
    monkeypatch.setattr(asyncio, "wrap_future", lambda fut: (_ for _ in ()).throw(asyncio.CancelledError()))

    await app.subscriber._subscribe_to_subscription(name, cfg)
    out = capfd.readouterr().out
    assert f"Info: Subscription {name} stopped" in out


@pytest.mark.asyncio
async def test_subscribe_to_subscription_error_on_listen(app, mock_subscriber_client, monkeypatch, capfd):
    name = "err"
    cfg = {"callback": MagicMock(), "exactly_once_delivery": False}

    monkeypatch.setattr(app.subscriber, "get_subscription_path", lambda n: name)
    mock_subscriber_client.subscribe.return_value = MagicMock()
    monkeypatch.setattr(asyncio, "wrap_future", lambda fut: (_ for _ in ()).throw(Exception("oops")))

    await app.subscriber._subscribe_to_subscription(name, cfg)
    out = capfd.readouterr().out
    assert f"Error: Something went wrong when listening to {name}: oops" in out


def test_start_subscription_tasks_starts_loop(app, mock_loop):
    app.subscriber._loop = mock_loop
    mock_loop.is_running.return_value = False

    app.subscriber.start_subscription_tasks()

    assert mock_loop.create_task.call_count == 1
    coro = mock_loop.create_task.call_args[0][0]
    assert inspect.iscoroutine(coro)
    assert coro.cr_code is app.subscriber._subscribe_to_subscriptions.__code__
    mock_loop.run_forever.assert_called_once()

    # suppress "never awaited" warning
    coro.close()


def test_start_subscription_tasks_noop_if_running(app, mock_loop):
    app.subscriber._loop = mock_loop
    mock_loop.is_running.return_value = True

    app.subscriber.start_subscription_tasks()
    mock_loop.create_task.assert_not_called()
    mock_loop.run_forever.assert_not_called()


def test_start_subscription_tasks_keyboard_interrupt(app, mock_loop):
    app.subscriber._loop = mock_loop
    mock_loop.is_running.side_effect = KeyboardInterrupt

    with patch("builtins.print") as printer:
        app.subscriber.start_subscription_tasks()
    printer.assert_called_once_with("Info: Interrupted, stopping listening to subscriptions")

@pytest.mark.asyncio
async def test_subscribe_to_subscription_exactly_once_success(app, mock_subscriber_client, monkeypatch, capfd):
    config = {'callback': MagicMock(), 'exactly_once_delivery': True}
    path = "projects/p/topics/t"
    monkeypatch.setattr(app.subscriber, "get_subscription_path", lambda name: path)
    monkeypatch.setattr(asyncio, "wrap_future", lambda fut: (_ for _ in ()).throw(asyncio.CancelledError()))
    def fake_run(coro, loop):
        try:
            coro.close()
        except Exception:
            pass
        class Dummy:
            def add_done_callback(self, cb):
                class F:
                    def exception(self): return None
                cb(F())
        return Dummy()
    monkeypatch.setattr(asyncio, "run_coroutine_threadsafe", fake_run)

    msg = MagicMock(spec=Message)
    ack_fut = MagicMock()
    msg.ack_with_response.return_value = ack_fut

    await app.subscriber._subscribe_to_subscription("sub", config)

    call_args = mock_subscriber_client.subscribe.call_args
    cb = call_args[1]['callback']

    cb(msg)

    ack_fut.ack.assert_called_once()
    ack_fut.nack.assert_not_called()
    msg.nack.assert_not_called()


@pytest.mark.asyncio
async def test_subscribe_to_subscription_exactly_once_error(app, mock_subscriber_client, monkeypatch, capfd):
    config = {'callback': MagicMock(), 'exactly_once_delivery': True}
    path = "projects/p/topics/t"
    monkeypatch.setattr(app.subscriber, "get_subscription_path", lambda name: path)
    monkeypatch.setattr(asyncio, "wrap_future", lambda fut: (_ for _ in ()).throw(asyncio.CancelledError()))
    def fake_run_err(coro, loop):
        try:
            coro.close()
        except Exception:
            pass
        class Dummy:
            def add_done_callback(self, cb):
                class F:
                    def exception(self): return RuntimeError("whoops")
                cb(F())
        return Dummy()
    monkeypatch.setattr(asyncio, "run_coroutine_threadsafe", fake_run_err)

    msg = MagicMock(spec=Message)
    ack_fut = MagicMock()
    msg.ack_with_response.return_value = ack_fut

    await app.subscriber._subscribe_to_subscription("sub", config)
    cb = mock_subscriber_client.subscribe.call_args[1]['callback']
    cb(msg)

    out = capfd.readouterr().out
    assert "Error in handler:" in out
    ack_fut.nack.assert_called_once()
    ack_fut.ack.assert_not_called()


@pytest.mark.asyncio
async def test_subscribe_to_subscription_nack_on_error(app, mock_subscriber_client, monkeypatch, capfd):
    config = {'callback': MagicMock(), 'exactly_once_delivery': False}
    path = "projects/p/topics/t"
    monkeypatch.setattr(app.subscriber, "get_subscription_path", lambda name: path)
    monkeypatch.setattr(asyncio, "wrap_future", lambda fut: (_ for _ in ()).throw(asyncio.CancelledError()))
    def fake_run_err(coro, loop):
        try:
            coro.close()
        except Exception:
            pass
        class Dummy:
            def add_done_callback(self, cb):
                class F:
                    def exception(self): return ValueError("boom")
                cb(F())
        return Dummy()
    monkeypatch.setattr(asyncio, "run_coroutine_threadsafe", fake_run_err)

    msg = MagicMock(spec=Message)
    msg.ack = MagicMock()
    msg.nack = MagicMock()

    await app.subscriber._subscribe_to_subscription("sub", config)
    cb = mock_subscriber_client.subscribe.call_args[1]['callback']
    cb(msg)

    out = capfd.readouterr().out
    assert "Error in handler:" in out
    msg.nack.assert_called_once()
    msg.ack.assert_not_called()


def test_publish_wrapper_success(app):
    # Given
    topic_name = "test-topic"
    message = "test-data"

    with patch.object(app.publisher, "publish", return_value='mocked_response') as mock_publish:
        @app.publish(topic_name, timeout=20, retry="retry_option")
        def publish():
            return message

    # When
        result = publish()

    # Then
        assert result == 'mocked_response', "Expected the topic to be published"
        mock_publish.assert_called_once_with(
            "test-topic", "test-data", 20, "retry_option"
        ), "Expected publish function to be called with correct arguments"