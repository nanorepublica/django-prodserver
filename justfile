# default := 'staging'
# default: deploy
#
# blank backend file
# ideally this would be a templated string!
# blank_backend := "from django.core import management

# from .base import BaseServerBackend


# class DjangoTasksWorker(BaseServerBackend):
#     """Backend to start a django task db worker."""

#     def start_server(self, *args: str) -> None:
#         """Call django-tasks management command."""
#         management.call_command("db_worker", *args)
# "

new_backend extra:
    # assumes a python packages
    uv add {{ extra }} --optional {{ extra }}
    touch src/django_prodserver/backends/{{ extra }}.py
    # echo 'from .base import BaseServerBackend


    # class {{ extra }}Worker(BaseServerBackend):\
    #     """Backend to start a {{ extra }} process."""\

    #     def start_server(self, *args: str) -> None:\
    #         """Start an {{ extra }} process."""\
    #         pass' > src/django_prodserver/backends/{{ extra }}.py

tests *FLAGS:
    python manage.py test {{FLAGS}}

envs := 'waitress,gunicorn,celery,uvicorn,coverage'
tox extras=envs:
    tox run -e py312-django52,{{extras}}

# activate:
#     source .venv/bin/activate
