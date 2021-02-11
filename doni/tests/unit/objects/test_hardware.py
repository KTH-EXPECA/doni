#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import pytest

from doni.objects.hardware import Hardware
from doni.tests.unit import utils


@pytest.fixture()
def existing_hardwares(database: "utils.DBFixtures"):
    """Fixture that creates a few fake hardware objects in the temp DB.

    This can be useful if a test requires operating against real data
    pre-existing in the DB, like for an update or destroy operation.
    """
    for _ in range(3):
        database.add_hardware()
    return database.hardwares


def test_create_hardware(database: "utils.DBFixtures"):
    fake_hardware = utils.get_test_hardware()
    hardware = Hardware(**fake_hardware)
    hardware.create()

    assert fake_hardware['name'] == hardware.name
    assert fake_hardware['project_id'] == hardware.project_id

    # Cleanup so that other tests in this module don't see this hardware item
    database.db.destroy_hardware(hardware.uuid)


def test_save_hardware(admin_context, existing_hardwares):
    hardware = Hardware(context=admin_context, **existing_hardwares[0])
    hardware.obj_reset_changes()
    hardware.name = 'new_fake_name'
    hardware.save()
    assert hardware.name == 'new_fake_name'


def test_destroy_hardware(admin_context, existing_hardwares):
    hardware = Hardware(context=admin_context, uuid=existing_hardwares[0]["uuid"])
    hardware.destroy()


def test_get_hardware_by_id(admin_context, existing_hardwares):
    existing = existing_hardwares[0]
    hardware = Hardware.get_by_id(admin_context, existing["id"])
    assert hardware.name == existing["name"]
    assert hardware.uuid == existing["uuid"]
    assert hardware.project_id == existing["project_id"]


def test_get_hardware_by_uuid(admin_context, existing_hardwares):
    existing = existing_hardwares[0]
    hardware = Hardware.get_by_uuid(admin_context, existing["uuid"])
    assert hardware.name == existing["name"]
    assert hardware.uuid == existing["uuid"]
    assert hardware.project_id == existing["project_id"]


def test_get_harware_by_name(admin_context, existing_hardwares):
    existing = existing_hardwares[0]
    hardware = Hardware.get_by_name(admin_context, existing["name"])
    assert hardware.name == existing["name"]
    assert hardware.uuid == existing["uuid"]
    assert hardware.project_id == existing["project_id"]


def test_list(admin_context, existing_hardwares):
    hardwares = Hardware.list(admin_context)
    assert len(hardwares) == len(existing_hardwares)
    assert hardwares[0].name == existing_hardwares[0]["name"]
    assert hardwares[0].uuid == existing_hardwares[0]["uuid"]
    assert hardwares[0].project_id == existing_hardwares[0]["project_id"]
