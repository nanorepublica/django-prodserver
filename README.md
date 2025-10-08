# Django prodserver

<p align="center">
  <a href="https://github.com/nanorepublica/django-prodserver/actions/workflows/ci.yml?query=branch%3Amain">
    <img src="https://img.shields.io/github/actions/workflow/status/nanorepublica/django-prodserver/ci.yml?branch=main&label=CI&logo=github&style=flat-square" alt="CI Status" >
  </a>
  <a href="https://django-prodserver.readthedocs.io">
    <img src="https://img.shields.io/readthedocs/django-prodserver.svg?logo=read-the-docs&logoColor=fff&style=flat-square" alt="Documentation Status">
  </a>
  <a href="https://codecov.io/gh/nanorepublica/django-prodserver">
    <img src="https://img.shields.io/codecov/c/github/nanorepublica/django-prodserver.svg?logo=codecov&logoColor=fff&style=flat-square" alt="Test coverage percentage">
  </a>
</p>
<p align="center">
  <a href="https://github.com/astral-sh/uv">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff">
  </a>
  <a href="https://github.com/pre-commit/pre-commit">
    <img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=flat-square" alt="pre-commit">
  </a>
</p>
<p align="center">
  <a href="https://pypi.org/project/django-prodserver/">
    <img src="https://img.shields.io/pypi/v/django-prodserver.svg?logo=python&logoColor=fff&style=flat-square" alt="PyPI Version">
  </a>
  <img src="https://img.shields.io/pypi/pyversions/django-prodserver.svg?style=flat-square&logo=python&amp;logoColor=fff" alt="Supported Python versions">
  <img src="https://img.shields.io/pypi/l/django-prodserver.svg?style=flat-square" alt="License">
</p>

---

**Documentation**: <a href="https://django-prodserver.readthedocs.io" target="_blank">https://django-prodserver.readthedocs.io </a>

**Source Code**: <a href="https://github.com/nanorepublica/django-prodserver" target="_blank">https://github.com/nanorepublica/django-prodserver </a>

---

A management command to start production servers/workers with a consistent interface

## Installation

Install this via pip (or your favourite package manager):

`pip install django-prodserver`

Add the app to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_prodserver",
]
```

## Configuration

Add the `PRODUCTION_PROCESSES` setting to your `settings.py`. Below shows an example with a web process and worker process defined.

The comments show other available backend processes that are available to use.

```py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8111"},
    },
    # "web": {
    #     "BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
    #     "ARGS": {"address": "0.0.0.0", "port": "8000", "workers": "4"},
    # },
    # "web": {
    #     "BACKEND": "django_prodserver.backends.granian.GranianWSGIServer",
    #     "ARGS": {"address": "0.0.0.0", "port": "8000", "workers": "4"},
    # },
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

## Usage

Once the `PRODUCTION_PROCESSES` setting has been configured you can then start the processes as follows:

```sh
python manage.py prodserver web
```

```sh
python manage.py prodserver worker
```

## Creating a new backend.

Creating a backend is fairly simple. Subclass the `BaseServerBackend` class, then implement
the `start_server` method which should call the underlying process in the best possible way for a production
setting. You can also optionally override `prep_server_args` method to aid with this to provide any default arguments
or formatting to the `start_server` command.

See `django_prodserver.backends` for examples of existing backends for inspiration. Pull Request's are welcome for
additional backends.

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- prettier-ignore-start -->
<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- markdownlint-disable -->
<!-- markdownlint-enable -->
<!-- ALL-CONTRIBUTORS-LIST:END -->
<!-- prettier-ignore-end -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!

## Credits

[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-orange.json)](https://github.com/copier-org/copier)

This package was created with
[Copier](https://copier.readthedocs.io/) and the
[browniebroke/pypackage-template](https://github.com/browniebroke/pypackage-template)
project template.
