"""Base classes for unit tests.

Allows overriding of config for use of fakes, and some magic for
inline callbacks.

"""

import os
import subprocess
import tempfile

import eventlet
eventlet.monkey_patch(os=False)
import fixtures
from oslo_concurrency import processutils
from oslo_config import fixture as config_fixture
from oslo_log import log as logging
from oslotest import base as oslo_test_base

from doni.conf import CONF
from doni.common import context as doni_context
from doni.common import config as doni_config

logging.register_options(CONF)
logging.setup(CONF, 'doni')


class TestCase(oslo_test_base.BaseTestCase):
    """Test case base class for all unit tests."""

    # By default block execution of utils.execute() and related functions.
    block_execute = True

    def setUp(self):
        """Run before each test method to initialize test environment."""
        super(TestCase, self).setUp()
        self.context = doni_context.get_admin_context()
        self._set_config()
        self.useFixture(fixtures.EnvironmentVariable('http_proxy'))

        # Ban running external processes via 'execute' like functions. If the
        # patched function is called, an exception is raised to warn the
        # tester.
        if self.block_execute:
            # NOTE(jlvillal): Intentionally not using mock as if you mock a
            # mock it causes things to not work correctly. As doing an
            # autospec=True causes strangeness. By using a simple function we
            # can then mock it without issue.
            self.patch(processutils, 'execute', do_not_call)
            self.patch(subprocess, 'call', do_not_call)
            self.patch(subprocess, 'check_call', do_not_call)
            self.patch(subprocess, 'check_output', do_not_call)
            # subprocess.Popen is a class
            self.patch(subprocess, 'Popen', DoNotCallPopen)

    def _set_config(self):
        self.cfg_fixture = self.useFixture(config_fixture.Config(CONF))
        self.config(use_stderr=False,
                    tempdir=tempfile.tempdir)
        self.set_defaults(host='fake-mini',
                          debug=True)
        self.set_defaults(connection="sqlite://",
                          sqlite_synchronous=False,
                          group='database')
        # This is a bit of a hack; this function does a lot more than
        # parse command line arguments! ;_;
        doni_config.parse_args([], default_config_files=[])

    def config(self, **kw):
        """Override config options for a test."""
        self.cfg_fixture.config(**kw)

    def set_defaults(self, **kw):
        """Set default values of config options."""
        group = kw.pop('group', None)
        for o, v in kw.items():
            self.cfg_fixture.set_default(o, v, group=group)

    def path_get(self, project_file=None):
        """Get the absolute path to a file. Used for testing the API.

        :param project_file: File whose path to return. Default: None.
        :returns: path to the specified file, or path to project root.
        """
        root = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            '..',
                                            '..',
                                            )
                               )
        if project_file:
            return os.path.join(root, project_file)
        else:
            return root


def do_not_call(*args, **kwargs):
    """Helper function to raise an exception if it is called"""
    raise Exception(
        "Don't call ironic_lib.utils.execute() / "
        "processutils.execute() or similar functions in tests!")


class DoNotCallPopen(object):
    """Helper class to mimic subprocess.popen()

    It's job is to raise an exception if it is called. We create stub functions
    so mocks that use autospec=True will work.
    """
    def __init__(self, *args, **kwargs):
        do_not_call(*args, **kwargs)

    def communicate(input=None):
        pass

    def kill():
        pass

    def poll():
        pass

    def terminate():
        pass

    def wait():
        pass
