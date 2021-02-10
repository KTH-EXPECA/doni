import threading

from oslo_db import api as oslo_db_api
from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import enginefacade
# db_utils have some utility functions that are useful
# from oslo_db.sqlalchemy import utils as db_utils
from oslo_log import log
from oslo_utils import uuidutils
from osprofiler import sqlalchemy as osp_sqlalchemy
import sqlalchemy as sa
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from doni.common import exception
from doni.conf import CONF
from doni.db import models

LOG = log.getLogger(__name__)

_CONTEXT = threading.local()


def get_instance():
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


def model_query(model, *args, **kwargs):
    """Query helper for simpler session usage.
    :param session: if present, the session to use
    """

    with _session_for_read() as session:
        query = session.query(model, *args)
        return query


class Connection(object):
    """SqlAlchemy connection."""
    def __init__(self):
        pass

    @oslo_db_api.retry_on_deadlock
    def create_hardware(self, values):
        if 'uuid' not in values:
            values['uuid'] = uuidutils.generate_uuid()

        hardware = models.Hardware()
        hardware.update(values)
        with _session_for_write() as session:
            try:
                session.add(hardware)
                session.flush()
            except db_exc.DBDuplicateEntry as exc:
                if 'name' in exc.columns:
                    raise exception.HardwareDuplicateName(name=values['name'])
                raise exception.HardwareAlreadyExists(uuid=values['uuid'])
        return hardware

    def get_hardware_by_id(self, hardware_id):
        query = model_query(models.Hardware).filter_by(id=hardware_id)
        try:
            return query.one()
        except NoResultFound:
            raise exception.HardwareNotFound(node=hardware_id)

    def get_hardware_by_uuid(self, hardware_uuid):
        query = model_query(models.Hardware).filter_by(uuid=hardware_uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.HardwareNotFound(node=hardware_uuid)

    def get_hardware_by_name(self, hardware_name):
        query = model_query(models.Hardware).filter_by(name=hardware_name)
        try:
            return query.one()
        except NoResultFound:
            raise exception.HardwareNotFound(node=hardware_name)
