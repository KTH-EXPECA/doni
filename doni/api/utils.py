from flask import request, make_response
import jsonpatch
from oslo_utils import uuidutils

from doni.common import exception
from doni.objects import fields as doni_fields

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doni.common.context import RequestContext
    from doni.objects.base import DoniObject
    from typing import Type


_JSONPATCH_EXCEPTIONS = (jsonpatch.JsonPatchConflict,
                         jsonpatch.JsonPatchException,
                         jsonpatch.JsonPointerException,
                         KeyError,
                         IndexError)


def object_to_dict(obj, include_created_at=True, include_updated_at=True,
                   include_uuid=True, link_resource=None,
                   link_resource_args=None, fields=None):
    """Helper function to convert RPC objects to REST API dicts.

    Args:
        obj (DoniObject): RPC object to convert to a dict.
        include_created_at (bool): Whether to include standard base class
            attribute ``created_at``.
        include_updated_at (bool): Whether to include standard base class
            attribute ``updated_at``.
        include_uuid (bool): Whether to include standard base class attribute
            ``uuid``.
        link_resource (bool): When specified, generate a ``links`` value with
            a ``self`` and ``bookmark`` using this resource name.
        link_resource_args (any): Resource arguments to be added to generated
            links. When not specified, the object ``uuid`` will be used.
        fields (list[str]): Key names for dict values to populate directly from
            object attributes.

    Returns:
        A dict containing values from the object.
    """
    url = request.url
    to_dict = {}

    all_fields = []

    if include_uuid:
        all_fields.append('uuid')
    if include_created_at:
        all_fields.append('created_at')
    if include_updated_at:
        all_fields.append('updated_at')

    if fields:
        all_fields.extend(fields)

    for field in all_fields:
        value = to_dict[field] = getattr(obj, field)
        empty_value = None
        if isinstance(obj.fields[field], doni_fields.DateTimeField):
            if value:
                value = value.isoformat()

        if value is not None:
            to_dict[field] = value
        else:
            to_dict[field] = empty_value

    # if link_resource:
    #     if not link_resource_args:
    #         link_resource_args = obj.uuid
    #     to_dict['links'] = [
    #         link.make_link('self', url, link_resource, link_resource_args),
    #         link.make_link('bookmark', url, link_resource, link_resource_args,
    #                        bookmark=True)
    #     ]

    return to_dict


def make_error_response(message=None, status_code=None):
    return make_response({
        "error": message,
    }, status_code)


def apply_jsonpatch(state: dict, patch):
    """Apply a JSON patch, one operation at a time.

    If the patch fails to apply, this allows us to determine which operation
    failed, making the error message a little less cryptic.

    Args:
        state (dict): The state to apply the JSON patch to. State is expected
            to be key/value pairs where keys are field names and values are
            DoniObject instances or lists of instances. These will be flattened
            via ``as_dict``. If the state has "self" key, the resulting dict
            is flattened directly into the state. For example, for the state::

                state = {"self": hardware}

            ultimately it would be converted to the following JSON document
            before applying the patch::

                {
                    "uuid": "...",
                    "name", "...",
                    ...hardware props
                }

            Whereas the following::

                state = {"self": hardware, "extra": other_obj}

            would result in::

                {
                    "uuid": "...",
                    "name": "...",
                    ...hardware props,
                    "extra": {
                        ...extra props
                    }
                }

        patch (list): The JSON patch to apply.

    Returns:
        The result of the patch operation.

    Raises:
        PatchError: If the patch fails to apply.
        ClientSideError: If the patch adds a new root attribute.
    """
    doc = {}
    self_ref = state.pop("self", None)
    if self_ref:
        doc.update(**self_ref.as_dict())
    for field, obj in state.items():
        if isinstance(obj, list):
            doc[field] = [item.as_dict() for item in obj]
        else:
            doc[field] = obj.as_dict()

    # Prevent removal of root attributes.
    for p in patch:
        if (p['op'] == 'add' and p['path'].count('/') == 1 and
            p['path'].lstrip('/') not in doc):
            msg = ('Adding a new attribute (%s) to the root of '
                    'the resource is not allowed')
            raise exception.PatchError(patch=p, reason=(msg % p["path"]))

    # Apply operations one at a time, to improve error reporting.
    for patch_op in patch:
        try:
            doc = jsonpatch.apply_patch(doc, jsonpatch.JsonPatch([patch_op]))
        except _JSONPATCH_EXCEPTIONS as e:
            raise exception.PatchError(patch=patch_op, reason=e)

    return doc


def apply_patch_updates(object: "DoniObject", updates: dict):
    """Apply any changes from a computed update patch directly to an object.

    This will mutate the object's fields. The object can then be saved later
    via ``save``.

    Args:
        object (DoniObject): The object to update.
        updates (dict): A set of updated field values. Any updates for fields
            not declared on the object are silently ignored.
    """
    for field in object.fields:
        patched_val = updates.get(field)
        if getattr(object, field) != patched_val:
            setattr(object, field, patched_val)


def apply_patch_updates_to_list(
    objects: "list[DoniObject]",
    updates: "list[dict]",
    obj_class: "Type[DoniObject]"=None,
    context: "RequestContext"=None,
    primary_key: str="uuid"
) -> "tuple[list[DoniObject],list[DoniObject],list[DoniObject]]":
    obj_map = {getattr(o, primary_key): o for o in objects}
    # Generate a default primary key if none exists; this will indicate that
    # this update corresponds to what should be a new object.
    update_map = {u.get(primary_key, uuidutils.generate_uuid()): u for u in updates}
    uniq_objs = set(obj_map.keys())
    uniq_updates = set(update_map.keys())

    to_add = []
    to_update = []
    to_remove = []

    for key in uniq_updates - uniq_objs:
        to_add.append(obj_class(context, **update_map[key]))

    for key in uniq_updates & uniq_objs:
        obj = obj_map[key]
        apply_patch_updates(obj, update_map[key])
        to_update.append(obj)

    for key in uniq_objs - uniq_updates:
        to_remove.append(obj_map[key])

    return to_add, to_update, to_remove


def get_patch_values(patch, path) -> "list[any]":
    """Get the patch values corresponding to the specified path.

    If there are multiple values specified for the same path, for example::

        [{'op': 'add', 'path': '/name', 'value': 'abc'},
         {'op': 'add', 'path': '/name', 'value': 'bca'}]

    return all of them in a list (preserving order)

    Args:
        patch (list): HTTP PATCH request body.
        path (str): The path to get the patch values for.

    Returns:
        A list of values for the specified path in the patch.
    """
    return [p['value'] for p in patch
            if p['path'] == path and p['op'] != 'remove']


def is_path_removed(patch, path):
    """Returns whether the patch includes removal of the path (or subpath of).

    Args:
        patch (list): HTTP PATCH request body.
        path (str): the path to check.

    Returns:
        True if path or subpath being removed, False otherwise.
    """
    path = path.rstrip('/')
    for p in patch:
        if ((p['path'] == path or p['path'].startswith(path + '/'))
                and p['op'] == 'remove'):
            return True


def is_path_updated(patch, path):
    """Returns whether the patch includes operation on path (or subpath of).

    Args:
        patch (list): HTTP PATCH request body.
        path (str): the path to check.

    Returns:
        True if path or subpath being patched, False otherwise.
    """
    path = path.rstrip('/')
    for p in patch:
        return p['path'] == path or p['path'].startswith(path + '/')
