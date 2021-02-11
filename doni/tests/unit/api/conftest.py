from flask.testing import FlaskClient
from keystoneauth1 import fixture as ksa_fixture
from keystonemiddleware.fixture import AuthTokenFixture
import pytest

from doni import create_app


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


@pytest.fixture
def user_token(tokens: "AuthTokenFixture") -> str:
    # Creates a project scoped V3 token, with 1 entry in the catalog
    token = ksa_fixture.V3Token()
    token.set_project_scope()

    s = token.add_service('identity')
    s.add_standard_endpoints(public='http://example.com/identity/public',
                             admin='http://example.com/identity/admin',
                             internal='http://example.com/identity/internal',
                             region='RegionOne')

    token_id = tokens.add_token(token)
    return token_id
