from django.core import management

from .base import BaseServerBackend


class DjangoTasksWorker(BaseServerBackend):
    """Backend to start a django task db worker."""

    def start_server(self, *args: str) -> None:
        """Call django-tasks management command."""
        management.call_command("db_worker", *args)
