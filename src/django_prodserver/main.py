from .conf import app_settings


def add(n1: int, n2: int) -> int:
    """Add the arguments."""
    return n1 + n2


def is_enabled() -> bool:
    """Example usage of app settings."""
    return app_settings.PRODSERVER_ENABLED
