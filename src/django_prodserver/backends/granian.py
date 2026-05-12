"""Deprecated; see ``django_prodserver.backends.servers.granian``."""

import warnings

from .servers.granian import GranianASGIServer, GranianServerBase, GranianWSGIServer

warnings.warn(
    "django_prodserver.backends.granian is deprecated; import from "
    "django_prodserver.backends.servers.granian instead. This module will be "
    "removed in django-prodserver 4.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["GranianASGIServer", "GranianServerBase", "GranianWSGIServer"]
