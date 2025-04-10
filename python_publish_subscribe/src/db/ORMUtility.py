from typing import Type, TypeVar, Dict, Tuple, Any, cast

from sqlalchemy.orm import declarative_base, registry
from sqlalchemy import Column, Integer

Base = declarative_base()
mapper_registry = registry()

ModelType = TypeVar('ModelType', bound=Base)


def get_base() -> declarative_base:
    """
    Gets the declarative base class.
    :return: declarative base class
    """
    return Base


def get_registry() -> registry:
    """
    Gets the mapper registry.
    :return: Mapper registry
    """
    return mapper_registry


# TODO: Revist - doesn't work currently since sqlalchemy will attempt to create the class before tablename is passed
def orm_model(tablename: str):
    def decorator(cls):
        cls.__tablename__ = tablename
        return cls
    return decorator


def create_model(
    name: str,
    tablename: str,
    fields: Dict[str, Tuple[Any, Dict[str, Any]]]
) -> Type[ModelType]:
    """
    Creates a new model from the given name and tablename.
    :param name: Name of the model/class
    :param tablename: Table name in the database
    :param fields: Map of fields/attributes that the model has
    :return: Model created
    """
    attrs = {
        '__tablename__': tablename,
        'id': Column(Integer, primary_key=True)
    }
    for field_name, (field_type, kwargs) in fields.items():
        attrs[field_name] = Column(field_type, **kwargs)
    return cast(Type[ModelType], type(name, (Base,), attrs))


def register_model(model: Type[ModelType]) -> Type[ModelType]:
    """
    Registers a new model to the database.
    :param model: Model to register
    :return: Model created
    """
    mapper_registry.map_imperatively(model, model.__table__)
    return model


def create_and_register_model(    name: str,
    tablename: str,
    fields: Dict[str, Tuple[Any, Dict[str, Any]]]
) -> Type[ModelType]:
    """
    Creates a new model from the given name and tablename then registers it.
    :param name: Name of the model/class
    :param tablename: Table name in the database
    :param fields: Map of fields/attributes that the model has
    :return: Model created
    """
    model = create_model(name, tablename, fields)
    register_model(model)
    return model