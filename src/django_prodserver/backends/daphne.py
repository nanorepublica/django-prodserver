"""Deprecated; see ``django_prodserver.backends.dev.daphne``."""

import warnings

from .dev.daphne import DaphneRunserver

warnings.warn(
    "django_prodserver.backends.daphne is deprecated; import from "
    "django_prodserver.backends.dev.daphne instead. This module will be "
    "removed in django-prodserver 4.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["DaphneRunserver"]
