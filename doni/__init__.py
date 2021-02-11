from importlib.metadata import version
import logging
import os

from flask import Flask, request
from keystonemiddleware.auth_token import AuthProtocol
from keystonemiddleware.auth_token._request import _AuthTokenRequest
from oslo_middleware import healthcheck
from werkzeug.middleware import dispatcher as wsgi_dispatcher

from doni.conf import CONF

try:
    __version__ = version(__name__)
except:
    pass


def _add_vary_x_auth_token_header(res):
    res.headers['Vary'] = 'X-Auth-Token'
    return res


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
            headers=request.headers)
        res = self.keystonemiddleware.process_request(auth_token_request)
        if res:
            return res


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config:
        app.config.from_mapping(test_config)
    else:
        # TODO: set anything relevant from CONF
        app.config.update(
            PROPAGATE_EXCEPTIONS=True
        )

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register Error Handler Function for Keystone Errors.
    # NOTE(morgan): Flask passes errors to an error handling function. All of
    # keystone's api errors are explicitly registered in
    # keystone.exception.KEYSTONE_API_EXCEPTIONS and those are in turn
    # registered here to ensure a proper error is bubbled up to the end user
    # instead of a 500 error.
    # for exc in exception.KEYSTONE_API_EXCEPTIONS:
    #     app.register_error_handler(exc, _handle_keystone_exception)

    # Register extra (python) exceptions with the proper exception handler,
    # specifically TypeError. It will render as a 400 error, but presented in
    # a "web-ified" manner
    # app.register_error_handler(TypeError, _handle_unknown_keystone_exception)

    # Add core before request functions
    # app.before_request(req_logging.log_request_info)
    # app.before_request(json_body.json_body_before_request)
    app.before_request(AuthTokenFlaskMiddleware().before_request)
    app.after_request(_add_vary_x_auth_token_header)

    from . import monitor
    app.register_blueprint(monitor.bp)
    app.logger.info("Registered apps")

    # Propagate gunicorn log level to Flask
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.setLevel(gunicorn_logger.level)

    app_mounts = {}

    # oslo_middleware healthcheck is a separate app; mount it at
    # the well-known /healthcheck endpoint.
    hc_app = healthcheck.Healthcheck.app_factory(
        {}, oslo_config_project='doni')
    app_mounts['/healthcheck'] = hc_app

    app.wsgi_app = wsgi_dispatcher.DispatcherMiddleware(
        app.wsgi_app,
        app_mounts)

    return app
