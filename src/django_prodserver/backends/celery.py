from typing import Any

from django.utils.module_loading import import_string

from .base import BaseServerBackend


class CeleryWorker(BaseServerBackend):
    """Backend to start a celery worker."""

    def __init__(self, **server_config: Any) -> None:
        celery_app_str = server_config.get("APP")
        self.app = import_string(celery_app_str)
        super().__init__(**server_config)

    def start_server(self, *args: str) -> None:
        """Start Celery Worker."""
        self.app.Worker(*args).start()


class CeleryBeat(CeleryWorker):
    """Backend to start a celery beat process."""

    def start_server(self, *args: str) -> None:
        """Start Celery beat."""
        self.app.Beat(*args).start()
