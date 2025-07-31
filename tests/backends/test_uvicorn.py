import pytest
from unittest.mock import Mock, patch

# Handle optional dependency
uvicorn = pytest.importorskip("uvicorn")

from django_prodserver.backends.uvicorn import UvicornServer, UvicornWSGIServer


class TestUvicornServer:
    """Tests for UvicornServer class."""

    def test_init_without_args(self):
        """Test UvicornServer initialization without args."""
        server = UvicornServer()
        assert server.args == []

    def test_init_with_args(self):
        """Test UvicornServer initialization with args."""
        server = UvicornServer(ARGS={"host": "0.0.0.0", "port": "8000"})
        assert server.args == ["--host=0.0.0.0", "--port=8000"]

    @patch(
        "django_prodserver.backends.uvicorn.asgi_app_name",
        return_value="tests.asgi:application",
    )
    def test_prep_server_args(self, mock_asgi_app_name):
        """Test prep_server_args method."""
        server = UvicornServer(ARGS={"host": "0.0.0.0", "port": "8000"})
        args = server.prep_server_args()

        assert args == ["tests.asgi:application", "--host=0.0.0.0", "--port=8000"]
        mock_asgi_app_name.assert_called_once()

    @patch(
        "django_prodserver.backends.uvicorn.asgi_app_name",
        return_value="tests.asgi:application",
    )
    def test_prep_server_args_no_args(self, mock_asgi_app_name):
        """Test prep_server_args with no args."""
        server = UvicornServer()
        args = server.prep_server_args()

        assert args == ["tests.asgi:application"]
        mock_asgi_app_name.assert_called_once()

    @patch("uvicorn.main.main")
    def test_start_server(self, mock_uvicorn_main):
        """Test start_server method."""
        server = UvicornServer()
        args = ["--host=0.0.0.0", "--port=8000"]

        server.start_server(*args)

        mock_uvicorn_main.assert_called_once_with(args)

    @patch("uvicorn.main.main")
    def test_start_server_no_args(self, mock_uvicorn_main):
        """Test start_server method with no args."""
        server = UvicornServer()

        server.start_server()

        mock_uvicorn_main.assert_called_once_with(())

    def test_inheritance_from_base_backend(self):
        """Test that UvicornServer properly inherits from BaseServerBackend."""
        from django_prodserver.backends.base import BaseServerBackend

        server = UvicornServer()
        assert isinstance(server, BaseServerBackend)

    @patch(
        "django_prodserver.backends.uvicorn.asgi_app_name",
        return_value="myapp.asgi:application",
    )
    def test_prep_server_args_with_complex_args(self, mock_asgi_app_name):
        """Test prep_server_args with complex arguments."""
        server = UvicornServer(
            ARGS={"host": "127.0.0.1", "port": "8080", "workers": "4", "reload": "true"}
        )
        args = server.prep_server_args()

        assert args[0] == "myapp.asgi:application"
        assert "--host=127.0.0.1" in args
        assert "--port=8080" in args
        assert "--workers=4" in args
        assert "--reload=true" in args
        assert len(args) == 5

    @patch("uvicorn.main.main")
    @patch(
        "django_prodserver.backends.uvicorn.asgi_app_name",
        return_value="tests.asgi:application",
    )
    def test_full_workflow(self, mock_asgi_app_name, mock_uvicorn_main):
        """Test the complete workflow from initialization to server start."""
        server = UvicornServer(ARGS={"host": "0.0.0.0", "port": "8000"})
        prepared_args = server.prep_server_args()
        server.start_server(*prepared_args)

        mock_asgi_app_name.assert_called_once()
        mock_uvicorn_main.assert_called_once_with(
            ["tests.asgi:application", "--host=0.0.0.0", "--port=8000"]
        )


