import time
from functools import wraps
from textwrap import shorten
from typing import TYPE_CHECKING

import jsonpatch
from keystoneauth1 import exceptions as kaexception
from oslo_log import log

from doni.common import args, exception, keystone
from doni.conf import auth as auth_conf
from doni.worker import BaseWorker, WorkerField, WorkerResult

if TYPE_CHECKING:
    from doni.common.context import RequestContext
    from doni.objects.availability_window import AvailabilityWindow
    from doni.objects.hardware import Hardware

LOG = log.getLogger(__name__)

IRONIC_API_VERSION = "1"
# 1.51 provides a "description" field for the node, which we may want to use.
# It is supported in Stein and later[1].
# https://docs.openstack.org/ironic/latest/contributor/webapi-version-history.html#id13
IRONIC_API_MICROVERSION = "1.51"
PROVISION_STATE_TIMEOUT = 60  # Seconds to wait for provision_state changes
_IRONIC_ADAPTER = None

# Ironic's provision state API takes target arguments that
# are annoyingly different than the state the node ultimately winds up in.
IRONIC_STATE_TARGETS = {
    "manageable": "manage",
    "available": "provide",
}


def _get_ironic_adapter():
    global _IRONIC_ADAPTER
    if not _IRONIC_ADAPTER:
        _IRONIC_ADAPTER = keystone.get_adapter(
            "ironic",
            session=keystone.get_session("ironic"),
            auth=keystone.get_auth("ironic"),
            version=IRONIC_API_VERSION,
        )
    return _IRONIC_ADAPTER


