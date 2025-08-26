from unittest.mock import patch

import pytest

# Handle optional dependency
waitress = pytest.importorskip("waitress")

from django_prodserver.backends.waitress import WaitressServer  # NOQA: E402


class TestWaitressServer:
    """Tests for WaitressServer class."""

    def test_init_without_args(self):
        """Test WaitressServer initialization without args."""
        server = WaitressServer()
        assert server.args == []

    def test_init_with_args(self):
        """Test WaitressServer initialization with args."""
        server = WaitressServer(ARGS={"host": "127.0.0.1", "port": "8000"})
        assert server.args == ["--host=127.0.0.1", "--port=8000"]

    @patch(
        "django_prodserver.backends.waitress.wsgi_app_name",
        return_value="tests.wsgi:application",
    )
    def test_prep_server_args(self, mock_wsgi_app_name):
        """Test prep_server_args method."""
        server = WaitressServer(ARGS={"host": "127.0.0.1", "port": "8000"})
        args = server.prep_server_args()

        assert args == [
            "waitress",
            "--host=127.0.0.1",
            "--port=8000",
            "tests.wsgi:application",
        ]
        mock_wsgi_app_name.assert_called_once()

    @patch(
        "django_prodserver.backends.waitress.wsgi_app_name",
        return_value="tests.wsgi:application",
    )
    def test_prep_server_args_no_args(self, mock_wsgi_app_name):
        """Test prep_server_args with no args."""
        server = WaitressServer()
        args = server.prep_server_args()

        assert args == ["waitress", "tests.wsgi:application"]
        mock_wsgi_app_name.assert_called_once()

    @patch("waitress.runner.run")
    def test_start_server(self, mock_waitress_run):
        """Test start_server method."""
        server = WaitressServer()
        args = ("--host=0.0.0.0", "--port=8000")

        server.start_server(*args)

        mock_waitress_run.assert_called_once_with(argv=args)

    @patch("waitress.runner.run")
    def test_start_server_no_args(self, mock_waitress_run):
        """Test start_server method with no args."""
        server = WaitressServer()

        server.start_server()

        mock_waitress_run.assert_called_once_with(argv=())

    def test_inheritance_from_base_backend(self):
        """Test that WaitressServer properly inherits from BaseServerBackend."""
        from django_prodserver.backends.base import BaseServerBackend

        server = WaitressServer()
        assert isinstance(server, BaseServerBackend)

    @patch(
        "django_prodserver.backends.waitress.wsgi_app_name",
        return_value="myapp.wsgi:application",
    )
    def test_prep_server_args_with_complex_args(self, mock_wsgi_app_name):
        """Test prep_server_args with complex arguments."""
        server = WaitressServer(
            ARGS={
                "host": "127.0.0.1",
                "port": "8080",
                "threads": "8",
                "connection-limit": "1000",
            }
        )
        args = server.prep_server_args()

        assert args[0] == "waitress"
        assert args[-1] == "myapp.wsgi:application"
        assert "--host=127.0.0.1" in args
        assert "--port=8080" in args
        assert "--threads=8" in args
        assert "--connection-limit=1000" in args
        assert len(args) == 6  # waitress + 4 args + wsgi_app_name

    @patch("waitress.runner.run")
    @patch(
        "django_prodserver.backends.waitress.wsgi_app_name",
        return_value="tests.wsgi:application",
    )
    def test_full_workflow(self, mock_wsgi_app_name, mock_waitress_run):
        """Test the complete workflow from initialization to server start."""
        server = WaitressServer(ARGS={"host": "127.0.0.1", "port": "8000"})
        prepared_args = server.prep_server_args()
        server.start_server(*prepared_args)

        mock_wsgi_app_name.assert_called_once()
        mock_waitress_run.assert_called_once_with(
            argv=(
                "waitress",
                "--host=127.0.0.1",
                "--port=8000",
                "tests.wsgi:application",
            )
        )

    def test_waitress_always_first_arg(self):
        """Test that 'waitress' is always the first argument."""
        server = WaitressServer(ARGS={"port": "8000"})
        args = server.prep_server_args()
        assert args[0] == "waitress"

    @patch(
        "django_prodserver.backends.waitress.wsgi_app_name",
        return_value="custom.wsgi:app",
    )
    def test_custom_wsgi_app_name(self, mock_wsgi_app_name):
        """Test with custom WSGI application name."""
        server = WaitressServer()
        args = server.prep_server_args()

        assert args[-1] == "custom.wsgi:app"
        mock_wsgi_app_name.assert_called_once()

    def test_wsgi_app_always_last_arg(self):
        """Test that WSGI app name is always the last argument."""
        with patch(
            "django_prodserver.backends.waitress.wsgi_app_name",
            return_value="tests.wsgi:application",
        ):
            server = WaitressServer(ARGS={"host": "127.0.0.1", "port": "9000"})
            args = server.prep_server_args()
            assert args[-1] == "tests.wsgi:application"

    @patch("waitress.runner.run")
    def test_start_server_with_various_arg_types(self, mock_waitress_run):
        """Test start_server with various argument types."""
        server = WaitressServer()
        args = ("--host=0.0.0.0", "--port=8000", "--threads=4")

        server.start_server(*args)

        mock_waitress_run.assert_called_once_with(argv=args)

    def test_server_args_formatting(self):
        """Test that server args are properly formatted from dict."""
        server = WaitressServer(
            ARGS={
                "host": "127.0.0.1",
                "port": "8000",
                "threads": "4",
                "url-scheme": "https",
            }
        )

        expected_args = [
            "--host=127.0.0.1",
            "--port=8000",
            "--threads=4",
            "--url-scheme=https",
        ]

        # Check all expected args are present in server.args
        for expected_arg in expected_args:
            assert expected_arg in server.args

        assert len(server.args) == 4

    @patch(
        "django_prodserver.backends.waitress.wsgi_app_name",
        return_value="tests.wsgi:application",
    )
    def test_empty_args_dict(self, mock_wsgi_app_name):
        """Test prep_server_args with explicitly empty ARGS dict."""
        server = WaitressServer(ARGS={})
        args = server.prep_server_args()

        assert args == ["waitress", "tests.wsgi:application"]
        mock_wsgi_app_name.assert_called_once()

    @patch("waitress.runner.run")
    def test_start_server_exception_propagation(self, mock_waitress_run):
        """Test that exceptions from waitress.runner.run are properly propagated."""
        mock_waitress_run.side_effect = RuntimeError("Waitress failed to start")

        server = WaitressServer()

        with pytest.raises(RuntimeError, match="Waitress failed to start"):
            server.start_server("--port=8000")
