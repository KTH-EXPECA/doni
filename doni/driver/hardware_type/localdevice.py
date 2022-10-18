from doni.common import args
from doni.driver.hardware_type.base import BaseHardwareType
from doni.worker import WorkerField


SUPPORTED_MACHINE_NAMES = [
    "sdr-host",
]

INTERFACES_SCHEMA = args.array(
    {
        "type": "object",
        "properties": {
            "name": args.STRING,
            "enabled": args.BOOLEAN,
            # There is no mac_address format in jsonschema yet[1]
            # [1]: https://github.com/json-schema-org/json-schema-spec/issues/540
            "mac_address": args.STRING,
            "vendor": args.STRING,
            "model": args.STRING,
            "switch_id": args.STRING,
            "switch_port_id": args.STRING,
            "switch_info": args.STRING,
        },
        "required": ["name", "mac_address"],
        "additionalProperties": False,
    },
    min_items=1,
)


class LocalDevice(BaseHardwareType):
    """A local device"""

    enabled_workers = (
        "blazar.device",
        "k8s",
    )

    default_fields = [
        WorkerField(
            "machine_name",
            schema=args.enum(SUPPORTED_MACHINE_NAMES),
            required=True,
            description=(
                "The type of device -- this must be an explicitly supported device type"
            ),
        ),
        WorkerField(
            "contact_email",
            schema=args.EMAIL,
            required=True,
            private=True,
            description=(
                "A contact email to use for any communication about the device. In "
                "some cases secure messages containing enrollment credentials may be "
                "sent here, so ensure it is an active mailbox."
            ),
        ),
        WorkerField(
            "management_address",
            schema=args.HOST_OR_IP,
            required=True,
            private=True,
            description="The out-of-band address",
        ),
        WorkerField(
            "interfaces",
            schema=INTERFACES_SCHEMA,
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
        WorkerField(
            "device_profiles",
            schema=args.array(args.STRING),
            required=False,
            private=False,
            description=(
                "A set of device profiles (representing a set of Linux resources that make "
                "it possible to access an attached peripheral, such as a USB or GPU "
                "device) currently supported on this device. Ideally this field is set via "
                "an automated process that has verified the required devices for the "
                "profile are all available."
            ),
        ),
    ]
