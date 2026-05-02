"""Pure-Python development server backend mirroring Django's runserver."""

import errno
import sys
from datetime import datetime
from typing import Any

from .base import BaseServerBackend

DEFAULT_PORT = 8000
DEFAULT_ADDR = "127.0.0.1"
DEFAULT_ADDR_IPV6 = "::1"


class DjangoRunserver(BaseServerBackend):
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

    def __init__(self, **server_args: Any) -> None:
        """Parse ARGS into typed Python attributes."""
        super().__init__(**server_args)
        args = server_args.get("ARGS") or {}
        self.use_ipv6 = bool(args.get("ipv6", False))
        self.use_reloader = not bool(args.get("noreload", False))
        self.use_threading = not bool(args.get("nothreading", False))
        self.use_static = not bool(args.get("nostatic", False))
        self.insecure = bool(args.get("insecure", False))
        self.addr, self.port = self._parse_addrport(
            args.get("addrport") or self._default_addrport()
        )
        self.protocol = "http"

    def _default_addrport(self) -> str:
        if self.use_ipv6:
            return f"[{DEFAULT_ADDR_IPV6}]:{DEFAULT_PORT}"
        return f"{DEFAULT_ADDR}:{DEFAULT_PORT}"

    @staticmethod
    def _parse_addrport(addrport: str | int) -> tuple[str, int]:
        s = str(addrport)
        if s.startswith("["):
            addr, _, port = s.rpartition(":")
            return addr.strip("[]"), int(port)
        if ":" in s:
            addr, port = s.rsplit(":", 1)
            return (addr or DEFAULT_ADDR), int(port)
        return DEFAULT_ADDR, int(s)

    def get_handler(self) -> Any:
        """Mirror runserver.get_handler + the staticfiles override."""
        from django.conf import settings
        from django.core.servers.basehttp import get_internal_wsgi_application

        handler = get_internal_wsgi_application()
        if not self.use_static:
            return handler
        if "django.contrib.staticfiles" not in settings.INSTALLED_APPS:
            return handler
        if not (settings.DEBUG or self.insecure):
            return handler
        from django.contrib.staticfiles.handlers import StaticFilesHandler

        return StaticFilesHandler(handler)

    def _inner_run(self) -> None:
        """1:1 mirror of django.core.management.commands.runserver.Command.inner_run."""
        from django import get_version
        from django.conf import settings
        from django.core.management.base import BaseCommand
        from django.core.servers.basehttp import (
            ThreadedWSGIServer,
            WSGIServer,
            run,
        )
        from django.utils import autoreload

        autoreload.raise_last_exception()

        cmd = BaseCommand()
        cmd.stdout.write("Performing system checks...\n\n")
        cmd.check(display_num_errors=True)
        cmd.check_migrations()

        now = datetime.now().strftime("%B %d, %Y - %X")
        cmd.stdout.write(
            f"{now}\n"
            f"Django version {get_version()}, using settings "
            f"{settings.SETTINGS_MODULE!r}\n"
            f"Starting development server at "
            f"{self.protocol}://{self._display_addr()}:{self.port}/\n"
            f"Quit the server with CONTROL-C.\n"
        )

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

    def start_server(self, *args: str) -> None:
        """Run the dev server, optionally under the autoreloader."""
        from django.utils import autoreload

        if self.use_reloader:
            autoreload.run_with_reloader(self._inner_run)
        else:
            self._inner_run()

    def _display_addr(self) -> str:
        return f"[{self.addr}]" if self.use_ipv6 else self.addr
