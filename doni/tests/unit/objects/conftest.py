from oslo_db.sqlalchemy import enginefacade
import pytest

from doni.db import migration
from doni.db import models
from doni.tests.unit.db import utils


@pytest.fixture(scope="module", autouse=True)
def database(set_defaults):
    """Automatically set up a temporary SQLite DB for tests in this module.
    """
    set_defaults(connection="sqlite://",
                 sqlite_synchronous=False,
                 group='database')
    if migration.version():
        return
    engine = enginefacade.writer.get_engine()
    engine.connect()
    models.Base.metadata.create_all(engine)
    migration.stamp('head')
    yield
    engine.dispose()


@pytest.fixture
def fake_hardware():
    return utils.get_test_hardware()
