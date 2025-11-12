# Product Roadmap

*Last updated: 2025-11-12*
*Source: [GitHub Project Board](https://github.com/users/nanorepublica/projects/1)*

## Current Backlog (From GitHub Issues)

### Phase 1: Core Command-Line & Configuration (Priority)

1. [ ] **Support arguments being passed from the command line** (#68) — Allow command-line arguments to be passed through to backend servers, enabling developers to override configuration on-the-fly. `S`

2. [ ] **Default options like --skip-checks don't get passed through** (#67) — Fix issue where Django's default options (--skip-checks, --noreload, etc.) aren't properly forwarded to backends. `S`

3. [ ] **Provide sane defaults for each backend** (#69) — Define and implement sensible default configurations for Gunicorn, Granian, Uvicorn, and other backends so they work out-of-the-box without extensive configuration. `M`

4. [ ] **Sane UvicornWorker default** (#72) — Specifically configure optimal defaults for Uvicorn when used as a Gunicorn worker class. `XS`

### Phase 2: Backend Expansion & Naming

5. [ ] **Consider the name of the commands** (#63) — Review and potentially rename management commands (prodserver, prodworker) for clarity and consistency with Django conventions. `S`

6. [ ] **Consider environments and command names** (#64) — Design how commands should behave differently across development/staging/production environments. `S`

7. [ ] **Support other commands** (#75) — Extend beyond prodserver/prodworker to support additional Django management commands through the unified interface. `M`

8. [ ] **Entrypoint support for backends** (#71) — Add support for custom entrypoints in backend configuration, allowing advanced customization of how servers start. `M`

### Phase 3: Extended Backend Support

9. [ ] **Add Celery Flower backend** (#88) — Integrate Celery Flower (task monitoring tool) as a managed backend for visibility into Celery workers. `M`

10. [ ] **Create Backends for Development Servers** (#89) — Add support for development-optimized server backends (runserver_plus, Werkzeug debugger, etc.) to use prodserver in development environments. `M`

---

## Strategic Roadmap (Future Features)

### Operational Excellence

11. [ ] **Configuration Validation System** — Add comprehensive validation for PRODUCTION_PROCESSES settings that checks backend availability, validates arguments, and detects configuration conflicts. `M`

12. [ ] **Graceful Shutdown Handler** — Implement signal handling for graceful shutdowns across all backends, ensuring in-flight requests complete and connections close cleanly. `S`

13. [ ] **Health Check Integration** — Build health check endpoints that work with all server backends, supporting Kubernetes readiness/liveness probes. `M`

14. [ ] **Structured Logging Framework** — Create standardized structured logging (JSON) across all backends for integration with log aggregation systems. `M`

### Developer Experience

15. [ ] **Multi-Process Orchestration** — Support running multiple processes (web + worker + beat) from a single command with lifecycle management. `M`

16. [ ] **Auto-Reload Configuration** — Implement hot-reload capabilities that detect code/config changes and restart processes with zero downtime. `M`

17. [ ] **Container Optimization Features** — Add Docker-specific optimizations including efficient layer caching and startup time improvements. `S`

### Advanced Features

18. [ ] **Process Monitoring Dashboard** — Build web-based monitoring interface showing real-time metrics for all prodserver processes. `L`

19. [ ] **Performance Profiling Integration** — Integrate profiling tools (py-spy, cProfile) with minimal overhead for production debugging. `L`

20. [ ] **Enhanced Backend Ecosystem** — Expand to include Hypercorn, Daphne, dramatiq, Huey, and provide a plugin system for third-party backends. `XL`

---

## Recently Completed

- [x] **Granian backend** (#74) — Added Granian as a supported ASGI server backend ✓
- [x] **devserver_plus** (#87) — Enhanced development server features ✓

---

## Notes

- **Backlog items (#1-10)** are actively tracked on GitHub and represent immediate priorities
- **Strategic items (#11-20)** are forward-looking features aligned with the product mission
- Ordering reflects technical dependencies and incremental value delivery
- Configuration and defaults are foundational for developer experience
- Backend expansion enables broader adoption across different deployment scenarios
- Operational features (health checks, logging, monitoring) support production reliability
