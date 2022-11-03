from doni.common import args
from doni.driver.hardware_type.base import BaseHardwareType
from doni.worker import WorkerField


BM_INTERFACES_SCHEMA = args.array(
    {
        "type": "object",
        "properties": {
            "name": args.STRING,
            "mac_addr": args.STRING,
            "local_link_information": args.array(
                {
                    "switch_id": args.STRING,
                    "port_id": args.STRING,
                    "switch_info": args.STRING,
                },
                min_items=1,
            ),
        },
        "required": ["name", "local_link_information"],
        "additionalProperties": False,
    },
    min_items=0,
)


class WorkerNode(BaseHardwareType):
    """A k8s worker node"""

    enabled_workers = (
        "blazar.device",
        "k8s",
    )

    default_fields = [
        WorkerField(
            "machine_name",
            schema=args.enum(["k8s-worker"]),
            required=True,
            default="k8s-worker",
            description=(
                "The type of device -- this must be an explicitly supported device type"
            ),
        ),
        WorkerField(
            "bm_interfaces",
            schema=BM_INTERFACES_SCHEMA,
            required=True,
            description=("A list of network interfaces installed on the node."),
        ),
        WorkerField(
            "cpu_arch",
            schema=args.CPU_ARCH,
            required=True,
            default="x86_64",
            description=("The CPU architecture."),
        ),
    ]

