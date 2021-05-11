import pytest

from doni.tests.unit import utils


@pytest.fixture(autouse=True)
def _init_database(database):
    """Ensure the 'database' fixture is auto-used for all these tests."""
    pass
