from oslo_config import cfg

from doni.conf import default
from doni.conf import worker

CONF = cfg.CONF

CONF.register_opts(default.opts, group=default.GROUP)
CONF.register_opts(worker.opts, group=worker.GROUP)
