from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import Session

from python_publish_subscribe.src.db.ORMUtility import get_base


class BaseModel(get_base()):
    """
    Base model that can be used.

    Contains the following attributes:
    id: Primary key, Integer
    created_at: DateTime
    updated_at: DateTime

    Also contains save and delete methods.
    """
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __init_subclass__(cls, tablename: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if tablename:
            cls.__tablename__ = tablename

    def save(self, session: Session) -> None:
        """
        Saves a model to the database.

        :param session: Session to commit to
        """
        session.add(self)
        session.commit()

    def delete(self, session: Session) -> None:
        """
        Deletes a model from the database.

        :param session: Session to commit to
        """
        session.delete(self)
        session.commit()