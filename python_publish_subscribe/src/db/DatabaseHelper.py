import sqlalchemy

from python_publish_subscribe.config import Config
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import engine
from sqlalchemy import URL

from python_publish_subscribe.src.db.ORMUtility import get_base

# Map of all the dialect names to respective start of url for sqlalchemy
DATABASE_DIALECTS = {
    'postgresql': 'postgresql',
    'psycopg2': 'postgresql+psycopg2',
    'pg8000': 'postgresql+pg8000',
    'mysql': 'mysql',
    'pymysql': 'mysql+pymysql',
}


def generate_database_url(dialect: str, username: str, password: str, port: str | int=None, name: str=None, host: str=None) -> URL:
    """
    Generates a database url.

    :param dialect: The dialect to use, could be just the name or the whole driver.
    :param name: The name of the database.
    :param username: The username of the database.
    :param password: The password of the database.
    :param port: The port of the database.
    :return: A database url.
    """
    if dialect is None or dialect.strip() == '':
        raise ValueError("Dialect has not been setup in the configuration.")
    if dialect.lower() in DATABASE_DIALECTS:
        dialect = DATABASE_DIALECTS[dialect] or dialect

    database_name = name
    if not name or name.strip() == '':
        print("Warning: Database name is set to default_schema since one was not provided in the configuration.")
        database_name = "default_schema"

    if not username or username.strip() == '':
        print("Info: Database name is set to default_schema since one was not provided in the configuration.")
        database_name = "appuser"

    return URL.create(
        dialect,
        username=username,
        password=password,
        port=port if port != '' else None,
        database=database_name,
        host=host if host != '' else None,
    )

class DatabaseHelper:
    _instance = None
    _ENGINE: engine
    _CONN: engine.Connection
    _session_maker: sessionmaker
    _setup: bool = False


    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseHelper, cls).__new__(cls)
        return cls._instance


    def __init__(self, config: Config):
        if hasattr(self, "_setup") and self._setup:
            return
        database_url = config.get(Config.ConfigKeys.DATABASE_URL)
        if database_url is None or database_url == "":
            database_url = generate_database_url(
                dialect=config.get(Config.ConfigKeys.DATABASE_DIALECT.name),
                username=config.get(Config.ConfigKeys.DATABASE_USERNAME.name),
                password=config.get(Config.ConfigKeys.DATABASE_PASSWORD.name),
                port=config.get(Config.ConfigKeys.DATABASE_PORT.name),
                name=config.get(Config.ConfigKeys.DATABASE_NAME.name),
                host=config.get(Config.ConfigKeys.DATABASE_HOST.name),
            )

        # Not catching any errors here as the framework SHOULD exit 1 if something goes wrong here
        self._ENGINE = sqlalchemy.create_engine(
            database_url)
        self._CONN = self._ENGINE.connect()

        if self._ENGINE is not None and self._CONN is not None:
            self._session_maker = sessionmaker(bind=self._ENGINE)
            self._setup = True


    @classmethod
    def get_instance(cls, config: Config=None):
        """
        Gets the singleton instance of the database helper.

        If an instance doesn't exist, it creates one if the config is given

        :param config: Optional config that can be used to set up an instance if an instance doesn't exist.
        :return: Instance of the database helper
        """
        if cls._instance is None:
            if config is None:
                raise ValueError("No configuration provided.")
            cls._instance = DatabaseHelper(config)
        return cls._instance


    @classmethod
    def create_session(cls) -> Session | None:
        """
        Creates a sqlalchemy session

        :return: The created session
        """
        instance = cls.get_instance()
        if instance._session_maker is None:
            print("Warning: Database engine has not been configured")
            return None
        return instance._session_maker()


    @classmethod
    def is_setup(cls) -> bool:
        """
        Checks if a database helper has been setup.

        :return: If a database helper has been setup
        """
        instance = cls.get_instance()
        return instance._setup


    @classmethod
    def get_engine(cls) -> sqlalchemy.engine.Engine:
        """
        Gets the sqlalchemy engine instance.

        :return: The sqlalchemy engine instance
        """
        instance = cls.get_instance()
        return instance._ENGINE


    @classmethod
    def drop_all(cls):
        instance = cls.get_instance()
        get_base().metadata.drop_all(instance.get_engine())


    @classmethod
    def create_all(cls):
        instance = cls.get_instance()
        get_base().metadata.create_all(instance.get_engine())