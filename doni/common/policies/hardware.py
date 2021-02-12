from oslo_policy import policy

from doni.common.policies import base

HARDWARE = "hardware:%s"

rules = [
    policy.DocumentedRuleDefault(
        name=HARDWARE % "get",
        check_str=base.RULE_ADMIN_OR_OWNER,
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
        check_str=base.ROLE_ADMIN,
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
        check_str=base.RULE_ADMIN_OR_OWNER,
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
        check_str=base.RULE_ADMIN_OR_OWNER,
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
    return rules
