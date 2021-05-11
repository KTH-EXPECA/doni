"""
The Ironic Management Service
"""

import sys

from oslo_config import cfg
from oslo_log import log
from oslo_reports import guru_meditation_report as gmr
from oslo_reports import opts as gmr_opts
from oslo_service import service

from doni import __version__
from doni.common import service as doni_service

CONF = cfg.CONF

LOG = log.getLogger(__name__)


def main():
    doni_service.prepare_service(sys.argv)
    gmr_opts.set_defaults(CONF)
    gmr.TextGuruMeditation.setup_autorun(__version__, conf=CONF)
    launcher = service.launch(
        CONF,
        doni_service.DoniService(CONF.host, "doni.worker.manager", "WorkerManager"),
        restart_method="reload",
    )
    launcher.wait()
