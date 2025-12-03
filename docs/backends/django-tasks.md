(backend-django-tasks)=

# Django Tasks

Django's built-in lightweight task queue (Django 6+). Uses the ORM for storage.

**Use when:** Simple background tasks, no external dependencies
**Don't use when:** Distributed processing, complex workflows (use {ref}`backend-celery-worker`)

## Requirements

Django 6+
django-tasks

## Installation

```bash
pip install django-prodserver[django-tasks]
```

```python
INSTALLED_APPS = [
    # ...
    "django-tasks",
]
```

```bash
python manage.py migrate
```

## Configuration

```python
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
        "ARGS": {
            "processes": "4",
            "threads": "1",
        }
    }
}
```

## ARGS

| Argument | Default | Description |
|----------|---------|-------------|
| `processes` | `1` | Worker processes |
| `threads` | `1` | Threads per process |
| `queue` | `default` | Queue to process |
| `verbosity` | `1` | Log verbosity (0-3) |

## Example

### Web + Worker

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000", "workers": "4"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
        "ARGS": {"processes": "2", "threads": "2"},
    },
}
```

## Defining Tasks

```python
# myapp/tasks.py
from django.contrib.tasks import task

@task()
def send_email(email_address, message):
    from django.core.mail import send_mail
    send_mail('Subject', message, 'from@example.com', [email_address])

# Enqueue
send_email.delay('user@example.com', 'Hello!')
```

## Scaling

| Volume | Config |
|--------|--------|
| Low (< 1K/day) | 1 process, 2 threads |
| Medium (1-10K/day) | 2 processes, 2 threads |
| High (> 10K/day) | Consider Celery |

## Troubleshooting

**Tasks not processing:** Check worker is running and migrations applied

**Django < 5.1:** Upgrade Django or use {ref}`backend-django-q2`

## Links

- [Django Tasks Docs](https://docs.djangoproject.com/en/stable/topics/tasks/)
