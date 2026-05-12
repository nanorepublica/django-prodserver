"""Tests for the DaphneRunserver ASGI development backend."""

import sys
from unittest.mock import patch

import pytest

# Handle optional dependency
daphne = pytest.importorskip("daphne")

from django.core.exceptions import ImproperlyConfigured  # NOQA: E402
from django.test import override_settings  # NOQA: E402
from django.utils.module_loading import import_string  # NOQA: E402

from django_prodserver.backends._runserver_base import (  # NOQA: E402
    BaseRunserverBackend,
)
from django_prodserver.backends.base import BaseServerBackend  # NOQA: E402
from django_prodserver.backends.dev.daphne import DaphneRunserver  # NOQA: E402

DEFAULT_ADDR = BaseRunserverBackend.DEFAULT_ADDR
DEFAULT_ADDR_IPV6 = BaseRunserverBackend.DEFAULT_ADDR_IPV6
DEFAULT_PORT = BaseRunserverBackend.DEFAULT_PORT


class TestParseAddrport:
    """Tests for DaphneRunserver._parse_addrport."""

    def test_port_only(self):
        assert DaphneRunserver._parse_addrport("9000") == ("127.0.0.1", 9000)

    def test_ipv4_addr_port(self):
        assert DaphneRunserver._parse_addrport("0.0.0.0:8000") == ("0.0.0.0", 8000)

    def test_ipv6_addr_port(self):
        assert DaphneRunserver._parse_addrport("[::1]:8000") == ("::1", 8000)

    def test_empty_addr_falls_back_to_default(self):
        assert DaphneRunserver._parse_addrport(":8080") == (DEFAULT_ADDR, 8080)

    def test_int_port_only(self):
        assert DaphneRunserver._parse_addrport(8000) == ("127.0.0.1", 8000)


class TestDependencyGuards:
    """Tests for the ImproperlyConfigured guards in __init__."""

    def test_raises_when_daphne_missing(self):
        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "daphne":
                raise ImportError("simulated missing daphne")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            with pytest.raises(ImproperlyConfigured, match="daphne is required"):
                DaphneRunserver()

    def test_raises_when_asgi_application_unset(self):
        with override_settings(ASGI_APPLICATION=None):
            with pytest.raises(ImproperlyConfigured, match="ASGI_APPLICATION"):
                DaphneRunserver()

    def test_raises_when_asgi_application_empty(self):
        with override_settings(ASGI_APPLICATION=""):
            with pytest.raises(ImproperlyConfigured, match="ASGI_APPLICATION"):
                DaphneRunserver()


