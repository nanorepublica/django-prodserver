"""Tests for the DjangoRunserver development backend."""

import errno
from unittest.mock import patch

import pytest
from django.test import override_settings
from django.utils.module_loading import import_string

from django_prodserver.backends._runserver_base import (
    BaseRunserverBackend,
)
from django_prodserver.backends.base import BaseServerBackend
from django_prodserver.backends.dev.django_runserver import DjangoRunserver

DEFAULT_ADDR = BaseRunserverBackend.DEFAULT_ADDR
DEFAULT_ADDR_IPV6 = BaseRunserverBackend.DEFAULT_ADDR_IPV6
DEFAULT_PORT = BaseRunserverBackend.DEFAULT_PORT


class TestParseAddrport:
    """Tests for DjangoRunserver._parse_addrport."""

    def test_port_only(self):
        assert DjangoRunserver._parse_addrport("9000") == ("127.0.0.1", 9000)

    def test_ipv4_addr_port(self):
        assert DjangoRunserver._parse_addrport("0.0.0.0:8000") == ("0.0.0.0", 8000)

    def test_ipv6_addr_port(self):
        assert DjangoRunserver._parse_addrport("[::1]:8000") == ("::1", 8000)

    def test_empty_addr_falls_back_to_default(self):
        assert DjangoRunserver._parse_addrport(":8080") == (DEFAULT_ADDR, 8080)

    def test_int_port_only(self):
        assert DjangoRunserver._parse_addrport(8000) == ("127.0.0.1", 8000)


class TestInitDefaults:
    """Tests for DjangoRunserver.__init__ defaults and ARGS parsing."""

    def test_inheritance_from_base_backend(self):
        backend = DjangoRunserver()
        assert isinstance(backend, BaseServerBackend)

    def test_does_not_accept_extra_args(self):
        """Runserver-style backends reject forwarded command-line args."""
        assert BaseRunserverBackend.accepts_extra_args is False
        assert DjangoRunserver().accepts_extra_args is False

    def test_defaults_with_no_args(self):
        backend = DjangoRunserver()
        assert backend.use_ipv6 is False
        assert backend.use_reloader is True
        assert backend.use_threading is True
        assert backend.use_static is True
        assert backend.insecure is False
        assert backend.addr == DEFAULT_ADDR
        assert backend.port == DEFAULT_PORT
        assert backend.protocol == "http"

    def test_defaults_with_empty_args(self):
        backend = DjangoRunserver(ARGS={})
        assert backend.addr == DEFAULT_ADDR
        assert backend.port == DEFAULT_PORT

    def test_default_addrport_for_ipv6(self):
        backend = DjangoRunserver(ARGS={"ipv6": True})
        assert backend.use_ipv6 is True
        assert backend.addr == DEFAULT_ADDR_IPV6
        assert backend.port == DEFAULT_PORT

    def test_addrport_overrides_default(self):
        backend = DjangoRunserver(ARGS={"addrport": "0.0.0.0:9000"})
        assert backend.addr == "0.0.0.0"
        assert backend.port == 9000

    def test_noreload_flag(self):
        backend = DjangoRunserver(ARGS={"noreload": True})
        assert backend.use_reloader is False

    def test_nothreading_flag(self):
        backend = DjangoRunserver(ARGS={"nothreading": True})
        assert backend.use_threading is False

    def test_nostatic_flag(self):
        backend = DjangoRunserver(ARGS={"nostatic": True})
        assert backend.use_static is False

    def test_insecure_flag(self):
        backend = DjangoRunserver(ARGS={"insecure": True})
        assert backend.insecure is True

    def test_unknown_args_keys_ignored(self):
        backend = DjangoRunserver(
            ARGS={"addrport": "127.0.0.1:8000", "unknown_key": "ignored"}
        )
        assert backend.addr == "127.0.0.1"
        assert backend.port == 8000

    def test_extra_top_level_config_keys_ignored(self):
        backend = DjangoRunserver(
            ARGS={"addrport": "127.0.0.1:8000"},
            EXTRA_KEY="ignored",
        )
        assert backend.addr == "127.0.0.1"


