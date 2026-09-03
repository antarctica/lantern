# AGENTS.md

Guidance for AI coding agents working in this repository. See `/docs` for full human documentation (linked below).

## Big picture

Lantern (`src/lantern`) is the BAS Data Catalogue: a static site generator over Records (ISO 19115 / MAGIC
Discovery Profile metadata). Core flow: **Store → Repository → Catalogue → Site → Outputs → Exporter**.

- `lantern.stores` — read/write Records in a backend (`GitLabStore` is the source of truth; `AlgoliaStore` is a
  search index). See `/docs/stores.md`. `lantern.site.Site` runs Outputs across records in parallel (via `joblib`);
  stores holding unpicklable/expensive in-memory state MUST override `StoreBase.prep_parallel()` /
  `restore_parallel()` rather than being pickled whole per job (see `GitLabCachedStore` for an example).
- `lantern.repositories` — coordinate one or more Stores for a Catalogue (e.g. keep Algolia in sync when GitLab's
  default branch is merged).
- `lantern.catalogues.BasCatalogue` — the only supported Catalogue; wires together a Store, Site, Exporter, Checker.
- `lantern.site.Site` — builds a static site from Records using `lantern.outputs.*` (item pages, resources, API/health
  endpoints, redirects) and Jinja2 templates in `src/lantern/resources/templates`.
- `lantern.exporters` — write generated files locally or to AWS S3 (untrusted/public) or via rsync (trusted/internal,
  contains decrypted Administrative Metadata — see "Trusted Publishing" in `/docs/architecture.md`).
- `lantern.models.item.catalogue` — transforms a `Record` into presentation-ready `ItemCatalogue`/`Tab`/`Distribution`
  classes consumed by templates; this is where most record-property → UI logic lives.
- `lantern.lib` — extensions to third-party dependencies (e.g. `bas-metadata-library`), tested in `tests.lib_tests`.
- `lantern.contrib` — code meant for reuse by *other* applications, tested in `tests.contrib_tests`.
- `tasks/` — standalone CLI scripts (not part of the deployable `lantern` package) run via `python -m tasks.xxx`,
  exposed as `taskipy` tasks in `pyproject.toml` (e.g. `bootstrap-records`, `records_build`, `serve`).

Read `/docs/architecture.md` first for terminology (Catalogue, Store, Repository, Site, Output, Exporter) — these
words are used precisely and consistently across the codebase.

## Adding a feature: follow the recipes in docs/dev.md

`/docs/dev.md` contains step-by-step checklists for common extension points — **use these instead of guessing**,
since each touches multiple files that must stay in sync:

- Adding config options (`Adding configuration options`) — must update `Config`, `ConfigDumpSafe`, `dumps_safe()`,
  `docs/config.md`, `.env.tpl`, `[tool.pytest_env]` in `pyproject.toml`, and `test_config.py`.
- Adding a new item/hierarchy-level type (`Adding catalogue item types`).
- Adding a distribution format (`Adding distribution formats`) — new class under
  `lantern.models.item.catalogue.distributions`, enum member, macro in `_macros/_tabs/data.html.j2`.
- Adding an item tab (`Adding catalogue item tabs`) — class in `.tabs`, wired into `ItemCatalogue.tabs`, macro under
  `_macros/tabs` or `_macros/_tabs`, then run the `tailwind` task to pick up new classes.
- Adding a licence, site page, or relation type — see corresponding sections.

## Conventions (from docs/dev.md)

- All deployable code lives under `lantern` package; `tasks/` and `tests/` are excluded from `ty` type checking
  (`[tool.ty.src]` in `pyproject.toml`).
- Use `Path.resolve()` when logging/displaying paths; log via `logger = logging.getLogger('lantern')`.
- Ruff enforces `ban-relative-imports = "all"` — always use absolute imports (`from lantern.foo import Bar`).
- 100% test coverage is required (`fail_under = 100` in `[tool.coverage.report]`); use `# pragma: no cover` /
  `# pragma: no branch` for justified exceptions, and `@pytest.mark.cov()` for coverage-only tests.
- `ruff` (lint+format+bandit) and `ty` (type checking, main app code only) are the linters; `pymarkdown` lints docs.
- The Jinja environment (`lantern.utils.get_jinja_env()`) is `lru_cache`d — do not construct a new `Environment` per
  Output/record, this previously caused an 80%+ slowdown by recompiling all templates on every access.
- Prefer `functools.cached_property` for derived Output/Item properties that are read more than once per instance
  (e.g. `OutputBase.content`, `ItemCatalogue.*`) to avoid rebuilding object graphs or re-rendering templates.

## Developer workflows

Use [Taskipy](https://github.com/taskipy/taskipy) tasks (`uv run task --list`), not raw commands:

```shell
uv sync --all-groups && uv run playwright install   # setup
uv run task test            # pytest -n auto (main suite, tests/)
uv run task test-slow       # e2e/Playwright/Schemathesis suite (tests_slow/), slow
uv run task test-cov        # coverage (--cov-report=html -> htmlcov/)
uv run task lint            # ruff check
uv run task format          # ruff format
uv run task types           # ty check src/
uv run task css             # rebuild Tailwind CSS: builds a temp site, extracts used classes, writes main.css
uv run task build-test-records   # build a static site from tests.resources.records test fixtures
uv run task serve            # serve a built static site locally (HTTPS via trustme, basic auth)
```

- Run a single test: `uv run pytest tests/path/to/test_module.py::Class.method`.
- If tests fail with `NotImplementedError` after renaming/reparametrizing a test, run `uv run task test-reset`
  (clears the `--failed-first` pytest cache — see `docs/dev.md#pytest-fast-fail`).
- After changing CSS/JS, always re-run `build-test-records` afterwards — builds embed a local copy of compiled
  assets that won't reflect source changes otherwise (`task css && task build-test-records`).
- HTTP calls to external APIs are recorded/mocked via `pytest-recording`; update cassettes with
  `uv run pytest --record-mode=once tests/...::Test::test_x` (review cassettes for secrets before committing).
- Config is env-var driven (`LANTERN_*` prefix, see `lantern.Config`); tests get fake values from
  `[tool.pytest_env]` in `pyproject.toml` — new config options must be added there too.

## Testing conventions

- Fixtures go in `tests/conftest.py`, prefixed `fx_` (e.g. `fx_exporter_static_server`).
- Tests needing a real static site (Playwright, template checks) use `tests.resources.catalogues.fake_catalogue`
  / `tests.resources.stores.fake_records_store.FakeRecordsStore` and test records under `tests/resources/records/`
  (`item_cat_*.py`, built with `tests.resources.records.utils.make_record()`).
- Tests sharing the `fx_exporter_static_server` fixture MUST use the same xdist group:
  `@pytest.mark.xdist_group("e2e")` (see `docs/dev.md#pytest-xdist`).
- New test records must be registered in `item_cat_collection_all.collection_members` AND
  `FakeRecordsStore._fake_records()`.

## Style

`src/lantern/resources/templates` uses Jinja2 + Tailwind CSS (`_assets/css/main.css.j2`, compiled via the `css`
task — never hand-edit `resources/css/main.css`, it's generated). Follow `docs/site.md#styling-guidelines` for CSS
changes.
