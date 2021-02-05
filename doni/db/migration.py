"""Database setup and migration commands."""

from oslo_config import cfg
from oslo_db import api as db_api

_BACKEND_MAPPING = {'sqlalchemy': 'doni.db.sqlalchemy.migration'}
IMPL = db_api.DBAPI.from_config(cfg.CONF, backend_mapping=_BACKEND_MAPPING,
                                lazy=True)


def upgrade(version=None):
    """Migrate the database to `version` or the most recent version."""
    return IMPL.upgrade(version)


def version():
    return IMPL.version()


def stamp(version):
    return IMPL.stamp(version)


def revision(message, autogenerate):
    return IMPL.revision(message, autogenerate)


def create_schema():
    return IMPL.create_schema()
