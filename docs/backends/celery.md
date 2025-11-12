(backend-celery)=

# Celery Worker and Beat

Celery is a distributed task queue system for processing background jobs. django-prodserver supports both Celery Worker (for processing tasks) and Celery Beat (for scheduling periodic tasks).

## Overview

Celery allows you to run time-consuming tasks asynchronously in the background, separate from your web application. This improves response times and enables complex workflows, scheduled tasks, and distributed processing.

**Components:**
- **Celery Worker:** Processes tasks from the queue
- **Celery Beat:** Schedules periodic tasks (like cron)

## When to Use

**Choose Celery when you need:**
- Distributed task processing across multiple machines
- Complex task workflows (chains, groups, chords)
- Periodic/scheduled tasks (like cron jobs)
- Production-grade reliability and monitoring
- Task retries, rate limiting, and timeouts
- Mature ecosystem and extensive documentation

**Consider alternatives if:**
- You need simple task queues without external dependencies → Use {ref}`backend-django-tasks`
- You want ORM-backed task storage → Use {ref}`backend-django-q2`
- Your tasks are very simple and low-volume

## Installation

Install Celery with your chosen message broker:

```bash
# With Redis (recommended)
pip install celery[redis]

# With RabbitMQ
pip install celery[rabbitmq]

# Minimal installation
pip install celery
```

You'll also need a message broker:
- **Redis:** `pip install redis` + Redis server
- **RabbitMQ:** RabbitMQ server installation

For more installation options, see the [official Celery installation guide](https://docs.celeryq.dev/en/stable/getting-started/introduction.html).

## Basic Configuration

### Celery App Setup

First, create a Celery app in your Django project:

```python
# myproject/celery.py
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()
```

```python
# myproject/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### Django Settings

```python
# settings.py
# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'

# django-prodserver configuration
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "loglevel": "info",
        }
    }
}
```

Start the worker:
```bash
python manage.py prodserver worker
```

(backend-celery-worker)=

## Celery Worker

### Minimal Configuration

```python
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "loglevel": "info",
        }
    }
}
```

### Recommended Production Setup

```python
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": "4",
            "loglevel": "info",
            "max-tasks-per-child": "1000",
            "pool": "prefork",
        }
    }
}
```

### ARGS Translation for Worker

The `ARGS` dictionary is translated to Celery worker command-line arguments:

```python
"ARGS": {
    "concurrency": "4",              # --concurrency=4
    "loglevel": "info",              # --loglevel=info
    "max-tasks-per-child": "1000",  # --max-tasks-per-child=1000
    "queues": "default,priority",    # --queues=default,priority
}
```

This translates to:
```bash
celery -A myproject.celery.app worker --concurrency=4 --loglevel=info --max-tasks-per-child=1000 --queues=default,priority
```

### Common Worker ARGS Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `concurrency` | integer | CPU count | Number of concurrent worker processes/threads |
| `loglevel` | string | `info` | Log level (`debug`, `info`, `warning`, `error`, `critical`) |
| `pool` | string | `prefork` | Worker pool type (`prefork`, `solo`, `eventlet`, `gevent`, `threads`) |
| `queues` | string | All queues | Comma-separated list of queues to consume |
| `max-tasks-per-child` | integer | None | Max tasks before worker process restart (prevents memory leaks) |
| `max-memory-per-child` | integer | None | Max memory (KB) before worker process restart |
| `time-limit` | integer | None | Hard time limit (seconds) for tasks |
| `soft-time-limit` | integer | None | Soft time limit (seconds) for tasks |
| `prefetch-multiplier` | integer | `4` | How many messages to prefetch per worker |
| `autoscale` | string | None | Autoscaling settings (e.g., `"10,3"` = max 10, min 3) |

### Advanced Worker Examples

#### High-Concurrency Worker

```python
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": "8",
            "pool": "prefork",
            "loglevel": "info",
            "max-tasks-per-child": "1000",
            "max-memory-per-child": "500000",  # 500MB
            "time-limit": "300",
            "soft-time-limit": "270",
        }
    }
}
```

#### Multiple Workers for Different Queues

```python
PRODUCTION_PROCESSES = {
    "default_worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "queues": "default",
            "concurrency": "4",
            "loglevel": "info",
        }
    },
    "priority_worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "queues": "priority",
            "concurrency": "2",
            "loglevel": "info",
        }
    },
    "email_worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "queues": "email",
            "concurrency": "1",
            "loglevel": "warning",
        }
    }
}
```

#### Gevent Pool for I/O-Bound Tasks

```bash
# First install: pip install celery[gevent]
```

```python
PRODUCTION_PROCESSES = {
    "io_worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "pool": "gevent",
            "concurrency": "100",  # Many concurrent greenlets
            "loglevel": "info",
        }
    }
}
```

(backend-celery-beat)=

## Celery Beat

Celery Beat is the scheduler for periodic tasks (like cron).

### Basic Beat Configuration

```python
PRODUCTION_PROCESSES = {
    "beat": {
        "BACKEND": "django_prodserver.backends.celery.CeleryBeat",
        "APP": "myproject.celery.app",
        "ARGS": {
            "loglevel": "info",
        }
    }
}
```

Start the scheduler:
```bash
python manage.py prodserver beat
```

::::{important}
Run **only one Beat instance** per application. Multiple Beat schedulers will cause duplicate task execution.
::::

### ARGS Translation for Beat

```python
"ARGS": {
    "loglevel": "info",              # --loglevel=info
    "scheduler": "django",           # --scheduler=django
}
```

This translates to:
```bash
celery -A myproject.celery.app beat --loglevel=info --scheduler=django
```

### Common Beat ARGS Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `loglevel` | string | `info` | Log level (`debug`, `info`, `warning`, `error`, `critical`) |
| `scheduler` | string | `celery.beat:PersistentScheduler` | Scheduler class to use |
| `schedule` | string | None | Path to custom schedule file |
| `max-interval` | integer | None | Max sleep interval between schedule checks (seconds) |

### Advanced Beat Examples

#### With Django Database Scheduler

For managing scheduled tasks via Django admin:

```bash
# Install django-celery-beat
pip install django-celery-beat
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'django_celery_beat',
]