class TestInitDefaults:
    """Tests for DaphneRunserver.__init__ defaults and ARGS parsing."""

    def test_inheritance_from_base_backend(self):
        backend = DaphneRunserver()
        assert isinstance(backend, BaseServerBackend)

    def test_defaults_with_no_args(self):
        backend = DaphneRunserver()
        assert backend.use_ipv6 is False
        assert backend.use_reloader is True
        assert backend.use_static is True
        assert backend.insecure is False
        assert backend.addr == DEFAULT_ADDR
        assert backend.port == DEFAULT_PORT
        assert backend.protocol == "http"
        assert backend.http_timeout is None
        assert backend.websocket_handshake_timeout == 5
        assert backend.websocket_timeout == 86400
        assert backend.websocket_connect_timeout == 20
        assert backend.ping_interval == 20
        assert backend.ping_timeout == 30
        assert backend.application_close_timeout == 10
        assert backend.request_buffer_size == 8192
        assert backend.verbosity == 1
        assert backend.server_name == "daphne"
        assert backend.root_path == ""
        assert backend.unix_socket is None
        assert backend.fd is None
        assert backend.raw_endpoints == []
        assert backend.proxy_headers is False
        assert backend.access_log_path is None

    def test_defaults_with_empty_args(self):
        backend = DaphneRunserver(ARGS={})
        assert backend.addr == DEFAULT_ADDR
        assert backend.port == DEFAULT_PORT

    def test_default_addrport_for_ipv6(self):
        backend = DaphneRunserver(ARGS={"ipv6": True})
        assert backend.use_ipv6 is True
        assert backend.addr == DEFAULT_ADDR_IPV6
        assert backend.port == DEFAULT_PORT

    def test_addrport_overrides_default(self):
        backend = DaphneRunserver(ARGS={"addrport": "0.0.0.0:9000"})
        assert backend.addr == "0.0.0.0"
        assert backend.port == 9000

    def test_noreload_flag(self):
        backend = DaphneRunserver(ARGS={"noreload": True})
        assert backend.use_reloader is False

    def test_nostatic_flag(self):
        backend = DaphneRunserver(ARGS={"nostatic": True})
        assert backend.use_static is False

    def test_insecure_flag(self):
        backend = DaphneRunserver(ARGS={"insecure": True})
        assert backend.insecure is True

    def test_nothreading_flag_is_no_op(self):
        # Accepted for parity with DjangoRunserver; Daphne ignores it.
        backend = DaphneRunserver(ARGS={"nothreading": True})
        assert backend.addr == DEFAULT_ADDR

    def test_daphne_kwarg_overrides(self, tmp_path):
        log_path = str(tmp_path / "access.log")
        backend = DaphneRunserver(
            ARGS={
                "http_timeout": 30,
                "websocket_handshake_timeout": 7,
                "websocket_timeout": 100,
                "websocket_connect_timeout": 11,
                "ping_interval": 12,
                "ping_timeout": 13,
                "application_close_timeout": 14,
                "request_buffer_size": 4096,
                "verbosity": 2,
                "server_name": "custom",
                "root_path": "/api",
                "proxy_headers": True,
                "access_log": log_path,
            }
        )
        assert backend.http_timeout == 30
        assert backend.websocket_handshake_timeout == 7
        assert backend.websocket_timeout == 100
        assert backend.websocket_connect_timeout == 11
        assert backend.ping_interval == 12
        assert backend.ping_timeout == 13
        assert backend.application_close_timeout == 14
        assert backend.request_buffer_size == 4096
        assert backend.verbosity == 2
        assert backend.server_name == "custom"
        assert backend.root_path == "/api"
        assert backend.proxy_headers is True
        assert backend.access_log_path == log_path

    def test_unix_socket_arg(self, tmp_path):
        sock = str(tmp_path / "d.sock")
        backend = DaphneRunserver(ARGS={"unix_socket": sock})
        assert backend.unix_socket == sock

    def test_fd_arg(self):
        backend = DaphneRunserver(ARGS={"fd": 3})
        assert backend.fd == 3

    def test_raw_endpoints_arg(self):
        eps = ["tcp:port=9000:interface=0.0.0.0", "ssl:443:..."]
        backend = DaphneRunserver(ARGS={"endpoints": eps})
        assert backend.raw_endpoints == eps

    def test_root_path_falls_back_to_force_script_name(self):
        with override_settings(FORCE_SCRIPT_NAME="/prefix"):
            backend = DaphneRunserver()
        assert backend.root_path == "/prefix"

    def test_unknown_args_keys_ignored(self):
        backend = DaphneRunserver(
            ARGS={"addrport": "127.0.0.1:8000", "unknown_key": "ignored"}
        )
        assert backend.addr == "127.0.0.1"
        assert backend.port == 8000

    def test_extra_top_level_config_keys_ignored(self):
        backend = DaphneRunserver(
            ARGS={"addrport": "127.0.0.1:8000"},
            EXTRA_KEY="ignored",
        )
        assert backend.addr == "127.0.0.1"


class TestBuildEndpoints:
    """Tests for DaphneRunserver._build_endpoints."""

    def test_tcp_endpoint(self):
        backend = DaphneRunserver(ARGS={"addrport": "127.0.0.1:8000"})
        assert backend._build_endpoints() == ["tcp:port=8000:interface=127.0.0.1"]

    def test_ipv6_endpoint(self):
        backend = DaphneRunserver(ARGS={"ipv6": True, "addrport": "[::1]:8000"})
        assert backend._build_endpoints() == ["tcp:port=8000:interface=\\:\\:1"]

    def test_unix_socket_excludes_tcp(self, tmp_path):
        sock = str(tmp_path / "d.sock")
        backend = DaphneRunserver(ARGS={"unix_socket": sock})
        assert backend._build_endpoints() == [f"unix:{sock}"]

    def test_fd_excludes_tcp(self):
        backend = DaphneRunserver(ARGS={"fd": 3})
        assert backend._build_endpoints() == ["fd:fileno=3"]

    def test_raw_endpoints_merged_and_sorted(self):
        backend = DaphneRunserver(
            ARGS={
                "addrport": "127.0.0.1:8000",
                "endpoints": ["tcp:port=9000:interface=0.0.0.0"],
            }
        )
        assert backend._build_endpoints() == [
            "tcp:port=8000:interface=127.0.0.1",
            "tcp:port=9000:interface=0.0.0.0",
        ]


