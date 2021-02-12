import sys

from oslo_config import cfg
from oslo_policy import policy

from doni import PROJECT_NAME
from doni.common import policies

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.common.context import RequestContext
    from doni.objects.base import DoniBase

CONF = cfg.CONF
_ENFORCER = None

def get_enforcer():
    CONF([], project=PROJECT_NAME)
    global _ENFORCER
    if not _ENFORCER:
        _ENFORCER = policy.Enforcer(CONF)
        _ENFORCER.register_defaults(policies.list_rules())
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


def authorize(rule, target: "DoniBase", context: "RequestContext"):
    return get_enforcer().authorize(
        rule, target.as_dict(), context.to_policy_values(), do_raise=True)