PRODUCTION_PROCESSES = {
    "beat": {
        "BACKEND": "django_prodserver.backends.celery.CeleryBeat",
        "APP": "myproject.celery.app",
        "ARGS": {
            "loglevel": "info",
            "scheduler": "django_celery_beat.schedulers:DatabaseScheduler",
        }
    }
}
```

### Defining Periodic Tasks

```python
# myproject/celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('myproject')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Schedule periodic tasks
app.conf.beat_schedule = {
    'send-report-every-morning': {
        'task': 'myapp.tasks.send_daily_report',
        'schedule': crontab(hour=8, minute=0),
    },
    'cleanup-every-hour': {
        'task': 'myapp.tasks.cleanup_old_data',
        'schedule': crontab(minute=0),  # Top of every hour
    },
    'update-every-30-seconds': {
        'task': 'myapp.tasks.update_cache',
        'schedule': 30.0,
    },
}

app.autodiscover_tasks()
```

## Complete Application Stack

Web server + worker + beat for a full production deployment:

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
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": "4",
            "loglevel": "info",
            "max-tasks-per-child": "1000",
        }
    },
    "beat": {
        "BACKEND": "django_prodserver.backends.celery.CeleryBeat",
        "APP": "myproject.celery.app",
        "ARGS": {
            "loglevel": "info",
        }
    }
}
```

Run each process:
```bash
# Terminal 1
python manage.py prodserver web

# Terminal 2
python manage.py prodserver worker

# Terminal 3
python manage.py prodserver beat
```

See {ref}`guide-multi-process` for managing multiple processes with systemd or Docker.

## Common Issues

### Broker Connection Failed

**Symptom:** `[ERROR] consumer: Cannot connect to redis://localhost:6379/0`

**Solution:**
- Verify Redis/RabbitMQ is running
- Check `CELERY_BROKER_URL` in settings
- Test connection: `redis-cli ping` (for Redis)

### Tasks Not Discovered

**Symptom:** Tasks are not being found or executed

**Solution:**
- Ensure `app.autodiscover_tasks()` is called in your Celery app
- Create `tasks.py` in your Django apps
- Import Celery app in `__init__.py`

### APP Import Error

**Symptom:** `ImportError: No module named 'myproject.celery'`

**Solution:**
- Verify the `APP` path is correct: `"APP": "myproject.celery.app"`
- Ensure your `celery.py` file exists and defines `app`
- Check Python path and working directory

### Worker Memory Leaks

**Symptom:** Workers consume increasing memory over time

**Solution:** Configure worker recycling:
```python
"ARGS": {
    "max-tasks-per-child": "1000",
    "max-memory-per-child": "500000",  # 500MB
}
```

### Multiple Beat Instances

**Symptom:** Periodic tasks running multiple times

**Solution:** Run only **one** Beat instance per application. Use proper process management to ensure this.

## Performance Tuning

### Concurrency Recommendations

**CPU-bound tasks:**
```python
"ARGS": {
    "concurrency": str(multiprocessing.cpu_count()),
    "pool": "prefork",
}
```

**I/O-bound tasks:**
```python
"ARGS": {
    "pool": "gevent",  # or eventlet
    "concurrency": "100",  # More greenlets
}
```

### Task Prefetching

Control how many tasks workers prefetch:

```python
"ARGS": {
    "prefetch-multiplier": "1",  # Prefetch only 1 task per worker
}
```

Lower values improve load distribution but may reduce throughput.

### Autoscaling Workers

Dynamically scale workers based on load:

```python
"ARGS": {
    "autoscale": "10,3",  # Scale between 3 and 10 workers
    "loglevel": "info",
}
```

Format: `"max_workers,min_workers"`

## Integration Examples

### With Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:alpine

  web:
    build: .
    command: python manage.py prodserver web
    ports:
      - "8000:8000"
    depends_on:
      - redis

  worker:
    build: .
    command: python manage.py prodserver worker
    depends_on:
      - redis

  beat:
    build: .
    command: python manage.py prodserver beat
    depends_on:
      - redis
```

### With systemd

```ini
# /etc/systemd/system/myapp-worker.service
[Unit]
Description=MyApp Celery Worker
After=network.target redis.service

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

```ini
# /etc/systemd/system/myapp-beat.service
[Unit]
Description=MyApp Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/myapp
Environment="PATH=/var/www/myapp/venv/bin"
ExecStart=/var/www/myapp/venv/bin/python manage.py prodserver beat
Restart=always

[Install]
WantedBy=multi-user.target
```

## Official Documentation

For complete Celery documentation:
- [Celery Documentation](https://docs.celeryq.dev/)
- [First Steps with Django](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html)
- [User Guide](https://docs.celeryq.dev/en/stable/userguide/index.html)
- [Configuration Reference](https://docs.celeryq.dev/en/stable/userguide/configuration.html)
- [Workers Guide](https://docs.celeryq.dev/en/stable/userguide/workers.html)
- [Periodic Tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)

## Related Documentation

- {ref}`configuration-reference` - Complete PRODUCTION_PROCESSES reference
- {ref}`guide-multi-process` - Multi-process deployments with Celery
- {ref}`backend-django-tasks` - Lightweight alternative to Celery
- {ref}`backend-django-q2` - ORM-backed queue alternative
- {ref}`troubleshooting` - General troubleshooting guide
