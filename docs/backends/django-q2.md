(backend-django-q2)=

# Django-Q2

Django-Q2 is a Django ORM-backed task queue with advanced features like task scheduling, result storage, and Django admin integration. It's a maintained fork of the original Django-Q project.

**Use when:** ORM-backed queue, admin UI, scheduled tasks without Celery
**Don't use when:** High volume distributed tasks (use {ref}`backend-celery-worker`)

## Installation

```bash
pip install django-prodserver[django-q2]
```

```python
INSTALLED_APPS = [
    # ...
    "django_q",  # Note: django_q, not django_q2
]
```

```bash
python manage.py migrate
```

## Configuration

```python
# Django-Q2 settings
Q_CLUSTER = {
    'name': 'myproject',
    'workers': 4,
    'timeout': 90,
    'retry': 120,
    'orm': 'default',
}

# django-prodserver
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {"verbosity": "1"},
    }
}
```

## Q_CLUSTER Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `name` | Required | Cluster name |
| `workers` | CPU count | Worker processes |
| `timeout` | `None` | Task timeout (seconds) |
| `retry` | `None` | Retry timeout |
| `recycle` | `500` | Tasks before worker restart |
| `queue_limit` | Workers × 2 | Max queued tasks |
| `save_limit` | `250` | Successful tasks to keep |
| `orm` | `default` | Database alias |

## ARGS

| Argument | Default | Description |
|----------|---------|-------------|
| `verbosity` | `1` | Log verbosity (0-3) |

## Example

### Web + Worker

```python
Q_CLUSTER = {
    'name': 'myproject',
    'workers': 4,
    'timeout': 60,
    'orm': 'default',
}

PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000", "workers": "4"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {"verbosity": "1"},
    },
}
```

## Tasks

```python
# myapp/tasks.py
def send_email(email_address, message):
    from django.core.mail import send_mail
    send_mail('Subject', message, 'from@example.com', [email_address])

# Enqueue
from django_q.tasks import async_task
async_task('myapp.tasks.send_email', 'user@example.com', 'Hello!')
```

## Scheduled Tasks

```python
from django_q.tasks import schedule

# Once
schedule('myapp.tasks.report', schedule_type='O', next_run=tomorrow)

# Hourly
schedule('myapp.tasks.cleanup', schedule_type='H', name='hourly-cleanup')

# Cron
schedule('myapp.tasks.daily', schedule_type='C', cron='0 8 * * *')
```

## Admin Interface

Access at `/admin/django_q/` to:
- View task results
- Monitor workers
- Manage schedules
- Retry failed tasks

## Troubleshooting

**Tasks not processing:** Check worker running, migrations applied

**Database locks:** Reduce workers or switch to Redis:
```python
Q_CLUSTER = {'redis': {'host': 'localhost', 'port': 6379}}
```

**Old tasks accumulating:** Run `python manage.py qclean` or set `save_limit`

## Links

- [Django-Q2 Docs](https://django-q2.readthedocs.io/)
