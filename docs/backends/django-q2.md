(backend-django-q2)=

# Django-Q2

Django-Q2 is a Django ORM-backed task queue with advanced features like task scheduling, result storage, and Django admin integration. It's a maintained fork of the original Django-Q project.

## Overview

Django-Q2 provides a full-featured task queue using Django's ORM for storage. Unlike Django Tasks (which is minimal), Django-Q2 offers scheduling, retries, task groups, and a comprehensive Django admin interface.

## When to Use

**Choose Django-Q2 when you need:**
- ORM-backed task queue without external dependencies
- Task scheduling (like cron jobs)
- Django admin interface for monitoring tasks
- Task groups and result tracking
- More features than Django Tasks but simpler than Celery
- No message broker setup (Redis/RabbitMQ)

**Consider alternatives if:**
- You need minimal task queue → Use {ref}`backend-django-tasks`
- You need distributed processing across machines → Use {ref}`backend-celery-worker`
- You have very high task volume → Use {ref}`backend-celery-worker` with Redis

## Installation

Install Django-Q2 via pip:

```bash
pip install django-q2
```

Add to your `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    "django_q",  # Note: app name is django_q, not django_q2
]
```

Run migrations:

```bash
python manage.py migrate
```

For more installation options, see the [Django-Q2 documentation](https://django-q2.readthedocs.io/).

## Basic Configuration

### Minimal Setup

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    "django_q",
]

# Django-Q2 configuration
Q_CLUSTER = {
    'name': 'myproject',
    'workers': 4,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
}

# django-prodserver configuration
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {
            "verbosity": "1",
        }
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
Q_CLUSTER = {
    'name': 'myproject',
    'workers': 8,
    'recycle': 500,
    'timeout': 60,
    'compress': True,
    'save_limit': 250,
    'queue_limit': 500,
    'cpu_affinity': 1,
    'label': 'Django Q2',
    'redis': None,  # Use ORM, not Redis
}

PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {
            "verbosity": "1",
        }
    }
}
```

## ARGS Translation

The `ARGS` dictionary is passed to the Django-Q2 `qcluster` management command:

```python
"ARGS": {
    "verbosity": "2",           # --verbosity=2
    "cluster-name": "myworker", # --cluster-name=myworker
}
```

This translates to:
```bash
python manage.py qcluster --verbosity=2 --cluster-name=myworker
```

::::{important}
Most Django-Q2 configuration is done through the `Q_CLUSTER` setting in Django settings, not through ARGS. The ARGS are primarily for runtime options.
::::

## Configuration Reference

### ARGS Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `verbosity` | integer | `1` | Logging verbosity (0-3) |
| `cluster-name` | string | From Q_CLUSTER | Override cluster name |

### Q_CLUSTER Settings

Configure Django-Q2 behavior in the `Q_CLUSTER` dictionary:

#### Worker Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `name` | string | Required | Cluster name for identification |
| `workers` | integer | CPU count | Number of worker processes |
| `recycle` | integer | `500` | Tasks per worker before recycling |
| `timeout` | integer | `None` | Task timeout in seconds |
| `retry` | integer | `None` | Retry timeout for failed tasks |
| `max_attempts` | integer | `1` | Maximum retry attempts |

#### Queue Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `queue_limit` | integer | Workers × 2 | Maximum tasks in queue |
| `bulk` | integer | `1` | Tasks to process per batch |
| `orm` | string | `default` | Database alias to use |

#### Performance Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `compress` | boolean | `False` | Compress task data |
| `save_limit` | integer | `250` | Maximum successful tasks to keep |
| `cpu_affinity` | integer | `1` | CPU affinity for workers |
| `catch_up` | boolean | `True` | Run missed scheduled tasks on startup |

For complete settings, see the [Django-Q2 configuration](https://django-q2.readthedocs.io/en/master/configure.html).

## Advanced Examples

### High-Performance Worker

```python
Q_CLUSTER = {
    'name': 'high-performance',
    'workers': 12,
    'recycle': 1000,
    'timeout': 120,
    'compress': True,
    'save_limit': 100,
    'queue_limit': 1000,
    'bulk': 10,
    'orm': 'default',
}

PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {
            "verbosity": "1",
        }
    }
}
```

### With Redis (Optional)

Django-Q2 can use Redis for better performance:

```bash
pip install redis
```

```python
Q_CLUSTER = {
    'name': 'redis-cluster',
    'workers': 8,
    'timeout': 90,
    'redis': {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
    }
}
```

### Multiple Clusters

Run different worker clusters:

```python
# settings.py
Q_CLUSTER = {
    'name': 'default',
    'workers': 4,
}

