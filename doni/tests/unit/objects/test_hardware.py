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

from unittest import mock

from doni.common import context
from doni.db import api as dbapi
from doni import objects
from doni.tests.unit.db import base as db_base
from doni.tests.unit.db import utils as db_utils


class TestHardwareObject(db_base.DbTestCase):

    def setUp(self):
        super(TestHardwareObject, self).setUp()
        self.ctxt = context.get_admin_context()
        self.fake_hardware = db_utils.get_test_hardware()

    @mock.patch.object(dbapi.IMPL, 'create_hardware', autospec=True)
    def test_create(self, mock_create):
        hardware = objects.Hardware(context=self.context, **self.fake_hardware)
        mock_create.return_value = db_utils.get_test_hardware()

        hardware.create()

        args, _kwargs = mock_create.call_args
        self.assertEqual(1, mock_create.call_count)

        self.assertEqual(self.fake_hardware['name'], hardware.name)
        self.assertEqual(self.fake_hardware['project_id'], hardware.project_id)

    @mock.patch.object(dbapi.IMPL, 'update_hardware', autospec=True)
    def test_save(self, mock_update):
        hardware = objects.Hardware(context=self.context, **self.fake_hardware)
        hardware.obj_reset_changes()

        mock_update.return_value = db_utils.get_test_hardware(
            name='new_fake_name')

        hardware.name = 'new_fake_name'
        hardware.save()

        mock_update.assert_called_once_with(
            self.fake_hardware['uuid'],
            {'name': 'new_fake_name'})

        self.assertEqual('new_fake_name', hardware.name)

    @mock.patch.object(dbapi.IMPL, 'destroy_hardware', autospec=True)
    def test_destroy(self, mock_destroy):
        hardware = objects.Hardware(context=self.context,
                                          id=self.fake_hardware['id'])

        hardware.destroy()

        mock_destroy.assert_called_once_with(self.fake_hardware['id'])

    @mock.patch.object(dbapi.IMPL, 'get_hardware_by_id', autospec=True)
    def test_get_by_id(self, mock_get):
        mock_get.return_value = self.fake_hardware

        hardware = objects.Hardware.get_by_id(
            self.context, self.fake_hardware['id'])

        mock_get.assert_called_once_with(self.fake_hardware['id'])
        self.assertEqual(self.fake_hardware['name'], hardware.name)
        self.assertEqual(self.fake_hardware['uuid'], hardware.uuid)
        self.assertEqual(self.fake_hardware['project_id'], hardware.project_id)

    @mock.patch.object(dbapi.IMPL, 'get_hardware_by_uuid',
                       autospec=True)
    def test_get_by_uuid(self, mock_get):
        mock_get.return_value = self.fake_hardware

        hardware = objects.Hardware.get_by_uuid(
            self.context, self.fake_hardware['uuid'])

        mock_get.assert_called_once_with(self.fake_hardware['uuid'])
        self.assertEqual(self.fake_hardware['name'], hardware.name)
        self.assertEqual(self.fake_hardware['uuid'], hardware.uuid)
        self.assertEqual(self.fake_hardware['extra'], hardware.extra)

    @mock.patch.object(dbapi.IMPL, 'get_hardware_by_name',
                       autospec=True)
    def test_get_by_name(self, mock_get):
        mock_get.return_value = self.fake_hardware

        hardware = objects.Hardware.get_by_name(
            self.context, self.fake_hardware['name'])

        mock_get.assert_called_once_with(self.fake_hardware['name'])
        self.assertEqual(self.fake_hardware['name'], hardware.name)
        self.assertEqual(self.fake_hardware['uuid'], hardware.uuid)
        self.assertEqual(self.fake_hardware['extra'], hardware.extra)

    @mock.patch.object(dbapi.IMPL, 'get_hardware_list', autospec=True)
    def test_list(self, mock_list):
        mock_list.return_value = [self.fake_hardware]

        hardwares = objects.Hardware.list(self.context)

        mock_list.assert_called_once_with(limit=None, marker=None,
                                          sort_dir=None, sort_key=None)
        self.assertEqual(1, len(hardwares))
        self.assertEqual(self.fake_hardware['name'], hardwares[0].name)
        self.assertEqual(self.fake_hardware['uuid'], hardwares[0].uuid)
        self.assertEqual(self.fake_hardware['extra'], hardwares[0].extra)

    @mock.patch.object(dbapi.IMPL, 'get_hardware_list_by_names',
                       autospec=True)
    def test_list_by_names(self, mock_list):
        mock_list.return_value = [self.fake_hardware]

        names = [self.fake_hardware['name']]
        hardwares = objects.Hardware.list_by_names(self.context, names)

        mock_list.assert_called_once_with(names)
        self.assertEqual(1, len(hardwares))
        self.assertEqual(self.fake_hardware['name'], hardwares[0].name)
        self.assertEqual(self.fake_hardware['uuid'], hardwares[0].uuid)
        self.assertEqual(self.fake_hardware['extra'], hardwares[0].extra)
