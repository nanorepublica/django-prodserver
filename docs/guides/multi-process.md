(guide-multi-process)=

# Multi-Process Deployment Guide

Learn how to run and manage multiple process types (web servers, workers, schedulers) simultaneously using systemd, Docker Compose, and process managers.

## Overview

Most production applications need multiple process types:
- **Web servers**: Handle HTTP requests
- **Workers**: Process background tasks
- **Beat schedulers**: Run periodic tasks
- **Additional services**: Cache, queue, database

This guide covers deploying and managing all these processes together.

## Process Management Options

### 1. systemd (Linux)

The standard init system for modern Linux distributions.

**Advantages:**
- Native to Linux
- Auto-restart on failure
- Dependency management
- Resource limits
- Logging to journald

### 2. Docker Compose

Container orchestration for multiple services.

**Advantages:**
- Cross-platform
- Isolated environments
- Easy scaling
- Portable configurations

### 3. Supervisor

Python-based process manager.

**Advantages:**
- Python-native
- Cross-platform
- Web UI for monitoring
- Simple configuration

## systemd Deployment

### Service Files

Create separate service files for each process:

#### Web Server Service

```ini
# /etc/systemd/system/myapp-web.service
[Unit]
Description=MyApp Web Server
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/myapp
Environment="PATH=/var/www/myapp/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=myproject.settings.prod"
ExecStart=/var/www/myapp/venv/bin/python manage.py prodserver web
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
LimitNOFILE=4096
MemoryLimit=2G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

#### Worker Service

```ini
# /etc/systemd/system/myapp-worker.service
[Unit]
Description=MyApp Celery Worker
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/myapp
Environment="PATH=/var/www/myapp/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=myproject.settings.prod"
ExecStart=/var/www/myapp/venv/bin/python manage.py prodserver worker
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
LimitNOFILE=4096
MemoryLimit=4G
CPUQuota=400%

[Install]
WantedBy=multi-user.target
```

#### Beat Scheduler Service

```ini
# /etc/systemd/system/myapp-beat.service
[Unit]
Description=MyApp Celery Beat Scheduler
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/myapp
Environment="PATH=/var/www/myapp/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=myproject.settings.prod"
ExecStart=/var/www/myapp/venv/bin/python manage.py prodserver beat
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Managing Services

```bash
# Reload systemd after creating/editing service files
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable myapp-web myapp-worker myapp-beat

# Start all services
sudo systemctl start myapp-web myapp-worker myapp-beat

# Check status
sudo systemctl status myapp-web
sudo systemctl status myapp-worker
sudo systemctl status myapp-beat

# View logs
sudo journalctl -u myapp-web -f
sudo journalctl -u myapp-worker -f

# Restart services
sudo systemctl restart myapp-web myapp-worker myapp-beat

# Stop services
sudo systemctl stop myapp-web myapp-worker myapp-beat
```

### systemd Target (Group Services)

Create a target to manage all services as a group:

```ini
# /etc/systemd/system/myapp.target
[Unit]
Description=MyApp All Services
Wants=myapp-web.service myapp-worker.service myapp-beat.service

[Install]
WantedBy=multi-user.target
```

```bash
# Enable the target
sudo systemctl enable myapp.target

# Start all services
sudo systemctl start myapp.target

# Stop all services
sudo systemctl stop myapp.target
```

## Docker Compose Deployment

### Complete Stack

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
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myapp"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - backend

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - backend

  web:
    build: .
    command: python manage.py prodserver web
    volumes:
      - ./staticfiles:/app/staticfiles
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=myproject.settings.prod
      - DATABASE_URL=postgres://myapp:${DB_PASSWORD}@db:5432/myapp
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - backend
      - frontend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  worker:
    build: .
    command: python manage.py prodserver worker
    environment:
      - DJANGO_SETTINGS_MODULE=myproject.settings.prod
      - DATABASE_URL=postgres://myapp:${DB_PASSWORD}@db:5432/myapp
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - backend
    deploy:
      replicas: 2  # Run 2 worker instances

  beat:
    build: .
    command: python manage.py prodserver beat
    environment:
      - DJANGO_SETTINGS_MODULE=myproject.settings.prod
      - DATABASE_URL=postgres://myapp:${DB_PASSWORD}@db:5432/myapp
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - backend
    deploy:
      replicas: 1  # Only 1 beat instance!

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./staticfiles:/staticfiles:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    restart: unless-stopped
    networks:
      - frontend

