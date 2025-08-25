from unittest.mock import Mock, patch

import pytest

from django_prodserver.utils import (
    WarmupFailure,
    asgi_app_name,
    wsgi_app_name,
    wsgi_healthcheck,
)


def test_wsgi_app_name():
    """Test wsgi_app_name function."""
    assert wsgi_app_name() == "tests.wsgi:application"


def test_asgi_app_name():
    """Test asgi_app_name function."""
    assert asgi_app_name() == "tests.asgi:application"


@patch("django_prodserver.utils.settings")
def test_wsgi_app_name_custom_setting(mock_settings):
    """Test wsgi_app_name with custom WSGI_APPLICATION setting."""
    mock_settings.WSGI_APPLICATION = "myproject.wsgi.application"
    assert wsgi_app_name() == "myproject.wsgi:application"


@patch("django_prodserver.utils.settings")
def test_asgi_app_name_custom_setting(mock_settings):
    """Test asgi_app_name with custom ASGI_APPLICATION setting."""
    mock_settings.ASGI_APPLICATION = "myproject.asgi.application"
    assert asgi_app_name() == "myproject.asgi:application"


def test_warmup_failure_exception():
    """Test WarmupFailure exception can be raised and caught."""
    with pytest.raises(WarmupFailure):
        raise WarmupFailure("Test failure message")


def test_warmup_failure_exception_with_message():
    """Test WarmupFailure exception preserves error message."""
    message = "Healthcheck failed with status 500"
    try:
        raise WarmupFailure(message)
    except WarmupFailure as e:
        assert str(e) == message


