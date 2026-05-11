(backend-celery)=

# Celery Worker and Beat

Celery is a distributed task queue system for processing background jobs. django-prodserver supports both Celery Worker (for processing tasks) and Celery Beat (for scheduling periodic tasks).

**Use when:** Background tasks, scheduled jobs, distributed processing
**Don't use when:** Simple tasks without external deps (use {ref}`backend-django-tasks`)

## Installation

```bash
pip install django-prodserver[celery]

# Plus a broker
pip install redis  # or rabbitmq
```

## Setup

### Celery App

```python
# myproject/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

```python
# myproject/__init__.py
from .celery import app as celery_app
__all__ = ('celery_app',)
```

### Django Settings

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

(backend-celery-worker)=

## Worker

```python
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.workers.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": "4",
            "loglevel": "info",
        }
    }
}
```

### Worker ARGS

| Argument               | Default   | Description                             |
| ---------------------- | --------- | --------------------------------------- |
| `concurrency`          | CPU count | Worker processes/threads                |
| `loglevel`             | `info`    | Log level                               |
| `pool`                 | `prefork` | Pool type (`prefork`, `gevent`, `solo`) |
| `queues`               | All       | Comma-separated queue names             |
| `max-tasks-per-child`  | `None`    | Restart after N tasks                   |
| `max-memory-per-child` | `None`    | Restart after N KB                      |
| `time-limit`           | `None`    | Hard task timeout                       |
| `soft-time-limit`      | `None`    | Soft task timeout                       |

(backend-celery-beat)=

## Beat (Scheduler)

```python
PRODUCTION_PROCESSES = {
    "beat": {
        "BACKEND": "django_prodserver.backends.workers.celery.CeleryBeat",
        "APP": "myproject.celery.app",
        "ARGS": {"loglevel": "info"},
    }
}
```

**Important:** Run only ONE beat instance per application.

### Beat ARGS

| Argument    | Default | Description     |
| ----------- | ------- | --------------- |
| `loglevel`  | `info`  | Log level       |
| `scheduler` | Default | Scheduler class |

(backend-celery-flower)=

## Flower (Monitoring)

[Flower](https://flower.readthedocs.io/) is a web-based tool for monitoring and
administering Celery clusters. The `CeleryFlower` backend starts Flower via the
`flower` subcommand registered on your Celery app.

### Installation

```bash
pip install django-prodserver[flower]
```

### Configuration

```python
PRODUCTION_PROCESSES = {
    "flower": {
        "BACKEND": "django_prodserver.backends.workers.celery.CeleryFlower",
        "APP": "myproject.celery.app",
        "ARGS": {"port": "5555", "address": "0.0.0.0"},
    }
}
```

```bash
python manage.py server flower
```

### Flower ARGS

| Argument     | Default   | Description                                |
| ------------ | --------- | ------------------------------------------ |
| `port`       | `5555`    | Port the Flower web server listens on      |
| `address`    | `0.0.0.0` | Address to bind to                         |
| `url_prefix` | `None`    | Run Flower under a URL prefix              |
| `basic_auth` | `None`    | `user:password` pairs for HTTP basic auth  |
| `persistent` | `False`   | Persist monitoring data across restarts    |
| `db`         | `flower`  | Database file when `persistent` is enabled |
| `max_tasks`  | `10000`   | Maximum number of tasks to keep in memory  |

See the [Flower documentation](https://flower.readthedocs.io/en/latest/config.html)
for the full list of options. Options can also be supplied via `FLOWER_*`
environment variables.

## Examples

### Full Stack

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000", "workers": "4"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.workers.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {"concurrency": "4", "max-tasks-per-child": "1000"},
    },
    "beat": {
        "BACKEND": "django_prodserver.backends.workers.celery.CeleryBeat",
        "APP": "myproject.celery.app",
        "ARGS": {"loglevel": "info"},
    },
}
```

### Multiple Queues

```python
PRODUCTION_PROCESSES = {
    "default_worker": {
        "BACKEND": "django_prodserver.backends.workers.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {"queues": "default", "concurrency": "4"},
    },
    "priority_worker": {
        "BACKEND": "django_prodserver.backends.workers.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {"queues": "priority", "concurrency": "2"},
    },
}
```

### Gevent Pool

```bash
pip install celery[gevent]
```

```python
"ARGS": {"pool": "gevent", "concurrency": "100"}
```

## Troubleshooting

**Broker connection failed:** Check Redis/RabbitMQ is running and `CELERY_BROKER_URL`

**Tasks not discovered:** Ensure `autodiscover_tasks()` and `tasks.py` in apps

**Memory leaks:** Add `max-tasks-per-child`

**Duplicate scheduled tasks:** Run only one beat instance

## Links

- [Celery Docs](https://docs.celeryq.dev/)
- [Django Integration](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html)
