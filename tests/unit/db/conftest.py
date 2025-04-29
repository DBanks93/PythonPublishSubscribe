from unittest.mock import patch, MagicMock

import pytest

from python_publish_subscribe.src.db import DatabaseHelper


@pytest.fixture(autouse=True)
def reset_dbhelper_singleton():
    DatabaseHelper._instance = None
    DatabaseHelper._setup = False
    DatabaseHelper.is_async = False
    yield
    DatabaseHelper._instance = None
    DatabaseHelper._setup = False
    DatabaseHelper.is_async = False