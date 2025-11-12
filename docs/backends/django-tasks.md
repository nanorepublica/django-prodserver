(backend-django-tasks)=

# Django Tasks

Django Tasks is Django's built-in lightweight task queue system (available in Django 5.1+). It provides simple background task processing without external dependencies like Redis or RabbitMQ.

## Overview

Django Tasks uses the Django ORM to manage task queues, making it a lightweight alternative to Celery for simple background job processing. Tasks are stored in the database and processed by worker processes.

## When to Use

**Choose Django Tasks when you need:**
- Simple background task processing
- No external dependencies (uses Django ORM)
- Lightweight task queue for low to medium volume
- Django-native task management
- Easy setup and maintenance

**Consider alternatives if:**
- You need distributed task processing across multiple machines → Use {ref}`backend-celery-worker`
- You need complex workflows (chains, groups, chords) → Use {ref}`backend-celery-worker`
- You have high-volume task processing → Use {ref}`backend-celery-worker`
- You want ORM-backed with more features → Use {ref}`backend-django-q2`

## Requirements

Django Tasks requires **Django 5.1 or higher**.

## Installation

Django Tasks is included with Django 5.1+, no separate installation needed:

```bash
# Ensure you have Django 5.1+
pip install "django>=5.1"
```

Add to your `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    "django.contrib.tasks",
]
```

Run migrations:

```bash
python manage.py migrate
```

For more information, see the [Django Tasks documentation](https://docs.djangoproject.com/en/stable/topics/tasks/).

## Basic Configuration

### Minimal Setup

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    "django.contrib.tasks",
]

PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
        "ARGS": {}
    }
}
```

Start the worker:
```bash
python manage.py prodserver worker
```

### Recommended Production Setup

```python
# settings.py
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

## ARGS Translation

The `ARGS` dictionary is passed to the Django `db_worker` management command:

```python
"ARGS": {
    "processes": "4",           # --processes=4
    "threads": "1",             # --threads=1
    "queue": "default",         # --queue=default
}
```

This translates to:
```bash
python manage.py db_worker --processes=4 --threads=1 --queue=default
```

## Configuration Reference

### Common ARGS Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `processes` | integer | `1` | Number of worker processes |
| `threads` | integer | `1` | Number of threads per process |
| `queue` | string | `default` | Queue name to process |
| `verbosity` | integer | `1` | Logging verbosity (0-3) |

::::{note}
Most Django Tasks configuration is done through Django settings, not through ARGS. The ARGS primarily control the worker process behavior.
::::

### Django Settings Configuration

Configure Django Tasks in your settings:

```python
# settings.py

# Task queue backend (default: database)
TASKS = {
    'default': {
        'BACKEND': 'django.core.tasks.backends.database.DatabaseBackend',
    }
}

# Task result expiration (days)
TASKS_RESULT_EXPIRATION_DAYS = 30

# Task logging
TASKS_LOG_LEVEL = 'INFO'
```

## Advanced Examples

### Multiple Worker Processes

```python
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
        "ARGS": {
            "processes": "4",
            "threads": "2",
            "verbosity": "1",
        }
    }
}
```

### Multiple Queues

Process different queues with separate workers:

```python
PRODUCTION_PROCESSES = {
    "default_worker": {
        "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
        "ARGS": {
            "queue": "default",
            "processes": "4",
        }
    },
    "priority_worker": {
        "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
        "ARGS": {
            "queue": "priority",
            "processes": "2",
        }
    }
}
```

### Complete Application Stack

Web server + task worker:

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "4",
        }
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
        "ARGS": {
            "processes": "2",
            "threads": "2",
        }
    }
}
```

## Defining and Running Tasks

### Creating Tasks

```python
# myapp/tasks.py
from django.contrib.tasks import task

@task()
def send_email(email_address, message):
    """Send an email in the background."""
    from django.core.mail import send_mail
    send_mail(
        'Subject',
        message,
        'from@example.com',
        [email_address],
    )

@task(priority='high')
def urgent_task():
    """High priority task."""
    # Process urgent work
    pass

@task(queue='reports')
def generate_report():
    """Task for specific queue."""
    # Generate report
    pass
```

### Enqueuing Tasks

```python
# In your views or other code
from myapp.tasks import send_email, generate_report

# Enqueue task
send_email.delay('user@example.com', 'Hello!')

# Task with priority
urgent_task.delay()

# Task to specific queue
generate_report.delay()
```

### Task Results

```python
# Get task result
result = send_email.delay('user@example.com', 'Hello!')

