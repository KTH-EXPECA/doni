from oslo_log import log
from oslo_service import service

from doni.common import config
from doni.conf import CONF
from doni.conf import opts
from doni import objects


def prepare_service(argv=None):
    argv = [] if argv is None else argv
    log.register_options(CONF)
    opts.update_opt_defaults()
    config.parse_args(argv)
    # NOTE(vdrok): We need to setup logging after argv was parsed, otherwise
    # it does not properly parse the options from config file and uses defaults
    # from oslo_log
    log.setup(CONF, 'ironic')
    objects.register_all()


def process_launcher():
    return service.ProcessLauncher(CONF, restart_method='mutate')
