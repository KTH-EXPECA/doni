import itertools

from doni.common.policies import base
from doni.common.policies import hardware


def list_rules():
    return itertools.chain(
        base.list_rules(),
        hardware.list_rules(),
    )
