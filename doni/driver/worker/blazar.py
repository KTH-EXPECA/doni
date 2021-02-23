from doni.driver.worker import AbstractWorker

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.objects.hardware import Hardware


class BlazarWorker(AbstractWorker):
    def on_hardware_create(self, hardware: "Hardware"):
        pass

    def on_hardware_update(self, harware: "Hardware"):
        pass
