import abc

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.objects.hardware import Hardware


class AbstractWorker(abc.ABC):
    """A base interface implementing common functions for Driver Interfaces.

    Attributes:
        supported (bool): Indicates if the driver is supported. This will be
            set to False for drivers which are untested or otherwise not
            production-ready. (Default True)
        worker_type (str): The name of the worker type.
    """

    supported = True
    worker_type = "base"

    @abc.abstractmethod
    def on_hardware_create(self, hardware: "Hardware"):
        pass

    @abc.abstractmethod
    def on_hardware_update(self, harware: "Hardware"):
        pass
