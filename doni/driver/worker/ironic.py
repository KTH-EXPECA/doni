from functools import wraps
from textwrap import shorten
import time

import jsonpatch
from keystoneauth1 import exceptions as kaexception
from oslo_log import log

from doni.common import args
from doni.common import exception
from doni.common import keystone
from doni.conf import auth as auth_conf
from doni.worker import BaseWorker
from doni.worker import WorkerField
from doni.worker import WorkerResult

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from doni.common.context import RequestContext
    from doni.objects.availability_window import AvailabilityWindow
    from doni.objects.hardware import Hardware

LOG = log.getLogger(__name__)

IRONIC_API_VERSION = "1"
IRONIC_API_MICROVERSION = "1.65"
PROVISION_STATE_TIMEOUT = 60  # Seconds to wait for provision_state changes
_IRONIC_ADAPTER = None


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
            "driver": hw_props.get("baremetal_driver"),
            "driver_info": {
                "ipmi_address": hw_props.get("management_address"),
                "ipmi_username": hw_props.get("ipmi_username"),
                "ipmi_password": hw_props.get("ipmi_password"),
                "ipmi_terminal_port": hw_props.get("impi_terminal_port"),
            },
        }

        existing = _call_ironic(
            context, f"/nodes/{hardware.uuid}", method="get", allowed_status_codes=[404]
        )

        if not existing:
            node = _call_ironic(context, "/nodes", method="post", json=desired_state)
            # This 'created_at' isn't really used for anything but may provide comfort
            return WorkerResult.Success({"created_at": node["created_at"]})

        if existing["maintenance"]:
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

        existing_state = {
            key: existing.get(key) for key in ["driver", "driver_info", "uuid"]
        }
        # Copy unknown or empty keys from existing state to avoid overwriting w/ patch
        # NOTE: this means we cannot null out Ironic properties! But this is
        # probably the safest thing to do for now.
        desired_state["driver_info"].update(
            {
                key: existing_state["driver_info"][key]
                for key in existing_state["driver_info"].keys()
                if desired_state["driver_info"].get(key) is None
            }
        )
        patch = jsonpatch.make_patch(existing_state, desired_state)
        _call_ironic(
            context, f"/nodes/{hardware.uuid}", method="patch", json=list(patch)
        )

        # Put back into available state
        _wait_for_provision_state(context, hardware.uuid, target_state="available")

        return WorkerResult.Success()


def _wait_for_provision_state(
    context, node_uuid, target_state=None, timeout=PROVISION_STATE_TIMEOUT
):
    _call_ironic(
        context,
        f"/nodes/{node_uuid}",
        method="patch",
        json=[
            {"op": "replace", "path": "/provision_state", "value": target_state},
        ],
    )
    start_time = time.perf_counter()
    provision_state = None
    while provision_state != target_state:
        if (time.perf_counter() - start_time) > timeout:
            raise IronicNodeProvisionStateTimeout(node=node_uuid, state=target_state)
        time.sleep(15)
        node = _call_ironic(context, f"/nodes/{node_uuid}", method="get")
        provision_state = node["provision_state"]


def _call_ironic(context, path, method="get", json=None, allowed_status_codes=[]):
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

    if resp.status_code >= 400 and resp.status_code not in allowed_status_codes:
        raise IronicAPIError(code=resp.status_code, text=shorten(resp.text, width=50))

    try:
        # Treat empty response bodies as None
        return resp.json() if resp.text else None
    except Exception:
        raise IronicAPIMalformedResponse(text=shorten(resp.text, width=50))
