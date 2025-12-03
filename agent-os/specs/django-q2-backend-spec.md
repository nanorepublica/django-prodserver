# Django-Q2 Backend Specification

## Overview

Add Django-Q2 as an optional backend to django-prodserver, providing a consistent interface to start Django-Q2 task queue workers alongside existing server backends. Django-Q2 is a modern fork of Django-Q that provides multiprocessing distributed task queues with support for multiple brokers (Redis, ORM, SQS, MongoDB).

This integration will allow users to manage Django-Q2 workers using the same `prodserver` management command interface used for web servers and other worker processes.

## Requirements

### Functional Requirements

- **FR1**: Users can configure Django-Q2 workers in `PRODUCTION_PROCESSES` settings
- **FR2**: Workers start using `python manage.py prodserver worker` command
- **FR3**: Backend gracefully handles missing django-q2 dependency with clear error messages
- **FR4**: Support all `qcluster` command arguments through `ARGS` configuration
- **FR5**: Integration works with all Django-Q2 broker backends (Redis, ORM, SQS, MongoDB)
- **FR6**: Maintain compatibility with existing django-prodserver functionality

### Non-Functional Requirements

- **NFR1**: Performance impact should be minimal (no overhead when django-q2 not used)
- **NFR2**: Installation remains lightweight (django-q2 as optional dependency)
- **NFR3**: Error handling provides actionable guidance for configuration issues
- **NFR4**: Documentation covers common configuration patterns and troubleshooting

## Technical Design

### Architecture

The Django-Q2 backend follows the established pattern of other django-prodserver backends:

1. **DjangoQ2Worker Class**: Inherits from `BaseServerBackend`
2. **Management Command Integration**: Uses Django's `management.call_command()`
3. **Optional Dependency**: Uses graceful import handling
4. **Configuration Integration**: Leverages Django settings for Q_CLUSTER configuration

### Backend Implementation

```python
# src/django_prodserver/backends/django_q2.py
from django.core import management
from django.core.exceptions import ImproperlyConfigured

from .base import BaseServerBackend


class DjangoQ2Worker(BaseServerBackend):
    """Backend to start a Django-Q2 task queue worker."""

    def __init__(self, **server_config):
        try:
            import django_q
        except ImportError as e:
            raise ImproperlyConfigured(
                "django-q2 is required to use DjangoQ2Worker backend. "
                "Install it with: pip install django-q2"
            ) from e

        # Verify django_q is in INSTALLED_APPS
        from django.conf import settings
        if 'django_q' not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured(
                "Add 'django_q' to INSTALLED_APPS to use DjangoQ2Worker backend"
            )

        super().__init__(**server_config)

    def start_server(self, *args):
        """Start Django-Q2 cluster using qcluster management command."""
        management.call_command("qcluster", *args)

    def prep_server_args(self):
        """Prepare arguments for qcluster command."""
        args = super().prep_server_args()

        # Add any default arguments for qcluster if needed
        # Most configuration should be in Q_CLUSTER settings
        return args
```

### Configuration Examples

#### Basic Configuration

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'django_prodserver',
    'django_q',  # Required for Django-Q2
]

# Django-Q2 configuration
Q_CLUSTER = {
    'name': 'myproject',
    'workers': 4,
    'recycle': 500,
    'timeout': 60,
    'django_redis': 'default',
}

