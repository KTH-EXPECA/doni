#    Copyright 2013 IBM Corp.
#
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

"""Doni common internal object model"""

from oslo_log import log
from oslo_versionedobjects import base as object_base

from doni.objects import fields as object_fields

LOG = log.getLogger(__name__)


class DoniObject(object_base.VersionedObject):
    """Base class and object factory.
    This forms the base of all objects that can be remoted or instantiated
    via RPC. Simply defining a class that inherits from this base class
    will make it remotely instantiatable. Objects should implement the
    necessary "get" classmethod routines as well as "save" object methods
    as appropriate.
    """

    OBJ_SERIAL_NAMESPACE = 'doni_object'
    OBJ_PROJECT_NAMESPACE = 'doni'

    # TODO(lintan) Refactor these fields and create PersistentObject and
    # TimeStampObject like Nova when it is necessary.
    fields = {
        'created_at': object_fields.DateTimeField(nullable=True),
        'updated_at': object_fields.DateTimeField(nullable=True),
    }

    def as_dict(self):
        """Return the object represented as a dict.
        The returned object is JSON-serialisable.
        """

        def _attr_as_dict(field):
            """Return an attribute as a dict, handling nested objects."""
            attr = getattr(self, field)
            if isinstance(attr, DoniObject):
                attr = attr.as_dict()
            return attr

        return dict((k, _attr_as_dict(k))
                    for k in self.fields
                    if self.obj_attr_is_set(k))

    def _set_from_db_object(self, context, db_object, fields=None):
        """Sets object fields.
        :param context: security context
        :param db_object: A DB entity of the object
        :param fields: list of fields to set on obj from values from db_object.
        """
        fields = fields or self.fields
        for field in fields:
            setattr(self, field, db_object[field])

    @staticmethod
    def _from_db_object(context, obj, db_object, fields=None):
        """Converts a database entity to a formal object.
        :param context: security context
        :param obj: An object of the class.
        :param db_object: A DB entity of the object
        :param fields: list of fields to set on obj from values from db_object.
        :return: The object of the class with the database entity added
        :raises: ovo_exception.IncompatibleObjectVersion
        """
        obj._set_from_db_object(context, db_object, fields)

        obj._context = context

        # NOTE(rloo). We now have obj, a versioned object that corresponds to
        # its DB representation. A versioned object has an internal attribute
        # ._changed_fields; this is a list of changed fields -- used, e.g.,
        # when saving the object to the DB (only those changed fields are
        # saved to the DB). The obj.obj_reset_changes() clears this list
        # since we didn't actually make any modifications to the object that
        # we want saved later.
        obj.obj_reset_changes()

        return obj


class DoniObjectListBase(object_base.ObjectListBase):

    def as_dict(self):
        """Return the object represented as a dict.
        The returned object is JSON-serialisable.
        """
        return {'objects': [obj.as_dict() for obj in self.objects]}
