from unittest.mock import patch

from python_publish_subscribe.config import Config

def test_config_init():
    # Given

    # When
    config = Config()

    # Then
    assert config is not None,"Expected config to be initialised"
    assert config._config == {
            'PUBLISH_TOPICS': {},
            'SUBSCRIPTION_TOPICS': {},
            'DEFAULT_TIMEOUT': 10,
            'PROJECT_ID': ''
        }