# Production processes configuration
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {"verbosity": 2},
    },
}
```

#### Advanced Configuration with Multiple Clusters

```python
# Multiple worker processes with different configurations
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000"},
    },
    "worker-high": {
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {"cluster-name": "high-priority"},
    },
    "worker-low": {
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {"cluster-name": "low-priority"},
    },
}
```

### Dependency Management

Update `pyproject.toml` to include django-q2 as optional dependency:

```toml
[project.optional-dependencies]
gunicorn = ["gunicorn>=23.0.0"]
django-tasks = ["django-tasks>=0.7.0"]
celery = ["celery>=5.5.2"]
django-q2 = ["django-q2>=1.6.0", "django-picklefield"]
uvicorn = ["uvicorn>=0.34.2"]
waitress = ["waitress>=3.0.2"]
```

### Error Handling

The backend implements comprehensive error handling:

1. **Missing django-q2**: Clear message with installation instructions
2. **Missing INSTALLED_APPS**: Guidance on adding 'django_q'
3. **Configuration errors**: Forward Django-Q2's built-in validation
4. **Runtime errors**: Preserve Django-Q2's error reporting

### Command Arguments Support

The backend supports all `qcluster` command arguments:

- `--cluster-name`: Specify cluster name
- `--verbosity`: Control logging verbosity
- `--settings`: Override Django settings module
- Any other arguments passed through transparently

## Implementation Plan

### Phase 1: Core Backend Implementation

**Tasks:**

1. Create `DjangoQ2Worker` backend class
2. Implement graceful import handling and error messages
3. Add django-q2 optional dependency to pyproject.toml
4. Create basic unit tests for backend initialization
5. Test integration with `qcluster` command

**Acceptance Criteria:**

- Backend can be imported without django-q2 installed (with clear error on use)
- Backend successfully starts qcluster when properly configured
- All configuration errors provide actionable error messages
- Basic functionality tests pass

**Estimated Effort:** 1 day

### Phase 2: Documentation and Examples

**Tasks:**

1. Update README.md with django-q2 configuration examples
2. Add django-q2 section to existing documentation
3. Document common configuration patterns
4. Create troubleshooting guide
5. Add integration tests with different broker configurations

**Acceptance Criteria:**

- README includes django-q2 examples alongside other backends
- Documentation covers installation, basic and advanced configuration
- Troubleshooting guide addresses common setup issues
- Integration tests verify functionality with ORM and Redis brokers

**Estimated Effort:** 1 day

### Phase 3: Testing and Validation

**Tasks:**

1. Create comprehensive test suite for django-q2 backend
2. Test with different Django-Q2 broker configurations
3. Validate error handling and edge cases
4. Performance testing to ensure no overhead when unused
5. Compatibility testing with different Django versions

**Acceptance Criteria:**

- Test coverage >90% for new backend code
- Tests pass with Redis, ORM, and mock brokers
- Error conditions properly tested and documented
- No performance regression in existing functionality
- Compatible with supported Django versions

**Estimated Effort:** 1 day

## Testing Strategy

### Unit Tests

```python
# tests/backends/test_django_q2.py
import pytest
from django.core.exceptions import ImproperlyConfigured
from unittest.mock import patch, MagicMock

class TestDjangoQ2Worker:
    def test_import_error_handling(self):
        """Test graceful handling when django-q2 not installed."""
        with patch('django_prodserver.backends.django_q2.import_string') as mock_import:
            mock_import.side_effect = ImportError("No module named 'django_q'")

            with pytest.raises(ImproperlyConfigured) as exc_info:
                DjangoQ2Worker()

            assert "django-q2 is required" in str(exc_info.value)
            assert "pip install django-q2" in str(exc_info.value)

    def test_missing_installed_apps(self):
        """Test error when django_q not in INSTALLED_APPS."""
        with patch('django_prodserver.backends.django_q2.settings') as mock_settings:
            mock_settings.INSTALLED_APPS = []

            with pytest.raises(ImproperlyConfigured) as exc_info:
                DjangoQ2Worker()

            assert "Add 'django_q' to INSTALLED_APPS" in str(exc_info.value)

    @patch('django_prodserver.backends.django_q2.management.call_command')
    def test_start_server(self, mock_call_command):
        """Test qcluster command is called correctly."""
        worker = DjangoQ2Worker()
        worker.start_server("--verbosity", "2")

        mock_call_command.assert_called_once_with("qcluster", "--verbosity", "2")
```

### Integration Tests

```python
# tests/integration/test_django_q2_integration.py
@pytest.mark.django_db
class TestDjangoQ2Integration:
    def test_worker_starts_with_orm_broker(self):
        """Test worker starts successfully with ORM broker."""
        # Test with Q_CLUSTER configured for ORM broker

    def test_worker_with_custom_args(self):
        """Test worker accepts custom arguments."""
        # Test ARGS configuration passes through correctly
