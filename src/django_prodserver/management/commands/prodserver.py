
from django.conf import settings
from django.core.management import BaseCommand
from django.core.servers.basehttp import get_internal_wsgi_application
from django.utils.module_loading import import_string

from ...utils import wsgi_healthcheck

import djclick as click

@click.command()
@click.argument('server_name')
def command(server_name: str):
    try:
        server_config = settings.PROD_SERVERS[server_name]
    except KeyError:
        raise click.ClickException("Server named {} not found in settings.PROD_SERVERS".format(server_name))

    click.secho('Starting server named {}'.format(server_name), fg='red')

    try:
        server_backend = server_config["BACKEND"]
    except KeyError:
        raise click.ClickException("Backend not configured for server named {}".format(server_name))

    backend_class = import_string(server_backend)

    backend = backend_class(*server_config.get("ARGS", []))
    backend.start_server(*backend.prep_server_args())

# class ProdServerCommand(BaseCommand):
#     help = "Closes the specified poll for voting"

#     def add_arguments(self, parser):
#         parser.add_argument("server_name", nargs="+", type=str)

#     def handle(self, *args, **options):

#     # def start_server(self, *args):
#     #     raise NotImplementedError

#     # def prep_server_args(self, argv):
#     #     return argv

#     # def run_from_argv(self, argv):
#     #     if getattr(settings, "WEBSERVER_WARMUP", True):
#     #         app = get_internal_wsgi_application()
#     #         if getattr(settings, "WEBSERVER_WARMUP_HEALTHCHECK", None):
#     #             wsgi_healthcheck(app, settings.WEBSERVER_WARMUP_HEALTHCHECK)

#     #     server_name = argv[0]

#     #     # assume a dictionary for settings

#     #     self.start_server(*self.prep_server_args(argv))

#     # def execute(self, *args, **options):
#     #     raise NotImplementedError

#     def handle(self)
