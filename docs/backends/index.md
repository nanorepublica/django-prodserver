(backend-reference)=

# Backend Reference

django-prodserver supports multiple production-ready server backends for WSGI/ASGI applications and background workers. Each backend is configured using the `PRODUCTION_PROCESSES` setting in your Django settings file.

## Available Backends

### WSGI Servers

WSGI servers are used for traditional synchronous Django applications.

- **{ref}`backend-gunicorn`** - Industry-standard WSGI server, mature and battle-tested
- **{ref}`backend-waitress`** - Pure Python WSGI server with excellent Windows support
- **{ref}`backend-granian-wsgi`** - Modern Rust-based high-performance WSGI server

### ASGI Servers

ASGI servers are used for asynchronous Django applications with WebSocket and async support.

- **{ref}`backend-uvicorn-asgi`** - Popular ASGI server built on uvloop
- **{ref}`backend-uvicorn-wsgi`** - Uvicorn running in WSGI compatibility mode
- **{ref}`backend-granian-asgi`** - Modern Rust-based high-performance ASGI server

### Background Workers

Background workers handle asynchronous tasks and scheduled jobs.

- **{ref}`backend-celery-worker`** - Industry-standard distributed task queue
- **{ref}`backend-celery-beat`** - Celery scheduler for periodic tasks
- **{ref}`backend-django-tasks`** - Django's built-in lightweight task system
- **{ref}`backend-django-q2`** - Django ORM-backed task queue

## Backend Comparison

| Backend | Type | Async Support | Windows Support | External Dependencies |
|---------|------|---------------|-----------------|----------------------|
| Gunicorn | WSGI | No | Limited | None |
| Waitress | WSGI | No | Excellent | None |
| Granian (WSGI) | WSGI | No | Yes | None |
| Uvicorn (ASGI) | ASGI | Yes | Yes | None |
| Uvicorn (WSGI) | WSGI | No | Yes | None |
| Granian (ASGI) | ASGI | Yes | Yes | None |
| Celery | Worker | Yes | Yes | Message Broker (Redis/RabbitMQ) |
| Django Tasks | Worker | Yes | Yes | None |
| Django-Q2 | Worker | Yes | Yes | None |

## How ARGS Translation Works

All backends use the `ARGS` dictionary in `PRODUCTION_PROCESSES` to pass configuration to the underlying server. The framework automatically converts dictionary keys to command-line arguments:

```python
# In settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "4",
            "timeout": "30"
        }
    }
}
```

This translates to CLI arguments:
```bash
gunicorn --bind=0.0.0.0:8000 --workers=4 --timeout=30
```

Each backend page provides specific examples and ARGS reference tables.

## Choosing the Right Backend

**For traditional Django apps:**
- Use **Gunicorn** for production-ready WSGI serving on Linux
- Use **Waitress** if you need Windows compatibility
- Use **Granian WSGI** for maximum performance

**For async Django apps:**
- Use **Uvicorn ASGI** for WebSocket and async view support
- Use **Granian ASGI** for high-performance async applications

**For background tasks:**
- Use **Celery** for complex distributed task processing
- Use **Django Tasks** for simple in-process task queues
- Use **Django-Q2** for ORM-backed task queues

## Next Steps

- See {ref}`installation` for setup instructions
- Read {ref}`guide-quickstart` for a beginner-friendly tutorial
- Explore individual backend pages for detailed configuration options
