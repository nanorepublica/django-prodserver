
from django.conf import settings
from django.core.management import BaseCommand
from django.core.servers.basehttp import get_internal_wsgi_application

from ..utils import wsgi_healthcheck

class BaseServerBackend:

    def __init__(self, *server_args):
        self.args = server_args

    def start_server(self, *args):
        raise NotImplementedError

    def prep_server_args(self):
        return self.args

    # def run_from_argv(self, argv):
        # TODO: The below should be looked into and implemented
    #     if getattr(settings, "WEBSERVER_WARMUP", True):
    #         app = get_internal_wsgi_application()
    #         if getattr(settings, "WEBSERVER_WARMUP_HEALTHCHECK", None):
    #             wsgi_healthcheck(app, settings.WEBSERVER_WARMUP_HEALTHCHECK)
    #     # self.start_server(*self.prep_server_args())