# Check if complete
if result.ready():
    print(result.get())
```

## Process and Thread Recommendations

### Process Count

Formula: `1-2 processes per CPU core`

```python
import multiprocessing

processes = multiprocessing.cpu_count()

PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
        "ARGS": {
            "processes": str(processes),
        }
    }
}
```

### Thread Count

- **I/O-bound tasks:** More threads (2-4 per process)
- **CPU-bound tasks:** Fewer threads (1 per process)
- **Database-heavy:** Moderate threads (1-2 per process)

## Common Issues

### Tasks Not Processing

**Symptom:** Tasks sit in the database but aren't processed

**Solution:**
- Ensure worker is running: `python manage.py prodserver worker`
- Check that `django.contrib.tasks` is in `INSTALLED_APPS`
- Verify migrations are applied: `python manage.py migrate`

### Database Locking Issues

**Symptom:** Workers blocking each other or slow processing

**Solution:** Reduce processes/threads:
```python
"ARGS": {
    "processes": "2",  # Reduce processes
    "threads": "1",     # Single thread per process
}
```

### Django 5.1 Not Available

**Symptom:** `ImportError: cannot import name 'tasks'`

**Solution:** Django Tasks requires Django 5.1+:
```bash
pip install --upgrade "django>=5.1"
```

### High Database Load

**Symptom:** Database CPU usage very high

**Solution:**
- Reduce worker count
- Consider migrating to Celery with Redis/RabbitMQ
- Add database indexes for task tables

## Performance Considerations

### Database as Message Broker

Django Tasks uses the database for task storage, which has limitations:

**Advantages:**
- No external dependencies
- Simple setup
- Built-in with Django

**Limitations:**
- Database load increases with task volume
- Not ideal for high-throughput scenarios
- Potential locking contention with many workers

### Scaling Recommendations

**Low volume (< 1000 tasks/day):**
```python
"ARGS": {
    "processes": "1",
    "threads": "2",
}
```

**Medium volume (1000-10000 tasks/day):**
```python
"ARGS": {
    "processes": "2",
    "threads": "2",
}
```

**High volume (> 10000 tasks/day):**
Consider migrating to {ref}`backend-celery-worker` with Redis/RabbitMQ.

## Integration Examples

### With Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: myapp
      POSTGRES_PASSWORD: secret

  web:
    build: .
    command: python manage.py prodserver web
    ports:
      - "8000:8000"
    depends_on:
      - db

  worker:
    build: .
    command: python manage.py prodserver worker
    depends_on:
      - db
```

### With systemd

```ini
# /etc/systemd/system/myapp-worker.service
[Unit]
Description=MyApp Django Tasks Worker
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/myapp
Environment="PATH=/var/www/myapp/venv/bin"
ExecStart=/var/www/myapp/venv/bin/python manage.py prodserver worker
Restart=always

[Install]
WantedBy=multi-user.target
```

## Task Cleanup

Clean up old task results periodically:

```python
# myapp/management/commands/cleanup_tasks.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.tasks.models import TaskResult

class Command(BaseCommand):
    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=30)
        TaskResult.objects.filter(created_at__lt=cutoff).delete()
```

Run with cron or Celery Beat:
```bash
python manage.py cleanup_tasks
```

## Migration from Celery

If migrating from Celery to Django Tasks:

```python
# Before (Celery)
from celery import shared_task

@shared_task
def send_email(email_address, message):
    # Send email
    pass

# After (Django Tasks)
from django.contrib.tasks import task

@task()
def send_email(email_address, message):
    # Send email
    pass
```

Task enqueuing is similar:
```python
# Both Celery and Django Tasks
send_email.delay('user@example.com', 'Hello!')
```

::::{note}
Django Tasks doesn't support all Celery features (chains, groups, etc.). Evaluate your needs before migrating.
::::

## Official Documentation

For complete Django Tasks documentation:
- [Django Tasks Documentation](https://docs.djangoproject.com/en/stable/topics/tasks/)
- [Background Tasks Reference](https://docs.djangoproject.com/en/stable/ref/tasks/)

## Related Documentation

- {ref}`configuration-reference` - Complete PRODUCTION_PROCESSES reference
- {ref}`guide-multi-process` - Multi-process deployments
- {ref}`backend-celery-worker` - More powerful alternative
- {ref}`backend-django-q2` - Similar ORM-backed queue
- {ref}`troubleshooting` - General troubleshooting guide
