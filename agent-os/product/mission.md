# Product Mission

## Pitch

Django prodserver is a production server management tool that helps Django developers and DevOps engineers start and manage production servers and background workers with a unified, consistent interface, regardless of the underlying server technology being used.

## Users

### Primary Customers

- **Django Developers**: Individual developers and development teams building Django applications that need simple, reliable production server management
- **DevOps Engineers**: Operations teams managing Django deployments across multiple projects and environments
- **System Administrators**: Infrastructure teams responsible for standardizing server management across their Django application portfolio

### User Personas

**Solo Django Developer** (25-40)

- **Role:** Full-stack developer working on side projects or small commercial applications
- **Context:** Building Django applications that need to be deployed to production, often managing multiple projects simultaneously
- **Pain Points:**
  - Each server backend (Gunicorn, Uvicorn, Waitress) has different command-line interfaces and configuration patterns
  - Switching between projects with different server backends requires remembering different commands
  - Setting up workers (Celery, Django Tasks) adds another layer of configuration complexity
  - Documentation and examples are scattered across different projects
- **Goals:**
  - Simple, consistent command to start any production server or worker
  - Easy to switch between server backends without rewriting deployment scripts
  - Minimal configuration required to get production-ready setup

**DevOps Engineer** (28-45)

- **Role:** Platform engineer managing Django deployments in containerized environments
- **Context:** Responsible for maintaining deployment pipelines and infrastructure for multiple Django applications across development, staging, and production environments
- **Pain Points:**
  - Each Django project uses different servers (Gunicorn, Uvicorn, Granian) with inconsistent startup commands
  - Dockerfile and deployment scripts need to be customized for each project's server choice
  - Difficulty standardizing logging, monitoring, and health checks across different server types
  - Worker management (Celery, Django-Q2) adds complexity to orchestration
- **Goals:**
  - Standardize server startup across all Django projects
  - Reduce duplication in Dockerfiles and deployment configurations
  - Simplify CI/CD pipelines with consistent interfaces
  - Easy integration with container orchestration platforms

**Enterprise System Administrator** (35-55)

- **Role:** Infrastructure architect managing large-scale Django deployments
- **Context:** Corporate environment with strict standards, compliance requirements, and multiple Django applications serving different business units
- **Pain Points:**
  - Need to enforce consistent server management practices across dozens of Django projects
  - Different teams choose different server backends, creating operational complexity
  - Difficult to implement company-wide standards when each project has custom startup scripts
  - Onboarding new team members requires training on multiple server configurations
- **Goals:**
  - Establish organization-wide standards for Django server management
  - Simplify documentation and training materials
  - Enable teams to experiment with different backends without operational disruption
  - Reduce maintenance burden across application portfolio

## The Problem

### Fragmented Production Server Ecosystem

Django developers face a fragmented ecosystem when deploying applications to production. Each production server (Gunicorn, Uvicorn, Granian, Waitress) and worker system (Celery, Django Tasks, Django-Q2) has its own unique command-line interface, configuration approach, and startup mechanism. This creates several critical problems:

**Inconsistent Interfaces**: A developer using Gunicorn might run `gunicorn myapp.wsgi:application --bind 0.0.0.0:8000`, while using Uvicorn requires `uvicorn myapp.asgi:application --host 0.0.0.0 --port 8000`. Background workers add even more variation: Celery uses `celery -A myapp worker`, while Django Tasks uses a different pattern entirely. This inconsistency means deployment scripts, Dockerfiles, and documentation must be rewritten when switching server backends.

**Configuration Sprawl**: Each server backend requires understanding its specific configuration format and options. Teams spend significant time reading documentation, troubleshooting startup issues, and maintaining backend-specific configuration files across projects.

**Operational Complexity**: DevOps teams managing multiple Django projects face a multiplicative complexity problem. With 10 projects using 5 different server backends, they must maintain expertise in all combinations, leading to increased operational burden, documentation overhead, and longer incident response times.

**Migration Friction**: When teams want to migrate from one server backend to another (for example, from Gunicorn to Granian for better performance), they must update deployment scripts, CI/CD pipelines, Dockerfiles, and documentation. This friction often prevents teams from adopting newer, better-performing server technologies.

