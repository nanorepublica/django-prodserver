import sys
from argparse import ArgumentParser, Namespace

from gunicorn.app.wsgiapp import WSGIApplication

from ..utils import wsgi_app_name
from .base import BaseServerBackend


class DjangoApplication(WSGIApplication):
    """Dynamic Gunicorn WSGI Application."""

    def init(self, parser: ArgumentParser, opts: Namespace, args: object) -> None:
        """Initialised the Gunicorn Server."""
        # strip mgmt command name from args and insert WSGI module
        args = (wsgi_app_name(),)
        super().init(parser, opts, args)


class GunicornServer(BaseServerBackend):
    """
    Backend for gunicorn WSGI server.

    Bypasses any Django handling of the command and sends all arguments straight
    to gunicorn.
    """

    def start_server(self, *args: str) -> None:
        """Add args back into sys.argv and run the server."""
        sys.argv.extend(args)
        DjangoApplication("%(prog)s [OPTIONS]").run()
