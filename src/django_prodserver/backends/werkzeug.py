"""Deprecated; see ``django_prodserver.backends.dev.werkzeug``."""

import warnings

from .dev.werkzeug import RunserverPlus, WerkzeugRunserver

warnings.warn(
    "django_prodserver.backends.werkzeug is deprecated; import from "
    "django_prodserver.backends.dev.werkzeug instead. This module will be "
    "removed in django-prodserver 4.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["RunserverPlus", "WerkzeugRunserver"]
