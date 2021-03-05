import tempfile

from oslo_config import fixture as config_fixture
from oslo_db.sqlalchemy import enginefacade
import pytest

from doni.common import config as doni_config
from doni.common import context as doni_context
from doni.common import driver_factory
from doni.conf import CONF
from doni.db import migration
from doni.db import models
from doni.tests.unit import utils


@pytest.fixture
def admin_context():
    return doni_context.get_admin_context()


@pytest.fixture
def config():
    cfg_fixture = config_fixture.Config(CONF)
    cfg_fixture.setUp()
    cfg_fixture.config(use_stderr=False, tempdir=tempfile.tempdir)
    yield cfg_fixture
    cfg_fixture.cleanUp()


@pytest.fixture
def set_config(config: "config_fixture.Config"):
    def _wrapped(**kwargs):
        """Override values of config options."""
        return config.config(**kwargs)
    return _wrapped


@pytest.fixture
def database(set_config):
    """Automatically set up a temporary SQLite DB for tests in this module.
    """
    set_config(connection="sqlite://",
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


@pytest.fixture(autouse=True)
def _init_test_env(set_config):
    """Initialize environment and configuration for a test.

    This fixture is scoped to each test, meaning it should ensure a clean
    environment for each execution. Its main job is to ensure the overrides
    are in place for the test hardware and worker types. The extension
    manager is also cleared after each test run; this ensures that any tests
    that wish to override the enabled hardware types can do so (the extension
    manager caches entrypoints and filters based on the enabled_* conf option.)
    """
    set_config(
        host='fake-mini',
        debug=True,
        enabled_hardware_types=[utils.FAKE_HARDWARE_TYPE],
        enabled_worker_types=[utils.FAKE_WORKER_TYPE])
    # This is a bit of a hack; this function does a lot more than
    # parse command line arguments! ;_;
    doni_config.parse_args([], default_config_files=[])
    yield
    driver_factory.HardwareTypeFactory._extension_manager = None
