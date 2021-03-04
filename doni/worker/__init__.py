import abc

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.objects.hardware import Hardware


class WorkerState(object):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    ERROR = "ERROR"
    STEADY = "STEADY"


class WorkerResult:
    class Base(abc.ABC):
        """Abstract base class for worker result types."""

    class Defer(Base):
        """Indicates that the worker should defer execution of this task.

        Use this class when your worker can't proceed but could reasonably
        proceed in the near future once some state in the system has become
        eventually consistent to expectations.
        """

    class Success(Base):
        """Indicates that the worker completed successfully.

        Attributes:
            payload (dict): Some detailed information about the success. This
                payload will be saved in the worker "state_details" field.
        """
        payload: dict = {}

        def __init__(self, payload: dict):
            self.payload = payload


class BaseWorker(abc.ABC):
    """A base interface implementing common functions for Driver Interfaces.

    Attributes:
        worker_type (str): The name of the worker type.
        validator_schema (dict): A JSON schema that will be used to validate
            hardware properties when this worker is enabled for the hardware.
    """

    worker_type = "base"
    validator_schema = {}

    @abc.abstractmethod
    def process(self, hardware: "Hardware") -> "WorkerResult.Base":
        pass
