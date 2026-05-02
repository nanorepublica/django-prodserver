"""Pure-Python ASGI dev server backend mirroring channels runserver via Daphne."""

import sys
from datetime import datetime
from typing import Any

from django.core.exceptions import ImproperlyConfigured

from .base import BaseServerBackend

DEFAULT_PORT = 8000
DEFAULT_ADDR = "127.0.0.1"
DEFAULT_ADDR_IPV6 = "::1"


class DaphneRunserver(BaseServerBackend):
    """
    ASGI development server backend driving daphne.Server directly.

    Mirrors the behaviour of channels-runserver 3.0.5 (which Channels 4.x
    no longer ships) by calling out to Daphne's public API and Django's
    autoreload / system-check utilities, rather than going through any
    management command.

    Configured entirely through the standard ARGS dict, with key names that
    match Daphne's CLI flags 1:1::

        {
            "BACKEND": "django_prodserver.backends.daphne.DaphneRunserver",
            "ARGS": {
                "addrport": "127.0.0.1:8000",
                "ipv6": False,
                "noreload": False,
                "nostatic": False,
                "insecure": False,
                "http_timeout": None,
                "websocket_handshake_timeout": 5,
                # Full Daphne CLI surface also accepted:
                "unix_socket": None,
                "fd": None,
                "endpoints": [],
                "verbosity": 1,
                "root_path": "",
                "proxy_headers": False,
                "ping_interval": 20,
                "ping_timeout": 30,
                "application_close_timeout": 10,
                "websocket_timeout": 86400,
                "websocket_connect_timeout": 20,
                "request_buffer_size": 8192,
                "server_name": "daphne",
                "access_log": None,
            },
        }

    All keys are optional. ``nothreading`` is accepted for parity with
    DjangoRunserver but ignored — Daphne is single-reactor by design.
    """

    def __init__(self, **server_args: Any) -> None:
        """Validate dependencies and parse ARGS into typed Python attributes."""
        super().__init__(**server_args)

        try:
            import daphne  # noqa: F401
        except ImportError as e:
            raise ImproperlyConfigured(
                "daphne is required to use DaphneRunserver backend. "
                "Install it with: pip install daphne"
            ) from e

        from django.conf import settings

        if not getattr(settings, "ASGI_APPLICATION", None):
            raise ImproperlyConfigured(
                "ASGI_APPLICATION must be set to use DaphneRunserver backend."
            )

        args = server_args.get("ARGS") or {}

        self.use_ipv6 = bool(args.get("ipv6", False))
        self.use_reloader = not bool(args.get("noreload", False))
        self.use_static = not bool(args.get("nostatic", False))
        self.insecure = bool(args.get("insecure", False))

        self.addr, self.port = self._parse_addrport(
            args.get("addrport") or self._default_addrport()
        )
        self.protocol = "http"

        self.http_timeout = args.get("http_timeout")
        self.websocket_handshake_timeout = int(
            args.get("websocket_handshake_timeout", 5)
        )
        self.websocket_timeout = int(args.get("websocket_timeout", 86400))
        self.websocket_connect_timeout = int(args.get("websocket_connect_timeout", 20))
        self.ping_interval = int(args.get("ping_interval", 20))
        self.ping_timeout = int(args.get("ping_timeout", 30))
        self.application_close_timeout = int(args.get("application_close_timeout", 10))
        self.request_buffer_size = int(args.get("request_buffer_size", 8192))
        self.verbosity = int(args.get("verbosity", 1))
        self.server_name = str(args.get("server_name", "daphne"))
        self.root_path = str(
            args.get("root_path") or getattr(settings, "FORCE_SCRIPT_NAME", "") or ""
        )

        self.unix_socket = args.get("unix_socket")
        self.fd = args.get("fd")
        self.raw_endpoints = list(args.get("endpoints") or [])

        self.proxy_headers = bool(args.get("proxy_headers", False))

        self.access_log_path = args.get("access_log")

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

    def _build_endpoints(self) -> list[str]:
        """Build Twisted endpoint description strings using Daphne's helper."""
        from daphne.endpoints import build_endpoint_description_strings

        explicit_socket = self.unix_socket is not None or self.fd is not None
        generated = build_endpoint_description_strings(
            host=None if explicit_socket else self.addr,
            port=None if explicit_socket else self.port,
            unix_socket=self.unix_socket,
            file_descriptor=self.fd,
        )
        return sorted(self.raw_endpoints + generated)

    def get_application(self) -> Any:
        """Resolve the ASGI app and conditionally wrap with ASGIStaticFilesHandler."""
        from asgiref.compatibility import guarantee_single_callable
        from django.conf import settings
        from django.utils.module_loading import import_string

        app = guarantee_single_callable(import_string(settings.ASGI_APPLICATION))
        if not self.use_static:
            return app
        if "django.contrib.staticfiles" not in settings.INSTALLED_APPS:
            return app
        if not (settings.DEBUG or self.insecure):
            return app
        from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

        return ASGIStaticFilesHandler(app)

    def _action_logger(self) -> Any:
        """Build the Daphne access logger from the access_log / verbosity config."""
        from daphne.access import AccessLogGenerator

        if self.access_log_path:
            stream = open(self.access_log_path, "a", buffering=1)
            return AccessLogGenerator(stream)
        if self.verbosity >= 1:
            return AccessLogGenerator(sys.stdout)
        return None

    def _display_addr(self) -> str:
        return f"[{self.addr}]" if self.use_ipv6 else self.addr

    def _inner_run(self) -> None:
        """1:1 mirror of channels-runserver 3.0.5 inner_run, driving daphne directly."""
        from daphne.server import Server
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
            f"Starting ASGI development server at "
            f"{self.protocol}://{self._display_addr()}:{self.port}/\n"
            f"Quit the server with CONTROL-C.\n"
        )

        Server(
            application=self.get_application(),
            endpoints=self._build_endpoints(),
            signal_handlers=not self.use_reloader,
            action_logger=self._action_logger(),
            http_timeout=self.http_timeout,
            websocket_handshake_timeout=self.websocket_handshake_timeout,
            websocket_timeout=self.websocket_timeout,
            websocket_connect_timeout=self.websocket_connect_timeout,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
            application_close_timeout=self.application_close_timeout,
            request_buffer_size=self.request_buffer_size,
            root_path=self.root_path,
            verbosity=self.verbosity,
            server_name=self.server_name,
            proxy_forwarded_address_header=(
                "X-Forwarded-For" if self.proxy_headers else None
            ),
            proxy_forwarded_port_header=(
                "X-Forwarded-Port" if self.proxy_headers else None
            ),
            proxy_forwarded_proto_header=(
                "X-Forwarded-Proto" if self.proxy_headers else None
            ),
        ).run()

    def start_server(self, *args: str) -> None:
        """Run the dev server, optionally under the autoreloader."""
        from django.utils import autoreload

        if self.use_reloader:
            autoreload.run_with_reloader(self._inner_run)
        else:
            self._inner_run()
