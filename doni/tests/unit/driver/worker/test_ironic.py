import time
from typing import TYPE_CHECKING
from unittest import mock

import pytest
from keystoneauth1 import loading as ks_loading
from oslo_utils import uuidutils

from doni.driver.worker.ironic import (
    PROVISION_STATE_TIMEOUT,
    IronicNodeProvisionStateTimeout,
    IronicWorker,
)
from doni.objects.hardware import Hardware
from doni.tests.unit import utils
from doni.worker import WorkerResult

if TYPE_CHECKING:
    from doni.common.context import RequestContext


TEST_HARDWARE_UUID = uuidutils.generate_uuid()


@pytest.fixture
def ironic_worker(test_config):
    """Generate a test IronicWorker and ensure the environment is configured for it.

    Much of this is black magic to appease the gods of oslo_config.
    """
    # Configure the app to use a hardware type valid for this worker.
    test_config.config(
        enabled_hardware_types=["baremetal"], enabled_worker_types=["ironic"]
    )

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


def get_fake_ironic(mocker, request_fn):
    mock_adapter = mock.MagicMock()
    mock_request = mock_adapter.request
    mock_request.side_effect = request_fn
    mocker.patch(
        "doni.driver.worker.ironic._get_ironic_adapter"
    ).return_value = mock_adapter
    return mock_request


def get_fake_hardware(database: "utils.DBFixtures"):
    db_hw = database.add_hardware(
        uuid=TEST_HARDWARE_UUID,
        name="fake-name",
        hardware_type="baremetal",
        properties={
            "baremetal_driver": "fake-driver",
            "management_address": "fake-management_address",
            "ipmi_username": "fake-ipmi_username",
            "ipmi_password": "fake-ipmi_password",
        },
    )
    return Hardware(**db_hw)


def test_ironic_create_node(
    mocker,
    admin_context: "RequestContext",
    ironic_worker: "IronicWorker",
    database: "utils.DBFixtures",
):
    """Test that new nodes are created if not already existing."""
    get_node_count = 0
    patch_node_count = 0

    def _fake_ironic_for_create(path, method=None, json=None, **kwargs):
        if method == "get" and path == f"/nodes/{TEST_HARDWARE_UUID}":
            nonlocal get_node_count
            get_node_count += 1
            if get_node_count == 1:
                return utils.MockResponse(404)
            elif get_node_count == 2:
                return utils.MockResponse(200, {"provision_state": "manageable"})
            elif get_node_count == 3:
                return utils.MockResponse(200, {"provision_state": "available"})
        elif method == "post" and path == f"/nodes":
            assert json["uuid"] == TEST_HARDWARE_UUID
            assert json["name"] == "fake-name"
            assert json["driver"] == "fake-driver"
            assert json["driver_info"] == {
                "ipmi_address": "fake-management_address",
                "ipmi_username": "fake-ipmi_username",
                "ipmi_password": "fake-ipmi_password",
                "ipmi_terminal_port": None,
            }
            return utils.MockResponse(201, {"created_at": "fake-created_at"})
        elif method == "patch" and path == f"/nodes/{TEST_HARDWARE_UUID}":
            nonlocal patch_node_count
            patch_node_count += 1
            if patch_node_count == 1:
                provision_state = "manageable"
            elif patch_node_count == 2:
                provision_state = "available"
            assert json == [
                {"op": "replace", "path": "/provision_state", "value": provision_state}
            ]
            return utils.MockResponse(200, {})
        raise NotImplementedError("Unexpected request signature")

    fake_ironic = get_fake_ironic(mocker, _fake_ironic_for_create)

    result = ironic_worker.process(admin_context, get_fake_hardware(database))

    assert isinstance(result, WorkerResult.Success)
    assert result.payload == {"created_at": "fake-created_at"}
    # call 1 = check that node does not exist
    # call 2 = create the node
    # call 3 = patch the node to 'manageable' state
    # call 4 = get the node to see if state changed
    # call 5 = patch the node to 'available' state
    # call 6 = get the node to see if state changed
    assert fake_ironic.call_count == 6