PRODUCTION_PROCESSES = {
    "default_worker": {
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {
            "cluster-name": "default",
            "verbosity": "1",
        }
    },
    "priority_worker": {
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {
            "cluster-name": "priority",
            "verbosity": "1",
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
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {
            "verbosity": "1",
        }
    }
}
```

## Defining and Running Tasks

### Creating Tasks

```python
# myapp/tasks.py
def send_email(email_address, message):
    """Send an email in the background."""
    from django.core.mail import send_mail
    send_mail(
        'Subject',
        message,
        'from@example.com',
        [email_address],
    )

def generate_report(user_id):
    """Generate a report."""
    # Generate report logic
    pass
```

### Enqueuing Tasks

```python
from django_q.tasks import async_task, schedule

# Simple async task
async_task('myapp.tasks.send_email', 'user@example.com', 'Hello!')

# Task with options
async_task(
    'myapp.tasks.generate_report',
    user_id=123,
    timeout=300,
    group='reports'
)

# Scheduled task (run once)
schedule(
    'myapp.tasks.send_email',
    'user@example.com',
    'Scheduled message',
    schedule_type='O',  # Once
    next_run=timezone.now() + timedelta(hours=1)
)

# Recurring task (cron-like)
schedule(
    'myapp.tasks.generate_report',
    user_id=123,
    schedule_type='H',  # Hourly
    name='hourly-report'
)
```

### Task Results

```python
# Async task with result
task_id = async_task('myapp.tasks.generate_report', user_id=123)

# Check result later
from django_q.models import Task
task = Task.objects.get(id=task_id)
if task.success:
    print(task.result)
```

## Scheduled Tasks

### Schedule Types

- `O` - Once (run at specific time)
- `H` - Hourly
- `D` - Daily
- `W` - Weekly
- `M` - Monthly
- `Q` - Quarterly
- `Y` - Yearly
- `I` - Interval (minutes)
- `C` - Cron expression

### Cron-Style Scheduling

```python
from django_q.tasks import schedule

# Daily at 8 AM
schedule(
    'myapp.tasks.daily_report',
    schedule_type='D',
    cron='0 8 * * *',
    name='daily-report-8am'
)

# Every 15 minutes
schedule(
    'myapp.tasks.update_cache',
    schedule_type='I',
    minutes=15,
    name='cache-update'
)

# Weekly on Monday
schedule(
    'myapp.tasks.weekly_cleanup',
    schedule_type='W',
    repeats=-1,  # Repeat forever
    name='weekly-cleanup'
)
```

## Django Admin Integration

Django-Q2 provides a comprehensive admin interface:

### Viewing Tasks

```python
# Access at /admin/django_q/
- Task - View task results and status
- Schedule - Manage scheduled tasks
- Success - View successful tasks
- Failure - View failed tasks
```

### Admin Features

- View task execution history
- Monitor worker status
- Manage scheduled tasks
- Retry failed tasks
- View task results and tracebacks

## Worker Count Recommendations

Formula: `1-2 workers per CPU core`

```python
import multiprocessing

Q_CLUSTER = {
    'name': 'myproject',
    'workers': multiprocessing.cpu_count() * 2,
}
```

**Guidelines:**
- **Low volume:** 2-4 workers
- **Medium volume:** 4-8 workers
- **High volume:** 8-16 workers
- **Monitor:** Watch database load and adjust

## Common Issues

### Django-Q2 Not Installed

**Symptom:** `ImproperlyConfigured: django-q2 is required`

**Solution:**
```bash
pip install django-q2
```

### Not in INSTALLED_APPS

**Symptom:** `ImproperlyConfigured: Add 'django_q' to INSTALLED_APPS`

**Solution:**
```python
INSTALLED_APPS = [
    # ...
    "django_q",  # Add this
]
```

### Tasks Not Processing

**Symptom:** Tasks queued but not executing

**Solution:**
- Ensure worker is running: `python manage.py prodserver worker`
- Check Q_CLUSTER configuration
- Verify migrations: `python manage.py migrate`

### Database Lock Contention

**Symptom:** Slow task processing or database errors

**Solution:** Reduce workers or use Redis:
```python
Q_CLUSTER = {
    'workers': 4,  # Reduce workers
    'redis': {  # Or switch to Redis
        'host': 'localhost',
        'port': 6379,
    }
}
```

### Old Tasks Accumulating

**Symptom:** Database growing with old task records

**Solution:** Clean up old tasks:
```bash
python manage.py qclean
```

Or set save_limit:
```python
Q_CLUSTER = {
    'save_limit': 100,  # Keep only 100 successful tasks
}
```

## Performance Tuning

### For High Volume

```python
Q_CLUSTER = {
    'workers': 12,
    'recycle': 500,
    'bulk': 10,
    'queue_limit': 1000,
    'save_limit': 100,
    'compress': True,
}
```

### For Low Latency

```python
Q_CLUSTER = {
    'workers': 4,
    'bulk': 1,
    'timeout': 30,
    'queue_limit': 100,
}
```

### With Redis for Performance

```python
Q_CLUSTER = {
    'workers': 8,
    'redis': {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
    }
}
```

## Integration Examples

### With Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15

  web:
    build: .
    command: python manage.py prodserver web
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
Description=MyApp Django-Q2 Worker
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

## Monitoring and Maintenance

### Monitor via Admin

Access `/admin/django_q/` to:
- View task status
- Check worker health
- Monitor queue size
- Review failed tasks

### Clean Old Tasks

Regular cleanup:
```bash
# Manual cleanup
python manage.py qclean

# Or schedule it
from django_q.tasks import schedule
schedule(
    'django_q.tasks.clean_old_tasks',
    schedule_type='D',  # Daily
    name='daily-cleanup'
)
```

### Task Monitoring

```python
from django_q.models import Task, Success, Failure

# Count tasks
total = Task.objects.count()
successful = Success.objects.count()
failed = Failure.objects.count()

# Recent failures
recent_failures = Failure.objects.order_by('-stopped')[:10]
```

## Official Documentation

For complete Django-Q2 documentation:
- [Django-Q2 Documentation](https://django-q2.readthedocs.io/)
- [Configuration Guide](https://django-q2.readthedocs.io/en/master/configure.html)
- [Tasks Guide](https://django-q2.readthedocs.io/en/master/tasks.html)
- [Schedules Guide](https://django-q2.readthedocs.io/en/master/schedules.html)

## Related Documentation

- {ref}`configuration-reference` - Complete PRODUCTION_PROCESSES reference
- {ref}`guide-multi-process` - Multi-process deployments
- {ref}`backend-celery-worker` - More powerful alternative
- {ref}`backend-django-tasks` - Simpler alternative
- {ref}`troubleshooting` - General troubleshooting guide
