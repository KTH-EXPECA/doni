from doni.common import args
from doni.worker import BaseWorker
from doni.worker import WorkerField

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.objects.hardware import Hardware
    from doni.worker import WorkerResult


class IronicWorker(BaseWorker):

    fields = [
        WorkerField("baremetal_driver", schema=args.enum(["ipmi"]),
            default="ipmi", private=True, description=(
                "The Ironic hardware driver that will control this node. See "
                "https://docs.openstack.org/ironic/latest/admin/drivers.html "
                "for a list of all Ironic hardware types. "
                "Currently only the 'ipmi' driver is supported.")),
        WorkerField("ipmi_username", schema=args.STRING, private=True,
            description=(
                "The IPMI username to use for IPMI authentication. Only used "
                "if the ``baremetal_driver`` is 'ipmi'.")),
        WorkerField("ipmi_password", schema=args.STRING, private=True, sensitive=True,
            description=(
                "The IPMI password to use for IPMI authentication. Only used "
                "if the ``baremetal_driver`` is 'ipmi'.")),
    ]

    def process(self, hardware: "Hardware") -> "WorkerResult.Base":
        # Look up Ironic node by UUID (should match hardware UUID).
        # If found, we will be doing a patch.
