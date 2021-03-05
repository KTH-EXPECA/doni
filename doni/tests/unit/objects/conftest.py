import pytest

from doni.tests.unit import utils


@pytest.fixture(autouse=True)
def _init_database(database):
    """Ensure the 'database' fixture is auto-used for all these tests.
    """
    pass


@pytest.fixture(autouse=True)
def _use_fake_hardware(set_defaults):
    """Use the 'fake-hardware' Hardware type for testing.
    """
    set_defaults(enabled_hardware_types=[utils.FAKE_HARDWARE_TYPE])
