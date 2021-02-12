import eventlet
from oslo_config import cfg
from oslo_log import log

from doni import objects
from doni import PROJECT_NAME

eventlet.monkey_patch(os=False)

log.register_options(cfg.CONF)
log.setup(cfg.CONF, PROJECT_NAME)

objects.register_all()
