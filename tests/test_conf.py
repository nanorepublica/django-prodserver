from django.conf import settings

from django_prodserver.conf import app_settings


def test_app_settings():
    assert app_settings.PRODUCTION_PROCESSES == settings.PRODUCTION_PROCESSES
