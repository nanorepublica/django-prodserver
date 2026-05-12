"""Deprecated; see ``django_prodserver.backends.servers.uvicorn``."""

import warnings

from .servers.uvicorn import UvicornServer, UvicornWSGIServer

warnings.warn(
    "django_prodserver.backends.uvicorn is deprecated; import from "
    "django_prodserver.backends.servers.uvicorn instead. This module will be "
    "removed in django-prodserver 4.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["UvicornServer", "UvicornWSGIServer"]
