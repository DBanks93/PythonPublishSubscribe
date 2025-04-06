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
            'PROJECT_ID': ''
        }

def test_update_config(app):
    # Given
    dict = {'foo': 'bar'}

    # When
    app.config.update(dict)

    # Then
    assert 'foo' in app.config._config, "Expect key to be added to config dict"
    assert app.config._config['foo'] == 'bar', "Expect value to be added to config dict"

def test_update_config_value_error(app):
    # given
    data = None

    # When
    with pytest.raises(ValueError) as excinfo:
        app.config.update(data)

    # Then
    assert str(excinfo.value) == "Configuration data must be a dict"


def test_adding_dict_value_to_key(app):
    # Given
    app.config._config['dict'] = {}

    # When
    app.config.add_value_to_key('dict', {'foo': 'bar'})

    # Then
    assert app.config._config['dict'] == {'foo': 'bar'}

def test_adding_list_value_to_key(app):
    # Given
    app.config._config['list'] = []

    # When
    app.config.add_value_to_key('list', ['foo', 'bar'])

    # Then
    assert app.config._config['list'] == ['foo', 'bar']

def test_adding_value_to_non_existing_key(app):
    # Given
    data = {'foo': 'bar'}
    key = 'non-existent-dict'

    #When
    with pytest.raises(KeyError) as excinfo:
        app.config.add_value_to_key(key, data)

    # Then
    assert f"Key {key} does not exist" in str(excinfo.value)