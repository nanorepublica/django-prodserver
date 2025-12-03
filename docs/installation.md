(installation)=

# Installation

(quickstart)=

## Quickstart

```bash
# Install with your chosen backend
pip install django-prodserver[gunicorn]
```

Add to your `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    "django_prodserver",
]

PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000", "workers": "2"},
    }
}
```

Run your server:

```bash
python manage.py prodserver web
```

---

(choosing-backend)=

## Choosing a Backend

### Web Servers

| Backend | Best For |
|---------|----------|
| {ref}`Gunicorn <backend-gunicorn>` | Traditional sync Django apps, Linux production |
| {ref}`Uvicorn <backend-uvicorn-asgi>` | Async Django, WebSockets |
| {ref}`Waitress <backend-waitress>` | Windows, pure Python environments |
| {ref}`Granian <backend-granian-asgi>` | Maximum performance (Rust-based), WSGI/ASGI |

### Background Workers

| Backend | Best For |
|---------|----------|
| {ref}`Celery <backend-celery-worker>` | Distributed tasks, complex workflows, Redis/RabbitMQ |
| {ref}`Django Tasks <backend-django-tasks>` | Simple tasks, no external dependencies |
| {ref}`Django-Q2 <backend-django-q2>` | ORM-backed queues, scheduled tasks |

---

## Installing Backends

Backends can be installed via pip extras or separately.

### Via Pip Extras (Recommended)

```bash
pip install django-prodserver[gunicorn]
pip install django-prodserver[uvicorn]
pip install django-prodserver[waitress]
pip install django-prodserver[granian]
pip install django-prodserver[celery]
pip install django-prodserver[django-tasks]
pip install django-prodserver[django-q2]

# Multiple backends
pip install django-prodserver[gunicorn,celery]
```

### Separately

```bash
pip install gunicorn
pip install uvicorn
pip install waitress
pip install granian
pip install celery[redis]  # or celery[rabbitmq]
pip install django-q2
```

See individual {ref}`backend documentation <backend-reference>` for detailed requirements.

---

## Configuration

A more complete example with web and worker processes:

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000", "workers": "4"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {"concurrency": "4"},
    },
}
```

See {ref}`configuration-reference` for all options.

---

## Troubleshooting

**ImportError: No module named 'gunicorn'**
: Install the backend: `pip install django-prodserver[gunicorn]`

**Django app not found**
: Add `"django_prodserver"` to `INSTALLED_APPS`

**PRODUCTION_PROCESSES not found**
: Add the `PRODUCTION_PROCESSES` dict to your settings

For more help, see {ref}`troubleshooting`.

---

## Next Steps

- {ref}`usage` - Running your configured processes
- {ref}`backend-reference` - Detailed backend documentation
- {ref}`practical-guides` - Deployment tutorials
- {ref}`configuration-reference` - Advanced configuration
