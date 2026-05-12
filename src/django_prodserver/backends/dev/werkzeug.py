"""Pure-Python WSGI dev server backend mirroring runserver_plus via Werkzeug."""

import importlib
import logging
import os
import sys
import webbrowser
from pathlib import Path
from typing import Any

from django.core.exceptions import ImproperlyConfigured

from .._runserver_base import BaseRunserverBackend


class WerkzeugRunserver(BaseRunserverBackend):
    """
    WSGI dev server backend driving werkzeug.serving.run_simple directly.

    Mirrors django-extensions' ``runserver_plus`` 1:1 over the standard
    ARGS dict. ARGS keys match runserver_plus CLI flags::

        {
            "BACKEND": "django_prodserver.backends.dev.werkzeug.WerkzeugRunserver",
            "ARGS": {
                # base (shared with DjangoRunserver / DaphneRunserver):
                "addrport": "127.0.0.1:8000",
                "ipv6": False,
                "noreload": False,
                "nostatic": False,
                "insecure": False,
                # run_simple kwargs:
                "threaded": True,
                "nothreading": False,
                "processes": 1,
                "extra_files": [],
                "exclude_patterns": [],
                "reloader_type": "auto",
                "reloader_interval": 1,
                "passthrough_errors": False,
                # debugger:
                "use_debugger": True,
                "nopin": False,
                "trusted_hosts": [],
                "evalex": True,
                # ssl:
                "cert_file": None,
                "key_file": None,
                "ssl_dev_cert_dir": None,
                # ergonomics:
                "browser": False,
                "output": None,
                "print_sql": False,
                "truncate_sql": 1000,
                "print_sql_location": False,
                "pdb": False,
                "ipdb": False,
                "pm": False,
                "keep_meta_shutdown": False,
                "startup_messages": "reload",
            },
        }

    Werkzeug owns reloading: ``start_server`` does NOT wrap with
    ``django.utils.autoreload.run_with_reloader``; instead ``run_simple``
    is given ``use_reloader=...`` and forks/spawns its own child.
    """

    server_kind = "Werkzeug development"

    def __init__(self, **server_args: Any) -> None:
        """Validate Werkzeug is installed and parse the full ARGS surface."""
        super().__init__(**server_args)

        try:
            import werkzeug  # noqa: F401
        except ImportError as e:
            raise ImproperlyConfigured(
                "Werkzeug is required to use WerkzeugRunserver backend. "
                "Install it with: pip install werkzeug"
            ) from e

        args = server_args.get("ARGS") or {}

        nothreading = bool(args.get("nothreading", False))
        self.threaded = False if nothreading else bool(args.get("threaded", True))
        self.processes = int(args.get("processes", 1))
        if self.processes > 1 and self.threaded:
            raise ImproperlyConfigured(
                "WerkzeugRunserver: `threaded` and `processes>1` "
                "are mutually exclusive."
            )

        self.extra_files = list(args.get("extra_files") or [])
        self.exclude_patterns = list(args.get("exclude_patterns") or [])
        self.reloader_type = str(args.get("reloader_type", "auto"))
        self.reloader_interval = int(args.get("reloader_interval", 1))
        self.passthrough_errors = bool(args.get("passthrough_errors", False))

        self.use_debugger = bool(args.get("use_debugger", True))
        self.nopin = bool(args.get("nopin", False))
        self.trusted_hosts = list(args.get("trusted_hosts") or [])
        self.evalex = bool(args.get("evalex", True))

        self.cert_file: str | None = args.get("cert_file")
        self.key_file: str | None = args.get("key_file")
        self.ssl_dev_cert_dir: str | None = args.get("ssl_dev_cert_dir")

        self.browser = bool(args.get("browser", False))
        self.output_path: str | None = args.get("output")
        self.print_sql = bool(args.get("print_sql", False))
        self.truncate_sql = int(args.get("truncate_sql", 1000))
        self.print_sql_location = bool(args.get("print_sql_location", False))
        self.pdb = bool(args.get("pdb", False))
        self.ipdb = bool(args.get("ipdb", False))
        self.pm = bool(args.get("pm", False))
        self.keep_meta_shutdown = bool(args.get("keep_meta_shutdown", False))
        self.startup_messages = str(args.get("startup_messages", "reload"))

        # protocol mirrors what run_simple will do with ssl_context
        self.protocol = "https" if (self.cert_file or self.key_file) else "http"

    def get_handler(self) -> Any:
        """Mirror runserver.get_handler + the staticfiles override."""
        from django.core.servers.basehttp import get_internal_wsgi_application

        handler = get_internal_wsgi_application()
        if not self._should_wrap_static():
            return handler
        from django.contrib.staticfiles.handlers import StaticFilesHandler

        return StaticFilesHandler(handler)

    def _build_ssl_context(self) -> Any:
        """Mirror runserver_plus's SSL decision tree."""
        if not (self.cert_file or self.key_file):
            return None
        try:
            import OpenSSL  # type: ignore[import-untyped]  # noqa: F401
        except ImportError as e:
            raise ImproperlyConfigured(
                "pyOpenSSL is required for SSL support. Install it with: "
                "pip install pyOpenSSL"
            ) from e

        cert = self.cert_file or self.key_file
        key = self.key_file or self.cert_file
        assert cert is not None and key is not None  # noqa: S101
        if Path(cert).exists() and Path(key).exists():
            return (str(cert), str(key))

        from werkzeug.serving import make_ssl_devcert

        base_dir = self.ssl_dev_cert_dir or str(Path(cert).parent or ".")
        base_name = Path(cert).stem or "devcert"
        cert, key = make_ssl_devcert(str(Path(base_dir) / base_name), host="localhost")
        return (cert, key)

    def _wrap_debugger(self, handler: Any) -> Any:
        """Wrap with DebuggedApplication and assign trusted_hosts."""
        from werkzeug.debug import DebuggedApplication

        wrapped = DebuggedApplication(handler, evalex=self.evalex)
        if self.trusted_hosts:
            wrapped.trusted_hosts = self.trusted_hosts
        return wrapped

    def _build_request_handler_cls(self) -> Any:
        """WSGIRequestHandler subclass that strips ``werkzeug.server.shutdown``."""
        from werkzeug.serving import WSGIRequestHandler as _WRH

        keep = self.keep_meta_shutdown

        class WSGIRequestHandler(_WRH):
            def make_environ(self) -> dict[str, Any]:
                env = super().make_environ()
                if not keep:
                    env.pop("werkzeug.server.shutdown", None)
                env.setdefault("REMOTE_USER", "")
                return env

        return WSGIRequestHandler

    def _apply_print_sql_patch(self) -> None:
        """Monkey-patch CursorDebugWrapper to log every SQL statement."""
        from django.db.backends import utils as db_utils

        try:
            import sqlparse
        except ImportError:
            sqlparse = None
        try:
            from pygments import highlight
            from pygments.formatters import TerminalFormatter
            from pygments.lexers import SqlLexer
        except ImportError:
            highlight = None

        logger = logging.getLogger("django.db.backends")
        truncate = self.truncate_sql
        with_location = self.print_sql_location
        real = db_utils.CursorDebugWrapper

        def _format(sql: str) -> str:
            text = sql
            if sqlparse is not None:
                text = sqlparse.format(text, reindent=True, keyword_case="upper")
            if highlight is not None:
                text = highlight(text, SqlLexer(), TerminalFormatter())
            if truncate and len(text) > truncate:
                text = text[:truncate] + "..."
            return text

        class PrintCursorDebugWrapper(real):  # type: ignore[misc, valid-type]
            def execute(self, sql, params=None):  # type: ignore[no-untyped-def]
                try:
                    return super().execute(sql, params)
                finally:
                    msg = _format(sql)
                    if with_location:
                        import traceback

                        frame = traceback.extract_stack()[-3]
                        msg = f"{frame.filename}:{frame.lineno}\n{msg}"
                    logger.info(msg)

            def executemany(self, sql, param_list):  # type: ignore[no-untyped-def]
                try:
                    return super().executemany(sql, param_list)
                finally:
                    logger.info(_format(sql))

        db_utils.CursorDebugWrapper = PrintCursorDebugWrapper

    def _install_technical_500_handler(self) -> None:
        """
        Replace Django's technical_500_response so exceptions reach Werkzeug.

        Without this, Django's WSGI handler catches every exception and
        renders its own yellow debug page; Werkzeug's DebuggedApplication
        never sees the exception and the runserver_plus-style interactive
        in-browser debugger never fires.

        Mirrors runserver_plus's unconditional patch:
        - ``pm``/``pdb``/``ipdb`` set → drop into the chosen debugger on
          every uncaught exception (post-mortem).
        - Otherwise → re-raise so DebuggedApplication can render the
          interactive debug page.
        """
        try:
            from django.views import debug as django_debug
        except ImportError:
            return

        if self.pm or self.pdb or self.ipdb:
            if self.ipdb:
                try:
                    _debugger = importlib.import_module("ipdb")
                except ImportError as e:
                    raise ImproperlyConfigured(
                        "ipdb is required when ARGS['ipdb']=True. "
                        "Install it with: pip install ipdb"
                    ) from e
            else:
                _debugger = importlib.import_module("pdb")

            def _handler(  # type: ignore[no-untyped-def]
                request, exc_type, exc_value, tb, status_code=500
            ):
                print(
                    f"Exception occurred: {exc_type.__name__}: {exc_value}",
                    file=sys.stderr,
                )
                _debugger.post_mortem(tb)
        else:

            def _handler(  # type: ignore[no-untyped-def]
                request, exc_type, exc_value, tb, status_code=500
            ):
                if exc_value is None:
                    exc_value = exc_type()
                if exc_value.__traceback__ is not tb:
                    raise exc_value.with_traceback(tb)
                raise exc_value

        django_debug.technical_500_response = _handler

    def _apply_output_redirect(self) -> None:
        """Redirect sys.stdout/sys.stderr to the configured file."""
        assert self.output_path is not None  # guarded by caller  # noqa: S101
        stream = open(self.output_path, "w", buffering=1)
        sys.stdout = stream
        sys.stderr = stream

    def _bind_url(self) -> str:
        return f"{self.protocol}://{self._display_addr()}:{self.port}/"

    def _should_print_banner(self) -> bool:
        """Honour ARGS['startup_messages']: never / always / once / reload."""
        in_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
        if self.startup_messages == "never":
            return False
        if self.startup_messages == "always":
            return True
        if self.startup_messages == "once":
            return not in_child
        return True

    def _add_i18n_extras(self) -> None:
        from django.conf import settings

        if not getattr(settings, "USE_I18N", False):
            return
        from django.utils.autoreload import get_reloader

        try:
            watched = get_reloader().watched_files()
        except Exception:
            return
        self.extra_files += [f for f in watched if str(f).endswith(".mo")]

    def _inner_run(self) -> None:
        """Mirror runserver_plus.inner_run, driving werkzeug.serving.run_simple."""
        from werkzeug.serving import run_simple

        if self.output_path:
            self._apply_output_redirect()
        if self.print_sql:
            self._apply_print_sql_patch()
        if self.use_debugger or self.pm or self.pdb or self.ipdb:
            self._install_technical_500_handler()

        if self._should_print_banner():
            self._run_checks_and_banner()
            if self.browser and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
                webbrowser.open(self._bind_url())

        ssl_context = self._build_ssl_context()
        handler = self.get_handler()

        if self.use_reloader:
            self._add_i18n_extras()

        # WERKZEUG_RUN_MAIN is set by werkzeug's reloader when it spawns the
        # child process (along with WERKZEUG_SERVER_FD). When unset we're
        # either the noreload path or the reloader's parent — wrap once.
        # When set we're the reloader child — werkzeug.run_simple(use_debugger=True)
        # will handle the wrap there, so we skip ours.
        if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            if self.nopin:
                os.environ["WERKZEUG_DEBUG_PIN"] = "off"
            if self.use_debugger:
                handler = self._wrap_debugger(handler)

        run_simple(
            self.addr,
            self.port,
            handler,
            use_reloader=self.use_reloader,
            use_debugger=self.use_debugger,
            use_evalex=self.evalex,
            threaded=self.threaded,
            processes=self.processes,
            extra_files=self.extra_files or None,
            exclude_patterns=self.exclude_patterns or None,
            reloader_interval=self.reloader_interval,
            reloader_type=self.reloader_type,
            request_handler=self._build_request_handler_cls(),
            ssl_context=ssl_context,
            passthrough_errors=self.passthrough_errors,
        )

    def start_server(self, *args: str) -> None:
        """Werkzeug owns reloading; do NOT wrap with django.utils.autoreload."""
        self._inner_run()


class RunserverPlus(WerkzeugRunserver):
    """Alias for users coming from django-extensions runserver_plus."""
