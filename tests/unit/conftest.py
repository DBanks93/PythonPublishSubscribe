import pytest
import os
from python_publish_subscribe import PythonPublishSubscribe

@pytest.fixture
def app():
    yield PythonPublishSubscribe({'PROJECT_ID': 'test-project'})