import threading

from oslo_db import api as oslo_db_api
# db_exc is available for common DB exceptions
# from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import enginefacade
# db_utils have some utility functions that are useful
# from oslo_db.sqlalchemy import utils as db_utils
from oslo_log import log
from osprofiler import sqlalchemy as osp_sqlalchemy
import sqlalchemy as sa

from doni.conf import CONF
from doni.db import api

LOG = log.getLogger(__name__)

_CONTEXT = threading.local()


def get_backend():
    """The backend is this module itself."""
    return Connection()


def _session_for_read():
    return _wrap_session(enginefacade.reader.using(_CONTEXT))


# Please add @oslo_db_api.retry_on_deadlock decorator to all methods using
# _session_for_write (as deadlocks happen on write), so that oslo_db is able
# to retry in case of deadlocks.
def _session_for_write():
    return _wrap_session(enginefacade.writer.using(_CONTEXT))


def _wrap_session(session):
    if CONF.profiler.enabled and CONF.profiler.trace_sqlalchemy:
        session = osp_sqlalchemy.wrap_session(sa, session)
    return session


class Connection(api.Connection):
    """SqlAlchemy connection."""
