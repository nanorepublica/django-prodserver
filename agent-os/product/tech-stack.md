# Tech Stack

## Core Framework

### Python
- **Version**: 3.9+
- **Purpose**: Primary programming language
- **Rationale**: Provides broad compatibility while supporting modern type hints and language features

### Django
- **Version**: 4.2+
- **Purpose**: Web framework and integration point
- **Rationale**: Core dependency that defines the management command interface and settings system used throughout the project

## Production Server Backends

### Gunicorn
- **Version**: 23.0.0+
- **Purpose**: WSGI HTTP server for Python web applications
- **Optional Dependency**: Installed via `django-prodserver[gunicorn]`
- **Use Case**: Traditional synchronous Django applications, most common production deployment

### Granian
- **Version**: 1.0.0+
- **Purpose**: High-performance Rust-based HTTP server supporting both ASGI and WSGI
- **Optional Dependency**: Installed via `django-prodserver[granian]`
- **Use Case**: High-throughput applications requiring maximum performance

### Uvicorn
- **Version**: 0.34.2+
- **Purpose**: Lightning-fast ASGI server implementation
- **Optional Dependency**: Installed via `django-prodserver[uvicorn]`
- **Use Case**: Async Django applications using ASGI capabilities

### Waitress
- **Version**: 3.0.2+
- **Purpose**: Pure-Python WSGI server with good Windows support
- **Optional Dependency**: Installed via `django-prodserver[waitress]`
- **Use Case**: Cross-platform deployments, especially Windows environments

## Background Worker Backends

### Celery
- **Version**: 5.5.2+
- **Purpose**: Distributed task queue for background job processing
- **Optional Dependency**: Installed via `django-prodserver[celery]`
- **Use Case**: Complex task workflows, scheduled tasks, distributed processing

### Django Tasks
- **Version**: 0.7.0+
- **Purpose**: Lightweight background task processor for Django
- **Optional Dependency**: Installed via `django-prodserver[django-tasks]`
- **Use Case**: Simple background tasks without external dependencies

### Django-Q2
- **Version**: 1.6.0+
- **Purpose**: Multiprocessing task queue for Django
- **Optional Dependency**: Installed via `django-prodserver[django-q2]` (includes django-picklefield)
- **Use Case**: Task queuing with Django ORM backend, no external broker required

## Testing & Quality Assurance

### pytest
- **Version**: 8.x
- **Purpose**: Testing framework
- **Rationale**: Modern, powerful testing framework with excellent Django support

### pytest-django
- **Version**: 4.5+
- **Purpose**: Django integration for pytest
- **Rationale**: Provides Django-specific fixtures and test database management

### pytest-cov
- **Version**: 6.x
- **Purpose**: Coverage reporting
- **Rationale**: Tracks test coverage and generates reports for quality monitoring

### Codecov
- **Purpose**: Code coverage tracking and reporting
- **Integration**: CI/CD pipeline uploads coverage reports
- **Rationale**: Provides visibility into test coverage trends

### mypy
- **Purpose**: Static type checking
- **Configuration**: Strict type checking enabled for source code
- **Rationale**: Catches type errors before runtime, improves code quality and IDE support

## Code Quality & Formatting

### Ruff
- **Purpose**: Fast Python linter and formatter (replaces multiple tools)
- **Configuration**: Includes flake8-bugbear, flake8-docstrings, pyupgrade, isort, and more
- **Rationale**: Single tool that replaces Black, isort, flake8, and several plugins with significantly better performance

### pre-commit
- **Purpose**: Git hook management
- **Configuration**: Runs linters, formatters, and checks before commits
- **Rationale**: Ensures code quality standards before code enters version control

### commitlint
- **Purpose**: Commit message validation
- **Configuration**: Enforces conventional commit format
- **Rationale**: Maintains consistent commit history for automated changelog generation

### codespell
- **Purpose**: Spell checking for source code
- **Rationale**: Catches typos in code, comments, and documentation

### EditorConfig
- **Purpose**: Editor configuration standardization
- **Rationale**: Ensures consistent formatting across different editors and IDEs

## Documentation

### Sphinx
- **Version**: 4+
- **Purpose**: Documentation generation
- **Rationale**: Industry-standard Python documentation tool with extensive ecosystem

### Furo
- **Version**: 2023.5.20+
- **Purpose**: Modern Sphinx theme
- **Rationale**: Clean, responsive design with excellent user experience

### MyST Parser
- **Version**: 0.16+
- **Purpose**: Markdown support in Sphinx
- **Rationale**: Allows writing documentation in Markdown instead of reStructuredText

### ReadTheDocs
- **Purpose**: Documentation hosting
- **Integration**: Automatic builds on commits
- **Rationale**: Free hosting with version management for open source projects

## Build & Distribution

### setuptools
- **Purpose**: Python package building
- **Rationale**: Standard Python packaging tool with broad compatibility

### uv
- **Purpose**: Modern Python package installer and resolver
- **Rationale**: Extremely fast dependency resolution and installation, used in CI/CD

### python-semantic-release
- **Purpose**: Automated versioning and changelog generation
- **Configuration**: Reads conventional commits to determine version bumps
- **Rationale**: Automates release process based on commit history

## CI/CD

### GitHub Actions
- **Purpose**: Continuous integration and deployment
- **Workflows**: Test execution, coverage reporting, automated releases
- **Rationale**: Native GitHub integration with excellent ecosystem

### Just
- **Purpose**: Command runner (modern Make alternative)
- **Configuration**: justfile defines common development tasks
- **Rationale**: Simple, consistent interface for development tasks

### Renovate
- **Purpose**: Automated dependency updates
- **Configuration**: Monitors and creates PRs for dependency updates
- **Rationale**: Keeps dependencies current with minimal manual effort

## Development Tools

### Tox
- **Purpose**: Test automation across multiple Python versions
- **Configuration**: Tests against supported Python and Django versions
- **Rationale**: Ensures compatibility across supported version matrix

### Copier
- **Purpose**: Project template management
- **Template**: browniebroke/pypackage-template
- **Rationale**: Maintains consistent project structure and best practices

### Gitpod
- **Purpose**: Cloud development environment
- **Configuration**: Pre-configured environment for contributors
- **Rationale**: Reduces friction for new contributors

## Version Control

### Git
- **Purpose**: Source code management
- **Platform**: GitHub
- **Branch Strategy**: Main branch with feature branches

### GitHub Features
- **Issues**: Bug tracking and feature requests
- **Pull Requests**: Code review workflow
- **Releases**: Automated release management
- **Actions**: CI/CD automation

## Language Features & Standards

### Type Hints
- **Usage**: Comprehensive type hints throughout codebase
- **Checking**: mypy with strict configuration
- **Rationale**: Improves code quality, IDE support, and documentation

### Python Version Support
- **Minimum**: Python 3.9
- **Tested**: Python 3.12, 3.13
- **Rationale**: Balances modern features with broad compatibility

### Django Version Support
- **Minimum**: Django 4.2 LTS
- **Tested**: Django 5.2
- **Rationale**: Supports current LTS and latest stable versions
