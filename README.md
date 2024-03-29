# django-prodserver

[![PyPI](https://img.shields.io/pypi/v/django-prodserver.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/django-prodserver.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/django-prodserver)][pypi status]
[![License](https://img.shields.io/pypi/l/django-prodserver)][license]

[![Read the documentation at https://django-prodserver.readthedocs.io/](https://img.shields.io/readthedocs/django-prodserver/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/nanorepublica/django-prodserver/actions/workflows/tests.yml/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/nanorepublica/django-prodserver/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/django-prodserver/
[read the docs]: https://django-prodserver.readthedocs.io/
[tests]: https://github.com/nanorepublica/django-prodserver/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/nanorepublica/django-prodserver
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

## Features

This package features 2 new management commands

- `manage.py devserver` - this is a simple rename of `runserver`
- `manage.py prodserver` - this will start your wsgi/asgi server

Includes in this package are configurations for gunicorn, waitress and uvicorn (wgsi & asgi)

## Requirements

- django-click
- your wsgi/asgi server of choice

## Installation

You can install _django-prodserver_ via [pip] from [PyPI]:

```console
$ pip install django_prodserver
```

Add the following settings:

```py

INSTALLED_APPS += ["django_prodserver"]

PROD_SERVERS = {
    'web': {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": [
            "--bind=0.0.0.0:8111"
            # other gunicorn commmand line args go here
        ]
    }
}
```

Then you will be able to use the management command like so:
```console
$ python manage.py prodserver web
```

## Usage

Please see the [Command-line Reference] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_django-prodserver_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@OmenApps]'s [Cookiecutter Django Package] template.

[@omenapps]: https://github.com/OmenApps
[pypi]: https://pypi.org/
[cookiecutter django package]: https://github.com/OmenApps/cookiecutter-django-package
[file an issue]: https://github.com/nanorepublica/django-prodserver/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/nanorepublica/django-prodserver/blob/main/LICENSE
[contributor guide]: https://github.com/nanorepublica/django-prodserver/blob/main/CONTRIBUTING.md
[command-line reference]: https://django-prodserver.readthedocs.io/en/latest/usage.html
