from doni.driver.worker.ironic import IronicWorker
from doni.objects.hardware import Hardware
from doni.tests.unit import utils
from doni.worker import WorkerResult


def test_create_node(admin_context, set_config, database: "utils.DBFixtures"):
    set_config(group="ironic", autocreate=True, auth_url="")
    hw = database.add_hardware()
    worker = IronicWorker()
    result = worker.process(admin_context, Hardware(admin_context, **hw))
    assert result == WorkerResult.Success()
