import abc

class HardwareType(abc.ABC):
    """A base hardware type.

    A hardware type is a collection of workers considered valid for that type,
    and an optional list of default fields, which should be applied during any
    Hardware update or create operation.

    Attributes:
        enabled_workers (list[str]): A list of which workers can be enabled for
            this hardware type.
        default_fields (dict): A mapping of field names to a default value.
            This can be used to fill in defaults for worker required fields,
            for example.
    """
    enabled_workers = ()
    default_fields = ()


class Baremetal(HardwareType):
    """A bare metal node, provisionable via e.g., Ironic
    """
    enabled_workers = ("blazar", "ironic",)

    default_fields = {
        "blazar_resource_type": "physical:host",
    }


class Fake(HardwareType):
    """A fake hardware type, useful for development and testing.
    """
