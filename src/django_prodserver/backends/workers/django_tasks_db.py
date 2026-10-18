"""Worker backend for django-tasks-db."""

from django.core import management

from ..base import BaseWorkerBackend


class DjangoTasksDBWorker(BaseWorkerBackend):
    """Run the database-backed Django Tasks worker."""

    def start_server(self, *args: str) -> None:
        """Call the django-tasks-db management command."""
        management.call_command("db_worker", *args)
