from flask import Blueprint

bp = Blueprint("monitor", __name__, url_prefix="/-")


@bp.route("/health")
def health_check():
    return "OK"
