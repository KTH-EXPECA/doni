from functools import partial, wraps
import inspect

import jsonschema
from oslo_utils import uuidutils

from doni.common import exception

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Optional


def uuid(name, value) -> "Optional[str]":
    """Validate that the value is a UUID

    Args:
        name (str): Name of the argument
        value (any): A UUID string value

    Returns:
        The value, or None if value is None

    Raises:
        InvalidParameterValue: if the value is not a valid UUID
    """
    if value is None:
        return
    if not uuidutils.is_uuid_like(value):
        raise exception.InvalidParameterValue(
            ('Expected UUID for %s: %s') % (name, value))
    return value


# Some JSON schema helpers
STRING = {"type": "string"}
DATETIME = {"type": "string", "format": "date-time"}
PORT_RANGE = {"type": "integer", "minimum": 1, "maximum": 65536}
HOST_OR_IP = {"oneOf": [{"type": "string", "format": "hostname"},
                        {"type": "string", "format": "ipv4"},
                        {"type": "string", "format": "ipv6"}]}
NETWORK_DEVICE = {
    "type": "object",
    "properties": {
        "name": STRING,
        # There is no mac_address format in jsonschema yet[1]
        # [1]: https://github.com/json-schema-org/json-schema-spec/issues/540
        "mac_address": STRING,
        "vendor": STRING,
        "model": STRING,
    },
    "required": ["name", "mac_address"],
    "additionalProperties": False,
}
PATCH = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'path': {'type': 'string', 'pattern': '^(/[\\w-]+)+$'},
            'op': {'type': 'string', 'enum': ['add', 'replace', 'remove']},
            'value': {}
        },
        'additionalProperties': False,
        'required': ['op', 'path']
    }
}


def enum(values, type="string"):
    return {"type": type, "enum": values}


def optional(schema):
    return {
        "anyOf": [
            schema,
            {"type": "null"},
        ]
    }


def array(schema):
    return {"type": "array", "items": schema}


def _validate_schema(name, value, schema):
    if value is None:
        return
    try:
        jsonschema.validate(value, schema)
    except jsonschema.exceptions.ValidationError as e:

        # The error message includes the whole schema which can be very
        # large and unhelpful, so truncate it to be brief and useful
        error_msg = ' '.join(str(e).split("\n")[:3])[:-1]
        raise exception.InvalidParameterValue(
            ('Schema error for %s: %s') % (name, error_msg))
    return value


def schema(schema):
    """Return a validator function which validates the value with jsonschema

    Args:
        schema (dict): JSON schema to validate with.

    Returns:
        A validator function, which takes name and value arguments.
    """
    jsonschema.Draft4Validator.check_schema(schema)

    return partial(_validate_schema, schema=schema)


def _inspect(function):
    sig = inspect.signature(function)
    params = []

    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            params.append(param)
        else:
            assert False, 'Unsupported parameter kind %s %s' % (
                param.name, param.kind
            )
    return params


def validate(*args, **kwargs):
    """Decorator which validates and transforms function arguments
    """
    assert not args, 'Validators must be specifed by argument name'
    assert kwargs, 'No validators specified'
    validators = kwargs

    def inner_function(function):
        params = _inspect(function)

        @wraps(function)
        def inner_check_args(*args, **kwargs):
            args = list(args)
            kwargs_next = {}

            # ensure each named argument belongs to a param
            kwarg_keys = set(kwargs)
            param_names = set(p.name for p in params)
            extra_args = kwarg_keys - param_names
            if extra_args:
                raise exception.InvalidParameterValue(
                    ('Unexpected arguments: %s') % ', '.join(extra_args))

            args_len = len(args)

            for i, param in enumerate(params):
                val_function = validators.get(param.name)
                if not val_function:
                    continue

                if i < args_len:
                    # validate positional argument
                    args[i] = val_function(param.name, args[i])
                elif param.name in kwargs:
                    # validate keyword argument
                    kwargs_next[param.name] = val_function(
                        param.name, kwargs.pop(param.name))
                elif param.default == inspect.Parameter.empty:
                    # no argument was provided, and there is no default
                    # in the parameter, so this is a mandatory argument
                    raise exception.MissingParameterValue(
                        ('Missing mandatory parameter: %s') % param.name)

            return function(*args, **kwargs_next)
        return inner_check_args
    return inner_function
