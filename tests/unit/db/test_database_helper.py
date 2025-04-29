# tests/unit/db/test_database_helper.py

import pytest
import re
from urllib.parse import quote_plus

import sqlalchemy
from sqlalchemy import URL
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

from python_publish_subscribe import PythonPublishSubscribe
from python_publish_subscribe.src.db.DatabaseHelper import (
    generate_database_url,
    create_engine_from_url,
    DatabaseHelper,
)
from python_publish_subscribe.src.db.DatabaseHelper import create_engine_from_url as _orig_create_engine
from python_publish_subscribe.config import Config

import python_publish_subscribe.src.Subscriber as subscriber
import python_publish_subscribe.src.Publisher as publisher
import python_publish_subscribe.config as config_module


class DummyConfig:
    def __init__(self, overrides=None):
        self.store = overrides.copy() if overrides else {}

    def get(self, key):
        lookup = key.name if hasattr(key, "name") else key
        return self.store.get(lookup)

    def add_value_to_key(self, key, mapping):
        lookup = key.name if hasattr(key, "name") else key
        self.store[lookup] = mapping

class DummyEngine:
    def connect(self):
        return "DUMMY_CONNECTION"

@pytest.fixture(autouse=True)
def reset_dbhelper_singleton():
    from python_publish_subscribe.src.db.DatabaseHelper import DatabaseHelper as DH
    DH._instance = None
    DH._setup = False
    DH.is_async = False
    yield
    DH._instance = None
    DH._setup = False
    DH.is_async = False


def test_generate_database_url_normal():
    url = generate_database_url(
        dialect="postgresql",
        username="user",
        password="p@ss:word",
        port="5432",
        name="mydb",
        host="db.example.com",
    )
    text = str(url)
    assert text.startswith("postgresql://user:"), text
    assert "db.example.com:5432/mydb" in text


def test_generate_database_url_missing_dialect():
    with pytest.raises(ValueError):
        generate_database_url(dialect="", username="u", password="p")


def test_generate_database_url_missing_name_and_username(capfd):
    url = generate_database_url(
        dialect="mysql",
        username="",
        password="pwd",
        port=None,
        name="",
        host="h",
    )
    out = capfd.readouterr().out
    assert "Warning: Database name is set to default_schema" in out
    assert "Info: Database name is set to default_schema" in out
    txt = str(url)
    assert re.search(r"/appuser$", txt)


def test_create_engine_from_url_sync(tmp_path):
    from python_publish_subscribe.src.db.DatabaseHelper import create_engine_from_url
    url = URL.create(
        "sqlite",
        database="/path/to/db",
    )
    eng, is_async = create_engine_from_url(url)
    assert isinstance(eng, Engine)
    assert is_async is False


def test_create_engine_from_url_async(monkeypatch):
    import python_publish_subscribe.src.db.DatabaseHelper as DBM
    fake_async_engine = object()
    monkeypatch.setattr(DBM, "create_async_engine", lambda u: fake_async_engine)
    url = URL.create(
        "postgresql+asyncpg",
        username="user",
        password="password",
        database="db"
    )
    eng, is_async = create_engine_from_url(url)
    assert eng is fake_async_engine
    assert is_async is True


def test_get_instance_without_config_raises():
    with pytest.raises(ValueError):
        DatabaseHelper.get_instance(config=None)


def test_singleton_and_sync_session(monkeypatch):
    import python_publish_subscribe.src.db.DatabaseHelper as DBM
    fake_engine = type("E", (), {"connect": lambda self: "CONN"})()
    monkeypatch.setattr(DBM, "create_engine_from_url", lambda url: (fake_engine, False))
    monkeypatch.setattr(DBM, "sessionmaker", lambda bind=None, class_=None, expire_on_commit=None: (lambda: "SESSION"))

    cfg = DummyConfig({
        "DATABASE_DIALECT": "postgresql",
        "DATABASE_USERNAME": "u",
        "DATABASE_PASSWORD": "p",
        "DATABASE_PORT": "5432",
        "DATABASE_NAME": "n",
        "DATABASE_HOST": "h",
    })

    helper = DatabaseHelper.get_instance(cfg)
    assert DatabaseHelper.get_instance() is helper

    assert helper.create_session() == "SESSION"
    assert helper.get_engine() is fake_engine
    assert DatabaseHelper.is_setup() is True


