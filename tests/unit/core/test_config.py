from unittest.mock import patch

import pytest

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
            'PROJECT_ID': '',
            'DATABASE_URL': '',
            'DATABASE_DIALECT': '',
            'DATABASE_NAME': 'default_schema',
            'DATABASE_USERNAME': 'appuser',
            'DATABASE_PASSWORD': '',
            'DATABASE_PORT': '',
            'DATABASE_HOST': '',
        }

def test_update_config(config):
    # Given
    dict = {'foo': 'bar'}

    # When
    config.update(dict)

    # Then
    assert 'foo' in config._config, "Expect key to be added to config dict"
    assert config._config['foo'] == 'bar', "Expect value to be added to config dict"

def test_update_config_value_error(config):
    # given
    data = None

    # When
    with pytest.raises(ValueError) as excinfo:
        config.update(data)

    # Then
    assert str(excinfo.value) == "Configuration data must be a dict"


def test_adding_dict_value_to_key(config):
    # Given
    config._config['dict'] = {}

    # When
    config.add_value_to_key('dict', {'foo': 'bar'})

    # Then
    assert config._config['dict'] == {'foo': 'bar'}

def test_adding_list_value_to_key(config):
    # Given
    config._config['list'] = []

    # When
    config.add_value_to_key('list', ['foo', 'bar'])

    # Then
    assert config._config['list'] == ['foo', 'bar']

def test_adding_value_to_non_existing_key(config):
    # Given
    data = {'foo': 'bar'}
    key = 'non-existent-dict'

    #When
    with pytest.raises(KeyError) as excinfo:
        config.add_value_to_key(key, data)

    # Then
    assert f"Key {key} does not exist" in str(excinfo.value)

def test_adding_non_dict_to_dict(config):
    # Given
    data = 'non-dict'
    old_values = {'foo': 'bar'}
    key = 'dict'
    config._config[key] = old_values

    # When
    with pytest.raises(ValueError) as excinfo:
        config.add_value_to_key(key, data)

    assert config._config[key] == old_values, "Values should not be changed"

def test_setting_value(config):
    # Given
    config._config['key'] = 'value'

    # When
    config.set('key', 'new_value')

    # Then
    assert config._config['key'] == 'new_value', "value should equal new key"