import os

import alembic
from alembic import config as alembic_config
import alembic.migration as alembic_migration
from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import enginefacade

from doni.db import models


def _alembic_config():
    path = os.path.join(os.path.dirname(__file__), 'alembic.ini')
    config = alembic_config.Config(path)
    return config


def version(config=None, engine=None) -> str:
    """Current database version.

    Returns:
        The database version.
    """
    if engine is None:
        engine = enginefacade.writer.get_engine()
    with engine.connect() as conn:
        context = alembic_migration.MigrationContext.configure(conn)
        return context.get_current_revision()


def upgrade(revision, config=None):
    """Used for upgrading database.

    Args:
        revision (str): Desired database version.
    """
    revision = revision or 'head'
    config = config or _alembic_config()

    alembic.command.upgrade(config, revision or 'head')


def create_schema(config=None, engine=None):
    """Create database schema from models description.

    Can be used for initial installation instead of upgrade('head').
    """
    if engine is None:
        engine = enginefacade.writer.get_engine()

    # NOTE(viktors): If we will use metadata.create_all() for non empty db
    #                schema, it will only add the new tables, but leave
    #                existing as is. So we should avoid of this situation.
    if version(engine=engine) is not None:
        raise db_exc.DBMigrationError("DB schema is already under version"
                                      " control. Use upgrade() instead")

    models.Base.metadata.create_all(engine)
    stamp('head', config=config)


def downgrade(revision, config=None):
    """Used for downgrading database.

    Args:
        revision (str): Desired database version.
    """
    revision = revision or 'base'
    config = config or _alembic_config()
    return alembic.command.downgrade(config, revision)


def stamp(revision, config=None):
    """Stamps database with provided revision.

    Don't run any migrations.

    Args:
        revision (str): Should match one from repository or head - to stamp
            database with most recent revision
    """
    config = config or _alembic_config()
    return alembic.command.stamp(config, revision=revision)


def revision(message=None, autogenerate=False, config=None):
    """Creates template for migration.

    Args:
        message (str): Text that will be used for migration title
        autogenerate (bool): Whether to generate diff based on current database
            state
    """
    config = config or _alembic_config()
    return alembic.command.revision(config, message=message,
                                    autogenerate=autogenerate)
