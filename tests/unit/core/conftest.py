import pytest

from python_publish_subscribe.config import Config


@pytest.fixture
def config():
    yield Config()