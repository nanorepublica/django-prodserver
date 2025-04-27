from django.utils.module_loading import import_string
from .base import BaseServerBackend


class CeleryWorker(BaseServerBackend):
    """
    Backend to start a celery worker
    """

    def __init__(self, **server_config):
        celery_app_str = server_config.get("APP")
        self.app = import_string(celery_app_str)
        super().__init__(**server_config)

    def start_server(self, *args):
        self.app.Worker(*args).start()

    def prep_server_args(self):
        return self.args
