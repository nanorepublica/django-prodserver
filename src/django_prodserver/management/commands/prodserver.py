
from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.core.servers.basehttp import get_internal_wsgi_application
from django.utils.module_loading import import_string

from ...utils import wsgi_healthcheck

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("server_name", type=str)
    def handle(self, *args, **kwargs):
        server_name = kwargs['server_name']
        try:
            server_config = settings.PROD_SERVERS[server_name]
        except KeyError:
            raise CommandError("Server named {} not found in settings.PROD_SERVERS".format(server_name))

        self.stdout.write(self.style.SUCCESS('Starting server named {}'.format(server_name)))

        try:
            server_backend = server_config["BACKEND"]
        except KeyError:
            raise CommandError("Backend not configured for server named {}".format(server_name))

        backend_class = import_string(server_backend)
        backend = backend_class(*server_config.get("ARGS", []))
        backend.start_server(*backend.prep_server_args())
