import itertools

from doni.common.policies import hardware

SYSTEM_ADMIN = 'role:admin'
SYSTEM_ADMIN_OR_PROJECT_MEMBER = 'role:admin or project_id:%(project_id)s'


def list_rules():
    return itertools.chain(
        hardware.list_rules(),
    )
