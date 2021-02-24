import tempfile

from oslo_config import fixture as config_fixture
from oslo_db.sqlalchemy import enginefacade
import pytest

from doni.common import config as doni_config
from doni.common import context as doni_context
from doni.conf import CONF
from doni.db import migration
from doni.db import models
from doni.tests.unit import utils


@pytest.fixture(scope="session")
def admin_context():
    return doni_context.get_admin_context()


@pytest.fixture(scope="session")
def config():
    cfg_fixture = config_fixture.Config(CONF)
    cfg_fixture.setUp()
    cfg_fixture.config(use_stderr=False, tempdir=tempfile.tempdir)
    yield cfg_fixture
    cfg_fixture.cleanUp()


@pytest.fixture(scope="session")
def set_defaults(config):
    def _wrapped(**kw):
        """Set default values of config options."""
        group = kw.pop('group', None)
        for o, v in kw.items():
            config.set_default(o, v, group=group)
    return _wrapped


@pytest.fixture
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
    db_fixtures = utils.DBFixtures()
    yield db_fixtures
    db_fixtures.cleanup()
    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _init_config(set_defaults):
    set_defaults(host='fake-mini', debug=True)
    # This is a bit of a hack; this function does a lot more than
    # parse command line arguments! ;_;
    doni_config.parse_args([], default_config_files=[])