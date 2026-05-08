"""Tests for the WerkzeugRunserver / RunserverPlus dev backend."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Handle optional dependency
werkzeug = pytest.importorskip("werkzeug")

from django.core.exceptions import ImproperlyConfigured  # NOQA: E402
from django.test import override_settings  # NOQA: E402
from django.utils.module_loading import import_string  # NOQA: E402

from django_prodserver.backends._runserver_base import (  # NOQA: E402
    BaseRunserverBackend,
)
from django_prodserver.backends.base import BaseServerBackend  # NOQA: E402
from django_prodserver.backends.werkzeug import (  # NOQA: E402
    RunserverPlus,
    WerkzeugRunserver,
)


@pytest.fixture(autouse=True)
def _clear_werkzeug_env():
    """Make sure WERKZEUG_RUN_MAIN/WERKZEUG_DEBUG_PIN don't leak between tests."""
    original = {
        k: os.environ.get(k) for k in ("WERKZEUG_RUN_MAIN", "WERKZEUG_DEBUG_PIN")
    }
    os.environ.pop("WERKZEUG_RUN_MAIN", None)
    os.environ.pop("WERKZEUG_DEBUG_PIN", None)
    yield
    for k, v in original.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


class TestDependencyGuard:
    def test_raises_when_werkzeug_missing(self):
        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "werkzeug":
                raise ImportError("simulated missing werkzeug")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            with pytest.raises(ImproperlyConfigured, match="Werkzeug is required"):
                WerkzeugRunserver()


class TestInitDefaults:
    def test_inheritance_chain(self):
        backend = WerkzeugRunserver()
        assert isinstance(backend, BaseRunserverBackend)
        assert isinstance(backend, BaseServerBackend)

    def test_defaults(self):
        backend = WerkzeugRunserver()
        assert backend.use_ipv6 is False
        assert backend.use_reloader is True
        assert backend.use_static is True
        assert backend.insecure is False
        assert backend.addr == "127.0.0.1"
        assert backend.port == 8000
        assert backend.protocol == "http"

        assert backend.threaded is True
        assert backend.processes == 1
        assert backend.extra_files == []
        assert backend.exclude_patterns == []
        assert backend.reloader_type == "auto"
        assert backend.reloader_interval == 1
        assert backend.passthrough_errors is False

        assert backend.use_debugger is True
        assert backend.nopin is False
        assert backend.trusted_hosts == []
        assert backend.evalex is True

        assert backend.cert_file is None
        assert backend.key_file is None
        assert backend.ssl_dev_cert_dir is None

        assert backend.browser is False
        assert backend.output_path is None
        assert backend.print_sql is False
        assert backend.truncate_sql == 1000
        assert backend.print_sql_location is False
        assert backend.pdb is False
        assert backend.ipdb is False
        assert backend.pm is False
        assert backend.keep_meta_shutdown is False
        assert backend.startup_messages == "reload"

    def test_nothreading_overrides_threaded(self):
        backend = WerkzeugRunserver(ARGS={"threaded": True, "nothreading": True})
        assert backend.threaded is False

    def test_processes_threaded_mutually_exclusive(self):
        with pytest.raises(ImproperlyConfigured, match="mutually exclusive"):
            WerkzeugRunserver(ARGS={"threaded": True, "processes": 4})

    def test_processes_without_threading_ok(self):
        backend = WerkzeugRunserver(ARGS={"nothreading": True, "processes": 4})
        assert backend.threaded is False
        assert backend.processes == 4

    def test_protocol_https_when_cert_set(self):
        backend = WerkzeugRunserver(ARGS={"cert_file": "/x/cert.pem"})
        assert backend.protocol == "https"

    def test_protocol_https_when_only_key_set(self):
        backend = WerkzeugRunserver(ARGS={"key_file": "/x/key.pem"})
        assert backend.protocol == "https"

    def test_full_kwarg_overrides(self, tmp_path):
        out = str(tmp_path / "out.log")
        backend = WerkzeugRunserver(
            ARGS={
                "addrport": "0.0.0.0:9000",
                "ipv6": False,
                "noreload": True,
                "nostatic": True,
                "insecure": True,
                "threaded": False,
                "processes": 2,
                "extra_files": ["a.py", "b.py"],
                "exclude_patterns": ["*.pyc"],
                "reloader_type": "watchdog",
                "reloader_interval": 3,
                "passthrough_errors": True,
                "use_debugger": False,
                "nopin": True,
                "trusted_hosts": ["10.0.0.1"],
                "evalex": False,
                "cert_file": "/c.pem",
                "key_file": "/k.pem",
                "ssl_dev_cert_dir": "/etc/ssl",
                "browser": True,
                "output": out,
                "print_sql": True,
                "truncate_sql": 500,
                "print_sql_location": True,
                "pdb": True,
                "ipdb": False,
                "pm": True,
                "keep_meta_shutdown": True,
                "startup_messages": "once",
            }
        )
        assert backend.addr == "0.0.0.0"
        assert backend.port == 9000
        assert backend.use_reloader is False
        assert backend.processes == 2
        assert backend.threaded is False
        assert backend.extra_files == ["a.py", "b.py"]
        assert backend.exclude_patterns == ["*.pyc"]
        assert backend.reloader_type == "watchdog"
        assert backend.reloader_interval == 3
        assert backend.passthrough_errors is True
        assert backend.use_debugger is False
        assert backend.nopin is True
        assert backend.trusted_hosts == ["10.0.0.1"]
        assert backend.evalex is False
        assert backend.cert_file == "/c.pem"
        assert backend.key_file == "/k.pem"
        assert backend.ssl_dev_cert_dir == "/etc/ssl"
        assert backend.browser is True
        assert backend.output_path == out
        assert backend.print_sql is True
        assert backend.truncate_sql == 500
        assert backend.print_sql_location is True
        assert backend.pdb is True
        assert backend.pm is True
        assert backend.keep_meta_shutdown is True
        assert backend.startup_messages == "once"

    def test_unknown_args_keys_ignored(self):
        backend = WerkzeugRunserver(ARGS={"addrport": "127.0.0.1:8000", "junk": 1})
        assert backend.addr == "127.0.0.1"


