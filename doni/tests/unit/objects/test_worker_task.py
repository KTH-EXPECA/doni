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
from doni.objects.worker_task import WorkerTask
from doni.tests.unit import utils
from doni.worker import WorkerState


def test_list_for_hardware(admin_context, database: "utils.DBFixtures"):
    hw = database.add_hardware()
    tasks = WorkerTask.list_for_hardware(admin_context, hw["uuid"])
    assert len(tasks) == 1


def test_list_for_hardware_disabled_workers(
    test_config, admin_context, database: "utils.DBFixtures"
):
    test_config.config(enabled_worker_types=[])
    hw = database.add_hardware()
    tasks = WorkerTask.list_for_hardware(admin_context, hw["uuid"])
    assert len(tasks) == 0


def test_list_pending(admin_context, database: "utils.DBFixtures"):
    for _ in range(3):
        database.add_hardware()
    tasks = WorkerTask.list_pending(admin_context)
    assert len(tasks) == 3


def test_list_pending_with_steady(admin_context, database: "utils.DBFixtures"):
    for _ in range(3):
        database.add_hardware()
    tasks = WorkerTask.list_pending(admin_context)
    tasks[0].state = WorkerState.IN_PROGRESS
    tasks[0].save()
    assert len(WorkerTask.list_pending(admin_context)) == 2


def test_save(admin_context, database: "utils.DBFixtures"):
    hw = database.add_hardware()
    task = WorkerTask.list_for_hardware(admin_context, hw["uuid"])[0]
    task.state_details = {"foo": "bar"}
    task.save()
    assert task.state_details == {"foo": "bar"}


def test_save_invalid_transition(admin_context, database: "utils.DBFixtures"):
    hw = database.add_hardware()
    task = WorkerTask.list_for_hardware(admin_context, hw["uuid"])[0]
    with pytest.raises(ValueError):
        # Cannot move from PENDING to STEADY
        task.state = WorkerState.STEADY
