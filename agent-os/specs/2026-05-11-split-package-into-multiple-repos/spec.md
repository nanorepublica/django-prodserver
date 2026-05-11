# Specification: Split django-prodserver Into Multiple Repos/Packages

## Status

Exploratory spec. The goal of this spec is to **evaluate** structural options by
prototyping each on its own branch, then pick one. It is intentionally written as
parallel exploration tracks rather than a single linear implementation plan.

## Goal

Restructure django-prodserver so that:

1. A small, dependency-free **core** package can stand on its own and be a
   credible candidate for eventual inclusion in Django itself (via a DEP — Django
   Enhancement Proposal). The core owns the `server` / `devserver` / `prodserver`
   management commands, the `PRODUCTION_PROCESSES` setting, the `BaseServerBackend`
   / `BaseRunserverBackend` contract, and shared helpers.
2. Each third-party **backend adapter** (gunicorn, uvicorn, granian, waitress,
   werkzeug/runserver-plus, daphne, celery, django-tasks, django-q2) can live
   outside the core — ideally upstreamed into the server/worker project it wraps,
   or failing that in a dedicated satellite package — so users install only the
   adapters they actually run, and adapter releases track the upstream they
   depend on rather than the core's release cadence.

## Background & Motivation

The codebase already has a clean internal seam:

- **Core (no third-party deps):**
  - `src/django_prodserver/management/commands/server.py` (and the `prodserver`
    alias + `devserver`)
  - `src/django_prodserver/conf.py` (`AppSettings`, `PRODUCTION_PROCESSES`)
  - `src/django_prodserver/backends/base.py` (`BaseServerBackend`)
  - `src/django_prodserver/backends/_runserver_base.py` (`BaseRunserverBackend`)
  - `src/django_prodserver/backends/django_runserver.py` (wraps Django's own
    runserver — the only adapter with zero extra dependencies)
  - `src/django_prodserver/utils.py` (`wsgi_healthcheck`, `wsgi_app_name`,
    `asgi_app_name`)
  - `src/django_prodserver/apps.py`
- **Server adapters (one third-party dep each):** `gunicorn.py`, `uvicorn.py`,
  `granian.py`, `waitress.py`, `werkzeug.py` (379 lines — by far the largest),
  `daphne.py`.
- **Worker adapters (small, ≤72 lines):** `celery.py`, `django_tasks.py`,
  `django_q2.py`.

Backends are currently discovered by dotted path strings in
`PRODUCTION_PROCESSES["<name>"]["BACKEND"]` and the optional extras are declared
in `pyproject.toml` (`[project.optional-dependencies]`). Nothing in the runtime
actually depends on the adapters being in the same distribution — `import_string`
in `server.py:99` will happily import a backend class from any installed package.
That is what makes the split feasible.

This work is also aligned with roadmap items **#71 "Entrypoint support for
backends"** and **#20 "plugin system for third-party backends"** — the plugin
discovery mechanism described below is a hard prerequisite for any of the split
options, and is useful on its own even if the repo is never split.

## Non-Goals / Out of Scope

- Actually submitting a Django DEP or merging anything into Django. This spec only
  makes the core *shaped like* a merge candidate.
- Actually opening PRs against gunicorn / uvicorn / django-tasks / django-q2 /
  celery. We will document which adapters are upstream-PR candidates and what the
  integration surface would be, but coordinating those merges is follow-up work.
- Changing the public configuration format in a breaking way. `PRODUCTION_PROCESSES`
  with dotted-path `BACKEND` strings must keep working unchanged.
