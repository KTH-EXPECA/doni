from flask import request
from keystonemiddleware.auth_token import AuthProtocol
from keystonemiddleware.auth_token._request import _AuthTokenRequest

from doni.common import context as doni_context
from doni.conf import CONF


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
