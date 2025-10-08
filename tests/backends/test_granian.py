"""Tests for Granian server backends."""

from unittest.mock import Mock, patch

import pytest

# Handle optional dependency
granian = pytest.importorskip("granian")

from django_prodserver.backends.granian import (  # NOQA: E402
    GranianASGIServer,
    GranianServerBase,
    GranianWSGIServer,
)


class TestGranianServerBase:
    """Tests for GranianServerBase class."""

    def test_inheritance_from_base_backend(self):
        """Test that GranianServerBase inherits from BaseServerBackend."""
        from django_prodserver.backends.base import BaseServerBackend

        server = GranianASGIServer()  # Use concrete implementation
        assert isinstance(server, BaseServerBackend)
        assert isinstance(server, GranianServerBase)

    def test_parse_granian_kwargs_shared_logic(self):
        """Test that parsing logic is shared between ASGI and WSGI servers."""
        asgi_server = GranianASGIServer(
            ARGS={"address": "0.0.0.0", "port": "8000", "workers": "4"}
        )
        wsgi_server = GranianWSGIServer(
            ARGS={"address": "0.0.0.0", "port": "8000", "workers": "4"}
        )

        asgi_kwargs = asgi_server._parse_granian_kwargs()
        wsgi_kwargs = wsgi_server._parse_granian_kwargs()

        # Both should parse identically
        assert asgi_kwargs == wsgi_kwargs
        assert asgi_kwargs["address"] == "0.0.0.0"
        assert asgi_kwargs["port"] == 8000
        assert asgi_kwargs["workers"] == 4

    def test_get_interface_not_implemented(self):
        """Test that _get_interface must be implemented by subclasses."""

        class IncompleteGranianServer(GranianServerBase):
            def _get_app_target(self):
                return "app:app"

        server = IncompleteGranianServer()
        with pytest.raises(NotImplementedError):
            server._get_interface()

    def test_get_app_target_not_implemented(self):
        """Test that _get_app_target must be implemented by subclasses."""

        class IncompleteGranianServer(GranianServerBase):
            def _get_interface(self):
                from granian.constants import Interfaces

                return Interfaces.ASGI

        server = IncompleteGranianServer()
        with pytest.raises(NotImplementedError):
            server._get_app_target()