- Renaming the management commands (tracked separately as #63 / #64).
- Adding new backends (Celery Flower #88, etc.).
- Publishing anything to PyPI as part of the spike — prototypes can be built and
  installed locally / from git, but actual releases are a separate decision.

## Shared Prerequisite (applies to every option)

Before any repo/package split, land these on a base branch that all option
branches fork from. None of this is breaking.

### P1. Entry-point–based backend discovery

- Define an `importlib.metadata` entry-point group, e.g.
  `django_prodserver.backends`. Each adapter package registers its backend
  classes there, e.g.:
  ```toml
  [project.entry-points."django_prodserver.backends"]
  gunicorn = "django_prodserver_gunicorn:GunicornServer"
  ```
- In the core, build a registry that:
  - Collects entry points lazily (on first `server` invocation).
  - Lets `PRODUCTION_PROCESSES[...]["BACKEND"]` accept **either** a registered
    short name **or** a dotted path (back-compat). Short name wins only if it
    resolves; otherwise fall back to `import_string`.
  - Surfaces a friendly error when a backend name maps to a package that isn't
    installed (e.g. "backend 'gunicorn' requires the `django-prodserver-gunicorn`
    package — `pip install django-prodserver-gunicorn`").
- Update `server --list` (and ideally a new `server --list-backends`) to show
  registered backends and whether their dependency is importable.

### P2. Package-boundary cleanup in the current tree

- Make `utils.py` import-safe without any optional dep (it already is — only
  imports Django).
- Confirm no core module imports an adapter module at import time (currently
  true; lock it in with a test).
- Ensure each adapter module's heavy import (`import gunicorn`, `import granian`,
  ...) happens inside `start_server` / `__init__`, not at module top level, so
  the registry can reference the class without the dep installed. (Audit each
  adapter; several already do this.)
- Decide the import name / distribution name convention for satellites:
  - Distribution: `django-prodserver-<name>` (e.g. `django-prodserver-gunicorn`).
  - Import package: `django_prodserver_<name>` **or** a PEP 420 namespace
    package `django_prodserver.contrib.<name>` — this choice is itself one of the
    things the option branches should test.

### P3. Test-suite federation plan

- The current `tests/backends/` suite exercises every adapter together. Decide
  how that splits: shared conformance test (a parametrized `BaseServerBackend`
  contract test) that lives in core and can be re-used by each satellite, plus
  adapter-specific tests that move with the adapter.
- Provide a `tox`/CI matrix story for "core only" vs "core + one adapter" vs
  "everything" so a contributor can run the slice they care about.

## Options To Explore (one branch each)

Each option below should be prototyped far enough to answer the **decision
criteria** at the bottom. Suggested branch names are given; the requester will
create/drive these branches.

### Option A — Full multi-repo

**Branch:** `claude/split-multi-repo-spike`

- Core stays in this repo (possibly renamed to make the Django-merge intent
  obvious, e.g. `django-prodserver-core` distribution while keeping the
  `django_prodserver` import package).
- Each adapter (or logical group of adapters) moves to its own repo + PyPI
  package. Two sub-variants worth a quick look:
  - **A1:** one repo per adapter (`django-prodserver-gunicorn`,
    `django-prodserver-uvicorn`, ...). Maximal independence, maximal overhead.
  - **A2:** one `django-prodserver-contrib` repo holding all the adapters that
    *don't* get upstreamed, published either as one package with extras or as
    several packages from one repo.
- Adapters that are good upstream-PR candidates are documented as such
  (django-tasks, django-q2, celery, arguably gunicorn/uvicorn integrations) and
  the contrib repo carries them only until/unless upstream accepts them.
- Deliverables on the branch: a script or `git filter-repo` recipe showing how an
  adapter is extracted with history; a working `django-prodserver-gunicorn`
  prototype installed from a sibling directory; updated docs describing the new
  install story (`pip install django-prodserver django-prodserver-gunicorn`).

**Pros:** clean "lift core into Django" story; each upstream owns the code that
breaks when they release; users install only what they run.
**Cons:** N repos × release cadence × CI matrices is heavy for a small/solo
maintainer; cross-cutting `BaseServerBackend` changes need coordinated releases;
discoverability drops (no more single `pip install django-prodserver[gunicorn]`).

### Option B — Monorepo workspace of multiple publishable packages

**Branch:** `claude/split-monorepo-workspace-spike`

- Keep one repo, but restructure into a workspace (uv workspace or
  PDM/hatch equivalent) with several independently-publishable packages:
  ```
  packages/
    core/            -> django-prodserver-core   (the Django-merge candidate)
    gunicorn/        -> django-prodserver-gunicorn
    uvicorn/         -> django-prodserver-uvicorn
    granian/         -> django-prodserver-granian
    waitress/        -> django-prodserver-waitress
    werkzeug/        -> django-prodserver-werkzeug
    daphne/          -> django-prodserver-daphne
    celery/          -> django-prodserver-celery
    django-tasks/    -> django-prodserver-django-tasks
    django-q2/       -> django-prodserver-django-q2
    meta/            -> django-prodserver  (umbrella: depends on core + extras
                                            re-export the per-adapter packages)
  ```
- Shared CI, shared lint/format config, one place to make `BaseServerBackend`
  changes; each package still gets its own version + PyPI release + minimal
  dependency closure.
- The umbrella `django-prodserver` distribution keeps today's
  `pip install django-prodserver[gunicorn]` working by mapping extras to the
  per-adapter packages — no break for existing users.
- "Lift core into Django" = copy `packages/core/` — still clean, without the
  multi-repo tax.
- Deliverables on the branch: working uv workspace; `django-prodserver-core`
  builds with only `django` as a dep; at least two adapter packages build and
  install; CI runs the federated test matrix from P3; docs updated.

**Pros:** independent install/versioning + minimal deps per adapter, but one repo
to maintain; easiest migration path; can still flip individual packages out to
their own repos later (Option A) if an upstream bites.
**Cons:** workspace tooling complexity; publishing many packages from one tag
needs care (semantic-release config currently assumes one package); "merged into
respective upstream repos" still requires a later move.

### Option C — Single package, plugin-ready, no split (the "do less" option)

**Branch:** `claude/split-plugin-only-spike`

- Land only the Shared Prerequisite (entry points + boundary cleanup + test
  federation), keep shipping one `django-prodserver` distribution with the
  current extras.
- The payoff: third parties (including the upstream projects, if they want) can
  publish their *own* adapter packages against the documented entry-point
  contract, without us splitting anything. The "core" is already importable on
  its own; we just document the subset that would go to Django.
- Deliverables on the branch: the P1–P3 work, a `docs/extending.md` describing
  the backend plugin contract and entry-point group, and an example out-of-tree
  adapter package in `examples/` to prove the contract works.

**Pros:** smallest change, no release/CI multiplication, unblocks the ecosystem
goal immediately, fully reversible.
**Cons:** doesn't by itself achieve "core merged into Django" or "adapters in
upstream repos" — it just makes both *possible* later. The big adapters
(werkzeug, daphne, granian) still ship in the main distribution.

## Affected / Reference Files

Core (must remain dependency-free in every option):

- `src/django_prodserver/__init__.py`
- `src/django_prodserver/apps.py`
- `src/django_prodserver/conf.py`
- `src/django_prodserver/utils.py`
- `src/django_prodserver/backends/__init__.py`
- `src/django_prodserver/backends/base.py`
- `src/django_prodserver/backends/_runserver_base.py`
- `src/django_prodserver/backends/django_runserver.py` *(only zero-extra-dep adapter; candidate to ship with core)*
- `src/django_prodserver/management/__init__.py`
- `src/django_prodserver/management/commands/__init__.py`
- `src/django_prodserver/management/commands/server.py`
- `src/django_prodserver/management/commands/prodserver.py`
- `src/django_prodserver/management/commands/devserver.py`
- `src/django_prodserver/migrations/__init__.py`

Adapters to extract / make pluggable:

- `src/django_prodserver/backends/gunicorn.py`
- `src/django_prodserver/backends/uvicorn.py`
- `src/django_prodserver/backends/granian.py`
- `src/django_prodserver/backends/waitress.py`
- `src/django_prodserver/backends/werkzeug.py`
- `src/django_prodserver/backends/daphne.py`
- `src/django_prodserver/backends/celery.py`
- `src/django_prodserver/backends/django_tasks.py`
- `src/django_prodserver/backends/django_q2.py`

Packaging / tooling to touch:

- `pyproject.toml` (`[project.optional-dependencies]`, `[project.entry-points...]`,
  `[tool.semantic_release]` — currently single-package), `uv.lock`, `tox.ini`,
  `.github/` CI workflows, `docs/` (install + extending pages), `setup.py`.

Tests:

- `tests/backends/*` (federate per P3), `tests/test_server_command.py`,
  `tests/test_conf.py`, `tests/test_utils.py`.

## Decision Criteria (what each branch must let us judge)

1. **Install ergonomics:** how many `pip install ...` lines does a typical user
   need, and is the error message good when an adapter dep is missing?
2. **Maintainer overhead:** number of release pipelines, CI jobs, and changelogs;
   does `semantic-release` still work, or does it need replacing?
3. **Django-merge readiness:** can the core be built/tested/shipped with only
   `django` as a dependency, and is the public surface (commands + setting +
   `BaseServerBackend`) cleanly isolated?
4. **Upstream-PR viability:** for django-tasks, django-q2, celery — what exactly
   would a PR to those repos contain, and does the adapter need anything from the
   core beyond `BaseServerBackend`?
5. **Back-compat:** does an existing project with `PRODUCTION_PROCESSES` pointing
   at `django_prodserver.backends.gunicorn.GunicornServer` and
   `pip install django-prodserver[gunicorn]` keep working with no changes?
6. **Reversibility:** how hard is it to undo / re-merge if the experiment fails?

## Recommendation (to be confirmed after the spikes)

Start by landing the **Shared Prerequisite** (which is Option C in full). Then
prototype **Option B (monorepo workspace)** as the primary candidate — it
delivers the per-adapter install/versioning win and the "core is liftable into
Django" story with the least disruption, while keeping the door open to Option A
on a per-adapter basis whenever an upstream project agrees to host the adapter.
Treat **Option A** as the long-term end state for individual adapters, not a
big-bang migration.

## Success Criteria

- A base branch exists with entry-point discovery + boundary cleanup + a
  federated test plan, with no breaking change to `PRODUCTION_PROCESSES` and all
  existing tests green.
- Three exploration branches exist (A, B, C), each with enough working code to
  answer the decision criteria, plus a short `FINDINGS.md` on each branch.
- A written comparison (this spec updated, or a follow-up doc) recommending one
  option, with explicit answers to the six decision criteria.
- The core package's dependency closure is demonstrably just `django` in
  whichever option(s) implement a separate core.
- Docs describe the chosen install story and the backend plugin contract.

## Risks & Mitigations

- **Release tooling:** `semantic_release` config in `pyproject.toml` assumes one
  package; multi-package publishing needs new config or a different tool.
  *Mitigation:* spike this explicitly on the Option B branch before committing.
- **Discoverability regression:** users currently find everything via one
  package + extras. *Mitigation:* keep an umbrella `django-prodserver`
  distribution that pulls adapters via extras (Options A2 and B).
- **History loss on extraction:** *Mitigation:* use `git filter-repo` (document
  the recipe on the Option A branch) rather than fresh repos.
- **Upstreams say no:** gunicorn/uvicorn/celery may not want a Django-specific
  adapter. *Mitigation:* the contrib repo / per-adapter packages are the fallback
  home; nothing depends on upstream acceptance.
- **Namespace package pitfalls:** PEP 420 namespace packages (`django_prodserver.contrib.*`)
  can interact badly with some tooling. *Mitigation:* test both the namespace and
  the flat `django_prodserver_<name>` layouts on the option branches and pick the
  one that "just works".