volumes:
  postgres_data:
  redis_data:

networks:
  frontend:
  backend:
```

### Managing Docker Compose

```bash
# Start all services
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f web
docker-compose logs -f worker

# Scale workers
docker-compose up -d --scale worker=4

# Restart services
docker-compose restart web worker

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Supervisor Deployment

Install Supervisor:

```bash
pip install supervisor
```

### Configuration

```ini
# /etc/supervisor/conf.d/myapp.conf

[program:myapp-web]
command=/var/www/myapp/venv/bin/python manage.py prodserver web
directory=/var/www/myapp
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/myapp/web.log
environment=DJANGO_SETTINGS_MODULE="myproject.settings.prod"

[program:myapp-worker]
command=/var/www/myapp/venv/bin/python manage.py prodserver worker
directory=/var/www/myapp
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/myapp/worker.log
environment=DJANGO_SETTINGS_MODULE="myproject.settings.prod"
numprocs=2
process_name=%(program_name)s_%(process_num)02d

[program:myapp-beat]
command=/var/www/myapp/venv/bin/python manage.py prodserver beat
directory=/var/www/myapp
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/myapp/beat.log
environment=DJANGO_SETTINGS_MODULE="myproject.settings.prod"

[group:myapp]
programs=myapp-web,myapp-worker,myapp-beat
```

### Managing Supervisor

```bash
# Update configuration
sudo supervisorctl reread
sudo supervisorctl update

# Start all
sudo supervisorctl start myapp:*

# Check status
sudo supervisorctl status

# Restart
sudo supervisorctl restart myapp:*

# Stop all
sudo supervisorctl stop myapp:*

# View logs
sudo supervisorctl tail -f myapp-web
```

## Process Configuration

### Django Settings

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "8",
            "timeout": "60",
        }
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": "8",
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

## Monitoring and Maintenance

### Health Checks

Create health check endpoints:

```python
# myapp/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        connection.ensure_connection()
        return JsonResponse({"status": "healthy"})
    except Exception as e:
        return JsonResponse({"status": "unhealthy"}, status=500)
```

### Log Aggregation

#### systemd journald

```bash
# View all logs
sudo journalctl -u myapp-web -u myapp-worker -u myapp-beat -f

# Filter by time
sudo journalctl -u myapp-web --since "1 hour ago"

# Export logs
sudo journalctl -u myapp-web -o json > web.log
```

#### Docker logs

```bash
# View all service logs
docker-compose logs -f

# Specific service
docker-compose logs -f web worker

# Follow with timestamps
docker-compose logs -f --timestamps
```

## Scaling Strategies

### Horizontal Scaling

**Web servers:**
```yaml
# Docker Compose
web:
  deploy:
    replicas: 4
```

**Workers:**
```yaml
worker:
  deploy:
    replicas: 8
```

### Vertical Scaling

Increase workers per process:

```python
"ARGS": {
    "workers": "16",       # More web workers
    "concurrency": "16",   # More task workers
}
```

## Best Practices

1. **One beat per application**: Only run ONE beat scheduler instance
2. **Health checks**: Implement health check endpoints for all services
3. **Graceful shutdown**: Allow processes time to finish current work
4. **Resource limits**: Set memory and CPU limits
5. **Log rotation**: Prevent log files from filling disk
6. **Monitoring**: Use tools like Prometheus, Grafana, or Sentry
7. **Alerting**: Set up alerts for process failures

## Troubleshooting

### Process Won't Start

```bash
# Check logs
sudo journalctl -u myapp-web -n 50

# Verify permissions
ls -la /var/www/myapp

# Test manually
sudo -u www-data /var/www/myapp/venv/bin/python manage.py prodserver web
```

### Process Keeps Restarting

```bash
# Check resource usage
systemctl status myapp-web

# View recent crashes
sudo journalctl -u myapp-web --since "10 minutes ago"
```

### Database Connection Issues

```bash
# Test database connectivity
python manage.py dbshell

# Check service dependencies
systemctl list-dependencies myapp-web
```

## Related Documentation

- {ref}`configuration-reference` - PRODUCTION_PROCESSES configuration
- {ref}`guide-docker` - Docker deployment
- {ref}`guide-environment-configs` - Environment configuration
- {ref}`backend-reference` - Backend documentation
- {ref}`troubleshooting` - Troubleshooting guide
