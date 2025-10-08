"""Granian server backends for ASGI and WSGI applications."""

from typing import Any

from ..utils import asgi_app_name, wsgi_app_name
from .base import BaseServerBackend


class GranianServerBase(BaseServerBackend):
    """
    Base class for Granian server backends.

    Provides common functionality for both ASGI and WSGI Granian servers,
    including argument parsing and server configuration.
    """

    def __init__(self, **server_args: Any) -> None:
        """Initialize the Granian server backend."""
        super().__init__(**server_args)
        self.server_config = server_args.get("ARGS", {})

    def _parse_granian_kwargs(self) -> dict[str, Any]:
        """Parse server configuration into Granian constructor kwargs."""
        kwargs: dict[str, Any] = {}

        # Map common argument names to Granian constructor parameters
        arg_mapping = {
            "address": ("address", str),
            "host": ("address", str),  # Alias for address
            "port": ("port", int),
            "workers": ("workers", int),
            "blocking-threads": ("blocking_threads", int),
            "blocking_threads": ("blocking_threads", int),
            "threads": ("blocking_threads", int),  # Common alias
            "runtime-threads": ("runtime_threads", int),
            "runtime_threads": ("runtime_threads", int),
            "backlog": ("backlog", int),
            "http": ("http", str),
            "websockets": ("websockets", bool),
            "log-level": ("log_level", str),
            "log_level": ("log_level", str),
            "log-access": ("log_access", bool),
            "log_access": ("log_access", bool),
            "ssl-cert": ("ssl_cert", str),
            "ssl_cert": ("ssl_cert", str),
            "ssl-key": ("ssl_key", str),
            "ssl_key": ("ssl_key", str),
            "url-path-prefix": ("url_path_prefix", str),
            "url_path_prefix": ("url_path_prefix", str),
            "reload": ("reload", bool),
        }

        for key, value in self.server_config.items():
            if key in arg_mapping:
                param_name, param_type = arg_mapping[key]
                # Convert string values to appropriate types
                if param_type is int:
                    kwargs[param_name] = int(value)
                elif param_type is bool:
                    # Handle boolean string conversion
                    kwargs[param_name] = (
                        value.lower() in ("true", "1", "yes", "on")
                        if isinstance(value, str)
                        else bool(value)
                    )
                else:
                    kwargs[param_name] = value

        return kwargs

    def _get_interface(self) -> Any:
        """Get the Granian interface type. Must be implemented by subclasses."""
        raise NotImplementedError

    def _get_app_target(self) -> str:
        """Get the application target string. Must be implemented by subclasses."""
        raise NotImplementedError

    def start_server(self, *args: str) -> None:
        """Start the Granian server."""
        try:
            from granian import Granian
        except ImportError as e:
            msg = "Granian is not installed. Install it with: pip install granian"
            raise ImportError(msg) from e

        # Parse configuration
        kwargs = self._parse_granian_kwargs()

        # Create and start Granian server
        server = Granian(
            target=self._get_app_target(),
            interface=self._get_interface(),
            **kwargs,
        )
        server.serve()


class GranianASGIServer(GranianServerBase):
    """
    Granian ASGI Server Backend.

    This backend uses Granian's ASGI interface to serve Django ASGI applications.
    Granian is a Rust-based HTTP server with excellent performance characteristics.

    Example configuration:
        {
            "BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
            "ARGS": {
                "address": "0.0.0.0",
                "port": "8000",
                "workers": "4",
                "blocking_threads": "1",
            }
        }
    """

    def _get_interface(self) -> Any:
        """Get the ASGI interface type."""
        from granian.constants import Interfaces

        return Interfaces.ASGI

    def _get_app_target(self) -> str:
        """Get the ASGI application target."""
        return asgi_app_name()


class GranianWSGIServer(GranianServerBase):
    """
    Granian WSGI Server Backend.

    This backend uses Granian's WSGI interface to serve Django WSGI applications.
    Granian is a Rust-based HTTP server with excellent performance characteristics.

    Example configuration:
        {
            "BACKEND": "django_prodserver.backends.granian.GranianWSGIServer",
            "ARGS": {
                "address": "0.0.0.0",
                "port": "8000",
                "workers": "4",
                "blocking_threads": "2",
            }
        }
    """

    def _get_interface(self) -> Any:
        """Get the WSGI interface type."""
        from granian.constants import Interfaces

        return Interfaces.WSGI

    def _get_app_target(self) -> str:
        """Get the WSGI application target."""
        return wsgi_app_name()
