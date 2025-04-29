# tests/unit/db/test_orm_utility.py

import pytest
from sqlalchemy import Integer, String
from sqlalchemy.orm import declarative_base
from python_publish_subscribe.src.db.ORMUtility import (
    Base,
    mapper_registry,
    get_base,
    get_registry,
    create_model,
    register_model,
    create_and_register_model,
)


def test_get_base_and_registry():
    # get_base should return the module‐level Base
    assert get_base() is Base
    # get_registry should return the module‐level mapper_registry
    assert get_registry() is mapper_registry


def test_create_model_minimal():
    # no extra fields → just id(primary key) on given tablename
    Model = create_model("MyModel", "my_table", {})
    assert isinstance(Model, type)
    assert Model.__name__ == "MyModel"
    assert hasattr(Model, "__tablename__") and Model.__tablename__ == "my_table"

    # Table should have an 'id' column, integer primary key
    tbl = Model.__table__
    assert "id" in tbl.columns
    col = tbl.columns["id"]
    assert col.primary_key is True
    assert isinstance(col.type, Integer)


def test_create_model_with_fields():
    fields = {
        "name": (String(50), {"nullable": False}),
        "age": (Integer, {"default": 0}),
    }
    Person = create_model("Person", "person_table", fields)
    tbl = Person.__table__

    # Basic attributes
    assert Person.__tablename__ == "person_table"
    assert "id" in tbl.columns  # still has the id PK

    # 'name' column
    assert "name" in tbl.columns
    name_col = tbl.columns["name"]
    assert isinstance(name_col.type, String)
    assert name_col.type.length == 50
    assert name_col.nullable is False

    # 'age' column
    assert "age" in tbl.columns
    age_col = tbl.columns["age"]
    assert isinstance(age_col.type, Integer)
    # SQLAlchemy represents default as a DefaultClause on the column
    assert age_col.default is not None


def test_register_model(monkeypatch):
    Model = create_model("RegModel", "reg_table", {})
    called = {}
    def fake_map_imperative(model, table):
        called["model"] = model
        called["table"] = table

    # Monkey‐patch the registry’s map_imperatively
    monkeypatch.setattr(mapper_registry, "map_imperatively", fake_map_imperative)

    returned = register_model(Model)
    assert returned is Model
    # Ensure the registry was called with exactly (Model, Model.__table__)
    assert called["model"] is Model
    assert called["table"] is Model.__table__


def test_create_and_register_model(monkeypatch):
    fields = {"value": (Integer, {})}
    called = {}
    def fake_map(model, table):
        called["args"] = (model, table)

    monkeypatch.setattr(mapper_registry, "map_imperatively", fake_map)

    M = create_and_register_model("CRModel", "cr_table", fields)
    # Model properties
    assert isinstance(M, type)
    assert M.__name__ == "CRModel"
    assert M.__tablename__ == "cr_table"
    assert "id" in M.__table__.columns
    assert "value" in M.__table__.columns

    # Registered via our fake_map
    model_arg, table_arg = called["args"]
    assert model_arg is M
    assert table_arg is M.__table__
