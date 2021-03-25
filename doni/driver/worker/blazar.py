from typing import TYPE_CHECKING

from doni.worker import BaseWorker

if TYPE_CHECKING:
    from doni.common.context import RequestContext
    from doni.objects.availability_window import AvailabilityWindow
    from doni.objects.hardware import Hardware
    from doni.worker import WorkerResult


class BlazarPhysicalHostWorker(BaseWorker):
    def process(
        self,
        context: "RequestContext",
        hardware: "Hardware",
        availability_windows: "list[AvailabilityWindow]" = None,
        state_details: "dict" = None,
    ) -> "WorkerResult.Base":
        pass
