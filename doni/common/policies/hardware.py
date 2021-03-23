from oslo_policy import policy

from doni.common import policies

HARDWARE = "hardware:%s"

rules = [
    policy.DocumentedRuleDefault(
        name=HARDWARE % "get",
        check_str=policies.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
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
        check_str=policies.SYSTEM_ADMIN,
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
        check_str=policies.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
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
        check_str=policies.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
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
