"""Doni test utilities."""

from oslo_utils import uuidutils

from doni.common import exception
from doni.db import api as db_api

FAKE_HARDWARE_TYPE = "fake-hardware"


def get_test_hardware(**kw):
    default_uuid = uuidutils.generate_uuid()
    return {
        "created_at": kw.get("created_at"),
        "updated_at": kw.get("updated_at"),
        "id": kw.get("id", 234),
        "name": kw.get("name", "fake_name"),
        "uuid": kw.get("uuid", default_uuid),
        "hardware_type": kw.get("hardware_type", FAKE_HARDWARE_TYPE),
        "project_id": kw.get("project_id", "fake_project_id"),
        "properties": kw.get("properties", {}),
    }


class DBFixtures(object):
    """A helper utility for setting up test data in the test DB.
    """
    def __init__(self):
        self.db = db_api.get_instance()
        self._hardwares = []
        self._counter = 0

    def add_hardware(self, **hardware_kwargs) -> dict:
        """Add a hardware item to the test database.

        Args:
            **hardware_kwargs: attributes to set on the Hardware object.

        Returns:
            A dict representing the added hardware, with all fields set.
        """
        self._counter += 1
        # Avoid name collisions
        hardware_kwargs.setdefault("name", f"fake_name_{self._counter}")
        fake_hw = get_test_hardware(**hardware_kwargs)
        # ID will be auto-assigned by DB
        fake_hw.pop("id")
        self._hardwares.append(self.db.create_hardware(fake_hw))
        return fake_hw

    def remove_hardware(self, hardware_uuid):
        """Remove a hardware item from the test database.

        Args:
            hardware_uuid (str): The UUID of the hardware item to remove.

        Raises:
            ValueError: if a Hardware could not be found for the UUID.
        """
        hw = next(
            (hw for hw in self._hardwares if hw.uuid == hardware_uuid), None)
        if not hw:
            raise ValueError(
                f"Could not find Hardware {hardware_uuid} to delete")
        self.db.destroy_hardware(hw.uuid)
        self._hardwares.remove(hw)


    @property
    def hardwares(self):
        return [hw.as_dict() for hw in self._hardwares]

    def cleanup(self):
        for hw in self._hardwares:
            try:
                self.db.destroy_hardware(hw.uuid)
            except exception.HardwareNotFound:
                # Allow tests to destroy hardware
                pass
        self._hardwares = []
