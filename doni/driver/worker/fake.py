from doni.common import args
from doni.worker import BaseWorker
from doni.worker import WorkerField
from doni.worker import WorkerResult

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.objects.hardware import Hardware


class FakeWorker(BaseWorker):

    fields = [
        WorkerField("private-field", private=True),
        WorkerField("private-and-sensitive-field", private=True, sensitive=True),
        WorkerField("sensitive-field", sensitive=True),
    ]

    def process(self, hardware: "Hardware") -> "WorkerResult.Base":
        print(f"fake: processing hardware {hardware.uuid}")
        return WorkerResult.Success({
            "fake-result": f"fake-worker-prefix-{hardware.uuid}"
        })
