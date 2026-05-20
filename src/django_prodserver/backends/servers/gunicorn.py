import sys
from argparse import ArgumentParser, Namespace

from gunicorn.app.wsgiapp import WSGIApplication

from ...utils import wsgi_app_name
from ..base import BaseServerBackend


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
        """
        Reset sys.argv to a clean slate and run the server.

        Gunicorn re-parses ``sys.argv``; the management command name and any
        Django options (e.g. ``--skip-checks``) must be dropped first so they
        are not mistaken for gunicorn arguments.
        """
        sys.argv[:] = [sys.argv[0], *args]
        DjangoApplication("%(prog)s [OPTIONS]").run()
