#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from doni.db import api as db_api
from doni.objects import base
from doni.objects import fields as object_fields

@base.DoniObjectRegistry.register
class Hardware(base.DoniObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = db_api.get_instance()

    fields = {
        'id': object_fields.IntegerField(),
        'uuid': object_fields.UUIDField(nullable=False),
        'project_id': object_fields.StringField(nullable=False),
        'name': object_fields.StringField(nullable=False),
    }

    def create(self, context=None):
        """Create a Hardware record in the DB.
        :param context: security context.
        :raises: HardwareDuplicateName if a deploy template with the same
            name exists.
        :raises: HardwareAlreadyExists if a deploy template with the same
            UUID exists.
        """
        values = self.obj_get_changes()
        db_hardware = self.dbapi.create_hardware(values)
        self._from_db_object(self._context, self, db_hardware)

    def save(self, context=None):
        """Save updates to this Hardware.
        Column-wise updates will be made based on the result of
        self.what_changed().
        :param context: Security context.
        :raises: HardwareDuplicateName if a deploy template with the same
            name exists.
        :raises: HardwareNotFound if the deploy template does not exist.
        """
        updates = self.obj_get_changes()
        db_hardware = self.dbapi.update_hardware(self.uuid, updates)
        self._from_db_object(self._context, self, db_hardware)

    def destroy(self):
        """Delete the Hardware from the DB.
        :param context: security context..
        :raises: HardwareNotFound if the deploy template no longer
            appears in the database.
        """
        self.dbapi.destroy_hardware(self.id)
        self.obj_reset_changes()

    @classmethod
    def get_by_id(cls, context, hardware_id):
        """Find a deploy template based on its integer ID.
        :param context: security context.
        :param hardware_id: The ID of a deploy template.
        :raises: HardwareNotFound if the deploy template no longer
            appears in the database.
        :returns: a :class:`Hardware` object.
        """
        db_hardware = cls.dbapi.get_hardware_by_id(hardware_id)
        hardware = cls._from_db_object(context, cls(), db_hardware)
        return hardware

    @classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a hardware based on its UUID.
        :param context: security context..
        :param uuid: The UUID of a hardware.
        :raises: HardwareNotFound if the hardware no longer
            appears in the database.
        :returns: a :class:`Hardware` object.
        """
        db_hardware = cls.dbapi.get_hardware_by_uuid(uuid)
        hardware = cls._from_db_object(context, cls(), db_hardware)
        return hardware

    @classmethod
    def get_by_name(cls, context, name):
        """Find a hardware based on its name.
        :param context: security context..
        :param name: The name of a hardware.
        :raises: HardwareNotFound if the hardware no longer
            appears in the database.
        :returns: a :class:`Hardware` object.
        """
        db_hardware = cls.dbapi.get_hardware_by_name(name)
        hardware = cls._from_db_object(context, cls(), db_hardware)
        return hardware

    @classmethod
    def list(cls, context, limit=None, marker=None, sort_key=None,
             sort_dir=None):
        """Return a list of Hardware objects.
        :param context: security context..
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".
        :returns: a list of :class:`Hardware` objects.
        """
        db_templates = cls.dbapi.get_hardware_list(
            limit=limit, marker=marker, sort_key=sort_key, sort_dir=sort_dir)
        return cls._from_db_object_list(context, db_templates)