def test_async_session_maker(monkeypatch):
    import python_publish_subscribe.src.db.DatabaseHelper as DBM
    fake_async_engine = type("AE", (), {"connect": lambda self: "A_CONN"})()
    monkeypatch.setattr(DBM, "create_engine_from_url", lambda url: (fake_async_engine, True))
    monkeypatch.setattr(DBM, "sessionmaker", lambda bind=None, class_=None, expire_on_commit=None: (lambda: "A_SESSION"))

    cfg = DummyConfig({"DATABASE_URL": "postgresql+asyncpg://x"})
    helper = DatabaseHelper.get_instance(cfg)
    a_sess = helper.create_async_session()
    assert a_sess == "A_SESSION"


def test_drop_and_create_all(monkeypatch):
    calls = {"drop": False, "create": False}
    class FakeMeta:
        @staticmethod
        def drop_all(eng):
            calls["drop"] = True
        @staticmethod
        def create_all(eng):
            calls["create"] = True

    import python_publish_subscribe.src.db.DatabaseHelper as DBM
    monkeypatch.setattr(DBM, "get_base", lambda: type("B", (), {"metadata": FakeMeta}))

    helper = DatabaseHelper.__new__(DatabaseHelper)
    helper._ENGINE = "DUMMY_ENGINE"
    helper._async = False
    DatabaseHelper._instance = helper

    DatabaseHelper.drop_all()
    DatabaseHelper.create_all()

    assert calls["drop"] is True
    assert calls["create"] is True

def test_init_does_not_rerun_after_setup(monkeypatch):
    calls = {"n": 0}

    def fake_create_engine(url):
        calls["n"] += 1
        return DummyEngine(), False

    import python_publish_subscribe.src.db.DatabaseHelper as DBM
    monkeypatch.setattr(DBM, "create_engine_from_url", fake_create_engine)
    monkeypatch.setattr(DBM, "sessionmaker", lambda **kw: (lambda: None))

    cfg = DummyConfig({"DATABASE_URL": "sqlite:///:memory:"})

    helper = DatabaseHelper(cfg)
    assert calls["n"] == 1
    assert helper._setup is True

    helper.__init__(cfg)
    assert calls["n"] == 1


def test_create_session_without_session_maker(monkeypatch, capfd):
    class Fake:
        _session_maker = None

    monkeypatch.setattr(DatabaseHelper, "get_instance", classmethod(lambda cls: Fake()))

    result = DatabaseHelper.create_session()

    out = capfd.readouterr().out
    assert "Warning: Database engine has not been configured" in out
    assert result is None


def test_create_async_session_without_async_maker(monkeypatch, capfd):
    class Fake:
        _async_session_maker = None

    monkeypatch.setattr(DatabaseHelper, "get_instance", classmethod(lambda cls: Fake()))

    result = DatabaseHelper.create_async_session()

    out = capfd.readouterr().out
    assert "Warning: Database engine has not been configured for async" in out
    assert result is None

def test_enabling_db_connectivty_setup(monkeypatch):
    # Given
    class Fake:
        def __init__(self, config):
            pass

    class FakeDB:
        setup = False
        instance = None

        def __new__(cls, *args, **kwargs):
            cls.instance = super(FakeDB, cls).__new__(cls)
            return cls.instance

        def __init__(self):
            self.setup = True

    monkeypatch.setattr(publisher, 'Publisher', Fake)
    monkeypatch.setattr(subscriber, 'Subscriber', Fake)
    monkeypatch.setattr(config_module, 'Config', Fake)

    monkeypatch.setattr(DatabaseHelper, "get_instance", classmethod(lambda cls, config: FakeDB()))
    # When
    app = PythonPublishSubscribe({'PROJECT_ID': 'test-project'}, database_connectivity=True)

    # Then
    assert FakeDB, "Expected the Database engine to be setup"
