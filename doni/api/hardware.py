from flask import Blueprint, request

from doni.api.utils import make_error_response, object_to_dict
from doni.common import exception
from doni.common.policy import authorize
from doni.objects.hardware import Hardware

bp = Blueprint("hardware", __name__)


DEFAULT_FIELDS = ('name', 'project_id',)

@bp.route("/", methods=["GET"])
def get_all():
    return {
        "hardware": [
            object_to_dict(hw, fields=DEFAULT_FIELDS)
            for hw in Hardware.list(request.context)
        ],
    }


# TODO: most of this try/catch should be put in some decorator. Maybe
# flask has some decent hook for this.
@bp.route("/<uuid:hardware_uuid>/", methods=["GET"])
def get_one(hardware_uuid):
    ctx = request.context
    try:
        hardware = Hardware.get_by_uuid(ctx, str(hardware_uuid))
        if authorize("hardware:get", hardware, ctx):
            return object_to_dict(hardware, fields=DEFAULT_FIELDS)
    except exception.HardwareNotFound as exc:
        return make_error_response(str(exc), 404)
