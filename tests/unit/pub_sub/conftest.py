from unittest.mock import patch
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
def mock_get_topic(app):
    with patch.object(app.publisher, "get_topic") as mock_get_topic:
        app.publisher._get_topic = mock_get_topic
        mock_get_topic.return_value = ("projects/project_name/topics/topic_name", "test-topic")
        yield mock_get_topic
