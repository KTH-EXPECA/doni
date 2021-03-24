import threading

from oslo_db import api as oslo_db_api
from oslo_db import exception as db_exc
import oslo_db
from oslo_db.sqlalchemy import enginefacade
from oslo_db.sqlalchemy import utils as db_utils
from oslo_log import log
from oslo_utils import uuidutils
from osprofiler import sqlalchemy as osp_sqlalchemy
import sqlalchemy as sa
from sqlalchemy.orm.exc import NoResultFound

from doni.common import driver_factory
from doni.common import exception
from doni.conf import CONF
from doni.db import models
from doni.worker import WorkerState

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm.session import Session
    from typing import ContextManager

LOG = log.getLogger(__name__)

_CONTEXT = threading.local()


def get_instance():
    return Connection()


def _session_for_read() -> "ContextManager[Session]":
    return _wrap_session(enginefacade.reader.using(_CONTEXT))


# Please add @oslo_db_api.retry_on_deadlock decorator to all methods using
# _session_for_write (as deadlocks happen on write), so that oslo_db is able
# to retry in case of deadlocks.
def _session_for_write() -> "ContextManager[Session]":
    return _wrap_session(enginefacade.writer.using(_CONTEXT))


def _wrap_session(session):
    if CONF.profiler.enabled and CONF.profiler.trace_sqlalchemy:
        session = osp_sqlalchemy.wrap_session(sa, session)
    return session


def _paginate_query(model, limit=None, marker=None, sort_key=None,
                    sort_dir=None, query=None):
    if not query:
        query = model_query(model)
    sort_keys = ['id']
    if sort_key and sort_key not in sort_keys:
        sort_keys.insert(0, sort_key)
    try:
        query = db_utils.paginate_query(query, model, limit, sort_keys,
                                        marker=marker, sort_dir=sort_dir)
    except db_exc.InvalidSortKey:
        raise exception.InvalidParameterValue(
            ('The sort_key value "%(key)s" is an invalid field for sorting')
            % {'key': sort_key})
    return query.all()


def model_query(model, *args, **kwargs):
    """Query helper for simpler session usage.

    Args:
        model (models.Base): The model to query over.
    """
    with _session_for_read() as session:
        query = session.query(model, *args)
        return query


class Connection(object):
    """SqlAlchemy connection."""
    def __init__(self):
        pass

    @oslo_db_api.retry_on_deadlock
    def create_hardware(self, values: dict) -> "models.Hardware":
        if 'uuid' not in values:
            values['uuid'] = uuidutils.generate_uuid()

        hardware = models.Hardware()
        hardware.update(values)

        # Create one worker for each worker type we have.
        hardware_type = driver_factory.get_hardware_type(hardware.hardware_type)
        worker_tasks = []
        for worker_type in hardware_type.enabled_workers:
            task = models.WorkerTask()
            task.update({
                "uuid": uuidutils.generate_uuid(),
                "hardware_uuid": hardware.uuid,
                "worker_type": worker_type,
                "state": WorkerState.PENDING,
            })
            worker_tasks.append(task)

        with _session_for_write() as session:
            try:
                session.add(hardware)
                # Flush the hardware INSERT so that the foreign key constraint
                # for the worker tasks (on hardware UUID) can be satisfied.
                session.flush()
                for task in worker_tasks:
                    session.add(task)
            except db_exc.DBDuplicateEntry as exc:
                if 'name' in exc.columns:
                    raise exception.HardwareDuplicateName(name=values['name'])
                raise exception.HardwareAlreadyExists(uuid=values['uuid'])
        return hardware

    @oslo_db_api.retry_on_deadlock
    def update_hardware(self, hardware_uuid: str, values: dict) -> "models.Hardware":
        if 'uuid' in values:
            msg = ("Cannot overwrite UUID for existing Hardware.")
            raise exception.InvalidParameterValue(msg=msg)

        with _session_for_write() as session:
            query = session.query(models.Hardware).filter_by(uuid=hardware_uuid)
            try:
                count = query.update(values)
                if count != 1:
                    raise exception.HardwareNotFound(hardware=hardware_uuid)
            except db_exc.DBDuplicateEntry as exc:
                if 'name' in exc.columns:
                    raise exception.HardwareDuplicateName(name=values['name'])
                raise exception.HardwareAlreadyExists(uuid=values['uuid'])
            return query.one()

    @oslo_db_api.retry_on_deadlock
    def destroy_hardware(self, hardware_uuid: str):
        with _session_for_write() as session:
            query = session.query(models.Hardware).filter_by(uuid=hardware_uuid)
            try:
                _ = query.one()
            except NoResultFound:
                raise exception.HardwareNotFound(hardware=hardware_uuid)

            # NOTE: any attached relations that should be cascade-deleted should
            # be deleted here, before the parent Hardware record is deleted.

            query.delete()

    def get_hardware_by_id(self, hardware_id) -> "models.Hardware":
        query = model_query(models.Hardware).filter_by(id=hardware_id)
        try:
            return query.one()
        except NoResultFound:
            raise exception.HardwareNotFound(hardware=hardware_id)

    def get_hardware_by_uuid(self, hardware_uuid: str) -> "models.Hardware":
        query = model_query(models.Hardware).filter_by(uuid=hardware_uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.HardwareNotFound(hardware=hardware_uuid)

    def get_hardware_by_name(self, hardware_name: str) -> "models.Hardware":
        query = model_query(models.Hardware).filter_by(name=hardware_name)
        try:
            return query.one()
        except NoResultFound:
            raise exception.HardwareNotFound(hardware=hardware_name)

    def get_hardware_list(self, limit=None, marker=None, sort_key=None,
                          sort_dir=None) -> "list[models.Hardware]":
        return _paginate_query(
            models.Hardware, limit, marker, sort_key, sort_dir)

    def get_availability_window_list(self, hardware_uuid: str) -> "list[models.AvailabilityWindow]":
        query = model_query(models.AvailabilityWindow).filter_by(hardware_uuid=hardware_uuid)
        # TODO: how to communicate that hardware doesn't exist?
        return query.all()

    def get_worker_tasks_in_state(self, state: "WorkerState") -> "list[models.WorkerTask]":
        query = model_query(models.WorkerTask).filter_by(state=state)
        return query.all()

    def get_worker_tasks_for_hardware(self, hardware_uuid: str) -> "list[models.WorkerTask]":
        query = model_query(models.WorkerTask).filter_by(hardware_uuid=hardware_uuid)
        # TODO: how to communicate that hardware doesn't exist?
        return query.all()

    @oslo_db_api.retry_on_deadlock
    def update_worker_task(self, worker_task_uuid: str, values: dict) -> "models.WorkerTask":
        if 'uuid' in values:
            msg = ("Cannot overwrite UUID for existing WorkerTask.")
            raise exception.InvalidParameterValue(msg=msg)

        with _session_for_write() as session:
            query = session.query(models.WorkerTask).filter_by(uuid=worker_task_uuid)
            try:
                count = query.update(values)
                if count != 1:
                    raise exception.WorkerTaskNotFound(worker=worker_task_uuid)
            except db_exc.DBDuplicateEntry as exc:
                raise exception.WorkerTaskAlreadyExists(uuid=values['uuid'])
            return query.one()
