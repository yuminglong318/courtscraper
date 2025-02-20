import logging
import os
from logging.config import dictConfig

import dash
import diskcache
import sentry_sdk
from dash import Dash, DiskcacheManager
from flask_cors import CORS
from sentry_sdk.integrations.flask import FlaskIntegration

import src.callbacks as callbacks  # noqa
from src.core.auth import AdvancedAuth
from src.core.config import get_settings
from src.layout.horizontal import Layout
from src.routes.routing import add_routes

settings = get_settings()
# Use current folder
root_path = os.path.dirname(os.path.abspath(__file__))


def set_logging(app, logging_level):
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    if app.logger.hasHandlers():
        for handler in app.logger.handlers:
            handler.setFormatter(formatter)
            handler.setLevel(logging_level)


dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": "app.log",
                "formatter": "default",
            },
        },
        "root": {"level": "INFO", "handlers": ["wsgi", "file"]},
        "loggers": {
            "werkzeug": {
                "level": "INFO",
                "handlers": ["wsgi", "file"],
                "propagate": False,
            },
            "gunicorn": {
                "level": "INFO",
                "handlers": ["wsgi", "file"],
                "propagate": False,
            },
            "src": {
                "level": "INFO",
                "handlers": ["wsgi", "file"],
                "propagate": False,
            },
        },
    }
)


def init_app():
    pages_folder = os.path.join(root_path, "src/pages")
    assets_folder = os.path.join(root_path, "src/assets")

    background_callback_manager = DiskcacheManager(diskcache.Cache("./.cache"))

    dash._dash_renderer._set_react_version("18.2.0")

    app = Dash(
        meta_tags=[
            {
                "name": "viewport",
                "content": "width=device-width, initial-scale=1",
            }
        ],
        use_pages=True,
        external_stylesheets=[
            "https://unpkg.com/@mantine/dates@7/styles.css",
            "https://unpkg.com/@mantine/code-highlight@7/styles.css",
            "https://unpkg.com/@mantine/charts@7/styles.css",
            "https://unpkg.com/@mantine/carousel@7/styles.css",
            "https://unpkg.com/@mantine/notifications@7/styles.css",
            "https://unpkg.com/@mantine/nprogress@7/styles.css",
        ],
        pages_folder=pages_folder,
        external_scripts=[
            {
                "src": (
                    "https://cdnjs.cloudflare.com/ajax/libs/",
                    "html2canvas/1.4.0/html2canvas.min.js",
                )
            },
            {
                "src": (
                    "https://cdnjs.cloudflare.com/ajax/libs/"
                    "html2pdf.js/0.10.1/html2pdf.bundle.min.js"
                )
            },
        ],
        assets_folder=assets_folder,
        suppress_callback_exceptions=True,
        background_callback_manager=background_callback_manager,
    )

    # sentry
    if settings.SENTRY_ENV != "local":
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENV,
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )

    # Set the app title
    app.title = settings.PROJECT_NAME

    # Set the layout
    app.layout = Layout().render()

    # Set the server
    server = app.server

    # Set logging
    # filehandler = logging.FileHandler("app.log")

    # app.logger.addHandler(filehandler)
    # set_logging(app, settings.LOGGING_LEVEL)

    # Authentication
    auth = AdvancedAuth(app)

    # Add routes
    add_routes(server)

    # CORS
    CORS(server, resources={r"/*": {"origins": "*"}})

    return app, server, auth


app, server, auth = init_app()


if __name__ == "__main__":
    app.run_server(
        debug=True,
        port=3001,
        # Run in one thread
        threaded=False,
    )
