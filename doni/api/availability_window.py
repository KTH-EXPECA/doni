from flask import Blueprint
from flask import request

from doni.api.hooks import route
from doni.api import utils as api_utils
from doni.common import args
from doni.common.policy import authorize
from doni.objects.hardware import Hardware
from doni.objects.availability_window import AvailabilityWindow

bp = Blueprint("availability_window", __name__)


AVAILABILITY_WINDOW_SCHEMA = {
    "type": "object",
    "properties": {
        "start": args.optional(args.DATETIME),
        "end": args.optional(args.DATETIME),
    },
    "additionalProperties": False,
}

AVAILABILITY_WINDOW_VALIDATOR = args.schema(AVAILABILITY_WINDOW_SCHEMA)

DEFAULT_FIELDS = ('start', 'end',)


@route("/<uuid:hardware_uuid>/availability/", methods=["GET"], blueprint=bp)
def get_all(hardware_uuid):
    ctx = request.context
    hardware = Hardware.get_by_uuid(ctx, str(hardware_uuid))
    authorize("hardware:get", ctx, hardware)
    return {
        "availability": [
            api_utils.object_to_dict(win, fields=DEFAULT_FIELDS)
            for win in AvailabilityWindow.list(ctx, str(hardware_uuid))
        ],
    }