class TestGranianASGIServer:
    """Tests for GranianASGIServer class."""

    def test_init_without_args(self):
        """Test GranianASGIServer initialization without args."""
        server = GranianASGIServer()
        assert server.server_config == {}

    def test_init_with_args(self):
        """Test GranianASGIServer initialization with args."""
        server = GranianASGIServer(
            ARGS={"address": "0.0.0.0", "port": "8000", "workers": "4"}
        )
        assert server.server_config == {
            "address": "0.0.0.0",
            "port": "8000",
            "workers": "4",
        }

    def test_parse_granian_kwargs(self):
        """Test parsing of configuration to Granian kwargs."""
        server = GranianASGIServer(
            ARGS={"address": "0.0.0.0", "port": "8000", "workers": "4"}
        )
        kwargs = server._parse_granian_kwargs()
        assert kwargs["address"] == "0.0.0.0"
        assert kwargs["port"] == 8000  # Should be converted to int
        assert kwargs["workers"] == 4  # Should be converted to int

    def test_parse_granian_kwargs_empty(self):
        """Test parsing with no args."""
        server = GranianASGIServer()
        kwargs = server._parse_granian_kwargs()
        assert kwargs == {}

    def test_parse_granian_kwargs_with_aliases(self):
        """Test parsing with argument aliases."""
        server = GranianASGIServer(
            ARGS={
                "host": "127.0.0.1",
                "threads": "2",
            }  # host -> address, threads -> blocking_threads
        )
        kwargs = server._parse_granian_kwargs()
        assert kwargs["address"] == "127.0.0.1"
        assert kwargs["blocking_threads"] == 2

    def test_parse_granian_kwargs_boolean_conversion(self):
        """Test boolean argument conversion."""
        server = GranianASGIServer(ARGS={"reload": "true", "websockets": "false"})
        kwargs = server._parse_granian_kwargs()
        assert kwargs["reload"] is True
        assert kwargs["websockets"] is False

    @patch("django_prodserver.backends.granian.asgi_app_name")
    def test_start_server(self, mock_asgi_app_name):
        """Test start_server method."""
        mock_asgi_app_name.return_value = "tests.asgi:application"

        with patch("granian.Granian") as MockGranian:
            mock_server = Mock()
            MockGranian.return_value = mock_server

            server = GranianASGIServer(
                ARGS={"address": "0.0.0.0", "port": "8000", "workers": "4"}
            )
            server.start_server()

            # Verify Granian was instantiated with correct arguments
            MockGranian.assert_called_once()
            call_kwargs = MockGranian.call_args.kwargs
            assert call_kwargs["target"] == "tests.asgi:application"
            assert call_kwargs["address"] == "0.0.0.0"
            assert call_kwargs["port"] == 8000
            assert call_kwargs["workers"] == 4

            # Verify serve was called
            mock_server.serve.assert_called_once()

    @patch("django_prodserver.backends.granian.asgi_app_name")
    def test_start_server_no_args(self, mock_asgi_app_name):
        """Test start_server method with no args."""
        mock_asgi_app_name.return_value = "tests.asgi:application"

        with patch("granian.Granian") as MockGranian:
            mock_server = Mock()
            MockGranian.return_value = mock_server

            server = GranianASGIServer()
            server.start_server()

            # Verify Granian was instantiated
            MockGranian.assert_called_once()
            call_kwargs = MockGranian.call_args.kwargs
            assert call_kwargs["target"] == "tests.asgi:application"

            # Verify serve was called
            mock_server.serve.assert_called_once()

    def test_inheritance_from_base_backend(self):
        """Test that GranianASGIServer properly inherits from BaseServerBackend."""
        from django_prodserver.backends.base import BaseServerBackend

        server = GranianASGIServer()
        assert isinstance(server, BaseServerBackend)

    def test_server_config_with_various_args(self):
        """Test server configuration with various argument types."""
        server = GranianASGIServer(
            ARGS={
                "address": "127.0.0.1",
                "port": "8000",
                "workers": "2",
                "blocking_threads": "4",
                "log-level": "debug",
            }
        )
        kwargs = server._parse_granian_kwargs()
        assert kwargs["address"] == "127.0.0.1"
        assert kwargs["port"] == 8000
        assert kwargs["workers"] == 2
        assert kwargs["blocking_threads"] == 4
        assert kwargs["log_level"] == "debug"

    @patch("django_prodserver.backends.granian.asgi_app_name")
    def test_start_server_with_interface(self, mock_asgi_app_name):
        """Test that ASGI interface is correctly set."""
        mock_asgi_app_name.return_value = "tests.asgi:application"

        with patch("granian.Granian") as MockGranian:
            from granian.constants import Interfaces

            mock_server = Mock()
            MockGranian.return_value = mock_server

            server = GranianASGIServer()
            server.start_server()

            # Verify interface was set to ASGI
            call_kwargs = MockGranian.call_args.kwargs
            assert call_kwargs["interface"] == Interfaces.ASGI

    def test_import_error_handling(self):
        """Test that ImportError is raised with helpful message."""
        server = GranianASGIServer()

        # Patch the import to simulate granian not being installed
        import sys

        with patch.dict(sys.modules, {"granian": None}):
            with pytest.raises(ImportError, match="Granian is not installed"):
                server.start_server()


