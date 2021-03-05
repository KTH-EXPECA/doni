import pytest
from pytest_mock import MockerFixture
from stevedore import named

from doni.common import driver_factory
from doni.common import exception
from doni.tests.unit import utils


TEST_HARDWARE_TYPE = "test-hardware"

class TestHardwareType(object):
    name = TEST_HARDWARE_TYPE


@pytest.fixture(autouse=True)
def _use_fake_hardware(set_defaults):
    set_defaults(enabled_hardware_types=[TEST_HARDWARE_TYPE])


@pytest.fixture()
def init_factory():
    driver_factory.HardwareTypeFactory._extension_manager = None
    yield driver_factory.HardwareTypeFactory
    # Ensure that these tests don't pollute the singleton for other tests
    driver_factory.HardwareTypeFactory._extension_manager = None


def _driver_that_raises(exc, driver_name=TEST_HARDWARE_TYPE):
    class TestHardwareTypeThatRaises(object):
        name = driver_name
        def __init__(self):
            raise exc
    return TestHardwareTypeThatRaises


def make_fake_extension_manager(mocker: "MockerFixture", extensions=[]):
    def _create_extension_manager(namespace, names, **kwargs):
        on_load_failure_callback = kwargs["on_load_failure_callback"]
        em = named.NamedExtensionManager.make_test_instance(
            extensions, namespace,
            on_load_failure_callback=on_load_failure_callback)
        # NOTE(jason): ``make_test_instance`` doesn't actually do anything with
        # the on_load_failure_callback, nor does it attempt to invoke the
        # entrypoints. So, we do a kludgy mimicry of this here.
        for ep in extensions:
            try:
                ep()
            except Exception as exc:
                on_load_failure_callback(em, ep, exc)
        return em
    (mocker.patch("doni.common.driver_factory._create_extension_manager")
        .side_effect) = _create_extension_manager


def test_driver_load_error_if_driver_enabled(mocker: "MockerFixture", init_factory):
    make_fake_extension_manager(mocker, [
        _driver_that_raises(exception.DriverLoadError("uhoh"))
    ])
    with pytest.raises(exception.DriverLoadError):
        init_factory()


def test_wrap_in_driver_load_error_if_driver_enabled(mocker: "MockerFixture", init_factory):
    make_fake_extension_manager(mocker, [
        _driver_that_raises(NameError())
    ])
    with pytest.raises(exception.DriverLoadError):
        init_factory()


def test_no_driver_load_error_if_driver_disabled(mocker: "MockerFixture", init_factory):
    make_fake_extension_manager(mocker, [
        TestHardwareType,
        _driver_that_raises(NameError(), driver_name="should-be-disabled")
    ])
    init_factory()
