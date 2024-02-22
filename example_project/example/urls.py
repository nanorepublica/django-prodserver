"""URL configuration for ezemple app."""


from django.urls import path
from .views import index

urlpatterns = [
    path("", index, name="home"),
]