class TestGranianWSGIServer:
    """Tests for GranianWSGIServer class."""

    def test_init_without_args(self):
        """Test GranianWSGIServer initialization without args."""
        server = GranianWSGIServer()
        assert server.server_config == {}

    def test_init_with_args(self):
        """Test GranianWSGIServer initialization with args."""
        server = GranianWSGIServer(
            ARGS={"address": "0.0.0.0", "port": "8000", "workers": "4"}
        )
        assert server.server_config == {
            "address": "0.0.0.0",
            "port": "8000",
            "workers": "4",
        }

    def test_parse_granian_kwargs(self):
        """Test parsing of configuration to Granian kwargs."""
        server = GranianWSGIServer(
            ARGS={"address": "0.0.0.0", "port": "8000", "workers": "4"}
        )
        kwargs = server._parse_granian_kwargs()
        assert kwargs["address"] == "0.0.0.0"
        assert kwargs["port"] == 8000
        assert kwargs["workers"] == 4

    def test_parse_granian_kwargs_empty(self):
        """Test parsing with no args."""
        server = GranianWSGIServer()
        kwargs = server._parse_granian_kwargs()
        assert kwargs == {}

    @patch("django_prodserver.backends.granian.wsgi_app_name")
    def test_start_server(self, mock_wsgi_app_name):
        """Test start_server method."""
        mock_wsgi_app_name.return_value = "tests.wsgi:application"

        with patch("granian.Granian") as MockGranian:
            mock_server = Mock()
            MockGranian.return_value = mock_server

            server = GranianWSGIServer(
                ARGS={"address": "0.0.0.0", "port": "8000", "workers": "4"}
            )
            server.start_server()

            # Verify Granian was instantiated with correct arguments
            MockGranian.assert_called_once()
            call_kwargs = MockGranian.call_args.kwargs
            assert call_kwargs["target"] == "tests.wsgi:application"
            assert call_kwargs["address"] == "0.0.0.0"
            assert call_kwargs["port"] == 8000
            assert call_kwargs["workers"] == 4

            # Verify serve was called
            mock_server.serve.assert_called_once()

    @patch("django_prodserver.backends.granian.wsgi_app_name")
    def test_start_server_no_args(self, mock_wsgi_app_name):
        """Test start_server method with no args."""
        mock_wsgi_app_name.return_value = "tests.wsgi:application"

        with patch("granian.Granian") as MockGranian:
            mock_server = Mock()
            MockGranian.return_value = mock_server

            server = GranianWSGIServer()
            server.start_server()

            # Verify Granian was instantiated
            MockGranian.assert_called_once()
            call_kwargs = MockGranian.call_args.kwargs
            assert call_kwargs["target"] == "tests.wsgi:application"

            # Verify serve was called
            mock_server.serve.assert_called_once()

    def test_inheritance_from_base_backend(self):
        """Test that GranianWSGIServer properly inherits from BaseServerBackend."""
        from django_prodserver.backends.base import BaseServerBackend

        server = GranianWSGIServer()
        assert isinstance(server, BaseServerBackend)

    def test_server_config_with_various_args(self):
        """Test server configuration with various argument types."""
        server = GranianWSGIServer(
            ARGS={
                "address": "127.0.0.1",
                "port": "8000",
                "workers": "2",
                "blocking_threads": "4",
                "backlog": "2048",
            }
        )
        kwargs = server._parse_granian_kwargs()
        assert kwargs["address"] == "127.0.0.1"
        assert kwargs["port"] == 8000
        assert kwargs["workers"] == 2
        assert kwargs["blocking_threads"] == 4
        assert kwargs["backlog"] == 2048

    @patch("django_prodserver.backends.granian.wsgi_app_name")
    def test_start_server_with_interface(self, mock_wsgi_app_name):
        """Test that WSGI interface is correctly set."""
        mock_wsgi_app_name.return_value = "tests.wsgi:application"

        with patch("granian.Granian") as MockGranian:
            from granian.constants import Interfaces

            mock_server = Mock()
            MockGranian.return_value = mock_server

            server = GranianWSGIServer()
            server.start_server()

            # Verify interface was set to WSGI
            call_kwargs = MockGranian.call_args.kwargs
            assert call_kwargs["interface"] == Interfaces.WSGI

    def test_interface_asgi_vs_wsgi(self):
        """Test that servers use different interfaces."""
        from granian.constants import Interfaces

        with patch("granian.Granian") as MockGranian:
            with patch(
                "django_prodserver.backends.granian.asgi_app_name", return_value="app"
            ):
                with patch(
                    "django_prodserver.backends.granian.wsgi_app_name",
                    return_value="app",
                ):
                    mock_server = Mock()
                    MockGranian.return_value = mock_server

                    asgi_server = GranianASGIServer()
                    asgi_server.start_server()
                    asgi_interface = MockGranian.call_args.kwargs["interface"]

                    MockGranian.reset_mock()

                    wsgi_server = GranianWSGIServer()
                    wsgi_server.start_server()
                    wsgi_interface = MockGranian.call_args.kwargs["interface"]

                    assert asgi_interface == Interfaces.ASGI
                    assert wsgi_interface == Interfaces.WSGI
                    assert asgi_interface != wsgi_interface


