import eventlet
from oslo_config import cfg
from oslo_log import log

from doni import objects

eventlet.monkey_patch(os=False)

log.register_options(cfg.CONF)
log.setup(cfg.CONF, 'doni')

objects.register_all()
