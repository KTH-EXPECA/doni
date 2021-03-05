from collections import defaultdict
import itertools

import futurist
from futurist import periodics
from futurist import rejection
from futurist import waiters
from oslo_log import log

from doni.common import driver_factory
from doni.common import exception
from doni.conf import CONF
from doni.db import api as db_api
from doni.objects.hardware import Hardware
from doni.objects.worker_task import WorkerTask
from doni.worker import WorkerResult
from doni.worker import WorkerState

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from futurist import Future

LOG = log.getLogger(__name__)


class WorkerManager(object):

    def __init__(self, host):
        if not host:
            host = CONF.host
        self.host = host
        self._started = False
        self._shutdown = None
        self.dbapi = None

    def start(self, admin_context=None):
        """Initialize the worker host.

        Args:
            admin_context (RequestContext): The admin context to pass to
                periodic tasks.

        Raises:
            RuntimeError: when worker is already running.
            DriversNotLoaded: when no drivers are enabled on the worker.
            DriverNotFound: if a driver is enabled that does not exist.
            DriverLoadError: if an enabled driver cannot be loaded.
        """
        if self._started:
            raise RuntimeError('Attempt to start an already running worker')

        self._shutdown = False

        if not self.dbapi:
            LOG.debug(f'Initializing database client for {self.host}')
            self.dbapi = db_api.get_instance()

        rejection_func = rejection.reject_when_reached(
            CONF.worker.task_pool_size)
        self._executor = futurist.GreenThreadPoolExecutor(
            max_workers=CONF.worker.task_pool_size,
            check_and_reject=rejection_func)
        """Executor for performing tasks async."""

        hardware_types = driver_factory.hardware_types()
        worker_types = driver_factory.worker_types()

        if len(hardware_types) < 1 or len(worker_types) < 1:
            msg = ("Worker %s cannot be started because no hardware types "
                   "were specified in the 'enabled_hardware_types' config "
                   "option.")
            LOG.error(msg, self.host)
            raise exception.DriversNotLoaded(host=self.host)

        self._periodic_tasks = self._collect_periodic_tasks(
            list(worker_types.values()), admin_context)
        # Start periodic tasks
        self._periodic_tasks_worker = self._executor.submit(
            self._periodic_tasks.start, allow_empty=True)
        self._periodic_tasks_worker.add_done_callback(
            self._on_periodic_tasks_stop)

        self._started = True

    @periodics.periodic(
        spacing=CONF.worker.process_pending_task_interval,
        run_immediately=True
    )
    def process_pending(self, admin_context):
        hardware_table = {hw.uuid: hw for hw in Hardware.list(admin_context)}
        pending_tasks = WorkerTask.list_pending(admin_context)

        # Attempt to execute tasks in parallel if possible. We assume that
        # two tasks associated with different hardwares can be executed in
        # parallel. First, group all the tasks by their associated hardware,
        # then construct a few "layers" of tasks. A hardware item having two
        # pending tasks will have its first task executed along with any other
        # first tasks for other hardwares. After the entire set of first tasks
        # completes, the set of second tasks will be executed, and so on.
        grouped_tasks = defaultdict(list)
        for task in pending_tasks:
            grouped_tasks[task.hardware_uuid].append(task)
        task_batches = [
            list(filter(None, batch))
            for batch in itertools.zip_longest(*grouped_tasks.values())
        ]  # type: list[list[WorkerTask]]

        for i, batch in enumerate(task_batches):
            done, _ = waiters.wait_for_all([
                self._spawn_worker(self._process_task, task, hardware_table)
                for task in batch
            ])
            failures = [f.exception() for f in done if f.exception()]
            LOG.info((
                f"Processed batch {i+1}: successfully processed "
                f"{len(done) - len(failures)} tasks, {len(failures)} failed."))
            if failures:
                LOG.debug(f"failures={failures}")

    def _process_task(self, task: "WorkerTask", hardware_table: "dict[str,Hardware]"):
        assert task.state == WorkerState.PENDING
        pending_state_details = task.state_details.copy()

        task.state = WorkerState.IN_PROGRESS
        task.state_details = {}
        task.save()

        try:
            worker = driver_factory.get_worker_type(task.worker_type)
            hardware = hardware_table.get(task.hardware_uuid)
            if not hardware:
                raise exception.HardwareNotFound(hardware=task.hardware_uuid)
            process_result = worker.process(task)
        except exception.DoniException as exc:
            message = str(exc)
            LOG.error((
                f"{task.worker_type}: failed to process "
                f"{task.hardware_uuid}: {message}"))
            task.state = WorkerState.ERROR
            task.state_details = {"message": str(exc)}
        else:
            if isinstance(process_result, WorkerResult.Defer):
                task.state = WorkerState.PENDING
                # Update the deferral count; we may utilize this for back-off
                # at some point.
                pending_state_details["defer_count"] = (
                    pending_state_details.get("defer_count", 0) + 1)
                task.state_details = pending_state_details
            elif isinstance(process_result, WorkerResult.Success):
                LOG.info(
                    f"{task.worker_type}: finished processing {task.hardware_uuid}")
                task.state = WorkerState.STEADY
                task.state_details = process_result.payload
            else:
                LOG.warning((
                    f"{task.worker_type}: unexpected return type "
                    f"'{type(process_result).__name__}' from processing "
                    "function. Expected 'WorkerResult' type. Result will be "
                    "interpreted as success result."))
                task.state = WorkerState.STEADY
                task.state_details = {"result": process_result}

        # Commit changes to task
        task.save()

    def _collect_periodic_tasks(self, workers, admin_context):
        """Collect driver-specific periodic tasks.

        All tasks receive the admin context as an argument.

        Args:
            admin_context (DoniContext): Administrator context to pass to tasks.
        """
        LOG.debug('Collecting periodic tasks')
        # Look for tasks both on the manager itself and all workers
        objects = [self] + workers
        return periodics.PeriodicWorker.create(objects, args=(admin_context,),
            executor_factory=periodics.ExistingExecutor(self._executor))

    def stop(self):
        if self._shutdown:
            return
        self._shutdown = True
        # Waiting here to give workers the chance to finish.
        self._periodic_tasks.stop()
        self._periodic_tasks.wait()
        self._executor.shutdown(wait=True)

        self._started = False

    def _on_periodic_tasks_stop(self, fut):
        try:
            fut.result()
        except Exception as exc:
            LOG.critical('Periodic tasks worker has failed: %s', exc)
        else:
            LOG.info('Successfully shut down periodic tasks')

    def _spawn_worker(self, func, *args, **kwargs) -> "Future":
        """Create a greenthread to run func(*args, **kwargs).

        Spawns a greenthread if there are free slots in pool, otherwise raises
        exception. Execution control returns immediately to the caller.

        Returns:
            Future object.

        Raises:
            NoFreeWorker if worker pool is currently full.
        """
        try:
            return self._executor.submit(func, *args, **kwargs)
        except futurist.RejectedSubmission:
            raise exception.NoFreeWorker()
