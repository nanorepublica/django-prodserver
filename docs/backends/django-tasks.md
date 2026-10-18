(backend-django-tasks)=

# Django Tasks DB

The database backend supplied by `django-tasks-db`. Django's built-in task API does not itself provide a database worker.

**Use when:** Simple background tasks, no external dependencies
**Don't use when:** Distributed processing, complex workflows (use {ref}`backend-celery-worker`)

## Requirements

Django 6+
django-tasks-db

## Installation

```bash
pip install django-prodserver django-tasks-db
```

```python
INSTALLED_APPS = [
    # ...
    "django_tasks_db",
]
```

```bash
python manage.py migrate
```

Configure task storage alongside the installed app:

```python
TASKS = {
    "default": {
        "BACKEND": "django_tasks_db.DatabaseBackend",
        "QUEUES": ["default"],
    }
}
```

## Configuration

```python
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.workers.django_tasks_db.DjangoTasksDBWorker",
        "ARGS": {
            "queue-name": "default",
            "interval": "1",
        }
    }
}
```

## ARGS

| Argument     | Default   | Description                       |
| ------------ | --------- | --------------------------------- |
| `queue-name` | `default` | Comma-separated queues to process |
| `interval`   | `1`       | Seconds between checks when idle  |
| `backend`    | `default` | Configured task backend alias     |
| `verbosity`  | `1`       | Log verbosity (0–3)               |

Run `python manage.py db_worker --help` for the options supported by your
installed django-tasks-db version. Run multiple worker processes through your
process supervisor rather than passing `processes` or `threads` to this command.

## Example

### Web + Worker

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.servers.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000", "workers": "4"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.workers.django_tasks_db.DjangoTasksDBWorker",
        "ARGS": {"queue-name": "default", "interval": "1"},
    },
}
```

## Defining Tasks

```python
# myapp/tasks.py
from django.tasks import task

@task()
def send_email(email_address, message):
    from django.core.mail import send_mail
    send_mail('Subject', message, 'from@example.com', [email_address])

# Enqueue
send_email.enqueue('user@example.com', 'Hello!')
```

## Scaling

Run multiple instances of the configured worker using your process supervisor.
Select queues with `queue-name` to separate workloads. Assess database contention
and task duration before increasing concurrency.

## Troubleshooting

**Tasks not processing:** Check worker is running and migrations applied

**Django < 6:** Upgrade Django or use {ref}`backend-django-q2`

## Links

- [Django Tasks Docs](https://docs.djangoproject.com/en/stable/topics/tasks/)

## Compatibility

For Django 5.2, install `django-tasks-db[compat]` and import `task` from
`django_tasks` instead of `django.tasks`. Consult the installed backend version's
requirements when using older Django versions.

The original `django-tasks` extra is retained for projects using the legacy
bundled database backend.

The existing `django_prodserver.backends.workers.django_tasks.DjangoTasksWorker`
import remains available as an alias. Both paths run `db_worker`; neither is a
generic runner for every Django Tasks backend.
