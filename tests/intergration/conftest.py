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
    config = {
        'PROJECT_ID': 'test-project',
        'DATABASE_DIALECT': 'asyncpg',
        'DATABASE_USERNAME': 'appuser',
        'DATABASE_PASSWORD': 'S3cret',
        'DATABASE_HOST': 'localhost',
        'DATABASE_PORT': '5432',
        'DATABASE_NAME': 'integration',
    }
    yield PythonPublishSubscribe(config, database_connectivity=True)