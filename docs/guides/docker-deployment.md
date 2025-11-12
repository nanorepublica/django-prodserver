(guide-docker)=

# Docker Deployment Guide

Learn how to deploy django-prodserver applications using Docker and Docker Compose with production-ready configurations, multi-stage builds, and best practices.

## Overview

This guide covers:
- Creating Dockerfiles for django-prodserver applications
- Multi-stage builds for optimized images
- Docker Compose for multi-container deployments
- Environment configuration with Docker
- Best practices for container security and performance

## Prerequisites

- Docker installed on your system
- Docker Compose (usually included with Docker Desktop)
- Basic familiarity with Docker concepts
- A Django project configured with django-prodserver

## Basic Dockerfile

### Simple Single-Stage Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "manage.py", "prodserver", "web"]
```

### Build and Run

```bash
# Build image
docker build -t myapp:latest .

# Run container
docker run -p 8000:8000 myapp:latest
```

## Multi-Stage Dockerfile (Recommended)

Multi-stage builds create smaller, more secure images:

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install wheels
RUN pip install --upgrade pip && \
    pip install --no-cache /wheels/*

# Copy project files
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["python", "manage.py", "prodserver", "web"]
```

**Benefits:**
- Smaller image size (no build tools in final image)
- Better security (minimal attack surface)
- Faster deployments (smaller images)

## Docker Compose Setup

### Basic Web + Database

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=myapp
      - POSTGRES_PASSWORD=changeme
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myapp"]
      interval: 5s
      timeout: 5s
      retries: 5

  web:
    build: .
    command: python manage.py prodserver web
    volumes:
      - ./staticfiles:/app/staticfiles
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://myapp:changeme@db:5432/myapp
      - DEBUG=False
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
```

Start services:
```bash
docker-compose up -d
```

### Complete Stack (Web + Worker + Beat)

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=myapp
      - POSTGRES_PASSWORD=changeme

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  web:
    build: .
    command: python manage.py prodserver web
    volumes:
      - ./staticfiles:/app/staticfiles
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://myapp:changeme@db:5432/myapp
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  worker:
    build: .
    command: python manage.py prodserver worker
    environment:
      - DATABASE_URL=postgres://myapp:changeme@db:5432/myapp
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  beat:
    build: .
    command: python manage.py prodserver beat
    environment:
      - DATABASE_URL=postgres://myapp:changeme@db:5432/myapp
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
```

## Django Configuration for Docker

### Using Environment Variables

```python
# settings.py
import os
from pathlib import Path

# Read from environment
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

# Database from DATABASE_URL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'myapp'),
        'USER': os.getenv('POSTGRES_USER', 'myapp'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', 'db'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# Celery from CELERY_BROKER_URL
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')

# Production processes
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": os.getenv('WEB_WORKERS', '4'),
        }
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": os.getenv('WORKER_CONCURRENCY', '4'),
        }
    },
    "beat": {
        "BACKEND": "django_prodserver.backends.celery.CeleryBeat",
        "APP": "myproject.celery.app",
        "ARGS": {}
    }
}
```

## Environment Variables with .env File

### Development .env

```bash
# .env.dev
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=myapp_dev
POSTGRES_USER=myapp
POSTGRES_PASSWORD=devpassword
CELERY_BROKER_URL=redis://localhost:6379/0
WEB_WORKERS=2
WORKER_CONCURRENCY=2
```

### Production .env

```bash
# .env.prod
DEBUG=False
ALLOWED_HOSTS=example.com,www.example.com
POSTGRES_DB=myapp_prod
POSTGRES_USER=myapp
POSTGRES_PASSWORD=strongpassword
CELERY_BROKER_URL=redis://redis:6379/0
WEB_WORKERS=8
WORKER_CONCURRENCY=8
SECRET_KEY=your-secret-key-here
```

### Use with Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    env_file:
      - .env.prod
    # ... rest of config
```

## Initialization and Migrations

### Entrypoint Script

Create an entrypoint script to handle initialization:

```bash
#!/bin/bash
# entrypoint.sh

set -e

# Wait for database
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if needed
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py createsuperuser \
        --noinput \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL || true
fi

# Execute CMD
exec "$@"
```

Update Dockerfile:

```dockerfile
# ... rest of Dockerfile

# Copy entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "prodserver", "web"]
```

## Health Checks

### Django Health Check Endpoint

```python
# myapp/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        # Check database
        connection.ensure_connection()
        return JsonResponse({"status": "healthy"})
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=500)
```

### Docker Compose Health Check

```yaml
services:
  web:
    build: .
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Production Best Practices

### 1. Use Non-Root User

```dockerfile
# Create and use non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser
```

### 2. Optimize Layer Caching

```dockerfile
# Install dependencies first (changes less often)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Then copy code (changes more often)
COPY . .
```

### 3. Use .dockerignore

```
# .dockerignore
**/__pycache__
**/*.pyc
**/*.pyo
.git
.gitignore
.env
.venv
venv/
*.md
docs/
tests/
.pytest_cache
.coverage
htmlcov/
node_modules/
```

### 4. Security Scanning

```bash
# Scan for vulnerabilities
docker scan myapp:latest
```

### 5. Resource Limits

```yaml
services:
  web:
    build: .
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker-compose logs web
docker logs container_name
```

### Database Connection Issues

**Ensure database is ready:**
```yaml
depends_on:
  db:
    condition: service_healthy
```

### Permission Denied Errors

**Fix ownership:**
```dockerfile
RUN chown -R appuser:appuser /app
USER appuser
```

### Static Files Not Found

**Ensure collectstatic runs:**
```dockerfile
RUN python manage.py collectstatic --noinput
```

## Deployment Platforms

### Deploy to Fly.io

```toml
# fly.toml
app = "myapp"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"
```

### Deploy to Railway

```json
// railway.json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "python manage.py prodserver web",
    "healthcheckPath": "/health/"
  }
}
```

### Deploy to AWS ECS

Use Docker Compose integration:
```bash
docker compose up
docker context create ecs myapp-context
docker context use myapp-context
docker compose up
```

## Complete Example

See the [example directory](https://github.com/nanorepublica/django-prodserver/tree/main/examples/docker) for a complete working example with:
- Multi-stage Dockerfile
- Docker Compose with all services
- Environment configuration
- Health checks
- Nginx reverse proxy

## Next Steps

- {ref}`guide-environment-configs` - Environment-specific configuration
- {ref}`guide-multi-process` - Running multiple processes
- {ref}`backend-reference` - Explore different backends
- {ref}`troubleshooting` - Common issues and solutions
