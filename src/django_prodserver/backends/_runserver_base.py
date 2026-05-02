"""
Shared scaffolding for runserver-style development backends.

Used by ``DjangoRunserver`` (WSGI) and ``DaphneRunserver`` (ASGI) to share
the bits of Django's runserver that are identical between them: addrport
parsing, the staticfiles gating policy, the system-checks pipeline, the
banner header, and the autoreload dispatch.
"""

from datetime import datetime
from typing import Any

from .base import BaseServerBackend


class BaseRunserverBackend(BaseServerBackend):
    """
    Common scaffolding for runserver-style development backends.

    Subclasses must implement ``_inner_run`` to actually start the server.
    They typically also override ``server_kind`` (used in the banner) and
    extend ``__init__`` to parse any backend-specific ARGS keys.
    """

    DEFAULT_PORT = 8000
    DEFAULT_ADDR = "127.0.0.1"
    DEFAULT_ADDR_IPV6 = "::1"

    server_kind: str = "development"

    def __init__(self, **server_args: Any) -> None:
        """Parse ARGS keys shared by every runserver-style backend."""
        super().__init__(**server_args)
        args = server_args.get("ARGS") or {}
        self.use_ipv6 = bool(args.get("ipv6", False))
        self.use_reloader = not bool(args.get("noreload", False))
        self.use_static = not bool(args.get("nostatic", False))
        self.insecure = bool(args.get("insecure", False))
        self.addr, self.port = self._parse_addrport(
            args.get("addrport") or self._default_addrport()
        )
        self.protocol = "http"

    def _default_addrport(self) -> str:
        if self.use_ipv6:
            return f"[{self.DEFAULT_ADDR_IPV6}]:{self.DEFAULT_PORT}"
        return f"{self.DEFAULT_ADDR}:{self.DEFAULT_PORT}"

    @classmethod
    def _parse_addrport(cls, addrport: str | int) -> tuple[str, int]:
        s = str(addrport)
        if s.startswith("["):
            addr, _, port = s.rpartition(":")
            return addr.strip("[]"), int(port)
        if ":" in s:
            addr, port = s.rsplit(":", 1)
            return (addr or cls.DEFAULT_ADDR), int(port)
        return cls.DEFAULT_ADDR, int(s)

    def _display_addr(self) -> str:
        return f"[{self.addr}]" if self.use_ipv6 else self.addr

    def _should_wrap_static(self) -> bool:
        """Mirror runserver's exact decision on whether to serve static files."""
        from django.conf import settings

        return (
            self.use_static
            and "django.contrib.staticfiles" in settings.INSTALLED_APPS
            and bool(settings.DEBUG or self.insecure)
        )

    def _run_checks_and_banner(self) -> Any:
        """
        Run ``raise_last_exception`` + system checks and print the runserver banner.

        Returns the BaseCommand instance so callers can use ``cmd.stderr`` for
        their own error reporting.
        """
        from django import get_version
        from django.conf import settings
        from django.core.management.base import BaseCommand
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
            f"Starting {self.server_kind} server at "
            f"{self.protocol}://{self._display_addr()}:{self.port}/\n"
            f"Quit the server with CONTROL-C.\n"
        )
        return cmd

    def _inner_run(self) -> None:
        """Start the server. Must be implemented by subclasses."""
        raise NotImplementedError

    def start_server(self, *args: str) -> None:
        """Run the dev server, optionally under the autoreloader."""
        from django.utils import autoreload

        if self.use_reloader:
            autoreload.run_with_reloader(self._inner_run)
        else:
            self._inner_run()
