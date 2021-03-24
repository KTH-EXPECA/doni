from doni.db import api as db_api
from doni.objects import base
from doni.objects import fields as object_fields

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from doni.common.context import RequestContext


@base.DoniObjectRegistry.register
class AvailabilityWindow(base.DoniObject):
    # Version 1.0: Initial version
    VERSION = "1.0"

    dbapi = db_api.get_instance()

    fields = {
        "id": object_fields.IntegerField(),
        "uuid": object_fields.UUIDField(),
        "hardware_uuid": object_fields.UUIDField(),
        "start": object_fields.DateTimeField(),
        "end": object_fields.DateTimeField(),
    }

    @classmethod
    def list_for_hardware(
        cls, context: "RequestContext", hardware_uuid: str
    ) -> "list[AvailabilityWindow]":
        """Return a list of AvailabilityWindow objects for a specific hardware.

        Args:
            context (RequestContext): security context.
            hardware_uuid (str): The Hardware to look up availability windows on.

        Returns:
            A list of :class:`AvailabilityWindow` objects.
        """
        db_windows = cls.dbapi.get_hardware_availability_window_list(hardware_uuid)
        return cls._from_db_object_list(context, db_windows)

    @classmethod
    def list(cls, context: "RequestContext") -> "list[AvailabilityWindow]":
        """Return a list of all AvailabilityWindow objects.

        Args:
            context (RequestContext): security context.

        Returns:
            A list of :class:`AvailabilityWindow` objects.
        """
        db_windows = cls.dbapi.get_availability_window_list()
        return cls._from_db_object_list(context, db_windows)
