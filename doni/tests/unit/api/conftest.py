from flask.testing import FlaskClient
from keystoneauth1 import fixture as ksa_fixture
from keystonemiddleware.fixture import AuthTokenFixture
import pytest

from doni import create_app
from doni.tests.unit import utils


@pytest.fixture
def client(database) -> "FlaskClient":
    app = create_app(test_config={'TESTING': True})

    with app.test_client() as client:
        yield client


@pytest.fixture
def tokens() -> "AuthTokenFixture":
    ksm_fixture = AuthTokenFixture()
    ksm_fixture.setUp()
    yield ksm_fixture
    ksm_fixture.cleanUp()


def _token_fixture(**kwargs):
    token = ksa_fixture.V3Token(**kwargs)
    s = token.add_service('identity')
    s.add_standard_endpoints(public='http://example.com/identity/public',
                             admin='http://example.com/identity/admin',
                             internal='http://example.com/identity/internal',
                             region='RegionOne')
    return token


@pytest.fixture
def user_auth_headers(tokens: "AuthTokenFixture") -> dict:
    token = _token_fixture()
    token.set_project_scope()
    token_id = tokens.add_token(token)
    return {"X-Auth-Token": token_id}


@pytest.fixture
def admin_auth_headers(tokens: "AuthTokenFixture") -> dict:
    token = _token_fixture()
    token.set_project_scope()
    token.add_role(name="admin")
    token_id = tokens.add_token(token)
    return {"X-Auth-Token": token_id}


@pytest.fixture(autouse=True)
def _use_fake_hardware(set_defaults):
    """Use the 'fake-hardware' Hardware type for testing.
    """
    set_defaults(enabled_hardware_types=[utils.FAKE_HARDWARE_TYPE])
