import logging

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
from django.test import RequestFactory

log = logging.getLogger(__name__)


class WarmupFailure(Exception):
    """Exception to capture WarmupFailure."""

    pass


def wsgi_healthcheck(app: WSGIHandler, url: str, ok_status: int = 200) -> None:
    """Simple healthcheck function."""
    try:
        host = settings.ALLOWED_HOSTS[0]
        if host.startswith("."):
            host = "example" + host
        elif host == "*":
            host = "testserver"
        headers = {"HTTP_HOST": host}
    except (AttributeError, IndexError):
        headers = {}
    warmup = app.get_response(RequestFactory().get(url, **headers))
    if warmup.status_code != ok_status:
        raise WarmupFailure(
            f"WSGI warmup using endpoint {url} responded with a {warmup.status_code}."
        )


def wsgi_app_name() -> str:
    """Get the WSGI name from settings."""
    return ":".join(settings.WSGI_APPLICATION.rsplit(".", 1))


def asgi_app_name() -> str:
    """Get the ASGI name from settings."""
    return ":".join(settings.ASGI_APPLICATION.rsplit(".", 1))
