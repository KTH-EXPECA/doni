import abc

from doni.common import args

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from doni.common.context import RequestContext
    from doni.objects.availability_window import AvailabilityWindow
    from doni.objects.hardware import Hardware
    from oslo_config.cfg import Opt


class WorkerState(object):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    ERROR = "ERROR"
    STEADY = "STEADY"


class WorkerResult:
    class Base(abc.ABC):
        """Abstract base class for worker result types.

        Attributes:
            payload (dict): Some detailed information about the result. This
                payload will be saved in the worker "state_details" field.
        """

        payload: dict = {}

        def __init__(self, payload: dict = None):
            self.payload = payload

    class Defer(Base):
        """Indicates that the worker should defer execution of this task.

        Use this class when your worker can't proceed but could reasonably
        proceed in the near future once some state in the system has become
        eventually consistent to expectations.
        """

    class Success(Base):
        """Indicates that the worker completed successfully."""


class BaseWorker(abc.ABC):
    """A base interface implementing common functions for Driver Interfaces.

    Attributes:
        worker_type (str): The name of the worker type.
        fields (list[WorkerField]): A list of fields supported and/or required
            by the worker.
    """

    worker_type = "base"
    fields: "list[WorkerField]" = []
    opts: "list[Opt]" = []
    opt_group: str = ""

    @abc.abstractmethod
    def process(
        self,
        context: "RequestContext",
        hardware: "Hardware",
        availability_windows: "list[AvailabilityWindow]" = None,
        state_details: "dict" = None,
    ) -> "WorkerResult.Base":
        pass

    def register_opts(self, conf):
        conf.register_opts(self.opts)

    def list_opts(self):
        return self.opts

    def json_schema(self):
        """Get the JSON schema for validating hardware properties for this worker.

        Returns:
            The JSON schema that validates that all worker fields are present
                and valid.
        """
        return {
            "type": "object",
            "properties": {field.name: field.schema or {} for field in self.fields},
            "required": [field.name for field in self.fields if field.required],
        }


class WorkerField(object):
    """A Hardware field supported by a worker.

    Each worker defines which fields it uses for its functionality. Worker fields
    are ultimately stored on the Hardware as properties, but must pass validation
    at the API layer when fields are being added/updated by the end user.

    Fields persisted in a Hardware's properties that are no longer in use or
    supported by any worker are hidden from API responses and are not visible
    except to admins.

    .. note::

       Two workers cannot currently share the same field. If a worker depends
       on some field managed by another worker, that is technically possible,
       but such a field should not be declared by the dependant worker.

    Attributes:
        name (str): The name of the field.
        schema (dict): A JSON schema to validate the field against. If not
            defined, the field is assumed to be a string.
        default (any): The default value for this field, if none is provided.
        required (bool): Whether the field is required if the worker is in use.
        private (bool): Whether the field should be hidden (not serialized) when
            requested by an unauthorized user.
        sensitive (bool): Whether the field should be masked when serialized.
        description (str): A user-friendly description of the field's purpose
            and contents.
    """

    def __init__(
        self,
        name,
        schema=None,
        default=None,
        required=False,
        private=False,
        sensitive=False,
        description=None,
    ):
        self.name = name
        self.schema = schema or args.STRING
        self.default = default
        self.required = required
        self.private = private
        self.sensitive = sensitive
        self.description = description
