from doni.db import api as db_api
from doni.objects import base
from doni.objects import fields as object_fields

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.common.context import RequestContext


@base.DoniObjectRegistry.register
class Worker(base.DoniObject):
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
