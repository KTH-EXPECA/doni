"""The Doni Service API."""

import sys

from oslo_config import cfg
from oslo_log import log
from oslo_reports import guru_meditation_report as gmr
from oslo_reports import opts as gmr_opts

from doni.common import service as doni_service
from doni.common import wsgi
from doni import version

CONF = cfg.CONF

LOG = log.getLogger(__name__)


def main():
    # Parse config file and command line options, then start logging
    doni_service.prepare_service(sys.argv)
    gmr_opts.set_defaults(CONF)
    gmr.TextGuruMeditation.setup_autorun(version)

    # Build and start the WSGI app
    launcher = doni_service.process_launcher()
    server = wsgi.WSGIService('doni_api', CONF.api.enable_ssl_api)
    launcher.launch_service(server, workers=server.workers)
    launcher.wait()


if __name__ == '__main__':
    sys.exit(main())
