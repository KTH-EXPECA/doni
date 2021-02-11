import re

from flask.testing import FlaskClient
from oslo_utils import uuidutils

from doni.tests.unit import utils


def test_get_all_hardware(user_token, client: "FlaskClient"):
    res = client.get("/v1/hardware/", headers={"X-Auth-Token": user_token})
    assert res.status_code == 200
    assert res.json == {
        "hardware": [],
    }


def test_get_one_hardware(database: "utils.DBFixtures", user_token,
                          client: "FlaskClient"):
    hw = database.add_hardware()
    res = client.get(f"/v1/hardware/{hw['uuid']}/", headers={"X-Auth-Token": user_token})
    assert res.status_code == 200
    assert res.json["uuid"] == hw["uuid"]
    assert res.json["name"] == hw["name"]
    assert res.json["project_id"] == hw["project_id"]
    # Don't return internal IDs
    assert "id" not in res.json


def test_missing_hardware(user_token, client: "FlaskClient"):
    res = client.get(f"/v1/hardware/{uuidutils.generate_uuid()}/", headers={"X-Auth-Token": user_token})
    assert res.status_code == 404
    assert re.match(
        "Hardware .* could not be found", res.json["error"]) is not None
