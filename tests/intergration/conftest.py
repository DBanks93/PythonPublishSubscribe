import pytest
import os
from python_publish_subscribe import PythonPublishSubscribe


@pytest.fixture(scope="module", autouse=True)
def set_pubsub_emulator_env_vars():
    os.environ["PUBSUB_EMULATOR_HOST"] = "localhost:8085"
    yield

    del os.environ["PUBSUB_EMULATOR_HOST"]

@pytest.fixture
def app():
    yield PythonPublishSubscribe({'PROJECT_ID': 'test-project'})