class TestGetApplication:
    """Tests for DaphneRunserver.get_application matching channels-runserver."""

    @patch(
        "django.utils.module_loading.import_string",
        return_value="ASGI_APP",
    )
    @patch(
        "asgiref.compatibility.guarantee_single_callable",
        side_effect=lambda app: app,
    )
    def test_returns_plain_app_when_nostatic(self, _g, _i):
        backend = DaphneRunserver(ARGS={"nostatic": True})
        assert backend.get_application() == "ASGI_APP"

    @override_settings(INSTALLED_APPS=["django.contrib.auth"], DEBUG=True)
    @patch(
        "django.utils.module_loading.import_string",
        return_value="ASGI_APP",
    )
    @patch(
        "asgiref.compatibility.guarantee_single_callable",
        side_effect=lambda app: app,
    )
    def test_returns_plain_app_when_staticfiles_not_installed(self, _g, _i):
        backend = DaphneRunserver()
        assert backend.get_application() == "ASGI_APP"

    @override_settings(DEBUG=False)
    @patch(
        "django.utils.module_loading.import_string",
        return_value="ASGI_APP",
    )
    @patch(
        "asgiref.compatibility.guarantee_single_callable",
        side_effect=lambda app: app,
    )
    def test_returns_plain_app_when_debug_false_and_not_insecure(self, _g, _i):
        backend = DaphneRunserver(ARGS={"insecure": False})
        assert backend.get_application() == "ASGI_APP"

    @override_settings(DEBUG=True, STATIC_URL="/static/")
    @patch(
        "django.utils.module_loading.import_string",
        return_value="ASGI_APP",
    )
    @patch(
        "asgiref.compatibility.guarantee_single_callable",
        side_effect=lambda app: app,
    )
    def test_wraps_when_debug_true(self, _g, _i):
        from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

        backend = DaphneRunserver()
        handler = backend.get_application()
        assert isinstance(handler, ASGIStaticFilesHandler)

    @override_settings(DEBUG=False, STATIC_URL="/static/")
    @patch(
        "django.utils.module_loading.import_string",
        return_value="ASGI_APP",
    )
    @patch(
        "asgiref.compatibility.guarantee_single_callable",
        side_effect=lambda app: app,
    )
    def test_wraps_when_debug_false_but_insecure_true(self, _g, _i):
        from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

        backend = DaphneRunserver(ARGS={"insecure": True})
        handler = backend.get_application()
        assert isinstance(handler, ASGIStaticFilesHandler)


class TestActionLogger:
    """Tests for DaphneRunserver._action_logger."""

    def test_returns_none_when_verbosity_zero_and_no_path(self):
        backend = DaphneRunserver(ARGS={"verbosity": 0})
        assert backend._action_logger() is None

    def test_returns_stdout_logger_when_verbosity_set(self):
        from daphne.access import AccessLogGenerator

        backend = DaphneRunserver(ARGS={"verbosity": 1})
        logger = backend._action_logger()
        assert isinstance(logger, AccessLogGenerator)
        assert logger.stream is sys.stdout

    def test_opens_file_when_access_log_path_set(self, tmp_path):
        from daphne.access import AccessLogGenerator

        path = tmp_path / "access.log"
        backend = DaphneRunserver(ARGS={"access_log": str(path)})
        logger = backend._action_logger()
        assert isinstance(logger, AccessLogGenerator)
        try:
            assert logger.stream.name == str(path)
        finally:
            logger.stream.close()


