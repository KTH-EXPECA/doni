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

from doni.common import exception
from doni.db import api as db_api
from doni.objects.hardware import Hardware
from doni.tests.unit.objects import utils as db_utils


HARDWARE_COUNTER = 0

@pytest.fixture()
def existing_hardwares():
    """Fixture that creates a few fake hardware objects in the temp DB.

    This can be useful if a test requires operating against real data
    pre-existing in the DB, like for an update or destroy operation.
    """
    DBAPI = db_api.get_instance()
    def _make_fake_hardware():
        global HARDWARE_COUNTER
        HARDWARE_COUNTER += 1
        fake_hw = db_utils.get_test_hardware(
            name=f"fake_name_{HARDWARE_COUNTER}")
        # ID will be auto-assigned by DB
        fake_hw.pop("id")
        return DBAPI.create_hardware(fake_hw)
    hardwares = [_make_fake_hardware() for _ in range(3)]
    yield [hw.as_dict() for hw in hardwares]
    for hw in hardwares:
        try:
            DBAPI.destroy_hardware(hw.uuid)
        except exception.HardwareNotFound:
            # Allow tests to destroy hardware
            pass


def test_create_hardware(fake_hardware):
    hardware = Hardware(**fake_hardware)
    hardware.create()

    assert fake_hardware['name'] == hardware.name
    assert fake_hardware['project_id'] == hardware.project_id

    # Cleanup so that other tests in this module don't see this hardware item
    db_api.get_instance().destroy_hardware(hardware.uuid)


def test_save_hardware(context, existing_hardwares):
    hardware = Hardware(context=context, **existing_hardwares[0])
    hardware.obj_reset_changes()
    hardware.name = 'new_fake_name'
    hardware.save()
    assert hardware.name == 'new_fake_name'


def test_destroy_hardware(context, existing_hardwares):
    hardware = Hardware(context=context, uuid=existing_hardwares[0]["uuid"])
    hardware.destroy()


def test_get_hardware_by_id(context, existing_hardwares):
    existing = existing_hardwares[0]
    hardware = Hardware.get_by_id(context, existing["id"])
    assert hardware.name == existing["name"]
    assert hardware.uuid == existing["uuid"]
    assert hardware.project_id == existing["project_id"]


def test_get_hardware_by_uuid(context, existing_hardwares):
    existing = existing_hardwares[0]
    hardware = Hardware.get_by_uuid(context, existing["uuid"])
    assert hardware.name == existing["name"]
    assert hardware.uuid == existing["uuid"]
    assert hardware.project_id == existing["project_id"]


def test_get_harware_by_name(context, existing_hardwares):
    existing = existing_hardwares[0]
    hardware = Hardware.get_by_name(context, existing["name"])
    assert hardware.name == existing["name"]
    assert hardware.uuid == existing["uuid"]
    assert hardware.project_id == existing["project_id"]


def test_list(context, existing_hardwares):
    hardwares = Hardware.list(context)
    assert len(hardwares) == len(existing_hardwares)
    assert hardwares[0].name == existing_hardwares[0]["name"]
    assert hardwares[0].uuid == existing_hardwares[0]["uuid"]
    assert hardwares[0].project_id == existing_hardwares[0]["project_id"]
