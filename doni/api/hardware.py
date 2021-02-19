from flask import Blueprint
from flask import request

from doni.api.hooks import route
from doni.api.utils import make_error_response, object_to_dict
from doni.common import args
from doni.common import exception
from doni.common.policy import authorize
from doni.objects.hardware import Hardware

bp = Blueprint("hardware", __name__)


DEFAULT_FIELDS = ('name', 'project_id',)

HARDWARE_SCHEMA = {
    'type': 'object',
    'properties': {
        'name': {'type': ['string', 'null']},
        'uuid': {'type': ['string', 'null']},
        'project_id': {'type': ['string', 'null']},
    },
    'additionalProperties': False,
}

HARDWARE_VALIDATOR = args.schema(HARDWARE_SCHEMA)


@route("/", methods=["GET"], blueprint=bp)
def get_all():
    ctx = request.context
    authorize("hardware:get", ctx)
    return {
        "hardware": [
            object_to_dict(hw, fields=DEFAULT_FIELDS)
            for hw in Hardware.list(ctx)
        ],
    }


@route("/<uuid:hardware_uuid>/", methods=["GET"], blueprint=bp)
def get_one(hardware_uuid):
    ctx = request.context
    hardware = Hardware.get_by_uuid(ctx, str(hardware_uuid))
    authorize("hardware:get", ctx, hardware)
    return object_to_dict(hardware, fields=DEFAULT_FIELDS)


@route("/", methods=["POST"], blueprint=bp)
@args.validate(json_body=HARDWARE_VALIDATOR)
def create(json_body):
    ctx = request.context
    hardware = Hardware(ctx, **json_body)
    authorize("hardware:create", ctx, hardware)
    hardware.create()
    return object_to_dict(hardware, fields=DEFAULT_FIELDS), 201