class TestGetHandler:
    @patch(
        "django.core.servers.basehttp.get_internal_wsgi_application",
        return_value="WSGI_APP",
    )
    def test_returns_plain_app_when_nostatic(self, _g):
        backend = WerkzeugRunserver(ARGS={"nostatic": True})
        assert backend.get_handler() == "WSGI_APP"

    @override_settings(INSTALLED_APPS=["django.contrib.auth"], DEBUG=True)
    @patch(
        "django.core.servers.basehttp.get_internal_wsgi_application",
        return_value="WSGI_APP",
    )
    def test_returns_plain_app_when_staticfiles_not_installed(self, _g):
        backend = WerkzeugRunserver()
        assert backend.get_handler() == "WSGI_APP"

    @override_settings(DEBUG=False)
    @patch(
        "django.core.servers.basehttp.get_internal_wsgi_application",
        return_value="WSGI_APP",
    )
    def test_returns_plain_app_when_debug_false_and_not_insecure(self, _g):
        backend = WerkzeugRunserver(ARGS={"insecure": False})
        assert backend.get_handler() == "WSGI_APP"

    @override_settings(DEBUG=True, STATIC_URL="/static/")
    @patch(
        "django.core.servers.basehttp.get_internal_wsgi_application",
        return_value="WSGI_APP",
    )
    def test_wraps_when_debug_true(self, _g):
        from django.contrib.staticfiles.handlers import StaticFilesHandler

        backend = WerkzeugRunserver()
        assert isinstance(backend.get_handler(), StaticFilesHandler)


