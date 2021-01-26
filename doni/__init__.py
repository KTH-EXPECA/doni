import logging
import os

from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_object("doni.config")
        app.config.from_envvar("DONI_SETTINGS")
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import monitor

    app.register_blueprint(monitor.bp)
    app.logger.info("Registered apps")

    # Propagate gunicorn log level to Flask
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.setLevel(gunicorn_logger.level)

    return app
