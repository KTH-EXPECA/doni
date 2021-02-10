"""
SQLAlchemy models for hardware data.
"""

from os import path
from urllib import parse as urlparse

from oslo_db import options as db_options
from oslo_db.sqlalchemy import models
# db_types has various JSON-encoded helper types
#from oslo_db.sqlalchemy import types as db_types
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import schema, String
from sqlalchemy.ext.declarative import declarative_base
# orm has ways of modeling table relationships
#from sqlalchemy import orm

from doni.conf import CONF

_DEFAULT_SQL_CONNECTION = 'sqlite:///' + path.join('$state_path',
                                                   'doni.sqlite')


db_options.set_defaults(CONF, connection=_DEFAULT_SQL_CONNECTION)


def table_args():
    engine_name = urlparse.urlparse(CONF.database.connection).scheme
    if engine_name == 'mysql':
        return {'mysql_engine': CONF.database.mysql_engine,
                'mysql_charset': "utf8"}
    return None


class DoniBase(models.TimestampMixin,
               models.ModelBase):

    metadata = None

    def as_dict(self):
        d = {}
        for c in self.__table__.columns:
            d[c.name] = self[c.name]
        return d


Base = declarative_base(cls=DoniBase)


class Hardware(Base):
    __tablename__ = 'hardware'
    __table_args__ = (
        schema.UniqueConstraint('uuid', name='uniq_hardware0uuid'),
        schema.UniqueConstraint('name', name='uniq_hardware0name'),
        table_args()
    )
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36))
    project_id = Column(String(255))
    name = Column(String(255))
