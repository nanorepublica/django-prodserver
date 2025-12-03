(backend-reference)=

# Backend Reference

django-prodserver supports multiple production-ready server backends for WSGI/ASGI applications and background workers. Each backend is configured using the `PRODUCTION_PROCESSES` setting in your Django settings file.

## Available Backends

### Web Servers

| Backend                                    | Type | Best For                             |
| ------------------------------------------ | ---- | ------------------------------------ |
| {ref}`Gunicorn <backend-gunicorn>`         | WSGI | Traditional Django, Linux production |
| {ref}`Waitress <backend-waitress>`         | WSGI | Windows, pure Python                 |
| {ref}`Granian WSGI <backend-granian-wsgi>` | WSGI | High performance (Rust)              |
| {ref}`Uvicorn ASGI <backend-uvicorn-asgi>` | ASGI | Async Django, WebSockets             |
| {ref}`Uvicorn WSGI <backend-uvicorn-wsgi>` | WSGI | Traditional with Uvicorn perf        |
| {ref}`Granian ASGI <backend-granian-asgi>` | ASGI | High-perf async (Rust)               |

### Background Workers

| Backend                                      | Best For                             |
| -------------------------------------------- | ------------------------------------ |
| {ref}`Celery Worker <backend-celery-worker>` | Distributed tasks, complex workflows |
| {ref}`Celery Beat <backend-celery-beat>`     | Scheduled/periodic tasks             |
| {ref}`Django Tasks <backend-django-tasks>`   | Simple tasks, no dependencies        |
| {ref}`Django-Q2 <backend-django-q2>`         | ORM-backed, admin interface          |

## Quick Comparison

| Backend      | Async | Windows | External Deps  |
| ------------ | ----- | ------- | -------------- |
| Gunicorn     | No    | Limited | None           |
| Waitress     | No    | Yes     | None           |
| Granian      | Both  | Yes     | None           |
| Uvicorn      | Yes   | Yes     | None           |
| Celery       | Yes   | Yes     | Redis/RabbitMQ |
| Django Tasks | Yes   | Yes     | None           |
| Django-Q2    | Yes   | Yes     | None           |

## ARGS Translation

All backends convert the `ARGS` dict to CLI arguments:

```python
"ARGS": {"bind": "0.0.0.0:8000", "workers": "4"}
# becomes: --bind=0.0.0.0:8000 --workers=4
```

See individual backend pages for specific ARGS options.