class TestWsgiHealthcheck:
    """Tests for wsgi_healthcheck function."""

    def test_wsgi_healthcheck_success(self):
        """Test successful healthcheck."""
        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_app.get_response.return_value = mock_response

        # Should not raise an exception
        wsgi_healthcheck(mock_app, "/health/")

        mock_app.get_response.assert_called_once()

    def test_wsgi_healthcheck_failure(self):
        """Test failed healthcheck."""
        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_app.get_response.return_value = mock_response

        with pytest.raises(WarmupFailure) as exc_info:
            wsgi_healthcheck(mock_app, "/health/")

        assert "responded with a 500" in str(exc_info.value)
        mock_app.get_response.assert_called_once()

    def test_wsgi_healthcheck_custom_ok_status(self):
        """Test healthcheck with custom ok status."""
        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_app.get_response.return_value = mock_response

        # Should not raise an exception
        wsgi_healthcheck(mock_app, "/health/", ok_status=201)

        mock_app.get_response.assert_called_once()

    def test_wsgi_healthcheck_custom_ok_status_failure(self):
        """Test healthcheck with custom ok status that fails."""
        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_app.get_response.return_value = mock_response

        with pytest.raises(WarmupFailure) as exc_info:
            wsgi_healthcheck(mock_app, "/health/", ok_status=201)

        assert "responded with a 200" in str(exc_info.value)

    @patch("django_prodserver.utils.settings")
    def test_wsgi_healthcheck_with_allowed_hosts(self, mock_settings):
        """Test healthcheck with ALLOWED_HOSTS configured."""
        mock_settings.ALLOWED_HOSTS = ["example.com"]

        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_app.get_response.return_value = mock_response

        wsgi_healthcheck(mock_app, "/health/")

        # Check that the request was made with the correct host header
        call_args = mock_app.get_response.call_args
        request = call_args[0][0]
        assert request.META["HTTP_HOST"] == "example.com"

    @patch("django_prodserver.utils.settings")
    def test_wsgi_healthcheck_with_wildcard_host(self, mock_settings):
        """Test healthcheck with wildcard ALLOWED_HOSTS."""
        mock_settings.ALLOWED_HOSTS = ["*"]

        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_app.get_response.return_value = mock_response

        wsgi_healthcheck(mock_app, "/health/")

        # Check that the request was made with testserver host
        call_args = mock_app.get_response.call_args
        request = call_args[0][0]
        assert request.META["HTTP_HOST"] == "testserver"

    @patch("django_prodserver.utils.settings")
    def test_wsgi_healthcheck_with_dot_prefix_host(self, mock_settings):
        """Test healthcheck with dot-prefixed ALLOWED_HOSTS."""
        mock_settings.ALLOWED_HOSTS = [".example.com"]

        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_app.get_response.return_value = mock_response

        wsgi_healthcheck(mock_app, "/health/")

        # Check that the request was made with example.example.com host
        call_args = mock_app.get_response.call_args
        request = call_args[0][0]
        assert request.META["HTTP_HOST"] == "example.example.com"

    @patch("django_prodserver.utils.settings")
    def test_wsgi_healthcheck_no_allowed_hosts(self, mock_settings):
        """Test healthcheck with no ALLOWED_HOSTS configured."""
        # Simulate missing ALLOWED_HOSTS attribute
        del mock_settings.ALLOWED_HOSTS

        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_app.get_response.return_value = mock_response

        wsgi_healthcheck(mock_app, "/health/")

        # Check that the request was made without host header
        call_args = mock_app.get_response.call_args
        request = call_args[0][0]
        assert "HTTP_HOST" not in request.META

    @patch("django_prodserver.utils.settings")
    def test_wsgi_healthcheck_empty_allowed_hosts(self, mock_settings):
        """Test healthcheck with empty ALLOWED_HOSTS."""
        mock_settings.ALLOWED_HOSTS = []

        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_app.get_response.return_value = mock_response

        wsgi_healthcheck(mock_app, "/health/")

        # Check that the request was made without host header due to IndexError
        call_args = mock_app.get_response.call_args
        request = call_args[0][0]
        assert "HTTP_HOST" not in request.META

    @patch("django_prodserver.utils.settings")
    def test_wsgi_healthcheck_multiple_allowed_hosts(self, mock_settings):
        """Test healthcheck uses first host when multiple are configured."""
        mock_settings.ALLOWED_HOSTS = ["api.example.com", "example.com", "localhost"]

        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_app.get_response.return_value = mock_response

        wsgi_healthcheck(mock_app, "/health/")

        # Should use the first host
        call_args = mock_app.get_response.call_args
        request = call_args[0][0]
        assert request.META["HTTP_HOST"] == "api.example.com"

    def test_wsgi_healthcheck_request_factory_usage(self):
        """Test that wsgi_healthcheck uses RequestFactory correctly."""
        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_app.get_response.return_value = mock_response

        wsgi_healthcheck(mock_app, "/custom-health-endpoint/")

        # Verify request was made
        call_args = mock_app.get_response.call_args
        request = call_args[0][0]
        assert request.path == "/custom-health-endpoint/"
        assert request.method == "GET"

    def test_wsgi_healthcheck_different_error_codes(self):
        """Test healthcheck fails with various HTTP error codes."""
        error_codes = [400, 401, 403, 404, 500, 502, 503]

        for error_code in error_codes:
            mock_app = Mock()
            mock_response = Mock()
            mock_response.status_code = error_code
            mock_app.get_response.return_value = mock_response

            with pytest.raises(WarmupFailure) as exc_info:
                wsgi_healthcheck(mock_app, "/health/")

            assert f"responded with a {error_code}" in str(exc_info.value)

    def test_wsgi_healthcheck_custom_url_in_error_message(self):
        """Test that custom URL appears in error message."""
        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_app.get_response.return_value = mock_response

        custom_url = "/api/v1/health/"
        with pytest.raises(WarmupFailure) as exc_info:
            wsgi_healthcheck(mock_app, custom_url)

        assert custom_url in str(exc_info.value)

    @patch("django_prodserver.utils.settings")
    def test_wsgi_healthcheck_host_handling_edge_cases(self, mock_settings):
        """Test edge cases in host handling."""
        # Test with subdomain wildcard
        mock_settings.ALLOWED_HOSTS = [".api.example.com"]

        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_app.get_response.return_value = mock_response

        wsgi_healthcheck(mock_app, "/health/")

        call_args = mock_app.get_response.call_args
        request = call_args[0][0]
        assert request.META["HTTP_HOST"] == "example.api.example.com"

    def test_wsgi_healthcheck_app_exception_propagation(self):
        """Test that exceptions from the app are properly propagated."""
        mock_app = Mock()
        mock_app.get_response.side_effect = RuntimeError("App crashed")

        with pytest.raises(RuntimeError, match="App crashed"):
            wsgi_healthcheck(mock_app, "/health/")

    @patch("django_prodserver.utils.RequestFactory")
    def test_wsgi_healthcheck_request_factory_called_correctly(
        self, mock_request_factory
    ):
        """Test that RequestFactory is called with correct parameters."""
        mock_factory_instance = Mock()
        mock_request = Mock()
        mock_factory_instance.get.return_value = mock_request
        mock_request_factory.return_value = mock_factory_instance

        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_app.get_response.return_value = mock_response

        wsgi_healthcheck(mock_app, "/test/")

        mock_request_factory.assert_called_once()
        mock_factory_instance.get.assert_called_once_with(
            "/test/", HTTP_HOST="testserver"
        )
