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

import contextlib

from doni.objects.hardware import Hardware
from doni.tests.unit.db import utils as db_utils


@contextlib.contextmanager
def fake_hardware_list():
    def _make_fake_hardware(idx):
        fake_hw = db_utils.get_test_hardware(name=f"fake_name_{idx}")
        # ID will be auto-assigned by DB
        fake_hw.pop("id")
        hw = Hardware(**fake_hw)
        hw.create()
        return hw
    hardwares = [_make_fake_hardware(i) for i in range(3)]
    yield [hw.as_dict() for hw in hardwares]
    for hw in hardwares:
        hw.destroy()


def test_create_hardware(fake_hardware):
    hardware = Hardware(**fake_hardware)
    hardware.create()

    assert fake_hardware['name'] == hardware.name
    assert fake_hardware['project_id'] == hardware.project_id

def test_save_hardware(context):
    with fake_hardware_list() as hardwares:
        hardware = Hardware(context=context, **hardwares[0])
        hardware.obj_reset_changes()
        hardware.name = 'new_fake_name'
        hardware.save()
        assert hardware.name == 'new_fake_name'

# def test_destroy(self):
#     hardware = Hardware(context=self.context,
#                                         id=self.fake_hardware['id'])
#     hardware.destroy()

# def test_get_by_id(self):
#     hardware = Hardware.get_by_id(
#         self.context, self.fake_hardware['id'])

#     self.assertEqual(self.fake_hardware['name'], hardware.name)
#     self.assertEqual(self.fake_hardware['uuid'], hardware.uuid)
#     self.assertEqual(self.fake_hardware['project_id'], hardware.project_id)

# def test_get_by_uuid(self):
#     hardware = Hardware.get_by_uuid(
#         self.context, self.fake_hardware['uuid'])

#     self.assertEqual(self.fake_hardware['name'], hardware.name)
#     self.assertEqual(self.fake_hardware['uuid'], hardware.uuid)
#     self.assertEqual(self.fake_hardware['extra'], hardware.extra)

# def test_get_by_name(self):
#     hardware = Hardware.get_by_name(
#         self.context, self.fake_hardware['name'])

#     self.assertEqual(self.fake_hardware['name'], hardware.name)
#     self.assertEqual(self.fake_hardware['uuid'], hardware.uuid)
#     self.assertEqual(self.fake_hardware['extra'], hardware.extra)

# def test_list(self):
#     hardwares = Hardware.list(self.context)
#     self.assertEqual(1, len(hardwares))
#     self.assertEqual(self.fake_hardware['name'], hardwares[0].name)
#     self.assertEqual(self.fake_hardware['uuid'], hardwares[0].uuid)
#     self.assertEqual(self.fake_hardware['extra'], hardwares[0].extra)

# def test_list_by_names(self):
#     names = [self.fake_hardware['name']]
#     hardwares = Hardware.list_by_names(self.context, names)

#     self.assertEqual(1, len(hardwares))
#     self.assertEqual(self.fake_hardware['name'], hardwares[0].name)
#     self.assertEqual(self.fake_hardware['uuid'], hardwares[0].uuid)
#     self.assertEqual(self.fake_hardware['extra'], hardwares[0].extra)
