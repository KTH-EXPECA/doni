import abc

from doni.common import args
from doni.worker import WorkerField


class HardwareType(abc.ABC):
    """A base hardware type.

    A hardware type is a collection of workers considered valid for that type,
    and an optional list of default fields, which should be applied during any
    Hardware update or create operation.

    Attributes:
        enabled_workers (list[str]): A list of which workers can be enabled for
            this hardware type.
        default_fields (list[WorkerField]): A list of worker fields that apply
            to this hardware type generically.
    """

    enabled_workers: "list[str]" = ()
    default_fields: "list[WorkerField]" = []


class Baremetal(HardwareType):
    """A bare metal node, provisionable via e.g., Ironic"""

    enabled_workers = (
        "blazar.physical_host",
        "ironic",
    )

    default_fields = [
        WorkerField(
            "management_address",
            schema=args.HOST_OR_IP,
            required=True,
            private=True,
            description="The out-of-band address, e.g. IPMI.",
        ),
        WorkerField(
            "interfaces",
            schema=args.array(args.NETWORK_DEVICE, min_items=1),
            required=True,
            description=("A list of network interfaces installed on the node."),
        ),
    ]


class Fake(HardwareType):
    """A fake hardware type, useful for development and testing."""

    enabled_workers = ("fake-worker",)

    default_fields = [
        WorkerField("default_field", schema=args.STRING),
        WorkerField("default_required_field", schema=args.STRING, required=True),
    ]