**Our Solution:** Django prodserver provides a single, unified command interface for all production servers and workers. Instead of learning different commands for each backend, developers and operators use one consistent interface: `python manage.py prodserver web` for web servers and `python manage.py prodserver worker` for background workers. The backend choice becomes a simple configuration setting that can be changed without modifying deployment scripts or operational procedures. This dramatically reduces complexity, enables easy experimentation with different backends, and allows teams to standardize their deployment practices across all Django projects.

## Differentiators

### Unified Interface

Unlike traditional approaches where each server backend requires unique commands and startup scripts, Django prodserver provides a single, consistent interface. Developers configure their desired backend in Django settings and use the same `prodserver` command regardless of whether they're running Gunicorn, Uvicorn, Granian, or any other supported backend. This results in simplified deployment scripts, easier onboarding, and the flexibility to switch backends without operational disruption.

### Django-Native Integration

Unlike standalone server management tools or container orchestration solutions, Django prodserver integrates directly with Django's management command system. It understands Django's application structure, settings patterns, and conventions. This results in zero additional infrastructure requirements, familiar developer experience, and seamless integration with existing Django workflows.

### Extensible Backend Architecture

Unlike monolithic server solutions that lock you into a specific technology, Django prodserver provides a clean, well-documented backend API that makes it simple to add support for new servers or workers. The `BaseServerBackend` class requires implementing just one method (`start_server`), making it straightforward for teams to add custom backends or contribute new integrations to the community. This results in a growing ecosystem of supported backends and the ability to integrate organization-specific server technologies.

### Configuration-Driven Approach

Unlike deployment approaches that require writing custom startup scripts, Django prodserver uses Django's native settings system for configuration. All server and worker configurations live in `settings.py` using a consistent `PRODUCTION_PROCESSES` structure. This results in version-controlled configurations, environment-specific settings using Django's standard patterns, and elimination of scattered startup scripts throughout the codebase.

## Key Features

### Core Features

- **Unified Server Management**: Start any production server (Gunicorn, Granian, Uvicorn, Waitress) using a single consistent command `python manage.py prodserver web`. No need to remember backend-specific commands or flags.

- **Worker Process Management**: Launch background workers (Celery, Celery Beat, Django Tasks, Django-Q2) with the same unified interface: `python manage.py prodserver worker`. Consistent experience across all worker backends.

- **Settings-Based Configuration**: Configure all servers and workers through Django's familiar settings system using `PRODUCTION_PROCESSES`. All configuration is version-controlled and follows Django conventions.

- **Zero Infrastructure Requirements**: Works as a Django app with no external dependencies beyond your chosen server backend. No additional daemons, services, or orchestration tools required.

### Backend Support Features

- **Multiple WSGI Servers**: Native support for Gunicorn and Waitress for traditional Django WSGI applications, with consistent configuration and startup.

- **ASGI Server Support**: Full support for modern async servers including Uvicorn and Granian (both ASGI and WSGI modes) for async-capable Django applications.

- **High-Performance Options**: Includes support for Granian, a high-performance Rust-based server, enabling teams to achieve better performance without changing their deployment workflow.

- **Celery Integration**: Complete support for Celery workers and Celery Beat scheduler, supporting the most popular Django task queue solution.

- **Modern Worker Backends**: Support for Django Tasks and Django-Q2, giving teams flexibility to choose the worker backend that best fits their needs.

### Developer Experience Features

- **Consistent Argument Format**: All backend arguments are configured in a uniform dictionary format in settings, with automatic conversion to backend-specific command-line flags.

- **Easy Backend Switching**: Change server backends by modifying one line in settings. No need to update deployment scripts, Dockerfiles, or documentation.

- **Extensible Architecture**: Clean `BaseServerBackend` class makes it straightforward to add custom backends or contribute new integrations to the project.

- **Development Server Companion**: Includes a `devserver` command for local development that mirrors production configuration, ensuring consistency across environments.

### Advanced Features

- **Per-Process Configuration**: Define multiple named processes (web, worker, beat, etc.) each with their own backend and arguments, all managed through the same interface.

- **Environment-Specific Settings**: Leverage Django's settings system to use different server configurations across development, staging, and production environments.

- **Argument Customization**: Pass custom arguments to any backend through the uniform configuration format, maintaining full access to backend-specific features while keeping interface consistency.
