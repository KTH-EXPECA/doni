from doni.worker import BaseWorker
from doni.worker import WorkerResult

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.objects.hardware import Hardware


class FakeWorker(BaseWorker):
    def process(self, hardware: "Hardware") -> "WorkerResult.Base":
        print(f"fake: processing hardware {hardware.uuid}")
        return WorkerResult.Success({
            "fake-result": f"fake-worker-prefix-{hardware.uuid}"
        })
