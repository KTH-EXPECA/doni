from functools import wraps

from flask import request
from keystonemiddleware.auth_token import AuthProtocol
from keystonemiddleware.auth_token._request import _AuthTokenRequest
from oslo_policy.policy import PolicyNotAuthorized

from doni.api.utils import make_error_response
from doni.common import context as doni_context
from doni.common import exception
from doni.conf import CONF

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from flask import Blueprint


class AuthTokenFlaskMiddleware(object):
    """Wrap the keystonemiddleware.auth_token middleware for Flask.

    The auth_token middleware is designed to work for a more standard WSGI
    application using middleware components. Flask has some different design
    choices around how middleware are handled. This class just wraps up the
    middleware exposed by auth_token such that Flask can use it.
    """
    def __init__(self):
        self.keystonemiddleware = AuthProtocol(None, {
            "oslo_config_config": CONF,
        })

    def before_request(self):
        # When the middleware is invoked, it should mutate request.environ
        # and add 'keystone.auth_token' and 'keystone.auth_plugin' attributes.
        auth_token_request = _AuthTokenRequest(
            request.environ,
            # The request _should_ really only need headers for the middleware
            # to do its job.
            # NOTE: we have to cast to a dict structure because `headers` is
            # wrapped in a Flask/werkzeug data structure, and webob doesn't
            # properly interpret it as headers to be set in this form.
            headers=dict(request.headers))
        res = self.keystonemiddleware.process_request(auth_token_request)
        if res:
            return res


class ContextMiddleware(object):
    def before_request(self):
        request.context = (
            doni_context.RequestContext.from_environ(request.environ))

    def after_request(self, res):
        res.headers["OpenStack-Request-Id"] = request.context.request_id
        return res


def route(rule, blueprint: "Blueprint"=None, **options):
    """Decorator which validates and transforms function arguments
    """
    def inner_function(function):
        @wraps(function)
        def inner_check_args(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except PolicyNotAuthorized as exc:
                return make_error_response(str(exc), 403)
            except exception.NotFound as exc:
                return make_error_response(str(exc), 404)
        return blueprint.route(rule, **options)(inner_check_args)
    return inner_function
