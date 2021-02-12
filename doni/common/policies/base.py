from oslo_policy import policy

ROLE_ADMIN = 'role:admin'
RULE_ADMIN_OR_OWNER = 'is_admin:True or project_id:%(project_id)s'
RULE_ADMIN_API = 'rule:context_is_admin'
RULE_DENY_EVERYBODY = 'rule:deny_everybody'

rules = [
    policy.RuleDefault(
        name='context_is_admin',
        check_str=ROLE_ADMIN
    ),
    policy.RuleDefault(
        name='admin_or_owner',
        check_str=RULE_ADMIN_OR_OWNER
    ),
    policy.RuleDefault(
        name='admin_api',
        check_str=RULE_ADMIN_API
    ),
    policy.RuleDefault(
        name="deny_everybody",
        check_str="!",
        description="Default rule for deny everybody."),
]


def list_rules():
    return rules
