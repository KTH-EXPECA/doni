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

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.db.models import DoniBase
    from doni.common.context import RequestContext

from oslo_log import log
from oslo_versionedobjects import base as object_base

from doni import PROJECT_NAME
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
    OBJ_PROJECT_NAMESPACE = PROJECT_NAME

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

    def _set_from_db_object(self, context: "RequestContext",
                            db_object: "DoniBase", fields: "list[str]"=None):
        """Sets object fields.

        Args:
            context (RequestContext): security context
            db_object (DoniBase): A DB entity of the object
            fields (list[str]): A list of fields to set on obj from values from
                db_object.
        """
        fields = fields or self.fields
        for field in fields:
            setattr(self, field, db_object[field])

    @staticmethod
    def _from_db_object(context: "RequestContext", obj: "DoniObject",
                        db_object: "DoniBase", fields: "list[str]"=None):
        """Converts a database entity to a formal object.

        Args:
            context (RequestContext): Security context
            obj (DoniObject): An object of the class.
            db_object (DoniBase): A DB entity of the object
            fields (list[str]): List of fields to set on obj from values from
                db_object.

        Returns:
            The object of the class with the database entity added.

        Raises:
            ovo_exception.IncompatibleObjectVersion: if the object and DB model
                don't have compatible versions.
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

    @classmethod
    def _from_db_object_list(cls, context: "RequestContext",
                             db_objects: "list[DoniBase]"):
        """Returns objects corresponding to database entities.

        Returns a list of formal objects of this class that correspond to
        the list of database entities.

        Args:
            cls (class): The VersionedObject class of the desired object.
            context (RequestContext): Security context.
            db_objects (list[DoniBase]): List of DB models of the object.

        Returns:
            A list of objects corresponding to the database entities.
        """
        return [cls._from_db_object(context, cls(), db_obj)
                for db_obj in db_objects]


class DoniObjectListBase(object_base.ObjectListBase):

    def as_dict(self):
        """Return the object represented as a dict.
        The returned object is JSON-serialisable.
        """
        return {'objects': [obj.as_dict() for obj in self.objects]}


class DoniObjectRegistry(object_base.VersionedObjectRegistry):
    """Registry to hold all Doni VersionedObjects.

    Each VersionedObject must be registered with the registry via the
    @DoniObjectRegistry.register decorator in order to set up the proxy
    attr setters and getters that make the object functional.
    """
    pass
