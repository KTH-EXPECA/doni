from functools import partial, wraps
import inspect

from flask import request
import jsonschema

from doni.common import exception

# Some JSON schema helpers
STRING = {"type": "string"}
PORT_RANGE = {"type": "integer", "minimum": 1, "maximum": 65536}
HOST_OR_IP = {"oneOf": [{"type": "string", "format": "hostname"},
                        {"type": "string", "format": "ipv4"},
                        {"type": "string", "format": "ipv6"}]}
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

            # Add JSON body for validation as positional arg
            if "json_body" in validators:
                args.append(request.json)

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
