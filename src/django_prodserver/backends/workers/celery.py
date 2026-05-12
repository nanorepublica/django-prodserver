from typing import Any

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
