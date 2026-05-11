"""Deprecated; see ``django_prodserver.backends.workers.django_tasks``."""

import warnings

from .workers.django_tasks import DjangoTasksWorker

warnings.warn(
    "django_prodserver.backends.django_tasks is deprecated; import from "
    "django_prodserver.backends.workers.django_tasks instead. This module will "
    "be removed in django-prodserver 4.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["DjangoTasksWorker"]
