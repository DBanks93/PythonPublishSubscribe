from array import array

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
            'PUBLISH_TOPICS': []
        }

        if default_config is None:
            default_config = DEFAULT_CONFIG
            self._config.update(default_config)

    def get(self, key: str, default: object=None) -> object:
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

    def update(self, data) -> None:
        """
        Updates the configuration.
        :param data: Dictionary with updated values
        """
        if isinstance(data, dict):
            self._config.update(data)
        else:
            raise ValueError("Configuration data must be a dict")

    def add_value_to_key(self, key, value):
        if not self._config.__contains__(key):
            raise KeyError(f"Key {key} does not exist")

        old_values = self._config.get(key)

        if isinstance(old_values, dict):
            old_values.update(value)
        elif isinstance(old_values, list):
            old_values.append(value)
        else:
            raise ValueError()


    # TODO: add functionality to set config through env / local files
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
            return str(self.value)

        SUBSCRIPTION_TOPICS = 1
        PUBLISH_TOPICS = 2

DEFAULT_CONFIG = {
   Config.ConfigKeys.SUBSCRIPTION_TOPICS : {}
}