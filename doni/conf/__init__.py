from oslo_config import cfg

from doni.conf import default

CONF = cfg.CONF

default.register_opts(CONF)
