import os
from dotenv import load_dotenv, dotenv_values
from typing import Any, Optional, Dict


class Config:
    """
    Configuration for the Framework.

    All configuration is handled here,
    the main reason is to try and catch any errors
    as well to allow for the configuration to be configured
    by multiple ways.
    """
    def __init__(self, default_config=None):
        """
        Initialises the app configuration.

        :param default_config: Any default configuration for when the app starts
        """
        self._config = {
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

        if default_config is None:
            default_config = DEFAULT_CONFIG
        self._config.update(default_config)
        self.initialise()

    def initialise(self):
        self.load_dot_env()

    def get(self, key: str, default: object=None) -> Optional[Any]:
        """
        Get a configuration value.
        Same usage as a Dict get.

        :param key: Key of the value to get
        :param default: Value to return if the key is not found
        :return: Value of the key
        """
        return self._config.get(key, default)

    def set(self, key: str, value: object) -> None:
        """
        Set a configuration value.
        Same usage as a Dict set.

        :param key: Key of the value to set
        :param value: Value to set
        """
        self._config[key] = value

    def update(self, data, throw_error=True) -> None:
        """
        Updates the configuration.
        :param data: Dictionary with updated values
        :param throw_error: Boolean to throw error if the update fails
        """
        if isinstance(data, dict):
            self._config.update(data)
        elif throw_error:
            raise ValueError("Configuration data must be a dict")

    def add_value_to_key(self, key, value):
        if not key in self._config:
            raise KeyError(f"Key {key} does not exist")

        old_values = self._config.get(key)

        if isinstance(old_values, dict):
            old_values.update(value)
        elif isinstance(old_values, list):
            old_values = old_values + value
            self._config[key] = old_values
        else:
            raise ValueError("Value must be either a dict or a list")


    # TODO: add functionality to set config through env / local files

    def load_dot_env(self) -> None:
        dot_env_dict = dotenv_values(".env")

        # if dot_env_dict['DEFAULT_TIMEOUT']:
        #     dot_env_dict['DEFAULT_TIMEOUT'] = int(dot_env_dict['DEFAULT_TIMEOUT'])
        self.update(dot_env_dict)

    def from_file(self, filename) -> None:
        import json

        loader = None

        if filename.endswith(".json"):
            loader = json.load
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            loader = None

    from enum import Enum
    class ConfigKeys(Enum):
        """
        Enums for all the keys in the configuration keys.
        This isn't needed, but is used to prevent magic strings.
        """
        def __str__(self):
            return str(self.name)

        PROJECT_ID = 1
        SUBSCRIPTION_TOPICS = 2
        PUBLISH_TOPICS = 3
        DEFAULT_TIMEOUT = 4
        DATABASE_URL = 5
        DATABASE_DIALECT = 6
        DATABASE_NAME = 7
        DATABASE_USERNAME = 8
        DATABASE_PASSWORD = 9
        DATABASE_HOST = 10
        DATABASE_PORT = 11

DEFAULT_CONFIG = {
   # Config.ConfigKeys.SUBSCRIPTION_TOPICS : {}
}