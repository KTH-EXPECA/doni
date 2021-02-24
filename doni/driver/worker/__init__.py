import abc

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.objects.hardware import Hardware


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
    def on_hardware_create(self, hardware: "Hardware"):
        pass

    @abc.abstractmethod
    def on_hardware_update(self, harware: "Hardware"):
        pass