class TestBuildSslContext:
    def test_returns_none_when_no_cert_or_key(self):
        backend = WerkzeugRunserver()
        assert backend._build_ssl_context() is None

    def test_raises_when_pyopenssl_missing(self):
        backend = WerkzeugRunserver(ARGS={"cert_file": "/x.pem"})
        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "OpenSSL":
                raise ImportError("simulated missing pyOpenSSL")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            with pytest.raises(ImproperlyConfigured, match="pyOpenSSL is required"):
                backend._build_ssl_context()

    def test_returns_tuple_when_files_exist(self, tmp_path):
        cert = tmp_path / "c.pem"
        key = tmp_path / "k.pem"
        cert.write_text("x")
        key.write_text("y")
        backend = WerkzeugRunserver(
            ARGS={"cert_file": str(cert), "key_file": str(key)}
        )
        with patch.dict(sys.modules, {"OpenSSL": MagicMock()}):
            assert backend._build_ssl_context() == (str(cert), str(key))

    def test_calls_make_ssl_devcert_when_files_missing(self, tmp_path):
        backend = WerkzeugRunserver(
            ARGS={
                "cert_file": str(tmp_path / "missing.pem"),
                "key_file": str(tmp_path / "missing.key"),
                "ssl_dev_cert_dir": str(tmp_path),
            }
        )
        with patch.dict(sys.modules, {"OpenSSL": MagicMock()}):
            with patch(
                "werkzeug.serving.make_ssl_devcert",
                return_value=("/gen/cert.pem", "/gen/key.pem"),
            ) as mock_dev:
                ctx = backend._build_ssl_context()
        assert ctx == ("/gen/cert.pem", "/gen/key.pem")
        assert mock_dev.called


class TestWrapDebugger:
    def test_wraps_with_debugged_application(self):
        backend = WerkzeugRunserver()
        wrapped = backend._wrap_debugger("APP")
        from werkzeug.debug import DebuggedApplication

        assert isinstance(wrapped, DebuggedApplication)
        assert wrapped.evalex is True

    def test_assigns_trusted_hosts_when_set(self):
        backend = WerkzeugRunserver(ARGS={"trusted_hosts": ["10.0.0.1", "10.0.0.2"]})
        wrapped = backend._wrap_debugger("APP")
        assert wrapped.trusted_hosts == ["10.0.0.1", "10.0.0.2"]


class TestRequestHandlerCls:
    def _make_environ_via(self, backend):
        cls = backend._build_request_handler_cls()

        def fake_super_make_environ(self):
            return {"werkzeug.server.shutdown": object(), "OTHER": "x"}

        with patch.object(cls.__bases__[0], "make_environ", fake_super_make_environ):
            instance = cls.__new__(cls)
            return cls.make_environ(instance)

    def test_default_strips_shutdown_key(self):
        env = self._make_environ_via(WerkzeugRunserver())
        assert "werkzeug.server.shutdown" not in env
        assert env["OTHER"] == "x"
        assert env["REMOTE_USER"] == ""

    def test_keep_meta_shutdown_keeps_key(self):
        env = self._make_environ_via(
            WerkzeugRunserver(ARGS={"keep_meta_shutdown": True})
        )
        assert "werkzeug.server.shutdown" in env


class TestShouldPrintBanner:
    @pytest.mark.parametrize(
        ("setting", "in_child", "expected"),
        [
            ("never", False, False),
            ("never", True, False),
            ("always", False, True),
            ("always", True, True),
            ("once", False, True),
            ("once", True, False),
            ("reload", False, True),
            ("reload", True, True),
        ],
    )
    def test_matrix(self, setting, in_child, expected):
        backend = WerkzeugRunserver(ARGS={"startup_messages": setting})
        if in_child:
            os.environ["WERKZEUG_RUN_MAIN"] = "true"
        assert backend._should_print_banner() is expected


