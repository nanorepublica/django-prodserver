"""Pure-Python development server backend mirroring Django's runserver."""

import errno
import sys
from typing import Any

from ._runserver_base import BaseRunserverBackend


class DjangoRunserver(BaseRunserverBackend):
    """
    Development server backend mirroring django.core.management.commands.runserver.

    Configured entirely through the standard ARGS dict, with key names that
    match runserver's CLI flags 1:1::

        {
            "BACKEND": "django_prodserver.backends.django_runserver.DjangoRunserver",
            "ARGS": {
                "addrport": "127.0.0.1:8000",
                "ipv6": False,
                "noreload": False,
                "nothreading": False,
                "nostatic": False,
                "insecure": False,
            },
        }

    All keys are optional. Behaviour mirrors runserver's inner_run by calling
    out to Django's existing utilities (BaseCommand.check, basehttp.run,
    autoreload.run_with_reloader, StaticFilesHandler) rather than reimplementing
    them.
    """

    server_kind = "development"

    def __init__(self, **server_args: Any) -> None:
        """Parse the runserver-specific ARGS keys on top of the shared ones."""
        super().__init__(**server_args)
        args = server_args.get("ARGS") or {}
        self.use_threading = not bool(args.get("nothreading", False))

    def get_handler(self) -> Any:
        """Mirror runserver.get_handler + the staticfiles override."""
        from django.core.servers.basehttp import get_internal_wsgi_application

        handler = get_internal_wsgi_application()
        if not self._should_wrap_static():
            return handler
        from django.contrib.staticfiles.handlers import StaticFilesHandler

        return StaticFilesHandler(handler)

    def _inner_run(self) -> None:
        """1:1 mirror of django.core.management.commands.runserver.Command.inner_run."""
        from django.core.servers.basehttp import (
            ThreadedWSGIServer,
            WSGIServer,
            run,
        )

        cmd = self._run_checks_and_banner()

        server_cls = ThreadedWSGIServer if self.use_threading else WSGIServer
        try:
            run(
                self.addr,
                self.port,
                self.get_handler(),
                ipv6=self.use_ipv6,
                threading=self.use_threading,
                server_cls=server_cls,
            )
        except OSError as e:
            errors = {
                errno.EACCES: "You don't have permission to access that port.",
                errno.EADDRINUSE: "That port is already in use.",
                errno.EADDRNOTAVAIL: "That IP address can't be assigned to.",
            }
            cmd.stderr.write(f"Error: {errors.get(e.errno, str(e))}")
            sys.exit(1)
        except KeyboardInterrupt:
            sys.exit(0)