def test_ironic_update_node(
    mocker,
    admin_context: "RequestContext",
    ironic_worker: "IronicWorker",
    database: "utils.DBFixtures",
):
    """Test that existing nodes are patched from hardware properties."""
    get_node_count = 0
    patch_node_count = 0

    def _fake_ironic_for_update(path, method=None, json=None, **kwargs):
        if method == "get" and path == f"/nodes/{TEST_HARDWARE_UUID}":
            nonlocal get_node_count
            get_node_count += 1
            if get_node_count == 1:
                provision_state = "manageable"
            else:
                provision_state = "available"
            return utils.MockResponse(
                200,
                {
                    "uuid": TEST_HARDWARE_UUID,
                    "name": "fake-name",
                    "created_at": "fake-created_at",
                    "maintenance": False,
                    "provision_state": provision_state,
                    "driver": "fake-driver",
                    "driver_info": {
                        # Ironic-provided value should be replaced
                        "ipmi_address": "REPLACE-ipmi_address",
                        "ipmi_username": "fake-ipmi_username",
                        "ipmi_password": "fake-ipmi_password",
                        "ipmi_terminal_port": 30000,
                    },
                },
            )
        elif method == "patch" and path == f"/nodes/{TEST_HARDWARE_UUID}":
            nonlocal patch_node_count
            patch_node_count += 1
            if patch_node_count == 1:
                # Validate patch for node properties
                assert json == [
                    {
                        "op": "replace",
                        "path": "/driver_info/ipmi_address",
                        "value": "fake-management_address",
                    }
                ]
            else:
                # Validate patch for setting node to available
                assert json == [
                    {"op": "replace", "path": "/provision_state", "value": "available"}
                ]
            return utils.MockResponse(200)
        raise NotImplementedError("Unexpected request signature")

    # 'sleep' is used to wait for provision state changes
    mocker.patch("time.sleep")
    fake_ironic = get_fake_ironic(mocker, _fake_ironic_for_update)

    result = ironic_worker.process(admin_context, get_fake_hardware(database))

    assert isinstance(result, WorkerResult.Success)
    assert result.payload == {"created_at": "fake-created_at"}
    # call 1 = get the node
    # call 2 = patch the node's properties
    # call 3 = patch the node back to 'available' state
    # call 4 = get the node to see if state changed
    assert fake_ironic.call_count == 4


def test_ironic_update_defer_on_maintenance(
    mocker,
    admin_context: "RequestContext",
    ironic_worker: "IronicWorker",
    database: "utils.DBFixtures",
):
    """Test that nodes in maintenance mode are not updated."""

    def _fake_ironic_for_maintenance(path, method=None, json=None, **kwargs):
        if method == "get" and path == f"/nodes/{TEST_HARDWARE_UUID}":
            return utils.MockResponse(
                200,
                {
                    "uuid": TEST_HARDWARE_UUID,
                    "maintenance": True,
                },
            )
        raise NotImplementedError("Unexpected request signature")

    fake_ironic = get_fake_ironic(mocker, _fake_ironic_for_maintenance)

    result = ironic_worker.process(admin_context, get_fake_hardware(database))

    assert isinstance(result, WorkerResult.Defer)
    assert "in maintenance" in result.payload["message"]
    assert fake_ironic.call_count == 1


def test_ironic_provision_state_timeout(
    mocker,
    admin_context: "RequestContext",
    ironic_worker: "IronicWorker",
    database: "utils.DBFixtures",
):
    """Test that nodes in maintenance mode are not updated."""

    def _fake_ironic_for_timeout(path, method=None, json=None, **kwargs):
        if method == "get" and path == f"/nodes/{TEST_HARDWARE_UUID}":
            return utils.MockResponse(
                200,
                {
                    "uuid": TEST_HARDWARE_UUID,
                    "maintenance": False,
                    "provision_state": "available",
                },
            )
        elif method == "patch" and path == f"/nodes/{TEST_HARDWARE_UUID}":
            assert json == [
                {"op": "replace", "path": "/provision_state", "value": "manageable"}
            ]
            return utils.MockResponse(200)
        raise NotImplementedError("Unexpected request signature")

    count = int(time.perf_counter())

    def _fake_perf_counter():
        nonlocal count
        count += 15
        return count

    mocker.patch("time.perf_counter").side_effect = _fake_perf_counter
    mocker.patch("time.sleep")

    fake_ironic = get_fake_ironic(mocker, _fake_ironic_for_timeout)

    with pytest.raises(IronicNodeProvisionStateTimeout):
        ironic_worker.process(admin_context, get_fake_hardware(database))
    # 1. call to get node
    # 2. call to update provision state
    # 3..n calls to poll state until timeout
    assert fake_ironic.call_count == 2 + (PROVISION_STATE_TIMEOUT / 15)


def test_ironic_update_defer_on_locked(
    mocker,
    admin_context: "RequestContext",
    ironic_worker: "IronicWorker",
    database: "utils.DBFixtures",
):
    """Test that nodes in locked state are deferred."""

    def _fake_ironic_for_locked(path, method=None, json=None, **kwargs):
        if method == "get" and path == f"/nodes/{TEST_HARDWARE_UUID}":
            return utils.MockResponse(409)
        raise NotImplementedError("Unexpected request signature")

    fake_ironic = get_fake_ironic(mocker, _fake_ironic_for_locked)

    result = ironic_worker.process(admin_context, get_fake_hardware(database))

    assert isinstance(result, WorkerResult.Defer)
    assert "is locked" in result.payload["message"]
    assert fake_ironic.call_count == 1
