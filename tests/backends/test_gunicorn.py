from argparse import ArgumentParser, Namespace
from unittest.mock import Mock, patch

import pytest

# Handle optional dependency
gunicorn = pytest.importorskip("gunicorn")

from django_prodserver.backends.gunicorn import (  # NOQA: E402
    DjangoApplication,
    GunicornServer,
)


class TestDjangoApplication:
    """Tests for DjangoApplication class."""

    @patch("sys.argv", ["test_program"])
    def test_init(self):
        """Test DjangoApplication.init method."""
        app = DjangoApplication()
        parser = Mock(spec=ArgumentParser)
        opts = Mock(spec=Namespace)

        # Mock the parent init method
        with patch.object(app.__class__.__bases__[0], "init") as mock_parent_init:
            with patch(
                "django_prodserver.backends.gunicorn.wsgi_app_name",
                return_value="tests.wsgi:application",
            ):
                app.init(parser, opts, "extra_arg1", "extra_arg2")

                # Check that parent init was called with correct args
                mock_parent_init.assert_called_once_with(
                    parser, opts, ("tests.wsgi:application",)
                )


class TestGunicornServer:
    """Tests for GunicornServer class."""

    def test_init_without_args(self):
        """Test GunicornServer initialization without args."""
        server = GunicornServer()
        assert server.args == []

    def test_init_with_args(self):
        """Test GunicornServer initialization with args."""
        server = GunicornServer(ARGS={"bind": "0.0.0.0:8000", "workers": "4"})
        assert server.args == ["--bind=0.0.0.0:8000", "--workers=4"]

    @patch("sys.argv", ["manage.py", "prodserver"])
    @patch("django_prodserver.backends.gunicorn.DjangoApplication")
    def test_start_server(self, mock_django_app):
        """Test start_server method."""
        mock_app_instance = Mock()
        mock_django_app.return_value = mock_app_instance

        server = GunicornServer()
        args = ["--bind=0.0.0.0:8000", "--workers=4"]

        server.start_server(*args)

        # Check that args were added to sys.argv
        import sys

        assert "--bind=0.0.0.0:8000" in sys.argv
        assert "--workers=4" in sys.argv

        # Check that DjangoApplication was created and run was called
        mock_django_app.assert_called_once_with("%(prog)s [OPTIONS]", *args)
        mock_app_instance.run.assert_called_once()

    @patch("sys.argv", ["manage.py", "prodserver"])
    @patch("django_prodserver.backends.gunicorn.DjangoApplication")
    def test_start_server_no_args(self, mock_django_app):
        """Test start_server method with no args."""
        mock_app_instance = Mock()
        mock_django_app.return_value = mock_app_instance

        server = GunicornServer()
        server.start_server()

        mock_django_app.assert_called_once_with("%(prog)s [OPTIONS]")
        mock_app_instance.run.assert_called_once()

    def test_prep_server_args(self):
        """Test prep_server_args method."""
        server = GunicornServer(ARGS={"bind": "0.0.0.0:8000"})
        args = server.prep_server_args()
        assert args == ["--bind=0.0.0.0:8000"]

    def test_prep_server_args_empty(self):
        """Test prep_server_args with no args."""
        server = GunicornServer()
        args = server.prep_server_args()
        assert args == []

    def test_inheritance_from_base_backend(self):
        """Test that GunicornServer properly inherits from BaseServerBackend."""
        from django_prodserver.backends.base import BaseServerBackend

        server = GunicornServer()
        assert isinstance(server, BaseServerBackend)

    @patch("sys.argv", ["manage.py", "prodserver"])
    @patch("django_prodserver.backends.gunicorn.DjangoApplication")
    def test_start_server_with_mixed_args(self, mock_django_app):
        """Test start_server method with various argument types."""
        mock_app_instance = Mock()
        mock_django_app.return_value = mock_app_instance

        server = GunicornServer()
        args = ["--bind=0.0.0.0:8000", "--workers=4", "--timeout=30"]

        server.start_server(*args)

        # Check that all args were added to sys.argv
        import sys

        for arg in args:
            assert arg in sys.argv

        mock_django_app.assert_called_once_with("%(prog)s [OPTIONS]", *args)
        mock_app_instance.run.assert_called_once()

    def test_server_args_formatting(self):
        """Test that server args are properly formatted from dict."""
        server = GunicornServer(
            ARGS={
                "bind": "127.0.0.1:8000",
                "workers": "2",
                "timeout": "120",
                "worker-class": "sync",
            }
        )

        expected_args = [
            "--bind=127.0.0.1:8000",
            "--workers=2",
            "--timeout=120",
            "--worker-class=sync",
        ]

        # Check all expected args are present
        for expected_arg in expected_args:
            assert expected_arg in server.args

        assert len(server.args) == 4
