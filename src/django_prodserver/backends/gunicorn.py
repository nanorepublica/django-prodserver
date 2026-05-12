"""Deprecated; see ``django_prodserver.backends.servers.gunicorn``."""

import warnings

from .servers.gunicorn import DjangoApplication, GunicornServer

warnings.warn(
    "django_prodserver.backends.gunicorn is deprecated; import from "
    "django_prodserver.backends.servers.gunicorn instead. This module will be "
    "removed in django-prodserver 4.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["DjangoApplication", "GunicornServer"]
