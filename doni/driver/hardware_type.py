class HardwareType(object):
    pass

class Baremetal(HardwareType):
    """A bare metal node, provisionable via e.g., Ironic
    """
    enabled_workers = ['blazar', 'ironic']
