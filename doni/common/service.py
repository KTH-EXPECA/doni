from oslo_log import log
from oslo_service import service
from oslo_utils import importutils

from doni import objects
from doni import PROJECT_NAME
from doni.common import config
from doni.common import context as doni_context
from doni.conf import CONF
from doni.conf import opts

LOG = log.getLogger(__name__)


def prepare_service(argv=None):
    """Initialize a service.
    """
    argv = [] if argv is None else argv
    log.register_options(CONF)
    opts.update_opt_defaults()
    config.parse_args(argv)
    # NOTE(vdrok): We need to setup logging after argv was parsed, otherwise
    # it does not properly parse the options from config file and uses defaults
    # from oslo_log
    log.setup(CONF, PROJECT_NAME)
    # rpc.init(CONF)
    objects.register_all()


def process_launcher():
    return service.ProcessLauncher(CONF, restart_method='mutate')


class DoniService(service.Service):
    def __init__(self, host, manager_module, manager_class):
        super().__init__()
        manager_module = importutils.try_import(manager_module)
        manager_class = getattr(manager_module, manager_class)
        self.manager = manager_class(host)
        self.name = f'{manager_module}.{manager_class}'
        self.host = host

    def start(self):
        super().start()
        admin_context = doni_context.get_admin_context()
        self.manager.start(admin_context)
        LOG.info(f'Created service {self.name} on host {self.host}.')

    def stop(self):
        super().stop(graceful=True)
        self.manager.stop()
        LOG.info(f'Stopped service {self.name} on host {self.host}.')
