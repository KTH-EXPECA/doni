from contextlib import contextmanager

from doni.db import api as db_api


@contextmanager
def transaction():
    with db_api._session_for_write():
        yield
