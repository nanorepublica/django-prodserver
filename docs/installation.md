(installation)=

# Installation

The package is published on [PyPI](https://pypi.org/project/django-prodserver/) and can be installed with `pip` (or any equivalent):

```bash
pip install django-prodserver
```

Add the app to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_prodserver",
]
```

Add the `PRODUCTION_PROCESSES` setting to your `settings.py`. Below shows an example with a web process and worker process defined.

The comments show other available backend processes that are available to use.

```py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8111"},
    },
    # "web": {
    #     "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
    #     "ARGS": {},
    # },
    # "web": {
    #     "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
    #     "ARGS": {},
    # },
    # "web": {
    #     "BACKEND": "django_prodserver.backends.uvicorn.UvicornWSGIServer",
    #     "ARGS": {},
    # },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "tests.celery.app",
        "ARGS": {},
    },
    # "worker": {
    #     "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
    #     "ARGS": {},
    # },
}
```

Next, see the {ref}`section about usage <usage>` to see how to use it.
