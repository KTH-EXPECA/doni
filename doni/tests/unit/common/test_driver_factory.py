import pytest
from pytest_mock import MockerFixture

from doni.common import driver_factory
from doni.common import exception
from doni.tests.unit import utils


class TestDriver(object):
    pass


def _driver_that_raises(exc):
    class TestDriverThatRaises(object):
        def __init__(self):
            raise exc

    return TestDriverThatRaises


@pytest.mark.parametrize(
    "namespace,enabled_option,factory",
    [
        pytest.param(
            "doni.driver.hardware_type",
            "enabled_hardware_types",
            driver_factory.HardwareTypeFactory,
            id="hardware_type",
        ),
        pytest.param(
            "doni.driver.worker_type",
            "enabled_worker_types",
            driver_factory.WorkerTypeFactory,
            id="worker_type",
        ),
    ],
)
def test_driver_load_error_if_driver_enabled(
    mocker: "MockerFixture", set_config, namespace, enabled_option, factory
):
    """Test that DriverLoadErrors on init are raised from factory."""
    set_config(**{enabled_option: ["fake-with-err"]})
    utils.mock_drivers(
        mocker,
        {
            namespace: {
                "fake-with-err": _driver_that_raises(exception.DriverLoadError("uhoh"))
            }
        },
    )
    with pytest.raises(exception.DriverLoadError):
        factory()


@pytest.mark.parametrize(
    "namespace,enabled_option,factory",
    [
        pytest.param(
            "doni.driver.hardware_type",
            "enabled_hardware_types",
            driver_factory.HardwareTypeFactory,
            id="hardware_type",
        ),
        pytest.param(
            "doni.driver.worker_type",
            "enabled_worker_types",
            driver_factory.WorkerTypeFactory,
            id="worker_type",
        ),
    ],
)
def test_wrap_in_driver_load_error_if_driver_enabled(
    mocker: "MockerFixture", set_config, namespace, enabled_option, factory
):
    """Test that generic Exceptions are wrapped in a DriverLoadError."""
    set_config(**{enabled_option: ["fake-with-err"]})
    utils.mock_drivers(
        mocker, {namespace: {"fake-with-err": _driver_that_raises(NameError())}}
    )

    with pytest.raises(exception.DriverLoadError):
        factory()


@pytest.mark.parametrize(
    "namespace,enabled_option,factory",
    [
        pytest.param(
            "doni.driver.hardware_type",
            "enabled_hardware_types",
            driver_factory.HardwareTypeFactory,
            id="hardware_type",
        ),
        pytest.param(
            "doni.driver.worker_type",
            "enabled_worker_types",
            driver_factory.WorkerTypeFactory,
            id="worker_type",
        ),
    ],
)
def test_no_driver_load_error_if_driver_disabled(
    mocker: "MockerFixture", set_config, namespace, enabled_option, factory
):
    """Test that disabled drivers will not raise errors on factory creation."""
    # Only enable the driver w/o error
    set_config(**{enabled_option: ["fake-ok"]})
    utils.mock_drivers(
        mocker,
        {
            namespace: {
                "fake-ok": TestDriver,
                "fake-with-err": _driver_that_raises(NameError()),
            }
        },
    )
    assert factory().names == ["fake-ok"]