class TestUvicornWSGIServer:
    """Tests for UvicornWSGIServer class."""

    def test_init_without_args(self):
        """Test UvicornWSGIServer initialization without args."""
        server = UvicornWSGIServer()
        assert server.args == []

    def test_init_with_args(self):
        """Test UvicornWSGIServer initialization with args."""
        server = UvicornWSGIServer(ARGS={"host": "0.0.0.0", "port": "8000"})
        assert server.args == ["--host=0.0.0.0", "--port=8000"]

    @patch(
        "django_prodserver.backends.uvicorn.wsgi_app_name",
        return_value="tests.wsgi:application",
    )
    def test_prep_server_args(self, mock_wsgi_app_name):
        """Test prep_server_args method."""
        server = UvicornWSGIServer(ARGS={"host": "0.0.0.0", "port": "8000"})
        args = server.prep_server_args()

        assert args == [
            "tests.wsgi:application",
            "--interface=wsgi",
            "--host=0.0.0.0",
            "--port=8000",
        ]
        mock_wsgi_app_name.assert_called_once()

    @patch(
        "django_prodserver.backends.uvicorn.wsgi_app_name",
        return_value="tests.wsgi:application",
    )
    def test_prep_server_args_no_args(self, mock_wsgi_app_name):
        """Test prep_server_args with no args."""
        server = UvicornWSGIServer()
        args = server.prep_server_args()

        assert args == ["tests.wsgi:application", "--interface=wsgi"]
        mock_wsgi_app_name.assert_called_once()

    @patch("uvicorn.main.main")
    def test_start_server(self, mock_uvicorn_main):
        """Test start_server method."""
        server = UvicornWSGIServer()
        args = ["--host=0.0.0.0", "--port=8000"]

        server.start_server(*args)

        mock_uvicorn_main.assert_called_once_with(args)

    @patch("uvicorn.main.main")
    def test_start_server_no_args(self, mock_uvicorn_main):
        """Test start_server method with no args."""
        server = UvicornWSGIServer()

        server.start_server()

        mock_uvicorn_main.assert_called_once_with(())

    def test_inheritance_from_base_backend(self):
        """Test that UvicornWSGIServer properly inherits from BaseServerBackend."""
        from django_prodserver.backends.base import BaseServerBackend

        server = UvicornWSGIServer()
        assert isinstance(server, BaseServerBackend)

    @patch(
        "django_prodserver.backends.uvicorn.wsgi_app_name",
        return_value="myapp.wsgi:application",
    )
    def test_prep_server_args_with_complex_args(self, mock_wsgi_app_name):
        """Test prep_server_args with complex arguments."""
        server = UvicornWSGIServer(
            ARGS={
                "host": "127.0.0.1",
                "port": "8080",
                "workers": "2",
                "timeout-keep-alive": "30",
            }
        )
        args = server.prep_server_args()

        assert args[0] == "myapp.wsgi:application"
        assert args[1] == "--interface=wsgi"
        assert "--host=127.0.0.1" in args
        assert "--port=8080" in args
        assert "--workers=2" in args
        assert "--timeout-keep-alive=30" in args
        assert len(args) == 6

    @patch("uvicorn.main.main")
    @patch(
        "django_prodserver.backends.uvicorn.wsgi_app_name",
        return_value="tests.wsgi:application",
    )
    def test_full_workflow(self, mock_wsgi_app_name, mock_uvicorn_main):
        """Test the complete workflow from initialization to server start."""
        server = UvicornWSGIServer(ARGS={"host": "0.0.0.0", "port": "8000"})
        prepared_args = server.prep_server_args()
        server.start_server(*prepared_args)

        mock_wsgi_app_name.assert_called_once()
        mock_uvicorn_main.assert_called_once_with(
            [
                "tests.wsgi:application",
                "--interface=wsgi",
                "--host=0.0.0.0",
                "--port=8000",
            ]
        )

    def test_wsgi_interface_always_present(self):
        """Test that --interface=wsgi is always included for WSGI server."""
        server = UvicornWSGIServer()
        args = server.prep_server_args()
        assert "--interface=wsgi" in args

    @patch(
        "django_prodserver.backends.uvicorn.wsgi_app_name",
        return_value="custom.wsgi:app",
    )
    def test_custom_wsgi_app_name(self, mock_wsgi_app_name):
        """Test with custom WSGI application name."""
        server = UvicornWSGIServer()
        args = server.prep_server_args()

        assert args[0] == "custom.wsgi:app"
        mock_wsgi_app_name.assert_called_once()


class TestUvicornServerComparison:
    """Tests comparing UvicornServer and UvicornWSGIServer behavior."""

    @patch(
        "django_prodserver.backends.uvicorn.asgi_app_name",
        return_value="tests.asgi:application",
    )
    @patch(
        "django_prodserver.backends.uvicorn.wsgi_app_name",
        return_value="tests.wsgi:application",
    )
    def test_different_app_names(self, mock_wsgi_app_name, mock_asgi_app_name):
        """Test that ASGI and WSGI servers use different app names."""
        asgi_server = UvicornServer()
        wsgi_server = UvicornWSGIServer()

        asgi_args = asgi_server.prep_server_args()
        wsgi_args = wsgi_server.prep_server_args()

        assert asgi_args[0] == "tests.asgi:application"
        assert wsgi_args[0] == "tests.wsgi:application"

        mock_asgi_app_name.assert_called_once()
        mock_wsgi_app_name.assert_called_once()

    def test_interface_flag_difference(self):
        """Test that only WSGI server includes interface flag."""
        asgi_server = UvicornServer()
        wsgi_server = UvicornWSGIServer()

        asgi_args = asgi_server.prep_server_args()
        wsgi_args = wsgi_server.prep_server_args()

        assert "--interface=wsgi" not in asgi_args
        assert "--interface=wsgi" in wsgi_args
