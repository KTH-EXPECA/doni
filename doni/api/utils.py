from flask import request, make_response

from doni.objects import fields as doni_fields


def object_to_dict(obj, include_created_at=True, include_updated_at=True,
                   include_uuid=True, link_resource=None,
                   link_resource_args=None, fields=None):
    """Helper function to convert RPC objects to REST API dicts.
    :param obj:
        RPC object to convert to a dict
    :param include_created_at:
        Whether to include standard base class attribute created_at
    :param include_updated_at:
        Whether to include standard base class attribute updated_at
    :param include_uuid:
        Whether to include standard base class attribute uuid
    :param link_resource:
        When specified, generate a ``links`` value with a ``self`` and
        ``bookmark`` using this resource name
    :param link_resource_args:
        Resource arguments to be added to generated links. When not specified,
        the object ``uuid`` will be used.
    :param fields:
        Key names for dict values to populate directly from object attributes
    :returns: A dict containing values from the object
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
