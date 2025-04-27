import sys
from gunicorn.app.wsgiapp import WSGIApplication

from .base import BaseServerBackend
from ..utils import wsgi_app_name


class DjangoApplication(WSGIApplication):
    def init(self, parser, opts, args):
        # strip mgmt command name from args and insert WSGI module
        args = [wsgi_app_name()]
        super(DjangoApplication, self).init(parser, opts, args)


class GunicornServer(BaseServerBackend):
    """
    This bypasses any Django handling of the command and sends all arguments straight
    to gunicorn.
    """

    def start_server(self, *args):
        sys.argv.extend(args)
        DjangoApplication("%(prog)s [OPTIONS]", *args).run()
