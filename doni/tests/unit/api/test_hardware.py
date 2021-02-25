import json
import re

from flask.testing import FlaskClient
from oslo_policy.policy import PolicyNotAuthorized
from oslo_utils import uuidutils
import pytest

from doni.tests.unit import utils


def test_get_all_hardware(mocker, user_auth_headers, client: "FlaskClient"):
    mock_authorize = mocker.patch("doni.api.hardware.authorize")
    res = client.get("/v1/hardware/", headers=user_auth_headers)
    assert res.status_code == 200
    assert res.json == {
        "hardware": [],
    }
    assert mock_authorize.called_once_with("hardware:get")


def test_get_one_hardware(mocker, user_auth_headers, client: "FlaskClient",
                          database: "utils.DBFixtures"):
    mock_authorize = mocker.patch("doni.api.hardware.authorize")
    hw = database.add_hardware()
    res = client.get(f"/v1/hardware/{hw['uuid']}/", headers=user_auth_headers)
    assert res.status_code == 200
    assert res.json["uuid"] == hw["uuid"]
    assert res.json["name"] == hw["name"]
    assert res.json["project_id"] == hw["project_id"]
    # Don't return internal IDs
    assert "id" not in res.json
    assert mock_authorize.called_once_with("hardware:get")


def test_missing_hardware(mocker, user_auth_headers, client: "FlaskClient"):
    mocker.patch("doni.api.hardware.authorize")
    res = client.get(f"/v1/hardware/{uuidutils.generate_uuid()}/", headers=user_auth_headers)
    assert res.status_code == 404
    assert re.match(
        "Hardware .* could not be found", res.json["error"]) is not None


def test_enroll_hardware(mocker, user_auth_headers, client: "FlaskClient"):
    mock_authorize = mocker.patch("doni.api.hardware.authorize")
    enroll_payload = {
        "name": "fake-name",
        "project_id": "fake-project_id",
        "hardware_type": utils.FAKE_HARDWARE_TYPE,
        "properties": {},
    }
    res = client.post(f"/v1/hardware/",
        headers=user_auth_headers,
        content_type="application/json",
        data=json.dumps(enroll_payload))
    assert res.status_code == 201
    assert mock_authorize.called_once_with("hardware:create")


FAKE_UUID = uuidutils.generate_uuid()
@pytest.mark.parametrize("path,req_kwargs", [
    pytest.param("/v1/hardware/", {"method": "GET"}, id="get_all"),
    pytest.param(f"/v1/hardware/{FAKE_UUID}/", {"method": "GET"}, id="get_one"),
    pytest.param("/v1/hardware/", {
        "method": "POST",
        "content_type": "application/json",
        "data": json.dumps({"name": "fake-name", "project_id": "fake_project_id"}),
    }, id="enroll"),
])
def test_policy_disallow(mocker, user_auth_headers, path, req_kwargs,
                         client: "FlaskClient", database: "utils.DBFixtures"):
    """Check that for a given handler, it properly handles authorization errors.
    """
    database.add_hardware(uuid=FAKE_UUID)
    mock_authorize = mocker.patch("doni.api.hardware.authorize")
    mock_authorize.side_effect = PolicyNotAuthorized("fakerule", {}, {})
    res = client.open(path, headers=user_auth_headers, **req_kwargs)
    assert res.status_code == 403
