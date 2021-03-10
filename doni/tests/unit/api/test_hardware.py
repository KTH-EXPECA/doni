import json
import re

from flask.testing import FlaskClient
from oslo_policy.policy import PolicyNotAuthorized
from oslo_utils import uuidutils
import pytest

from doni.tests.unit import utils


def _assert_hardware_json_ok(hw_json, hw):
    assert hw_json["uuid"] == hw["uuid"]
    assert hw_json["name"] == hw["name"]
    assert hw_json["project_id"] == hw["project_id"]

    # Don't return internal IDs
    assert "id" not in hw_json

    # Return all fields
    properties = hw_json["properties"]
    assert properties["private-field"] == hw["properties"]["private-field"]
    # Ensure sensitive fields masked
    assert properties["sensitive-field"] == "************"
    assert properties["private-and-sensitive-field"] == "************"


def test_get_all_hardware(mocker, user_auth_headers, client: "FlaskClient",
                          database: "utils.DBFixtures"):
    mock_authorize = mocker.patch("doni.api.hardware.authorize")
    hw = database.add_hardware()
    res = client.get("/v1/hardware/", headers=user_auth_headers)
    assert res.status_code == 200
    assert len(res.json["hardware"]) == 1
    _assert_hardware_json_ok(res.json["hardware"][0], hw)
    assert mock_authorize.called_once_with("hardware:get")


def test_get_all_hardware_empty(mocker, user_auth_headers, client: "FlaskClient"):
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
    _assert_hardware_json_ok(res.json, hw)
     # Test nested workers object(s) -- these are only returned on this endpoint.
    workers = res.json["workers"]
    assert len(workers) == 1
    assert workers[0]["worker_type"] == utils.FAKE_WORKER_TYPE
    assert isinstance(workers[0]["state_details"], dict)
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
        "properties": {
            "default_required_field": "fake-default_required_field",
        },
    }
    res = client.post(f"/v1/hardware/",
        headers=user_auth_headers,
        content_type="application/json",
        data=json.dumps(enroll_payload))
    assert res.status_code == 201
    assert mock_authorize.called_once_with("hardware:create")


def test_enroll_hardware_fails_validation(mocker, user_auth_headers, client: "FlaskClient"):
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
    assert res.status_code == 400


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


def test_update_hardware(mocker, user_auth_headers, client: "FlaskClient",
                         database: "utils.DBFixtures"):
    database.add_hardware(uuid=FAKE_UUID)
    mock_authorize = mocker.patch("doni.api.hardware.authorize")
    patch = [{"path": "/name", "op": "replace", "value": "new-fake-name"}]
    res = client.patch(f"/v1/hardware/{FAKE_UUID}/",
        headers=user_auth_headers,
        content_type="application/json",
        data=json.dumps(patch))
    assert res.status_code == 200
    assert mock_authorize.called_once_with("hardware:update")
    assert res.json["uuid"] == FAKE_UUID
    assert res.json["name"] == "new-fake-name"
