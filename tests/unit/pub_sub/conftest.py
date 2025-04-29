from unittest.mock import patch, Mock
from google.cloud.pubsub_v1 import PublisherClient

import pytest
import os

@pytest.fixture(scope="module", autouse=True)
def set_pubsub_emulator_env_vars():
    os.environ["PUBSUB_EMULATOR_HOST"] = "localhost:8085"
    yield

    del os.environ["PUBSUB_EMULATOR_HOST"]

@pytest.fixture
def mock_publisher_client(app):
    with patch('google.cloud.pubsub_v1.PublisherClient.publish') as mock_publisher_client:
        app.publisher._publisher = mock_publisher_client
        yield mock_publisher_client

@pytest.fixture
def mock_subscriber_client(app):
    with patch('google.cloud.pubsub_v1.SubscriberClient.subscribe') as mock_subscriber_client:
        app.subscriber._subscriber = mock_subscriber_client
        yield mock_subscriber_client

@pytest.fixture
def mock_get_topic(app):
    with patch.object(app.publisher, "get_topic") as mock_get_topic:
        app.publisher._get_topic = mock_get_topic
        mock_get_topic.return_value = ("projects/project_name/topics/topic_name", "test-topic")
        yield mock_get_topic

@pytest.fixture
def mock_loop():
    loop = Mock()
    loop.is_running.return_value = False
    loop.create_task = Mock()
    loop.run_forever = Mock()
    return loop

@pytest.fixture
def mock_database_helper(monkeypatch):
    # Define a mock for the DatabaseHelper class
    class FakeAsyncSession:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def commit(self): pass
        async def rollback(self): pass

    class FakeSession:
        def __aenter__(self): return self
        def __aexit__(self, *args): pass
        def commit(self): pass
        def rollback(self): pass

    class FakeDBHelper:
        is_async = True
        @staticmethod
        def is_setup(): return True
        @staticmethod
        def create_async_session(): return FakeAsyncSession()
        @staticmethod
        def create_session(): return FakeSession()

    # Patch the DatabaseHelper class with the FakeDBHelper mock
    monkeypatch.setattr("python_publish_subscribe.src.db.DatabaseHelper", FakeDBHelper)

    return FakeDBHelper
