from flask import Blueprint, request

from doni.api import utils as api_utils
from doni.api.hooks import route
from doni.common import args
from doni.common.policy import authorize
from doni.objects.availability_window import AvailabilityWindow
from doni.objects.hardware import Hardware

bp = Blueprint("availability_window", __name__)


DEFAULT_FIELDS = (
    "start",
    "end",
)


@route("/<uuid:hardware_uuid>/availability", methods=["GET"], blueprint=bp)
def get_all(hardware_uuid):
    ctx = request.context
    hardware = Hardware.get_by_uuid(ctx, str(hardware_uuid))
    authorize("hardware:get", ctx, hardware)
    return {
        "availability": [
            api_utils.object_to_dict(win, fields=DEFAULT_FIELDS)
            for win in AvailabilityWindow.list_for_hardware(ctx, str(hardware_uuid))
        ],
    }
