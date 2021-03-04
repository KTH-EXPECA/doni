from doni.db import api as db_api
from doni.objects import base
from doni.objects import fields as object_fields
from doni.worker import WorkerState

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.common.context import RequestContext


@base.DoniObjectRegistry.register
class WorkerTask(base.DoniObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = db_api.get_instance()

    fields = {
        'id': object_fields.IntegerField(),
        'uuid': object_fields.UUIDField(),
        'hardware_uuid': object_fields.UUIDField(),
        'worker_type': object_fields.StringField(),
        'state': object_fields.WorkerStateField(),
        'details': object_fields.FlexibleDictField(),
    }

    @property
    def is_pending(self):
        return self.state == WorkerState.PENDING

    def save(self, context: "RequestContext"=None):
        """Save updates to this WorkerTask.

        Column-wise updates will be made based on the result of
        :func:`obj_what_changed`.

        Args:
            context (RequestContext): security context.
        """
        updates = self.obj_get_changes()
        db_worker_task = self.dbapi.update_worker_task(self.uuid, updates)
        self._from_db_object(self._context, self, db_worker_task)

    @classmethod
    def list_pending(cls, context: "RequestContext") -> "list[WorkerTask]":
        db_workers = cls.dbapi.get_worker_tasks_in_state(WorkerState.PENDING)
        return cls._from_db_object_list(context, db_workers)

    @classmethod
    def list_for_hardware(cls, context: "RequestContext", hardware_uuid: str) -> "list[WorkerTask]":
        pass
