from doni.common import driver_factory
from doni.driver.worker.ironic import IronicWorker
from doni.objects.hardware import Hardware
from doni.tests.unit import utils
from doni.worker import WorkerResult


def test_ironic_create_node(admin_context, set_config, database: "utils.DBFixtures"):
    set_config(enabled_hardware_types=["baremetal"], enabled_worker_types=["ironic"])
    worker = driver_factory.get_worker_type("ironic")
    # We have to defer setting the 'ironic' opts until after we've asked for
    # the worker; option registration happens lazily and the group isn't enabled yet.
    set_config(group="ironic", auth_url="")
    hw = database.add_hardware()
    result = worker.process(admin_context, Hardware(admin_context, **hw))
    assert result == WorkerResult.Success()
