# Task Breakdown: Backend Entry-Point Foundation (Phase 0)

## Overview

Total: 6 task groups, ~35 sub-tasks.

This implements Phase 0 of the parent spec
[`2026-05-11-split-package-into-multiple-repos`](../2026-05-11-split-package-into-multiple-repos/spec.md).
The end state is: `django_prodserver` is importable with no third-party
extras installed; backends are discoverable via `importlib.metadata` entry
points (closes [#71](https://github.com/nanorepublica/django-prodserver/issues/71))
while existing dotted-path configs keep working; the plugin contract is
documented; CI exercises a "core only" matrix slice.

**Target branch for implementation:** `claude/prodserver-entrypoint-foundation`
(separate from the branch this spec lives on).

---

## Task List

### Task Group 0: Audit & Decisions

**Dependencies:** none.

- [ ] 0.0 Resolve decision points before writing code
  - [ ] 0.1 Confirm final entry-point short-name table (see spec §P1).
    Document the chosen names in `docs/extending.md` (T4.1).
  - [ ] 0.2 Audit `granian.py`, `daphne.py`, `werkzeug.py` for any third-party
    top-level imports (`import granian`, `import daphne`, `import werkzeug.*`).
    Record findings in the PR description so reviewers don't re-check.
  - [ ] 0.3 Verify `devserver` and `prodserver` commands route through the same
    backend resolution path as `server` (they share `Command.start_server` per
    current read — confirm).
  - [ ] 0.4 Choose `BackendDependencyMissing` parent class
    (recommendation: subclass of `django.core.management.CommandError`).
  - [ ] 0.5 Choose short-name collision policy: first-wins vs. raise. Document
    in `extending.md`.

**Acceptance Criteria:** decisions recorded in the spec's "Decision Points"
section (edit in place) or in `extending.md`. No code changes yet.

---

### Task Group 1: Backend Registry & Entry-Point Discovery (P1)

**Dependencies:** Task Group 0.

- [ ] 1.0 Build the backend registry
  - [ ] 1.1 Write tests for `registry.resolve_backend` covering:
    - short-name resolution to an in-tree backend class
    - dotted-path back-compat resolution (existing
      `django_prodserver.backends.gunicorn.GunicornServer` path)
    - `BackendDependencyMissing` when a registered short-name's underlying
      module is missing (simulate via `monkeypatch` of `sys.modules`)
    - unknown name → `CommandError`-compatible exception with a helpful
      message listing registered names
    - collision behaviour matching the policy chosen in T0.5
  - [ ] 1.2 Create `src/django_prodserver/backends/registry.py` with:
    - `BackendDependencyMissing` exception (subclass per T0.4)
    - `BackendInfo` dataclass (`name`, `dotted_path`, `distribution`,
      `installed`)
    - `resolve_backend(name_or_path: str) -> type[BaseServerBackend]`
    - `iter_registered() -> Iterable[BackendInfo]`
    - Internal cached `_load_entry_points()` that calls
      `importlib.metadata.entry_points(group="django_prodserver.backends")`
  - [ ] 1.3 Optionally re-export `resolve_backend` and
    `BackendDependencyMissing` from `backends/__init__.py` (public surface).
  - [ ] 1.4 Update `src/django_prodserver/management/commands/server.py:99`
    to call `resolve_backend(server_backend)` instead of
    `import_string(server_backend)`. Catch `BackendDependencyMissing` and
    re-raise as `CommandError` with the friendly message.
  - [ ] 1.5 Add `--list-backends` to `server` command. Output format: one
    backend per line, `<short-name>  <dotted-path>  [installed|missing]`.
    Update `run_from_argv` to short-circuit when the flag is set, mirroring
    the existing `--list` handling.
  - [ ] 1.6 Register all in-tree adapters in `pyproject.toml` under
    `[project.entry-points."django_prodserver.backends"]` using the names
    confirmed in T0.1.
  - [ ] 1.7 Run the registry tests; all pass.

**Acceptance Criteria:**

- `from django_prodserver.backends.registry import resolve_backend` works.
- `PRODUCTION_PROCESSES["web"]["BACKEND"] = "gunicorn"` resolves to
  `GunicornServer` (new behaviour).
- `PRODUCTION_PROCESSES["web"]["BACKEND"] = "django_prodserver.backends.gunicorn.GunicornServer"`
  still resolves (back-compat).
- `manage.py server --list-backends` prints all 13 in-tree backends.
- Missing-dep case produces `BackendDependencyMissing` with `pip install` hint.

---

### Task Group 2: Lazy-Import Refactor of Adapters (P2)

**Dependencies:** Task Group 1.

- [ ] 2.0 Make adapter modules importable with their third-party dep missing
  - [ ] 2.1 Write `tests/test_core_imports.py`:
    - Subprocess-based test that runs Python with each third-party dep
      blocked (e.g. `sys.modules["gunicorn"] = None` or a fake meta-finder
      that raises `ImportError` for `gunicorn`, `uvicorn`, `waitress`,
      `granian`, `daphne`, `werkzeug`, `celery`, `django_tasks`, `django_q`).
    - For each adapter module, attempt `importlib.import_module(...)` and
      assert no exception.
    - Run the test now — it should **fail** for `gunicorn.py`, `uvicorn.py`,
      `waitress.py` (and any others surfaced in T0.2). This proves the test
      bites; subsequent commits make it pass.
  - [ ] 2.2 Refactor `src/django_prodserver/backends/gunicorn.py`:
    - Remove module-level
      `from gunicorn.app.wsgiapp import WSGIApplication`.
    - Move the `DjangoApplication` class definition inside `start_server`
      (it's only used there) **or** keep it at module scope but defer the
      `WSGIApplication` base-class resolution via a `__init_subclass__` /
      runtime `import_string` trick. Prefer the first approach for clarity.
    - Verify existing gunicorn tests still pass with gunicorn installed.
  - [ ] 2.3 Refactor `src/django_prodserver/backends/uvicorn.py`:
    - Move `import uvicorn.main` from module top into `start_server`.
  - [ ] 2.4 Refactor `src/django_prodserver/backends/waitress.py`:
    - Move `import waitress.runner` from module top into `start_server`.
  - [ ] 2.5 Lazy-fy `granian.py`, `daphne.py`, `werkzeug.py` if T0.2 found
    any module-top third-party imports. Skip otherwise.
  - [ ] 2.6 Re-run `tests/test_core_imports.py` with **all** extras
    uninstalled in a clean venv. All assertions pass.
  - [ ] 2.7 Re-run the full existing test suite with all extras installed
    (current CI behaviour). All assertions pass — no regressions.

**Acceptance Criteria:**

- `python -c "import django_prodserver.backends.gunicorn"` succeeds in a
  fresh venv with only `django` installed.
- Same for every other adapter module.
- All existing tests still green when extras are installed.

---

### Task Group 3: Test-Suite Federation (P3)

**Dependencies:** Task Group 2.

- [ ] 3.0 Restructure tests so they can run as core-only or all-extras
  - [ ] 3.1 Create or extend `tests/backends/conftest.py` with a
    `parametrize_backends` fixture that yields each registered backend's
    `BackendInfo`. Backends whose dep is missing yield with
    `installed=False`; tests can then `pytest.skip` if they need the dep.
  - [ ] 3.2 Write `tests/backends/test_contract.py`:
    - For each registered backend, assert `resolve_backend("<short>")`
      returns the same class as `resolve_backend("<dotted.path>")`.
    - For each backend whose dep is installed, assert it can be instantiated
      with `ARGS={}` (skip if `installed=False`).
    - For each backend, assert `prep_server_args()` returns a `list`.
  - [ ] 3.3 Add `pytest.importorskip("<dep>")` (or equivalent skip marker) to
    the top of each existing `tests/backends/test_<adapter>.py` so they're
    silently skipped when the adapter's dep isn't installed:
    - `test_gunicorn.py` → `pytest.importorskip("gunicorn")`
    - `test_uvicorn.py` → `pytest.importorskip("uvicorn")`
    - `test_waitress.py` → `pytest.importorskip("waitress")`
    - `test_granian.py` → `pytest.importorskip("granian")`
    - `test_daphne.py` → `pytest.importorskip("daphne")`
    - `test_werkzeug.py` → `pytest.importorskip("werkzeug")`
    - `test_celery.py` → `pytest.importorskip("celery")`
    - `test_django_tasks.py` → `pytest.importorskip("django_tasks")`
    - `test_django_q2.py` → `pytest.importorskip("django_q")`
  - [ ] 3.4 Add `tox` envs for the new slices:
    - `core` — only `dev` group, no adapter extras
    - `gunicorn` — `dev` + `gunicorn` extra
    - `all` — current behaviour
  - [ ] 3.5 Verify locally:
    - `tox -e core` passes; reports adapter-specific tests as skipped.
    - `tox -e gunicorn` passes; runs core + gunicorn tests, skips others.
    - `tox -e all` passes; no regressions.

**Acceptance Criteria:**

- `tox -e core` finishes green with adapter tests cleanly skipped.
- `test_contract.py` runs against every registered backend.
- No existing per-adapter test was removed; only the skip marker added.

---

### Task Group 4: Plugin Contract Docs & Example Adapter (P4)

**Dependencies:** Task Groups 1–3.

- [ ] 4.0 Document the plugin contract and ship a working example
  - [ ] 4.1 Write `docs/extending.md`:
    - "Registering a backend" — entry-point group, naming conventions, the
      decision from T0.1 and T0.5 captured.
    - "`BaseServerBackend` reference" — methods to implement / override,
      with the cross-references to `base.py:BaseServerBackend`.
    - "Satellite package convention" — distribution `django-prodserver-<name>`,
      import `django_prodserver_<name>`, per T0 and the spec.
    - "Example: writing an echo backend" — code-listing for the example below.
    - Cross-link to backend reference pages in `docs/backends/`.
  - [ ] 4.2 Add `docs/extending.md` to `docs/index.md` TOC.
  - [ ] 4.3 Create `examples/django-prodserver-echo/`:
    - `pyproject.toml` with:
      ```toml
      [project]
      name = "django-prodserver-echo"
      version = "0.0.1"
      dependencies = ["django-prodserver"]

      [project.entry-points."django_prodserver.backends"]
      echo = "django_prodserver_echo:EchoServer"
      ```
    - `src/django_prodserver_echo/__init__.py` with an `EchoServer` subclass
      of `BaseServerBackend` whose `start_server` prints its args and exits 0.
    - `README.md` (very short).
  - [ ] 4.4 Add a CI step that:
    1. Installs the example: `pip install -e examples/django-prodserver-echo`
    2. Runs `python manage.py server --list-backends` and greps for `echo`
    3. Runs a smoke test that invokes the echo backend through
       `Command.start_server` (or via subprocess if simpler).
  - [ ] 4.5 Build the docs locally
    (`cd docs && make html`) and verify `extending.md` renders, links resolve.

**Acceptance Criteria:**

- `docs/extending.md` builds and is reachable from the TOC.
- The example adapter installs cleanly and shows up under
  `server --list-backends` in CI.
- The smoke test passes in CI.

---

### Task Group 5: CI Matrix & Release Note (P3 follow-up)

**Dependencies:** Task Groups 1–4.

- [ ] 5.0 Wire the new test slices into CI
  - [ ] 5.1 Update `.github/workflows/ci.yml` (or wherever the test matrix
    lives) to add:
    - `core-only` job: install with no extras, run `tox -e core`.
    - `gunicorn-only` job: install with `[gunicorn]`, run `tox -e gunicorn`.
    - Keep the existing `all` job.
    - Run the example-adapter smoke test from T4.4 in the `core-only` job.
  - [ ] 5.2 Verify all jobs pass on a draft PR.
  - [ ] 5.3 Update `CHANGELOG.md` with a Phase 0 entry referencing #71 and
    noting that short-name `BACKEND` values are now supported in
    `PRODUCTION_PROCESSES`.
  - [ ] 5.4 Update `README.md` "Configuration" section to mention the short
    names as a permitted form (with a note that dotted paths still work).

**Acceptance Criteria:**

- All three CI jobs green.
- Changelog and README reflect the new resolution behaviour.

---

### Task Group 6: Final Verification & PR

**Dependencies:** Task Groups 1–5.

- [ ] 6.0 Verify Phase 0 success criteria end-to-end
  - [ ] 6.1 Fresh venv:
    `pip install -e .` (no extras) → all module imports succeed (run
    `tests/test_core_imports.py`).
  - [ ] 6.2 Fresh venv: `pip install -e .[gunicorn]` → existing dotted-path
    config and new short-name config both start a server. Hit it with
    `curl` to confirm it serves.
  - [ ] 6.3 Fresh venv: `pip install -e .` → configure gunicorn backend →
    confirm `BackendDependencyMissing` message is friendly and
    actionable.
  - [ ] 6.4 Fresh venv: `pip install -e . -e examples/django-prodserver-echo`
    → `server --list-backends` lists `echo` as installed → `server echo`
    runs.
  - [ ] 6.5 Run the docs site locally and click through `extending.md` to
    `backends/`, confirm cross-references work.
  - [ ] 6.6 Open the PR with title `Phase 0: backend entry-point foundation
    (closes #71)` and a description that:
    - Links to this spec and the parent spec.
    - Lists every behavioural change (short-name resolution, lazy imports,
      `--list-backends`, `BackendDependencyMissing`).
    - Calls out that no public API was removed.

**Acceptance Criteria:**

- Every bullet under Spec §"Success Criteria" is demonstrated.
- PR description references #71 and the parent issue #98.

---

## Execution Order

1. **Task Group 0** — decisions first, code never.
2. **Task Group 1** — registry + entry-point wiring. Lands the user-visible
   capability behind the boundary cleanup.
3. **Task Group 2** — lazy imports. The regression test in T2.1 should be
   written before T2.2–T2.5 so each refactor makes the test go from red to
   green.
4. **Task Group 3** — test federation. Comes after T2 because the
   `pytest.importorskip` markers need T2 to be meaningful (otherwise the
   import fires before pytest gets a chance to skip).
5. **Task Group 4** — docs + example adapter. Validates the contract from
   the outside.
6. **Task Group 5** — CI wiring + changelog.
7. **Task Group 6** — final verification and PR.

## Success Metrics

- **#71 closed** by the PR that lands this work.
- **0 public-API removals.** Every existing `PRODUCTION_PROCESSES` config in
  the wild keeps working.
- **`tox -e core` green** with only `django` installed beyond the dev group.
- **`server --list-backends`** lists 13 in-tree backends + the `echo`
  example when installed.
- **`docs/extending.md` published** and linked from the docs TOC.
- **Parent spec unblocked:** the next branch (`claude/split-monorepo-workspace-spike`
  or `claude/split-multi-repo-spike`) can fork from `main` and start moving
  code with confidence that the seam is real.
