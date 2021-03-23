import itertools
import sys

from oslo_config import cfg
from oslo_policy import policy

from doni import PROJECT_NAME

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.common.context import RequestContext
    from doni.objects.base import DoniBase

CONF = cfg.CONF
_ENFORCER = None

SYSTEM_ADMIN = 'role:admin'
SYSTEM_ADMIN_OR_PROJECT_MEMBER = 'role:admin or project_id:%(project_id)s'
HARDWARE = "hardware:%s"

hardware_rules = [
    policy.DocumentedRuleDefault(
        name=HARDWARE % "get",
        check_str=SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        description="Get hardware details",
        operations=[
            {
                "path": "/v1/hardware/{hardware_uuid}",
                "method": "GET"
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=HARDWARE % "create",
        check_str=SYSTEM_ADMIN,
        description="Enroll a hardware",
        operations=[
            {
                "path": "/v1/hardware",
                "method": "POST"
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=HARDWARE % "update",
        check_str=SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        description="Update a hardware",
        operations=[
            {
                "path": "/v1/hardware/{hardware_uuid}",
                "method": "PATCH"
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=HARDWARE % "delete",
        check_str=SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        description="Delete a hardware",
        operations=[
            {
                "path": "/v1/hardware/{hardware_uuid}",
                "method": "DELETE"
            }
        ]
    )
]


def list_rules():
    return itertools.chain(
        hardware_rules,
    )


def get_enforcer():
    CONF([], project=PROJECT_NAME)
    global _ENFORCER
    if not _ENFORCER:
        _ENFORCER = policy.Enforcer(CONF)
        _ENFORCER.register_defaults(list_rules())
    return _ENFORCER


def get_oslo_policy_enforcer():
    # This method is for use by oslopolicy CLI scripts. Those scripts need the
    # 'output-file' and 'namespace' options, but having those in sys.argv means
    # loading the Ironic config options will fail as those are not expected to
    # be present. So we pass in an arg list with those stripped out.

    conf_args = []
    # Start at 1 because cfg.CONF expects the equivalent of sys.argv[1:]
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].strip('-') in ['namespace', 'output-file']:
            i += 2
            continue
        conf_args.append(sys.argv[i])
        i += 1

    cfg.CONF(conf_args, project=PROJECT_NAME)

    return get_enforcer()


def authorize(rule, context: "RequestContext", target: "DoniBase"=None):
    """Check if the request is authorized according to a given rule.

    Args:
        rule (str): The policy rule.
        context (RequestContext): The request context.
        target (DoniBase): The target domain object, if any.

    Raises:
        PolicyNotAuthorized: If the rule is not satisfied.
    """
    target = target.as_dict() if target else {}
    return get_enforcer().authorize(
        rule, target, context.to_policy_values(), do_raise=True)