class TestGranianEdgeCases:
    """Tests for edge cases in Granian backends."""

    def test_empty_config(self):
        """Test that empty config results in empty kwargs."""
        server = GranianASGIServer(ARGS={})
        kwargs = server._parse_granian_kwargs()
        assert kwargs == {}

    def test_boolean_conversion_variants(self):
        """Test various boolean string conversions."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ]

        for value, expected in test_cases:
            server = GranianASGIServer(ARGS={"reload": value})
            kwargs = server._parse_granian_kwargs()
            assert kwargs["reload"] is expected, f"Failed for value: {value}"

    def test_numeric_conversion(self):
        """Test numeric string to int conversion."""
        server = GranianASGIServer(
            ARGS={
                "port": "8000",
                "workers": "4",
                "backlog": "1024",
            }
        )
        kwargs = server._parse_granian_kwargs()
        assert kwargs["port"] == 8000
        assert kwargs["workers"] == 4
        assert kwargs["backlog"] == 1024
        assert isinstance(kwargs["port"], int)
        assert isinstance(kwargs["workers"], int)
        assert isinstance(kwargs["backlog"], int)

    def test_hyphenated_vs_underscore_args(self):
        """Test both hyphenated and underscore argument names."""
        # Test hyphenated
        server1 = GranianASGIServer(
            ARGS={"log-level": "debug", "url-path-prefix": "/api"}
        )
        kwargs1 = server1._parse_granian_kwargs()
        assert kwargs1["log_level"] == "debug"
        assert kwargs1["url_path_prefix"] == "/api"

        # Test underscore
        server2 = GranianASGIServer(
            ARGS={"log_level": "info", "url_path_prefix": "/v1"}
        )
        kwargs2 = server2._parse_granian_kwargs()
        assert kwargs2["log_level"] == "info"
        assert kwargs2["url_path_prefix"] == "/v1"

    def test_unknown_args_ignored(self):
        """Test that unknown arguments are safely ignored."""
        server = GranianASGIServer(
            ARGS={
                "port": "8000",
                "unknown_arg": "value",
                "another_unknown": "123",
            }
        )
        kwargs = server._parse_granian_kwargs()
        assert "port" in kwargs
        assert "unknown_arg" not in kwargs
        assert "another_unknown" not in kwargs

    def test_ssl_arguments(self):
        """Test SSL-related arguments."""
        server = GranianASGIServer(
            ARGS={
                "ssl-cert": "/path/to/cert.pem",
                "ssl-key": "/path/to/key.pem",
            }
        )
        kwargs = server._parse_granian_kwargs()
        assert kwargs["ssl_cert"] == "/path/to/cert.pem"
        assert kwargs["ssl_key"] == "/path/to/key.pem"
