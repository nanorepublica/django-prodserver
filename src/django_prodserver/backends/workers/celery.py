from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from ..base import BaseWorkerBackend


class CeleryWorker(BaseWorkerBackend):
    """Backend to start a celery worker."""

    def __init__(self, **server_config: Any) -> None:
        celery_app_str = server_config.get("APP")
        self.app = import_string(celery_app_str)
        super().__init__(**server_config)

    def start_server(self, *args: str) -> None:
        """Start Celery Worker via the ``worker`` subcommand on the Celery app."""
        self.app.start(argv=["worker", *args])


class CeleryBeat(CeleryWorker):
    """Backend to start a celery beat process."""

    def start_server(self, *args: str) -> None:
        """Start Celery beat via the ``beat`` subcommand on the Celery app."""
        self.app.start(argv=["beat", *args])


class CeleryFlower(CeleryWorker):
    """Backend to start a Celery Flower monitoring server."""

    def __init__(self, **server_config: Any) -> None:
        """
        Initialize the Celery Flower backend.

        Validates that the ``flower`` package is installed, since it is an
        optional dependency that registers the ``flower`` subcommand on the
        Celery app.

        Raises:
            ImproperlyConfigured: If the ``flower`` package is not installed.

        """
        try:
            import flower  # noqa: F401
        except ImportError as e:
            raise ImproperlyConfigured(
                "flower is required to use the CeleryFlower backend. "
                "Install it with: pip install django-prodserver[flower]"
            ) from e

        super().__init__(**server_config)

    def start_server(self, *args: str) -> None:
        """Start Celery Flower via the ``flower`` subcommand on the Celery app."""
        self.app.start(argv=["flower", *args])
