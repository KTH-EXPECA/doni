from oslo_config import cfg
import osprofiler.opts as profiler_opts

from doni.common import rpc
from doni import __version__


def parse_args(argv, default_config_files=None):
    """Initialize configuration defaults from argv.
    """
    cfg.CONF(argv[1:],
             project='doni',
             version=__version__,
             default_config_files=default_config_files)
    profiler_opts.set_defaults(cfg.CONF)
    rpc.set_defaults(control_exchange='doni')
