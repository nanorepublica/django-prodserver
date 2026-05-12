"""Deprecated; see ``django_prodserver.backends.servers.waitress``."""

import warnings

from .servers.waitress import WaitressServer

warnings.warn(
    "django_prodserver.backends.waitress is deprecated; import from "
    "django_prodserver.backends.servers.waitress instead. This module will be "
    "removed in django-prodserver 4.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["WaitressServer"]
