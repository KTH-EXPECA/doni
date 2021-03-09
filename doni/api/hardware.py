from flask import Blueprint
from flask import request

from doni.api.hooks import route
from doni.api import utils as api_utils
from doni.common import args
from doni.common import driver_factory
from doni.common.policy import authorize
from doni.objects.availability_window import AvailabilityWindow
from doni.objects.hardware import Hardware
from doni.objects.transaction import transaction

bp = Blueprint("hardware", __name__)


DEFAULT_FIELDS = ('name', 'project_id', 'hardware_type', 'properties',)

HARDWARE_SCHEMA = {
    'type': 'object',
    'properties': {
        'name': args.STRING,
        'uuid': args.STRING,
        'hardware_type': args.STRING,
        'project_id': args.STRING,
        'properties': {'type': 'object', 'additionalProperties': True},
    },
    'additionalProperties': False,
}

_HARDWARE_VALIDATOR = None


def hardware_validator():
    global _HARDWARE_VALIDATOR
    if not _HARDWARE_VALIDATOR:
        enabled_workers = driver_factory.worker_types()
        enabled_hardware_types = driver_factory.hardware_types()

        hardware_type_schemas = []
        for hwt_name, hwt in enabled_hardware_types.items():
            worker_schemas = [
                worker.validator_schema
                for worker_name, worker in enabled_workers.items()
                if worker_name in hwt.enabled_workers
            ]
            hwt_schema = {
                "type": "object",
                "properties": {
                    "hardware_type": {"const": hwt_name}
                }
            }
            # Validate nested properties against worker validators
            if worker_schemas:
                hwt_schema["properties"]["properties"] = {
                    "allOf": worker_schemas
                }
            hardware_type_schemas.append(hwt_schema)

        _HARDWARE_VALIDATOR = args.schema({
            "definitions": {
                "hardware": HARDWARE_SCHEMA
            },
            "allOf": [
                # Check base hardware schema
                {"$ref": "#/definitions/hardware"},
                # Check schema for hardware types
                {"oneOf": hardware_type_schemas},
            ]
        })

    return _HARDWARE_VALIDATOR


@route("/", methods=["GET"], blueprint=bp)
def get_all():
    ctx = request.context
    authorize("hardware:get", ctx)
    return {
        "hardware": [
            api_utils.object_to_dict(hw, fields=DEFAULT_FIELDS)
            for hw in Hardware.list(ctx)
        ],
    }


@route("/<hardware_uuid>/", methods=["GET"], blueprint=bp)
@args.validate(hardware_uuid=args.uuid)
def get_one(hardware_uuid=None):
    ctx = request.context
    hardware = Hardware.get_by_uuid(ctx, hardware_uuid)
    authorize("hardware:get", ctx, hardware)
    return api_utils.object_to_dict(hardware, fields=DEFAULT_FIELDS)


@route("/", methods=["POST"], json_body="hardware_params", blueprint=bp)
@args.validate(hardware_params=hardware_validator())
def create(hardware_params=None):
    ctx = request.context

    hardware = Hardware(ctx, **hardware_params)
    authorize("hardware:create", ctx, hardware)
    hardware.create()

    return api_utils.object_to_dict(hardware, fields=DEFAULT_FIELDS), 201


@route("/<hardware_uuid>/", methods=["PATCH"], json_body="patch", blueprint=bp)
@args.validate(hardware_uuid=args.uuid, patch=args.schema(args.PATCH))
def update(hardware_uuid=None, patch=None):
    ctx = request.context

    hardware = Hardware.get_by_uuid(ctx, hardware_uuid)
    authorize("hardware:update", ctx, hardware)

    state = {
        "self": hardware,
    }

    if api_utils.is_path_updated(patch, "/availability"):
        # If updating availability windows, pull current values to compute the
        # delta from the patch.
        state["availability"] = AvailabilityWindow.list(ctx, hardware_uuid)

    patched_state = api_utils.apply_jsonpatch(state, patch)

    with transaction():
        api_utils.apply_patch_updates(hardware, patched_state)
        hardware.save()

        if "availability" in patched_state:
            to_add, to_update, to_remove = api_utils.apply_patch_updates_to_list(
                state["availability"], patched_state["availability"])
            for window in to_add:
                window.create()
            for window in to_update:
                window.save()
            for window in to_remove:
                window.destroy()

    return api_utils.object_to_dict(hardware, fields=DEFAULT_FIELDS)
