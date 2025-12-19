"""WSGI-compatible entrypoint for hosting providers

This module exposes `create_app` and `application` so a WSGI server
can import `app` as in the provided `orcamento.wsgi` sample.
"""
import os
from run import create_app as _create_app


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'production')
    return _create_app(config_name)


# WSGI application object expected by hosting services
application = create_app()
