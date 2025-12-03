# Feature Specification: Granian Server Backend

## Overview

Add Granian server as a new backend option for django-prodserver. Granian is a Rust-based HTTP server for Python applications that supports ASGI, WSGI, and RSGI interfaces with superior performance characteristics compared to traditional Python-based servers.

## Motivation

- **Performance**: Granian demonstrates superior performance metrics (50k req/s vs Uvicorn's 45k, Gunicorn's 10k in benchmarks)
- **Memory Efficiency**: Lower memory footprint (~15MB per worker vs Uvicorn's 20MB, Gunicorn's 30MB)
- **Modern Protocol Support**: Native HTTP/1, HTTP/2, and WebSocket support
- **Flexibility**: Supports both ASGI and WSGI interfaces in a single server
- **Production Ready**: Rust-based implementation provides stability and performance for production workloads

## Technical Specification

### 1. Dependencies

**Package**: `granian>=1.0.0`

**Python Requirements**:

- Python >= 3.9 (already satisfied by project's >= 3.9 requirement)

**Optional Dependencies**:

- `granian[reload]` - for auto-reload functionality (development)
- `granian[uvloop]` - for uvloop event loop support

### 2. Architecture

#### 2.1 Backend Implementation

Create two backend classes following the existing pattern:

1. **GranianASGIServer** - For ASGI applications (default)
2. **GranianWSGIServer** - For WSGI applications

Both will inherit from `BaseServerBackend` and follow the established pattern used by Uvicorn and Gunicorn backends.

#### 2.2 File Structure

```
src/django_prodserver/backends/
├── granian.py              # New backend implementation
└── ...

tests/backends/
├── test_granian.py         # New test file
└── ...
```

### 3. Implementation Details

#### 3.1 GranianASGIServer Class

**Location**: `src/django_prodserver/backends/granian.py`

**Responsibilities**:

- Import and configure Granian's ASGI interface
- Prepare arguments for ASGI application serving
- Start Granian server with ASGI interface

**Key Methods**:

- `__init__(**server_args)`: Initialize with server arguments
- `prep_server_args() -> list[str]`: Format arguments for Granian CLI
- `start_server(*args)`: Launch Granian with ASGI interface

**Granian Invocation**:
Granian provides a CLI interface that should be invoked programmatically. The implementation should use `granian.server.Granian` class or CLI runner.

#### 3.2 GranianWSGIServer Class

**Location**: `src/django_prodserver/backends/granian.py`

**Responsibilities**:

- Import and configure Granian's WSGI interface
- Prepare arguments for WSGI application serving
- Start Granian server with WSGI interface

**Key Methods**: Same as ASGI variant with WSGI-specific interface

#### 3.3 Argument Handling

The backend must support common Granian CLI arguments through the `ARGS` configuration:

**Core Arguments**:

- `interface`: `asgi` or `wsgi` (auto-set by backend class)
- `host`: Bind host address (e.g., "0.0.0.0")
- `port`: Bind port number (e.g., 8000)
- `workers`: Number of worker processes
- `threads`: Number of blocking threads per worker
- `threading-mode`: Threading mode (`runtime` or `workers`)
- `backlog`: Maximum connections in backlog
- `http`: HTTP version (`1`, `2`, or `auto`)
- `log-level`: Logging level (`critical`, `error`, `warning`, `info`, `debug`)
- `reload`: Enable auto-reload (development only)

**SSL Arguments**:

- `ssl-keyfile`: Path to SSL key file
- `ssl-certificate`: Path to SSL certificate file

**Advanced Arguments**:

- `url-path-prefix`: URL path prefix for mounted apps
- `ws/no-ws`: WebSocket support toggle
- `loop`: Event loop implementation (`auto`, `asyncio`, `uvloop`)

**Argument Formatting**:

- Use base class `_format_server_args_from_dict()` method
- Granian expects arguments in format: `--arg=value` or `--arg value`
- Boolean flags: `--ws` or `--no-ws`

#### 3.4 Application Target

- **ASGI**: Use `asgi_app_name()` utility function to get `settings.ASGI_APPLICATION`
- **WSGI**: Use `wsgi_app_name()` utility function to get `settings.WSGI_APPLICATION`

Format: `module:application` (e.g., `myproject.asgi:application`)

### 4. Configuration Examples

#### 4.1 ASGI Configuration

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "workers": "4",
            "threads": "1",
            "http": "auto",
            "log-level": "info",
        },
    },
}
```

#### 4.2 WSGI Configuration

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.granian.GranianWSGIServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "workers": "4",
            "threads": "2",
            "backlog": "2048",
        },
    },
}
```

#### 4.3 Development Configuration with Auto-reload

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
        "ARGS": {
            "host": "127.0.0.1",
            "port": "8000",
            "reload": "true",
            "log-level": "debug",
        },
    },
}
```

### 5. Testing Strategy

#### 5.1 Unit Tests

**File**: `tests/backends/test_granian.py`

**Test Coverage**:

1. **Initialization Tests**:

   - Test `GranianASGIServer` initialization without args
   - Test `GranianASGIServer` initialization with args
   - Test `GranianWSGIServer` initialization without args
   - Test `GranianWSGIServer` initialization with args

2. **Argument Preparation Tests**:

   - Test `prep_server_args()` returns correct format for ASGI
   - Test `prep_server_args()` returns correct format for WSGI
   - Test argument formatting with various combinations
   - Test boolean flag handling (--ws, --no-ws)
   - Test interface flag is correctly set

3. **Server Start Tests**:

   - Mock Granian server start for ASGI
   - Mock Granian server start for WSGI
   - Verify correct application target is passed
   - Verify all args are properly formatted

4. **Inheritance Tests**:

   - Verify both classes inherit from `BaseServerBackend`
   - Test base class functionality works correctly

5. **Edge Cases**:
   - Empty args handling
   - String args handling (base class functionality)
   - Complex nested argument structures

#### 5.2 Integration Tests

- Manual testing with sample Django project
- Verify server starts correctly
- Verify requests are handled properly
- Verify graceful shutdown

### 6. Documentation Updates

#### 6.1 README.md

Add Granian examples to the configuration section:

```python
# ASGI variant
"web": {
    "BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
    "ARGS": {"host": "0.0.0.0", "port": "8000", "workers": "4"},
},