class TestGetHandler:
    """Tests for DjangoRunserver.get_handler matching runserver's policy."""

    @patch(
        "django.core.servers.basehttp.get_internal_wsgi_application",
        return_value="WSGI_APP",
    )
    def test_returns_plain_app_when_nostatic(self, _mock_get_app):
        backend = DjangoRunserver(ARGS={"nostatic": True})
        assert backend.get_handler() == "WSGI_APP"

    @override_settings(INSTALLED_APPS=["django.contrib.auth"], DEBUG=True)
    @patch(
        "django.core.servers.basehttp.get_internal_wsgi_application",
        return_value="WSGI_APP",
    )
    def test_returns_plain_app_when_staticfiles_not_installed(self, _mock_get_app):
        backend = DjangoRunserver()
        assert backend.get_handler() == "WSGI_APP"

    @override_settings(DEBUG=False)
    @patch(
        "django.core.servers.basehttp.get_internal_wsgi_application",
        return_value="WSGI_APP",
    )
    def test_returns_plain_app_when_debug_false_and_not_insecure(self, _mock_get_app):
        backend = DjangoRunserver(ARGS={"insecure": False})
        assert backend.get_handler() == "WSGI_APP"

    @override_settings(DEBUG=True, STATIC_URL="/static/")
    @patch(
        "django.core.servers.basehttp.get_internal_wsgi_application",
        return_value="WSGI_APP",
    )
    def test_wraps_when_debug_true(self, _mock_get_app):
        from django.contrib.staticfiles.handlers import StaticFilesHandler

        backend = DjangoRunserver()
        handler = backend.get_handler()
        assert isinstance(handler, StaticFilesHandler)

    @override_settings(DEBUG=False, STATIC_URL="/static/")
    @patch(
        "django.core.servers.basehttp.get_internal_wsgi_application",
        return_value="WSGI_APP",
    )
    def test_wraps_when_debug_false_but_insecure_true(self, _mock_get_app):
        from django.contrib.staticfiles.handlers import StaticFilesHandler

        backend = DjangoRunserver(ARGS={"insecure": True})
        handler = backend.get_handler()
        assert isinstance(handler, StaticFilesHandler)


class TestInnerRun:
    """Tests for DjangoRunserver._inner_run mirroring runserver's inner_run."""

    @patch("django.core.servers.basehttp.run")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_inner_run_calls_check_pipeline(
        self,
        mock_raise_last,
        mock_check,
        mock_check_migrations,
        mock_run,
    ):
        backend = DjangoRunserver(ARGS={"noreload": True, "nostatic": True})
        backend._inner_run()

        mock_raise_last.assert_called_once_with()
        mock_check.assert_called_once_with(display_num_errors=True)
        mock_check_migrations.assert_called_once_with()
        mock_run.assert_called_once()

    @patch("django.core.servers.basehttp.run")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_inner_run_passes_correct_args_to_run(
        self,
        _mock_raise,
        _mock_check,
        _mock_check_migrations,
        mock_run,
    ):
        # Django's basehttp.run() adds ThreadingMixIn internally when
        # threading=True; passing ThreadedWSGIServer as server_cls would
        # double-wrap and raise "inconsistent MRO". Always pass plain
        # WSGIServer and let `threading=...` control the mixin.
        from django.core.servers.basehttp import WSGIServer

        backend = DjangoRunserver(
            ARGS={
                "addrport": "0.0.0.0:9000",
                "nostatic": True,
                "noreload": True,
            }
        )
        with patch.object(backend, "get_handler", return_value="HANDLER"):
            backend._inner_run()

        args, kwargs = mock_run.call_args
        assert args == ("0.0.0.0", 9000, "HANDLER")
        assert kwargs["ipv6"] is False
        assert kwargs["threading"] is True
        assert kwargs["server_cls"] is WSGIServer

    @patch("django.core.servers.basehttp.run")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_inner_run_uses_wsgiserver_when_nothreading(
        self,
        _mock_raise,
        _mock_check,
        _mock_check_migrations,
        mock_run,
    ):
        from django.core.servers.basehttp import WSGIServer

        backend = DjangoRunserver(
            ARGS={"nothreading": True, "nostatic": True, "noreload": True}
        )
        with patch.object(backend, "get_handler", return_value="HANDLER"):
            backend._inner_run()

        kwargs = mock_run.call_args.kwargs
        assert kwargs["threading"] is False
        assert kwargs["server_cls"] is WSGIServer

    @patch("django.core.servers.basehttp.run")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_inner_run_uses_ipv6(
        self,
        _mock_raise,
        _mock_check,
        _mock_check_migrations,
        mock_run,
    ):
        backend = DjangoRunserver(
            ARGS={"ipv6": True, "nostatic": True, "noreload": True}
        )
        with patch.object(backend, "get_handler", return_value="HANDLER"):
            backend._inner_run()

        kwargs = mock_run.call_args.kwargs
        assert kwargs["ipv6"] is True

    @patch("django.core.servers.basehttp.run")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_inner_run_addr_in_use_exits_1(
        self,
        _mock_raise,
        _mock_check,
        _mock_check_migrations,
        mock_run,
    ):
        mock_run.side_effect = OSError(errno.EADDRINUSE, "addr in use")

        backend = DjangoRunserver(ARGS={"nostatic": True, "noreload": True})
        with patch.object(backend, "get_handler", return_value="HANDLER"):
            with pytest.raises(SystemExit) as excinfo:
                backend._inner_run()
        assert excinfo.value.code == 1

    @patch("django.core.servers.basehttp.run")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_inner_run_keyboard_interrupt_exits_0(
        self,
        _mock_raise,
        _mock_check,
        _mock_check_migrations,
        mock_run,
    ):
        mock_run.side_effect = KeyboardInterrupt()

        backend = DjangoRunserver(ARGS={"nostatic": True, "noreload": True})
        with patch.object(backend, "get_handler", return_value="HANDLER"):
            with pytest.raises(SystemExit) as excinfo:
                backend._inner_run()
        assert excinfo.value.code == 0

    @patch("django.core.servers.basehttp.run")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_inner_run_unknown_oserror_uses_str(
        self,
        _mock_raise,
        _mock_check,
        _mock_check_migrations,
        mock_run,
    ):
        # An errno not in the friendly map should fall back to str(e).
        mock_run.side_effect = OSError(errno.ENOSPC, "no space")

        backend = DjangoRunserver(ARGS={"nostatic": True, "noreload": True})
        with patch.object(backend, "get_handler", return_value="HANDLER"):
            with pytest.raises(SystemExit) as excinfo:
                backend._inner_run()
        assert excinfo.value.code == 1


