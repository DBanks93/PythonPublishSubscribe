from sqlalchemy.ext.automap import automap_base

from python_publish_subscribe.src.db.DatabaseHelper import DatabaseHelper

class AutomapManager:
    _automap_classes = None

    @classmethod
    def get_automap_classes(cls) -> list:
        """
        Automaps a database model and returns a list of automap classes.
        :return: list of automap classes
        """
        if cls._automap_classes is None:
            engine = DatabaseHelper.get_engine()

            automap_base_instance = automap_base()
            automap_base_instance.prepare(engine, reflect=True)

            cls._automap_classes = automap_base_instance.classes

        return cls._automap_classes