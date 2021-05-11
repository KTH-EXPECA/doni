from contextlib import contextmanager

from doni.db import api as db_api


@contextmanager
def transaction():
    """A helper context manager for batching several object operations."""
    with db_api._session_for_write():
        yield


def register_all():
    from doni.objects.availability_window import AvailabilityWindow
    from doni.objects.hardware import Hardware
    from doni.objects.worker_task import WorkerTask