class TestStartServer:
    """Tests for DjangoRunserver.start_server reload/no-reload dispatch."""

    @patch("django.utils.autoreload.run_with_reloader")
    def test_start_server_with_reloader(self, mock_run_with_reloader):
        backend = DjangoRunserver(ARGS={"addrport": "127.0.0.1:8000"})
        backend.start_server()
        mock_run_with_reloader.assert_called_once_with(backend._inner_run)

    def test_start_server_without_reloader_calls_inner_run(self):
        backend = DjangoRunserver(ARGS={"noreload": True})
        with patch.object(backend, "_inner_run") as mock_inner:
            backend.start_server()
        mock_inner.assert_called_once_with()


class TestDisplayAddr:
    """Tests for the small _display_addr helper."""

    def test_display_addr_ipv4(self):
        backend = DjangoRunserver(ARGS={"addrport": "127.0.0.1:8000"})
        assert backend._display_addr() == "127.0.0.1"

    def test_display_addr_ipv6(self):
        backend = DjangoRunserver(ARGS={"ipv6": True, "addrport": "[::1]:8000"})
        assert backend._display_addr() == "[::1]"


class TestInitFlagCombinations:
    """Sanity checks that combinations of ARGS flags don't interact unexpectedly."""

    def test_all_flags_set(self):
        backend = DjangoRunserver(
            ARGS={
                "addrport": "[::1]:9999",
                "ipv6": True,
                "noreload": True,
                "nothreading": True,
                "nostatic": True,
                "insecure": True,
            }
        )
        assert backend.addr == "::1"
        assert backend.port == 9999
        assert backend.use_ipv6 is True
        assert backend.use_reloader is False
        assert backend.use_threading is False
        assert backend.use_static is False
        assert backend.insecure is True

    def test_all_flags_explicitly_false(self):
        backend = DjangoRunserver(
            ARGS={
                "ipv6": False,
                "noreload": False,
                "nothreading": False,
                "nostatic": False,
                "insecure": False,
            }
        )
        assert backend.use_ipv6 is False
        assert backend.use_reloader is True
        assert backend.use_threading is True
        assert backend.use_static is True
        assert backend.insecure is False


def test_backend_resolves_via_import_string():
    """The dispatcher uses import_string; ensure the dotted path resolves."""
    cls = import_string(
        "django_prodserver.backends.dev.django_runserver.DjangoRunserver"
    )
    assert cls is DjangoRunserver
    instance = cls(ARGS={"addrport": "127.0.0.1:8000"})
    assert isinstance(instance, BaseServerBackend)