def _defer_on_node_locked(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except IronicAPIError as exc:
            if exc.code == 409:
                return WorkerResult.Defer({"message": "Node is locked."})
            raise

    return wrapper


class IronicUnavailable(exception.DoniException):
    _msg_fmt = (
        "Could not contact Ironic API. Please check the service "
        "configuration. The precise error was: %(message)s"
    )


class IronicAPIError(exception.DoniException):
    _msg_fmt = "Ironic responded with HTTP %(code)s: %(text)s"


class IronicAPIMalformedResponse(exception.DoniException):
    _msg_fmt = "Ironic response malformed: %(text)s"


class IronicNodeProvisionStateTimeout(exception.DoniException):
    _msg_fmt = (
        "Ironic node %(node)s timed out updating its provision state to %(state)s"
    )


class IronicWorker(BaseWorker):

    fields = [
        WorkerField(
            "baremetal_driver",
            schema=args.enum(["ipmi"]),
            default="ipmi",
            private=True,
            description=(
                "The Ironic hardware driver that will control this node. See "
                "https://docs.openstack.org/ironic/latest/admin/drivers.html "
                "for a list of all Ironic hardware types. "
                "Currently only the 'ipmi' driver is supported."
            ),
        ),
        WorkerField(
            "baremetal_resource_class",
            schema=args.STRING,
            default="baremetal",
            private=True,
            description=(
                "The Ironic node resource class, which is used to map instance "
                "launch requests onto specific nodes via different Nova flavors. "
                "See https://docs.openstack.org/ironic/latest/install/configure-nova-flavors.html "
                "for more information. Defaults to 'baremetal', a generic resource "
                "class."
            ),
        ),
        WorkerField(
            "ipmi_username",
            schema=args.STRING,
            private=True,
            description=(
                "The IPMI username to use for IPMI authentication. Only used "
                "if the ``baremetal_driver`` is 'ipmi'."
            ),
        ),
        WorkerField(
            "ipmi_password",
            schema=args.STRING,
            private=True,
            sensitive=True,
            description=(
                "The IPMI password to use for IPMI authentication. Only used "
                "if the ``baremetal_driver`` is 'ipmi'."
            ),
        ),
        WorkerField(
            "ipmi_port",
            schema=args.PORT_RANGE,
            private=True,
            description=(
                "The remote IPMI RMCP port. If not provided, this defaults to "
                "the default IPMI port of 623."
            ),
        ),
        WorkerField(
            "ipmi_terminal_port",
            schema=args.PORT_RANGE,
            private=True,
            description=(
                "A local port to use to provide a remote console for provisioners "
                "of the Ironic node. Each node should have its own free unique "
                "port on the host running Ironic."
            ),
        ),
    ]

    opts = []
    opt_group = "ironic"

    def register_opts(self, conf):
        conf.register_opts(self.opts, group=self.opt_group)
        auth_conf.register_auth_opts(conf, self.opt_group, service_type="baremetal")

    def list_opts(self):
        return auth_conf.add_auth_opts(self.opts, service_type="baremetal")

    @_defer_on_node_locked
    def process(
        self,
        context: "RequestContext",
        hardware: "Hardware",
        availability_windows: "list[AvailabilityWindow]" = None,
        state_details: "dict" = None,
    ) -> "WorkerResult.Base":
        hw_props = hardware.properties
        desired_state = {
            "uuid": hardware.uuid,
            "name": hardware.name,
            "driver": hw_props.get("baremetal_driver"),
            "driver_info": {
                "ipmi_address": hw_props.get("management_address"),
                "ipmi_username": hw_props.get("ipmi_username"),
                "ipmi_password": hw_props.get("ipmi_password"),
                "ipmi_port": hw_props.get("ipmi_port"),
                "ipmi_terminal_port": hw_props.get("impi_terminal_port"),
            },
            "resource_class": hw_props.get("baremetal_resource_class"),
        }

        existing = _call_ironic(
            context, f"/nodes/{hardware.uuid}", method="get", none_on_404=True
        )

        if not existing:
            node = _call_ironic(context, "/nodes", method="post", json=desired_state)
            # Move from enroll -> manageable (Ironic will perform verification)
            _wait_for_provision_state(context, hardware.uuid, target_state="manageable")
            # Move from manageable -> available
            _wait_for_provision_state(context, hardware.uuid, target_state="available")
            return WorkerResult.Success(_success_payload(node))

        if existing.get("maintenance"):
            # For operator sanity, avoid mutating any details about the node
            # if it is maintenance mode. It is likely this will fail anyways
            # if the node is in maintenance.
            # NOTE: there may be a future case where the 'maintenance' flag
            # is managed in the inventory, in which case this will have to change.
            return WorkerResult.Defer(
                {
                    "message": (
                        "Node is in maintenance mode. Please take the node "
                        "out of maintenance to apply this update."
                    ),
                }
            )

        # Nodes must be in 'manageable' state to change driver
        # TODO: we can tell by what kind of diff we need whether this is
        # actually required.
        if existing["provision_state"] != "manageable":
            _wait_for_provision_state(context, hardware.uuid, target_state="manageable")

        existing_state = {key: existing.get(key) for key in desired_state.keys()}
        _normalize_driver_info(
            existing_state["driver_info"], desired_state["driver_info"]
        )

        patch = jsonpatch.make_patch(existing_state, desired_state)

        _call_ironic(
            context, f"/nodes/{hardware.uuid}", method="patch", json=list(patch)
        )

        # Put back into available state
        _wait_for_provision_state(context, hardware.uuid, target_state="available")

        return WorkerResult.Success(_success_payload(existing))


def _success_payload(node):
    # This 'created_at' isn't really used for anything but may provide comfort
    return {
        "created_at": node.get("created_at"),
    }


def _normalize_driver_info(existing_driver_info, desired_driver_info):
    # Copy unknown or empty keys from existing state to avoid overwriting w/ patch
    # NOTE: this means we cannot null out Ironic properties! But this is
    # probably the safest thing to do for now.
    for key in existing_driver_info.keys():
        desired_driver_info.setdefault(key, existing_driver_info[key])
    # Remove keys from each if they evaluate to None; this prevents a desired
    # 'None' from being sent to Ironic if it already has no value for that key.
    for key in list(desired_driver_info.keys()):
        if (
            existing_driver_info.get(key) is None
            and desired_driver_info.get(key) is None
        ):
            existing_driver_info.pop(key, None)
            desired_driver_info.pop(key, None)


def _wait_for_provision_state(
    context, node_uuid, target_state=None, timeout=PROVISION_STATE_TIMEOUT
):
    _call_ironic(
        context,
        f"/nodes/{node_uuid}/states/provision",
        method="put",
        json={"target": IRONIC_STATE_TARGETS[target_state]},
    )
    start_time = time.perf_counter()
    provision_state = None
    while provision_state != target_state:
        if (time.perf_counter() - start_time) > timeout:
            raise IronicNodeProvisionStateTimeout(node=node_uuid, state=target_state)
        time.sleep(15)
        node = _call_ironic(context, f"/nodes/{node_uuid}", method="get")
        provision_state = node["provision_state"]


def _call_ironic(context, path, method="get", json=None, none_on_404=False):
    try:
        ironic = _get_ironic_adapter()
        resp = ironic.request(
            path,
            method=method,
            json=json,
            microversion=IRONIC_API_MICROVERSION,
            global_request_id=context.global_id,
            raise_exc=False,
        )
    except kaexception.ClientException as exc:
        raise IronicUnavailable(message=str(exc))

    if resp.status_code >= 400:
        if resp.status_code == 404 and none_on_404:
            return None
        try:
            error_message = resp.json()["error_message"]
        except Exception:
            error_message = shorten(resp.text, width=50)
        raise IronicAPIError(code=resp.status_code, text=error_message)

    try:
        # Treat empty response bodies as None
        return resp.json() if resp.text else None
    except Exception:
        raise IronicAPIMalformedResponse(text=shorten(resp.text, width=50))
