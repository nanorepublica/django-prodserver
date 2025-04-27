from django.core import management

from .base import BaseServerBackend


class DjangoTasksWorker(BaseServerBackend):
    """
    Backend to start a django task db worker
    """

    def start_server(self, *args):
        management.call_command("db_worker", *args)

    def prep_server_args(self):
        return self.args