```

### Manual Testing Scenarios

1. **Fresh Installation**: Test setup process from scratch
2. **Migration Testing**: Test upgrading from version without django-q2 support
3. **Configuration Validation**: Test various Q_CLUSTER configurations
4. **Error Recovery**: Test behavior when Q_CLUSTER misconfigured

## Documentation Updates

### README.md Changes

Add django-q2 example to the configuration section:

```python
PRODUCTION_PROCESSES = {
    # ... existing examples
    "worker": {
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {"verbosity": 2},
    },
    # "worker": {
    #     "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
    #     "APP": "tests.celery.app",
    #     "ARGS": {},
    # },
}
```

### Installation Documentation

Add django-q2 installation instructions:

```bash
# Install django-prodserver with django-q2 support
pip install django-prodserver[django-q2]

# Or install separately
pip install django-prodserver django-q2
```

### Configuration Guide

Document Q_CLUSTER configuration requirements and common patterns.

## Migration/Compatibility

### Backward Compatibility

- No breaking changes to existing functionality
- Django-Q2 backend is purely additive
- Existing configurations continue to work unchanged
- Optional dependency ensures minimal impact

### Migration from Standalone Django-Q2

Users already using Django-Q2 can easily migrate:

1. Install django-prodserver
2. Add backend configuration to PRODUCTION_PROCESSES
3. Replace `python manage.py qcluster` with `python manage.py prodserver worker`
4. Existing Q_CLUSTER configuration remains unchanged

### Version Compatibility

- Django-Q2: >=1.6.0 (latest stable)
- Django: >=4.2 (matching django-prodserver requirements)
- Python: >=3.9 (matching django-prodserver requirements)

## Risks and Mitigation

### Risk 1: Django-Q2 API Changes

**Impact:** High - Backend could break with django-q2 updates
**Probability:** Low - Django-Q2 has stable API
**Mitigation:**

- Pin to known-good django-q2 versions in optional dependencies
- Comprehensive test suite to catch API changes
- Monitor django-q2 releases for breaking changes

### Risk 2: Import Conflicts

**Impact:** Medium - Conflicts between django-q and django-q2
**Probability:** Low - Django-Q2 replaced django-q completely
**Mitigation:**

- Clear documentation about using django-q2 vs django-q
- Explicit error messages if both packages detected
- Test with both packages in CI if needed

### Risk 3: Configuration Complexity

**Impact:** Medium - Users struggle with Q_CLUSTER setup
**Probability:** Medium - Django-Q2 has many configuration options
**Mitigation:**

- Comprehensive documentation with examples
- Clear error messages for common misconfigurations
- Troubleshooting guide for setup issues
- Support for minimal configurations

### Risk 4: Performance Impact

**Impact:** Low - Import overhead even when unused
**Probability:** Low - Lazy import handling prevents this
**Mitigation:**

- Lazy imports only when backend is instantiated
- Performance tests to verify no overhead
- Benchmark against existing backends

## Success Metrics

### Functionality Metrics

- Backend successfully starts django-q2 workers
- All qcluster command arguments supported
- Error handling provides actionable guidance
- Integration tests pass with multiple broker types

### Code Quality Metrics

- Test coverage >90% for new code
- No performance regression in existing functionality
- Documentation completeness score >95%
- Zero critical security vulnerabilities

### User Experience Metrics

- Installation success rate >95%
- Configuration error resolution time <5 minutes
- User satisfaction with documentation quality
- Integration time for existing django-q2 users <30 minutes

## Future Enhancements

### Phase 4: Advanced Integration (Future)

1. **Multiple Cluster Support**: Enhanced configuration for running multiple named clusters
2. **Health Monitoring**: Integration with django-prodserver monitoring features
3. **Auto-scaling**: Dynamic worker scaling based on queue depth
4. **Metrics Integration**: Export django-q2 metrics to monitoring systems
5. **Development Tools**: Enhanced development mode support with auto-restart

### Potential Add-ons

- **django-q2-admin**: Enhanced admin interface integration
- **django-q2-metrics**: Prometheus/StatsD metrics export
- **django-q2-scaling**: Kubernetes-based auto-scaling support

These enhancements would be separate features, maintaining the simplicity of the core integration.