class TestInnerRun:
    @patch("werkzeug.serving.run_simple")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_run_simple_called_with_defaults(self, _r, _c, _cm, mock_run):
        # WERKZEUG_RUN_MAIN is unset (we're either the noreload path or the
        # reloader parent), so the explicit DebuggedApplication wrap fires.
        from werkzeug.debug import DebuggedApplication

        backend = WerkzeugRunserver(ARGS={"noreload": True, "nostatic": True})
        with patch.object(backend, "get_handler", return_value="HANDLER"):
            backend._inner_run()

        args, kwargs = mock_run.call_args
        assert args[0] == "127.0.0.1"
        assert args[1] == 8000
        assert isinstance(args[2], DebuggedApplication)
        assert kwargs["use_reloader"] is False
        assert kwargs["use_debugger"] is True
        assert kwargs["use_evalex"] is True
        assert kwargs["threaded"] is True
        assert kwargs["processes"] == 1
        assert kwargs["reloader_type"] == "auto"
        assert kwargs["reloader_interval"] == 1
        assert kwargs["ssl_context"] is None
        assert kwargs["passthrough_errors"] is False

    @patch("werkzeug.serving.run_simple")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_handler_wrapped_in_parent_when_reloader_on(
        self, _r, _c, _cm, mock_run
    ):
        # With reloader on (default) and WERKZEUG_RUN_MAIN unset, we're in
        # the parent process: explicit DebuggedApplication wrap fires.
        backend = WerkzeugRunserver(ARGS={"nostatic": True})
        with patch.object(backend, "get_handler", return_value="HANDLER"):
            backend._inner_run()
        from werkzeug.debug import DebuggedApplication

        assert isinstance(mock_run.call_args.args[2], DebuggedApplication)

    @patch("werkzeug.serving.run_simple")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_noreload_does_not_set_werkzeug_run_main(self, _r, _c, _cm, mock_run):
        # We must NOT set WERKZEUG_RUN_MAIN ourselves — werkzeug 3.x reads it as
        # "I'm the reloader child, expect WERKZEUG_SERVER_FD" and crashes.
        # Werkzeug sets it itself when its reloader spawns the child.
        assert "WERKZEUG_RUN_MAIN" not in os.environ
        backend = WerkzeugRunserver(ARGS={"noreload": True, "nostatic": True})
        with patch.object(backend, "get_handler", return_value="H"):
            backend._inner_run()
        assert "WERKZEUG_RUN_MAIN" not in os.environ

    @patch("werkzeug.serving.run_simple")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_debugger_skipped_in_child_process(self, _r, _c, _cm, mock_run):
        os.environ["WERKZEUG_RUN_MAIN"] = "true"
        backend = WerkzeugRunserver(ARGS={"nostatic": True})
        with patch.object(backend, "get_handler", return_value="HANDLER"):
            backend._inner_run()
        # in the child, handler is NOT wrapped; passed through as-is.
        assert mock_run.call_args.args[2] == "HANDLER"

    @patch("werkzeug.serving.run_simple")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_use_debugger_false_does_not_wrap(self, _r, _c, _cm, mock_run):
        backend = WerkzeugRunserver(
            ARGS={"noreload": True, "nostatic": True, "use_debugger": False}
        )
        with patch.object(backend, "get_handler", return_value="HANDLER"):
            backend._inner_run()
        assert mock_run.call_args.args[2] == "HANDLER"
        assert mock_run.call_args.kwargs["use_debugger"] is False

    @patch("werkzeug.serving.run_simple")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_nopin_sets_env_before_wrap(self, _r, _c, _cm, mock_run):
        # Wrap-block only fires in the parent (env != "true"), so use the
        # default reloader path (don't pass noreload).
        assert "WERKZEUG_DEBUG_PIN" not in os.environ
        backend = WerkzeugRunserver(
            ARGS={"nostatic": True, "nopin": True}
        )
        with patch.object(backend, "get_handler", return_value="H"):
            backend._inner_run()
        assert os.environ.get("WERKZEUG_DEBUG_PIN") == "off"

    @patch("werkzeug.serving.run_simple")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_browser_opens_in_parent_only(self, _r, _c, _cm, _mr):
        backend = WerkzeugRunserver(
            ARGS={"noreload": True, "nostatic": True, "browser": True}
        )
        with patch("webbrowser.open") as mock_open, patch.object(
            backend, "get_handler", return_value="H"
        ):
            backend._inner_run()
        mock_open.assert_called_once_with("http://127.0.0.1:8000/")

    @patch("werkzeug.serving.run_simple")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_browser_skipped_in_child(self, _r, _c, _cm, _mr):
        os.environ["WERKZEUG_RUN_MAIN"] = "true"
        backend = WerkzeugRunserver(
            ARGS={"nostatic": True, "browser": True}
        )
        with patch("webbrowser.open") as mock_open, patch.object(
            backend, "get_handler", return_value="H"
        ):
            backend._inner_run()
        mock_open.assert_not_called()

    @patch("werkzeug.serving.run_simple")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_full_kwargs_forwarded(self, _r, _c, _cm, mock_run):
        backend = WerkzeugRunserver(
            ARGS={
                "addrport": "0.0.0.0:9000",
                "noreload": True,
                "nostatic": True,
                "use_debugger": False,
                "nothreading": True,
                "processes": 4,
                "extra_files": ["a.py"],
                "exclude_patterns": ["*.pyc"],
                "reloader_type": "watchdog",
                "reloader_interval": 5,
                "passthrough_errors": True,
                "evalex": False,
            }
        )
        with patch.object(backend, "get_handler", return_value="H"):
            backend._inner_run()
        kw = mock_run.call_args.kwargs
        assert kw["use_reloader"] is False
        assert kw["use_debugger"] is False
        assert kw["use_evalex"] is False
        assert kw["threaded"] is False
        assert kw["processes"] == 4
        assert kw["extra_files"] == ["a.py"]
        assert kw["exclude_patterns"] == ["*.pyc"]
        assert kw["reloader_type"] == "watchdog"
        assert kw["reloader_interval"] == 5
        assert kw["passthrough_errors"] is True

    @patch("werkzeug.serving.run_simple")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_request_handler_subclass_passed(self, _r, _c, _cm, mock_run):
        from werkzeug.serving import WSGIRequestHandler as _WRH

        backend = WerkzeugRunserver(ARGS={"noreload": True, "nostatic": True})
        with patch.object(backend, "get_handler", return_value="H"):
            backend._inner_run()
        cls = mock_run.call_args.kwargs["request_handler"]
        assert issubclass(cls, _WRH)

    @patch("werkzeug.serving.run_simple")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    @override_settings(USE_I18N=True)
    def test_i18n_mo_files_added_to_extra_files(self, _r, _c, _cm, _mr):
        backend = WerkzeugRunserver(ARGS={"nostatic": True})

        class FakeReloader:
            def watched_files(self):
                return ["/x/locale.mo", "/x/views.py", "/y/messages.mo"]

        with patch("django.utils.autoreload.get_reloader", return_value=FakeReloader()):
            with patch.object(backend, "get_handler", return_value="H"):
                backend._inner_run()
        assert "/x/locale.mo" in backend.extra_files
        assert "/y/messages.mo" in backend.extra_files
        assert "/x/views.py" not in backend.extra_files


