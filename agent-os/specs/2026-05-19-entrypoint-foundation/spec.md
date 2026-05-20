# Specification: Backend Entry-Point Foundation (Phase 0)

## Status

Implementation spec. This is **Phase 0** of the parent spec
[`2026-05-11-split-package-into-multiple-repos`](../2026-05-11-split-package-into-multiple-repos/spec.md)
— a hard prerequisite that lands on `main` before any package-split spike
begins. It is also independently shippable: even if no further split ever
happens, this work closes [#71](https://github.com/nanorepublica/django-prodserver/issues/71)
on its own.

## Related Issues

- [#71](https://github.com/nanorepublica/django-prodserver/issues/71) —
  "Entrypoint support for backends" (primary; closed by this spec).
- [#98](https://github.com/nanorepublica/django-prodserver/issues/98) —
  "Splitting out the backends and the core API" (parent; unblocked by this spec
  but not closed).

## Goal

Make `django_prodserver` importable, configurable, and testable as if it were
already two layers — a dependency-free core and a set of pluggable adapters —
**without actually moving any code between distributions**. By the end of
Phase 0:

1. Backends are discoverable via `importlib.metadata` entry points under the
   group `django_prodserver.backends`, in addition to the existing dotted-path
   `BACKEND = "..."` configuration.
2. Installing `django-prodserver` with **no** extras (`pip install django-prodserver`)
   leaves the package fully importable — no `ImportError` from any module under
   `django_prodserver/` at import time.
3. The full backend test matrix can be run as: "core only" (no extras), "core +
   one adapter" (one extra installed), or "everything" (current behaviour).
4. The plugin contract is documented, and an example out-of-tree adapter under
   `examples/` proves the contract works end-to-end.

## Non-Goals / Out of Scope

- **Moving any adapter code out of `src/django_prodserver/backends/` into a
  separate distribution.** That is parent-spec work (Option A / Option B).
- **Changing what `pip install django-prodserver[gunicorn]` resolves to.** The
  extras keep depending on `gunicorn` directly today; they will switch to
  satellite packages in a later phase.
- **Breaking any public API.** Every existing `PRODUCTION_PROCESSES`
  configuration in the wild must keep working without edits — dotted-path
  `BACKEND` strings, the `APP` key, every adapter's `ARGS` schema.
- **Renaming management commands** (covered by #63 / #64).
- **Touching `semantic_release` config** for multi-package publishing (parent
  spec).

## Background

Today, `PRODUCTION_PROCESSES["<name>"]["BACKEND"]` is a dotted path that
`server.py` resolves with `django.utils.module_loading.import_string`. That works,
but it has two problems for the parent-spec direction:

1. **No way for an external package to advertise a backend.** If Chancy
   (#71's example) wanted to ship a `ChancyWorker` adapter, a user would have
   to know the exact dotted path to put in their settings. There is no
   registry, no `--list-backends`, no friendly error when the dep is missing.
2. **Importing `django_prodserver.backends.gunicorn`** *currently* imports
   `gunicorn` at module top level. So does `uvicorn.py` (`import uvicorn.main`)
   and `waitress.py` (`import waitress.runner`). That means an introspection
   tool, a docs builder, or a test runner with `gunicorn` uninstalled can't
   even *enumerate* the available backends without `ImportError`. This blocks
   "core is liftable into Django" — the core must not transitively reference
   third-party servers at import time.

The other adapters are already mostly clean:

- `celery.py`: only imports `django.utils.module_loading.import_string` at
  top; the Celery app is resolved at runtime.
- `django_tasks.py`: only imports `django.core.management`; the django-tasks
  worker is invoked via `call_command("db_worker")`.
- `django_q2.py`: only imports `django.*` at top; `import django_q` is inside
  `__init__` with `ImproperlyConfigured` raised on failure (the pattern we
  want).
- `granian.py`, `daphne.py`, `werkzeug.py`: only import `django` and stdlib at
  top per current inspection — to be verified during P2.

## Approach

### P1 — Backend registry & entry-point discovery

**New module: `src/django_prodserver/backends/registry.py`**

A small, lazy registry with these responsibilities:

- Discover entry points in the group `django_prodserver.backends` on first use,
  using `importlib.metadata.entry_points(group="django_prodserver.backends")`.
  Cache the result.
- Provide `resolve(name_or_path: str) -> type[BaseServerBackend]`:
  - If `name_or_path` matches a registered short name, load it (which may raise
    `ModuleNotFoundError` if the adapter's third-party dep is missing — that
    error is caught and re-raised as a `BackendDependencyMissing` with a
    `pip install ...` hint).
  - Otherwise, fall back to `import_string(name_or_path)` for back-compat with
    today's dotted-path configs.
- Provide `iter_registered() -> Iterable[BackendInfo]` where `BackendInfo`
  exposes name, dotted path, distribution name, and `installed: bool`
  (probed by attempting `entry_point.load()` and catching `ImportError`).

**Update `server.py:99`:**

```python
# before
backend_class = import_string(server_backend)

# after
from ..backends.registry import resolve_backend
backend_class = resolve_backend(server_backend)
```

**Built-in registration:** in `src/django_prodserver/pyproject.toml`'s
`[project.entry-points."django_prodserver.backends"]`, register each in-tree
adapter under a stable short name:

```toml
[project.entry-points."django_prodserver.backends"]
gunicorn      = "django_prodserver.backends.gunicorn:GunicornServer"
uvicorn       = "django_prodserver.backends.uvicorn:UvicornServer"
uvicorn-wsgi  = "django_prodserver.backends.uvicorn:UvicornWSGIServer"
granian-asgi  = "django_prodserver.backends.granian:GranianASGIServer"
granian-wsgi  = "django_prodserver.backends.granian:GranianWSGIServer"
waitress      = "django_prodserver.backends.waitress:WaitressServer"
werkzeug      = "django_prodserver.backends.werkzeug:WerkzeugRunserver"
daphne        = "django_prodserver.backends.daphne:DaphneRunserver"
django-runserver = "django_prodserver.backends.django_runserver:DjangoRunserver"
celery-worker = "django_prodserver.backends.celery:CeleryWorker"
celery-beat   = "django_prodserver.backends.celery:CeleryBeat"
django-tasks  = "django_prodserver.backends.django_tasks:DjangoTasksWorker"
django-q2    = "django_prodserver.backends.django_q2:DjangoQ2Worker"
```

(Final names to be decided in T1 — listed here as the working proposal.)

**New CLI affordance:** add `server --list-backends` that prints registered
backends with their dotted path and "installed" status. Keep `server --list`
as it is (lists *configured processes*).

**New error type: `BackendDependencyMissing`** subclassing `CommandError`. When
a registered backend's third-party module is missing, surface:

```
BackendDependencyMissing: backend 'gunicorn' requires the 'gunicorn' package.
  Install it with: pip install django-prodserver[gunicorn]
```

### P2 — Package-boundary cleanup

**Make all top-level adapter imports lazy.** Move third-party imports inside
`start_server` / `__init__` / `prep_server_args` so importing the adapter
module no longer requires the dep to be installed. Specifically:

- `gunicorn.py`: move `from gunicorn.app.wsgiapp import WSGIApplication` inside
  the `DjangoApplication` class body or `start_server`.
- `uvicorn.py`: move `import uvicorn.main` inside `start_server`.
- `waitress.py`: move `import waitress.runner` inside `start_server`.
- `granian.py`, `daphne.py`, `werkzeug.py`: audit; move any third-party top-level
  imports inside methods as needed (current read suggests they're already OK).

**Add a core-import guard test:**

```python
# tests/test_core_imports.py
def test_core_imports_without_third_party():
    """Importing django_prodserver with no adapters installed must not raise."""
    # Run as a subprocess with a constrained sys.path / PYTHONPATH-blocked
    # third-party modules. Asserts no ImportError when importing every module
    # under django_prodserver.backends.* including the adapter modules.
```

This is the regression lock that keeps P2 from regressing as new backends are
added.

**Decide on the distribution/import-name convention for future satellites.**
This decision is captured in `docs/extending.md` (P4) so future satellites are
consistent. The proposed default:

- Distribution: `django-prodserver-<name>` (e.g. `django-prodserver-gunicorn`).
- Import package: flat `django_prodserver_<name>` rather than a PEP 420
  namespace package, to dodge namespace-package tooling pitfalls. Final pick is
  validated by the example adapter in P4.

### P3 — Test-suite federation

The current `tests/backends/test_<adapter>.py` files run against the
single installed `django-prodserver` distribution. To support both today's
"all extras installed" CI and tomorrow's "core only" / "one adapter installed"
CI, restructure as follows:

- **`tests/backends/conftest.py`** gains a `parametrize_backends` fixture that
  yields each registered backend class. Tests that exercise the
  `BaseServerBackend` *contract* (arg formatting, lazy import behaviour,
  `BackendDependencyMissing` on missing dep) use this.
- **`tests/backends/test_contract.py`** (new): the shared conformance test.
  Asserts every registered backend can be `resolve()`d by its short name and
  by its dotted path, instantiated with an empty `ARGS`, and that
  `prep_server_args()` returns a list. Skips backends whose third-party dep is
  not importable.
- **Per-adapter tests stay where they are** but each gets a top-of-file
  `pytest.importorskip("<dep>")` so the file is skipped wholesale when the
  adapter's dep isn't installed.
- **CI matrix** (`.github/workflows/`): add jobs `core-only` (extras=none),
  `gunicorn-only` (extras=[gunicorn]), and keep the existing `all` job. The
  core-only job runs `test_core_imports.py` + `test_contract.py` + every other
  test file that doesn't depend on an adapter.

### P4 — Plugin contract documentation + example adapter

**`docs/extending.md`** (new):

- The `django_prodserver.backends` entry-point group: how to register, naming
  conventions, what the entry-point target must be (a `BaseServerBackend`
  subclass).
- `BaseServerBackend` API reference: `__init__(**server_args)`,
  `start_server(*args)`, `prep_server_args() -> list[str]`,
  `_format_server_args_from_dict()` (already public-ish in `base.py`).
- The satellite-package convention chosen in P2.
- Worked example: code listing for the example adapter below.

**`examples/django-prodserver-echo/`** (new): the smallest possible adapter
that registers via entry points.

- Its own `pyproject.toml` with `[project.entry-points."django_prodserver.backends"]`
  pointing at an `EchoServer` class.
- `EchoServer.start_server` just prints its args and exits — proves the wiring
  end-to-end with zero external dependencies.
- A CI step `pip install -e examples/django-prodserver-echo` followed by a
  pytest run that confirms `server echo` works and shows up under
  `server --list-backends`.

## Affected Files

**New files:**

- `src/django_prodserver/backends/registry.py`
- `tests/test_core_imports.py`
- `tests/backends/test_contract.py`
- `docs/extending.md`
- `examples/django-prodserver-echo/pyproject.toml`
- `examples/django-prodserver-echo/src/django_prodserver_echo/__init__.py`
- `examples/django-prodserver-echo/tests/test_echo.py`

**Modified files:**

- `src/django_prodserver/backends/__init__.py` — re-export
  `resolve_backend`, `BackendDependencyMissing` (optional).
- `src/django_prodserver/backends/gunicorn.py` — lazy import.
- `src/django_prodserver/backends/uvicorn.py` — lazy import.
- `src/django_prodserver/backends/waitress.py` — lazy import (if needed).
- `src/django_prodserver/backends/granian.py` — audit, lazy-fy if needed.
- `src/django_prodserver/backends/daphne.py` — audit, lazy-fy if needed.
- `src/django_prodserver/backends/werkzeug.py` — audit, lazy-fy if needed.
- `src/django_prodserver/management/commands/server.py` — call
  `resolve_backend`; add `--list-backends`.
- `src/django_prodserver/management/commands/devserver.py` — same registry
  hookup if it does its own resolution (verify in T0).
- `pyproject.toml` — add `[project.entry-points."django_prodserver.backends"]`.
- `tests/backends/conftest.py` (may not exist yet) — add
  `parametrize_backends` fixture.
- `tests/backends/test_*.py` — add `pytest.importorskip` at top of each
  adapter-specific test file.
- `.github/workflows/ci.yml` (or equivalent) — add `core-only` and
  `gunicorn-only` matrix jobs.
- `docs/index.md` — link `extending.md` into the TOC.
- `tox.ini` — add envs matching the new CI matrix.

## Decision Points (resolve during implementation)

1. **Entry-point names:** the table above is a proposal. Confirm before
   landing — names go on PyPI metadata and are hard to change later.
2. **`--list-backends` output format:** plain text vs. tabular. Lean plain text
   to match the existing `--list`.
3. **`BackendDependencyMissing`:** subclass `CommandError` (current
   recommendation) or a new `ImproperlyConfigured`-style exception? The former
   keeps the existing `server.py` error-formatting path working unchanged.
4. **Whether to also register `prodserver`/`devserver` short-name resolution**
   or only `server`. The aliases share `Command.start_server`, so the answer
   is "automatically yes" — but verify.
5. **Final naming of the flat-vs-namespace satellite import convention.** Pick
   one (recommendation: flat `django_prodserver_<name>`) and document it.

## Success Criteria

- `pip install django-prodserver` (no extras) installs cleanly and:
  - `python -c "import django_prodserver.backends.gunicorn"` does not raise.
  - `python -c "import django_prodserver.backends.uvicorn"` does not raise.
  - `python -c "import django_prodserver.backends.waitress"` does not raise.
- `python manage.py server --list-backends` lists all 13 in-tree backends with
  correct "installed" status given the extras configured.
- An existing project with
  `PRODUCTION_PROCESSES = {"web": {"BACKEND": "django_prodserver.backends.gunicorn.GunicornServer", "ARGS": {"bind": "0.0.0.0:8000"}}}`
  starts unchanged.
- The same project, written as
  `PRODUCTION_PROCESSES = {"web": {"BACKEND": "gunicorn", "ARGS": {"bind": "0.0.0.0:8000"}}}`,
  also starts (new short-name form).
- A user with no `gunicorn` installed who runs the gunicorn config gets the
  friendly `BackendDependencyMissing` error, not a raw `ModuleNotFoundError`.
- CI `core-only` job passes (all tests not requiring an adapter), proving the
  core import surface is clean.
- `pip install -e examples/django-prodserver-echo && manage.py server echo`
  works in CI without modifying `django-prodserver` itself.
- `docs/extending.md` is published in the doc site TOC.
- All existing tests still pass.
- #71 can be closed with a link to the released version.

## Risks & Mitigations

- **Lazy imports break import-time class-construction patterns.** E.g.
  `gunicorn.py` defines `class DjangoApplication(WSGIApplication):` at module
  top, which requires `WSGIApplication` at import time. *Mitigation:* refactor
  to construct `DjangoApplication` inside `start_server` (it's only used there
  anyway), or keep the class body but wrap the import in a `TYPE_CHECKING`
  guard plus a runtime `import_string` inside `__init__`.
- **Entry-point discovery cost.** `importlib.metadata.entry_points()` walks
  installed dists; it's cheap (~ms) but not free. *Mitigation:* cache the
  registry on first access; never call inside hot paths.
- **`pytest.importorskip` makes coverage misleading** for core-only CI runs.
  *Mitigation:* surface a "tests skipped due to missing optional deps" summary
  line; rely on the `all` CI job for full coverage measurement.
- **PEP 420 namespace pitfalls** for future satellites. *Mitigation:* the
  example adapter uses the flat layout this spec recommends; namespace layout
  can be revisited in the parent-spec spikes.
- **Short-name collisions** between in-tree backends and a satellite registering
  the same name. *Mitigation:* `resolve_backend` documents that the *first*
  registered entry point wins (or raises on collision — to be chosen in T1);
  in-tree backend names are namespaced loosely (`celery-worker`, not `worker`)
  to lower the collision surface.