class TestInnerRun:
    """Tests for DaphneRunserver._inner_run mirroring channels-runserver's inner_run."""

    @patch("daphne.server.Server")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_inner_run_calls_check_pipeline(
        self,
        mock_raise_last,
        mock_check,
        mock_check_migrations,
        mock_server_cls,
    ):
        backend = DaphneRunserver(ARGS={"noreload": True, "nostatic": True})
        with patch.object(backend, "get_application", return_value="APP"):
            backend._inner_run()

        mock_raise_last.assert_called_once_with()
        mock_check.assert_called_once_with(display_num_errors=True)
        mock_check_migrations.assert_called_once_with()
        mock_server_cls.assert_called_once()
        mock_server_cls.return_value.run.assert_called_once_with()

    @patch("daphne.server.Server")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_inner_run_passes_correct_kwargs_to_server(
        self,
        _mock_raise,
        _mock_check,
        _mock_check_migrations,
        mock_server_cls,
    ):
        backend = DaphneRunserver(
            ARGS={
                "addrport": "0.0.0.0:9000",
                "nostatic": True,
                "noreload": True,
                "http_timeout": 30,
                "websocket_handshake_timeout": 7,
                "verbosity": 2,
                "server_name": "custom",
            }
        )
        with patch.object(backend, "get_application", return_value="APP"):
            backend._inner_run()

        kwargs = mock_server_cls.call_args.kwargs
        assert kwargs["application"] == "APP"
        assert kwargs["endpoints"] == ["tcp:port=9000:interface=0.0.0.0"]
        # noreload=True -> use_reloader=False -> signal_handlers=True
        assert kwargs["signal_handlers"] is True
        assert kwargs["http_timeout"] == 30
        assert kwargs["websocket_handshake_timeout"] == 7
        assert kwargs["verbosity"] == 2
        assert kwargs["server_name"] == "custom"
        # proxy_headers default False -> all three headers None
        assert kwargs["proxy_forwarded_address_header"] is None
        assert kwargs["proxy_forwarded_port_header"] is None
        assert kwargs["proxy_forwarded_proto_header"] is None

    @patch("daphne.server.Server")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_signal_handlers_off_under_reloader(
        self,
        _mock_raise,
        _mock_check,
        _mock_check_migrations,
        mock_server_cls,
    ):
        # Default noreload=False -> use_reloader=True -> signal_handlers must be False.
        backend = DaphneRunserver(ARGS={"nostatic": True})
        with patch.object(backend, "get_application", return_value="APP"):
            backend._inner_run()

        assert mock_server_cls.call_args.kwargs["signal_handlers"] is False

    @patch("daphne.server.Server")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_proxy_headers_set_all_three_forwarded_headers(
        self,
        _mock_raise,
        _mock_check,
        _mock_check_migrations,
        mock_server_cls,
    ):
        backend = DaphneRunserver(
            ARGS={"proxy_headers": True, "noreload": True, "nostatic": True}
        )
        with patch.object(backend, "get_application", return_value="APP"):
            backend._inner_run()

        kwargs = mock_server_cls.call_args.kwargs
        assert kwargs["proxy_forwarded_address_header"] == "X-Forwarded-For"
        assert kwargs["proxy_forwarded_port_header"] == "X-Forwarded-Port"
        assert kwargs["proxy_forwarded_proto_header"] == "X-Forwarded-Proto"


class TestStartServer:
    """Tests for DaphneRunserver.start_server reload/no-reload dispatch."""

    @patch("django.utils.autoreload.run_with_reloader")
    def test_start_server_with_reloader(self, mock_run_with_reloader):
        backend = DaphneRunserver(ARGS={"addrport": "127.0.0.1:8000"})
        backend.start_server()
        mock_run_with_reloader.assert_called_once_with(backend._inner_run)

    def test_start_server_without_reloader_calls_inner_run(self):
        backend = DaphneRunserver(ARGS={"noreload": True})
        with patch.object(backend, "_inner_run") as mock_inner:
            backend.start_server()
        mock_inner.assert_called_once_with()


class TestDisplayAddr:
    """Tests for the small _display_addr helper."""

    def test_display_addr_ipv4(self):
        backend = DaphneRunserver(ARGS={"addrport": "127.0.0.1:8000"})
        assert backend._display_addr() == "127.0.0.1"

    def test_display_addr_ipv6(self):
        backend = DaphneRunserver(ARGS={"ipv6": True, "addrport": "[::1]:8000"})
        assert backend._display_addr() == "[::1]"


def test_backend_resolves_via_import_string():
    """The dispatcher uses import_string; ensure the dotted path resolves."""
    cls = import_string("django_prodserver.backends.dev.daphne.DaphneRunserver")
    assert cls is DaphneRunserver
    instance = cls(ARGS={"addrport": "127.0.0.1:8000"})
    assert isinstance(instance, BaseServerBackend)