# WSGI variant
"web": {
    "BACKEND": "django_prodserver.backends.granian.GranianWSGIServer",
    "ARGS": {"host": "0.0.0.0", "port": "8000", "workers": "4"},
},
```

#### 6.2 pyproject.toml

Add optional dependency:

```toml
[project.optional-dependencies]
granian = ["granian>=1.0.0"]
```

#### 6.3 docs/usage.md

Add comprehensive Granian backend documentation:

- Overview of Granian capabilities
- When to use ASGI vs WSGI variant
- Common configuration patterns
- Performance tuning recommendations
- SSL/TLS configuration examples

### 7. Implementation Approach

Granian can be invoked in two ways:

**Option A: Programmatic API** (Recommended)

```python
from granian import Granian

server = Granian(
    target="myapp.asgi:application",
    address="0.0.0.0",
    port=8000,
    interface="asgi",
    workers=4,
)
server.serve()
```

**Option B: CLI Runner**

```python
from granian.cli import main as granian_main

# Invoke with sys.argv or direct args
granian_main(["--interface", "asgi", "myapp.asgi:application"])
```

**Recommendation**: Use **Option A** (Programmatic API) if available, as it provides:

- Better Python integration
- Easier argument handling
- More explicit control
- Cleaner testing

If Option A is not feasible, use **Option B** following the pattern established by Uvicorn and Gunicorn backends.

### 8. Error Handling

- Handle missing `granian` dependency gracefully with `pytest.importorskip()` in tests
- Provide clear error messages if Granian is not installed
- Validate interface type during initialization
- Handle invalid argument combinations

### 9. Backward Compatibility

- No breaking changes to existing backends
- Follows established backend interface pattern
- Uses existing utility functions (`asgi_app_name()`, `wsgi_app_name()`)
- Optional dependency (doesn't affect users not using Granian)

### 10. Migration Path

Users can migrate from existing backends:

**From Gunicorn (WSGI)**:

```python
# Before
"BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
"ARGS": {"bind": "0.0.0.0:8000", "workers": "4"},

# After
"BACKEND": "django_prodserver.backends.granian.GranianWSGIServer",
"ARGS": {"host": "0.0.0.0", "port": "8000", "workers": "4"},
```

**From Uvicorn (ASGI)**:

```python
# Before
"BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
"ARGS": {"host": "0.0.0.0", "port": "8000"},

# After
"BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
"ARGS": {"host": "0.0.0.0", "port": "8000", "workers": "4"},
```

## Task Breakdown

### Phase 1: Core Implementation

1. Create `src/django_prodserver/backends/granian.py`
2. Implement `GranianASGIServer` class
3. Implement `GranianWSGIServer` class
4. Add proper imports and error handling

### Phase 2: Testing

5. Create `tests/backends/test_granian.py`
6. Implement initialization tests
7. Implement argument preparation tests
8. Implement server start tests (with mocking)
9. Implement inheritance tests
10. Implement edge case tests

### Phase 3: Configuration

11. Update `pyproject.toml` to add optional dependency
12. Verify CI/linting configuration compatibility

### Phase 4: Documentation

13. Update README.md with Granian examples
14. Update docs/usage.md with detailed Granian documentation
15. Update docs/installation.md if needed

### Phase 5: Quality Assurance

16. Run full test suite
17. Run linting and type checking
18. Manual integration testing
19. Performance benchmarking (optional)
20. Review and finalize

## Success Criteria

- [ ] Granian ASGI backend works with Django ASGI applications
- [ ] Granian WSGI backend works with Django WSGI applications
- [ ] All tests pass with 100% coverage for new code
- [ ] Linting and type checking pass
- [ ] Documentation is complete and accurate
- [ ] CI pipeline passes
- [ ] Manual testing confirms functionality

## Non-Goals

- Performance optimization beyond standard Granian configuration
- Custom Granian features beyond standard CLI arguments
- RSGI interface support (Granian-specific, not Django-compatible)
- Auto-detection of optimal Granian settings

## Future Enhancements

- Add support for Granian-specific advanced features
- Add configuration presets for common use cases
- Add performance monitoring integration
- Consider RSGI support if Django adds compatibility

## References

- Granian GitHub: https://github.com/emmett-framework/granian
- Granian PyPI: https://pypi.org/project/granian/
- Django ASGI Documentation: https://docs.djangoproject.com/en/stable/howto/deployment/asgi/
- Django WSGI Documentation: https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/
- Project README: README.md
- Existing backends: `src/django_prodserver/backends/`

## Estimated Effort

- **Implementation**: 2-3 hours
- **Testing**: 2-3 hours
- **Documentation**: 1-2 hours
- **Total**: 5-8 hours

## Risk Assessment

**Low Risk**:

- Follows established patterns
- Granian is mature and stable (v1.0+)
- Optional dependency (no impact on existing users)
- Well-defined interface

**Potential Issues**:

- Granian API changes between versions (mitigate with version pinning)
- Platform-specific issues (Rust compilation)
- Argument format differences from expectations

## Approval Checklist

- [x] Technical specification reviewed
- [x] Task breakdown defined
- [x] Testing strategy confirmed
- [x] Documentation plan approved
- [ ] Implementation approved to proceed
