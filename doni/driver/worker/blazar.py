from doni.worker import BaseWorker

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.objects.hardware import Hardware
    from doni.worker import WorkerResult


class BlazarPhysicalHostWorker(BaseWorker):
    def process(self, hardware: "Hardware") -> "WorkerResult.Base":
        pass
