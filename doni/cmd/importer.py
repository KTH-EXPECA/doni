"""
Import existing external resources into the registration DB.
"""
import sys
from collections import defaultdict

from oslo_config import cfg
from oslo_log import log

from doni.common import context as doni_context
from doni.common import driver_factory, service
from doni.conf import CONF
from doni.objects.hardware import Hardware
from doni.worker import WorkerState

LOG = log.getLogger(__name__)


def import_existing():
    ctx = doni_context.get_admin_context()
    existing = defaultdict(dict)
    for hwt_name, hwt in driver_factory.hardware_types().items():
        for wrk_name, wrk in driver_factory.worker_types().items():
            if wrk_name not in hwt.enabled_workers:
                LOG.debug(f"Worker {wrk_name} not enabled for {hwt_name}")
                continue
            items_from_worker = wrk.import_existing(ctx) or []
            LOG.debug(f"Importing {len(items_from_worker)} hardwares from {wrk_name}")
            for item in items_from_worker:
                exist_hw = existing[item["uuid"]]
                exist_hw["name"] = item.get("name")
                exist_hw["hardware_type"] = hwt_name
                if "properties" in exist_hw:
                    exist_hw["properties"].update(item["properties"])
                else:
                    exist_hw["properties"] = item["properties"].copy()

    for uuid, exist_hw in existing.items():
        hardware = Hardware(
            uuid=uuid,
            name=exist_hw["name"],
            hardware_type=exist_hw["hardware_type"],
            properties=exist_hw["properties"],
        )
        print(f"Registering {hardware}")
        if not CONF.dry_run:
            hardware.create(ctx, initial_worker_state=WorkerState.STEADY)


def main():
    CONF.register_cli_opts(
        [
            cfg.BoolOpt(
                "dry-run",
                dest="dry_run",
                default=False,
                help=(
                    "Print out hardwares that would be imported without importing them "
                    "into the system database."
                ),
            ),
        ],
    )
    service.prepare_service(sys.argv)
    import_existing()