class TestStartServer:
    def test_does_not_use_django_autoreload(self):
        backend = WerkzeugRunserver()
        with patch(
            "django.utils.autoreload.run_with_reloader"
        ) as mock_arl, patch.object(backend, "_inner_run") as mock_inner:
            backend.start_server()
        mock_arl.assert_not_called()
        mock_inner.assert_called_once_with()


class TestPrintSqlPatch:
    def test_replaces_cursor_debug_wrapper(self):
        from django.db.backends import utils as db_utils

        original = db_utils.CursorDebugWrapper
        backend = WerkzeugRunserver(ARGS={"print_sql": True})
        try:
            backend._apply_print_sql_patch()
            assert db_utils.CursorDebugWrapper is not original
            assert issubclass(db_utils.CursorDebugWrapper, original)
        finally:
            db_utils.CursorDebugWrapper = original


class TestTechnical500Handler:
    """Tests for the technical_500_response patch that lets exceptions through."""

    def test_default_handler_reraises_exception(self):
        from django.views import debug as django_debug

        original = django_debug.technical_500_response
        backend = WerkzeugRunserver()
        try:
            backend._install_technical_500_handler()
            handler = django_debug.technical_500_response
            assert handler is not original
            try:
                raise ValueError("boom")
            except ValueError as e:
                tb = e.__traceback__
                with pytest.raises(ValueError, match="boom"):
                    handler(None, type(e), e, tb)
        finally:
            django_debug.technical_500_response = original

    def test_pm_handler_drops_to_pdb(self):
        from django.views import debug as django_debug

        original = django_debug.technical_500_response
        backend = WerkzeugRunserver(ARGS={"pm": True})
        try:
            with patch("pdb.post_mortem") as mock_pm:
                backend._install_technical_500_handler()
                handler = django_debug.technical_500_response
                try:
                    raise RuntimeError("fail")
                except RuntimeError as e:
                    handler(None, type(e), e, e.__traceback__)
            mock_pm.assert_called_once()
        finally:
            django_debug.technical_500_response = original

    def test_ipdb_missing_raises(self):
        backend = WerkzeugRunserver(ARGS={"ipdb": True})
        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "ipdb":
                raise ImportError("simulated missing ipdb")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            with pytest.raises(ImproperlyConfigured, match="ipdb is required"):
                backend._install_technical_500_handler()

    @patch("werkzeug.serving.run_simple")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_inner_run_installs_handler_when_use_debugger(self, *_):
        from django.views import debug as django_debug

        original = django_debug.technical_500_response
        backend = WerkzeugRunserver(ARGS={"noreload": True, "nostatic": True})
        try:
            with patch.object(backend, "get_handler", return_value="H"):
                backend._inner_run()
            assert django_debug.technical_500_response is not original
        finally:
            django_debug.technical_500_response = original

    @patch("werkzeug.serving.run_simple")
    @patch("django.core.management.base.BaseCommand.check_migrations")
    @patch("django.core.management.base.BaseCommand.check")
    @patch("django.utils.autoreload.raise_last_exception")
    def test_inner_run_skips_handler_when_no_debug_features(self, *_):
        from django.views import debug as django_debug

        original = django_debug.technical_500_response
        backend = WerkzeugRunserver(
            ARGS={
                "noreload": True,
                "nostatic": True,
                "use_debugger": False,
                "pm": False,
                "pdb": False,
                "ipdb": False,
            }
        )
        try:
            with patch.object(backend, "get_handler", return_value="H"):
                backend._inner_run()
            assert django_debug.technical_500_response is original
        finally:
            django_debug.technical_500_response = original


class TestOutputRedirect:
    def test_redirects_stdout(self, tmp_path):
        path = tmp_path / "out.log"
        backend = WerkzeugRunserver(ARGS={"output": str(path)})
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        try:
            backend._apply_output_redirect()
            print("hello")
            sys.stdout.flush()
            redirected = sys.stdout
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            redirected.close()
        assert "hello" in path.read_text()


class TestRunserverPlusAlias:
    def test_alias_is_subclass(self):
        assert issubclass(RunserverPlus, WerkzeugRunserver)

    def test_alias_instantiates_identically(self):
        backend = RunserverPlus(ARGS={"addrport": "0.0.0.0:9000"})
        assert isinstance(backend, WerkzeugRunserver)
        assert backend.addr == "0.0.0.0"
        assert backend.port == 9000


def test_backend_resolves_via_import_string():
    cls = import_string("django_prodserver.backends.werkzeug.WerkzeugRunserver")
    assert cls is WerkzeugRunserver
    cls = import_string("django_prodserver.backends.werkzeug.RunserverPlus")
    assert cls is RunserverPlus
