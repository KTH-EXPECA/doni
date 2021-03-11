from keystoneauth1 import loading as ks_loading
from oslo_utils import uuidutils
import pytest
from unittest import mock

from doni.driver.worker.ironic import IronicWorker
from doni.objects.hardware import Hardware
from doni.tests.unit import utils
from doni.worker import WorkerResult

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.common.context import RequestContext


TEST_HARDWARE_UUID = uuidutils.generate_uuid()


@pytest.fixture
def ironic_worker(test_config):
    """Generate a test IronicWorker and ensure the environment is configured for it.

    Much of this is black magic to appease the gods of oslo_config.
    """
    # Configure the app to use a hardware type valid for this worker.
    test_config.config(enabled_hardware_types=["baremetal"], enabled_worker_types=["ironic"])

    worker = IronicWorker()
    worker.register_opts(test_config)
    # NOTE(jason):
    # At application runtime, Keystone auth plugins are registered dynamically
    # depending on what auth_type is provided in the config. I'm not sure how
    # it's possible to even express that here, as there's a chicken-or-egg
    # question of how you set the auth_type while it's registering all the
    # auth options. So we register the manually here.
    plugin = ks_loading.get_plugin_loader("v3password")
    opts = ks_loading.get_auth_plugin_conf_options(plugin)
    test_config.register_opts(opts, group=worker.opt_group)

    test_config.config(
        group="ironic",
        auth_type="v3password",
        auth_url="http://localhost:5000",
        username="fake-username",
        user_domain_name="fake-user-domain-name",
        password="fake-password",
        project_name="fake-project-name",
        project_domain_name="fake-project-domain-name",
    )
    return worker


@pytest.fixture
def mock_ironic_request(mocker):
    mock_adapter = mock.MagicMock()
    mocker.patch("doni.driver.worker.ironic.keystone.get_adapter").return_value = mock_adapter
    return mock_adapter.request


def get_fake_hardware(database: "utils.DBFixtures"):
    db_hw = database.add_hardware(uuid=TEST_HARDWARE_UUID, hardware_type="baremetal", properties={
        "baremetal_driver": "fake-driver",
        "management_address": "fake-management_address",
        "ipmi_username": "fake-ipmi_username",
        "ipmi_password": "fake-ipmi_password",
    })
    return Hardware(**db_hw)


def test_ironic_create_node(mock_ironic_request, admin_context: "RequestContext",
                            ironic_worker: "IronicWorker", database: "utils.DBFixtures"):
    """Test that new nodes are created if not already existing."""
    def _fake_ironic(path, method=None, json=None, **kwargs):
        if method == "get" and path == f"/nodes/{TEST_HARDWARE_UUID}":
            return utils.MockResponse(404)
        elif method == "post" and path == f"/nodes":
            assert json["uuid"] == TEST_HARDWARE_UUID
            assert json["driver"] == "fake-driver"
            assert json["driver_info"] == {
                "ipmi_address": "fake-management_address",
                "ipmi_username": "fake-ipmi_username",
                "ipmi_password": "fake-ipmi_password",
                "ipmi_terminal_port": None,
            }
            return utils.MockResponse(201, {"created_at": "fake-created_at"})
        else:
            raise NotImplementedError("Unexpected request signature")

    mock_ironic_request.side_effect = _fake_ironic

    result = ironic_worker.process(admin_context, get_fake_hardware(database))

    assert isinstance(result, WorkerResult.Success)
    assert result.payload == {"created_at": "fake-created_at"}
    assert mock_ironic_request.call_count == 2


def test_ironic_update_node(mocker, mock_ironic_request, admin_context: "RequestContext",
                            ironic_worker: "IronicWorker", database: "utils.DBFixtures"):
    """Test that existing nodes are patched from hardware properties."""
    get_node_count = 0
    patch_node_count = 0
    def _fake_ironic(path, method=None, json=None, **kwargs):
        if method == "get" and path == f"/nodes/{TEST_HARDWARE_UUID}":
            nonlocal get_node_count
            get_node_count += 1
            if get_node_count == 1:
                provision_state = "manageable"
            else:
                provision_state = "available"
            return utils.MockResponse(200, {
                "uuid": TEST_HARDWARE_UUID,
                "name": "ironic-name",
                "maintenance": False,
                "provision_state": provision_state,
                "driver": "fake-driver",
                "driver_info": {
                    # Ironic-provided value should be replaced
                    "ipmi_address": "ironic-ipmi_address",
                    "ipmi_username": "fake-ipmi_username",
                    "ipmi_password": "fake-ipmi_password",
                    "ipmi_terminal_port": 30000,
                },
            })
        elif method == "patch" and path == f"/nodes/{TEST_HARDWARE_UUID}":
            nonlocal patch_node_count
            patch_node_count += 1
            if patch_node_count == 1:
                # Validate patch for node properties
                assert json == [{
                    "op": "replace",
                    "path": "/driver_info/ipmi_address",
                    "value": "fake-management_address"
                }]
            else:
                # Validate patch for setting node to available
                assert json == [{
                    "op": "replace",
                    "path": "/provision_state",
                    "value": "available"
                }]
            return utils.MockResponse(200)
        else:
            raise NotImplementedError("Unexpected request signature")

    # 'sleep' is used to wait for provision state changes
    mocker.patch("time.sleep")
    mock_ironic_request.side_effect = _fake_ironic

    result = ironic_worker.process(admin_context, get_fake_hardware(database))

    assert isinstance(result, WorkerResult.Success)
    assert result.payload is None
    # call 1 = get the node
    # call 2 = patch the node's properties
    # call 3 = patch the node back to 'available' state
    # call 4 = get the node to see if state changed
    assert mock_ironic_request.call_count == 4


def test_ironic_update_defer_on_maintenance(mock_ironic_request, admin_context: "RequestContext",
                                            ironic_worker: "IronicWorker", database: "utils.DBFixtures"):
    """Test that nodes in maintenance mode are not updated."""
    def _fake_ironic(path, method=None, json=None, **kwargs):
        if method == "get" and path == f"/nodes/{TEST_HARDWARE_UUID}":
            return utils.MockResponse(200, {
                "uuid": TEST_HARDWARE_UUID,
                "maintenance": True,
            })
        else:
            raise NotImplementedError("Unexpected request signature")

    mock_ironic_request.side_effect = _fake_ironic

    result = ironic_worker.process(admin_context, get_fake_hardware(database))

    assert isinstance(result, WorkerResult.Defer)
    assert "in maintenance" in result.payload["message"]
    assert mock_ironic_request.call_count == 1
