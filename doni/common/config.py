from oslo_config import cfg
import osprofiler.opts as profiler_opts


def parse_args(argv, default_config_files=None):
    """Initialize configuration defaults from argv.
    """
    from doni import __version__
    from doni import PROJECT_NAME

    cfg.CONF(argv[1:],
             project=PROJECT_NAME,
             version=__version__,
             default_config_files=default_config_files)
    profiler_opts.set_defaults(cfg.CONF)
    # rpc.set_defaults(control_exchange=PROJECT_NAME)
