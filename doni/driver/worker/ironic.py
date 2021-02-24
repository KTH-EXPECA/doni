from doni.common import args
from doni.driver.worker import BaseWorker

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.objects.hardware import Hardware


class IronicWorker(BaseWorker):

    validator_schema = {
        "type": "object",
        "properties": {
            "ipmi_address": args.HOST_OR_IP,
            "ipmi_username": args.STRING,
            "ipmi_password": args.STRING,
            "ipmi_terminal_port": args.PORT_RANGE,
        },
        "required": ["ipmi_address", "ipmi_username", "ipmi_password"],
    }

    def on_hardware_create(self, hardware: "Hardware"):
        pass

    def on_hardware_update(self, harware: "Hardware"):
        pass
