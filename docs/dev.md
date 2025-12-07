# Lantern - Development

## Local development environment

Requirements:

- Git
- [UV](https://docs.astral.sh/uv/)
- [Pre-commit](https://pre-commit.com)
- [1Password CLI](https://developer.1password.com/docs/cli/get-started/)

Setup:

1. install tools (`brew install git uv pre-commit 1password-cli`)
1. clone and setup project [2]
1. configure app [3]
1. [generate](/docs/config.md#generate-an-environment-config-file) an `.env` file

[2]

```shell
% git clone https://gitlab.data.bas.ac.uk/MAGIC/lantern-exp.git
% cd lantern-exp/
% pre-commit install
% uv sync --all-groups
% uv run playwright install
```

## Development tasks

[Taskipy](https://github.com/taskipy/taskipy?tab=readme-ov-file#general) is used to define development tasks, such as
running tests and rebuilding site styles. These tasks are akin to NPM scripts or similar concepts.

Run `task --list` (or `uv run task --list`) for available commands.

Run `task [task]` (`uv run task [task]`) to run a specific task.

See [Adding development tasks](#adding-development-tasks) for how to add new tasks.

> [!TIP]
> If offline, use `uv run --offline task ...` to avoid lookup errors trying to the unconstrained build system
> requirements in `pyproject.toml`, which is a [Known Issue](https://github.com/astral-sh/uv/issues/5190) within UV.

## Contributing

All changes except minor tweaks (typos, comments, etc.) MUST:

- be associated with an issue (either directly or by reference)
- be included in the [Change Log](/CHANGELOG.md)

### Conventions

- all deployable code should be contained in the `lantern` package
- use `Path.resolve()` if displaying or logging file/directory paths
- use logging to record how actions progress, using the app logger (`logger = logging.getLogger('app')`)
- extensions to third party dependencies should be:
  - created in `lantern.lib`
  - documented in [Libraries](/docs/libraries.md)
  - tested in `tests.lib_tests/`

### Adding configuration options

In the `lantern.Config` class:

- define a new property
- add property to `ConfigDumpSafe` typed dict
- add property to `dumps_safe()` method
- if needed, add logic to `validate()` method

In the [Configuration](/docs/config.md) documentation:

- add to [Options Table](/docs/config.md#config-options) in alphabetical order
- if needed, add a subsection to explain the option in more detail

If configurable:

- update the `.env.tpl` template and any existing `.env` files
- update the `[tool.pytest_env]` section in `pyproject.toml`

In the `tests.lantern_tests.config` module:

- update the expected response in the `test_dumps_safe` method
- if validated, update the `test_validate` (valid) method and add new `test_validate_` (invalid) tests if needed
- if configurable, update the `test_configurable_property` method
- update or create other tests as needed

### Adding catalogue item types

> [!CAUTION]
> This section is Work in Progress (WIP) and may not be complete/accurate.

Update record schema to allow new item type in records:

1. if the type is not a member of the ISO 19115 `MD_ScopeCode` code list, create and agree a proposal in the
   [BAS Metadata Standards](https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-standards) project
2. if needed, add the type to the `hierarchy_level` enum in the ISO 19115 JSON Schema within the
   [BAS Metadata Library](https://github.com/antarctica/metadata-library) and make a new release as needed

Within this project:

1. if needed, upgrade the 'bas-metadata-library' dependency to a version including the new item type
2. add new [Test Records](#adding-new-test-records) as needed using the new item type
3. update the `prefixes` mapping in `lantern.models.record.record.Record._validate_aliases()` to set allowed aliases
4. update the allowed prefixes table in the [Record requirements](/docs/data-model.md#record-requirements) documentation
5. add item type to `lantern.models.item.base.enums.ResourceTypeLabel` enum
6. add item type to `lantern.models.item.catalogue.enums.ResourceTypeIcon` enum (see https://fontawesome.com/v5/search)
7. if a 'container' [Super Type](/docs/data-model.md#item-super-types), update the
  `lantern.models.item.catalogue.item.ItemCatalogue._super_type` property
8. verify the [Test Records](#test-records) build as a local site

If additional item relationships are needed:

1. add relevant properties to `lantern.models.item.catalogue.elements.Aggregations`
2. call new properties in `lantern.resources.templates._macros.related`
3. add tests as needed in:
   - `tests.lantern_tests.models.item.catalogue.test_elements.TestAggregations`
   - `tests.lantern_tests.templates.macros.test_tabs.TestRelatedTab`
4. update [Test records](#test-records) to set aggregations as needed

### Adding properties to items

> [!CAUTION]
> This section is Work in Progress (WIP) and may not be complete/accurate.

1. if needed, [Support New Record Properties](/docs/libraries.md#adding-new-record-properties)
2. if needed, update [Item](/docs/data-model.md#items) classes to process new and/or existing properties
   - existing properties may need updating such as `ItemBase.kv` handling
3. add new properties to the relevant item tab class in `lantern.models.item.catalogue.tabs`
   - work backwards to include additional Record properties in the main `lantern.models.item.catalogue` class
   - and/or `lantern.models.item.catalogue.elements` classes
   - amend tests that directly instantiate these classes to include the new property
     - some of these are not obvious where `kwargs` are used to pass properties such as:
       `lantern.models.item.catalogue.special.physical_map.AdditionalInfoTab`
4. update the [Site Template](/docs/site.md#templates) to include the new property as needed
5. add tests as needed for:
   - Record properties
   - Item properties
   - Item Catalogue tab, element and base classes
   - Item templates (static HTML tests and Playwright if needed)
6. update any relevant record authoring guides to explain how new properties are handled by the Catalogue
7. if a property is required for all items:
   - update the [Record Requirements](/docs/data-model.md#record-requirements) documentation
   - in future this may include updating a corresponding JSON Schema too
8. amend list of unsupported properties in `/docs/data-model.md#catalogue-item-limitations` as needed

### Adding distribution formats

1. create a new class under `lantern.models.item.catalogue.distributions` inheriting from `Distribution` or a relevant
   subclass
2. if needed register new media-types under the Metadata Standards resources site (`metadata-resources.data.bas.ac.uk`)
3. configure the new class:
   - set the `matches` class method to determine a exclusive match for the distribution (typically via media types)
   - add an item to the `lantern.models.item.catalogue.enums.DistributionType` enum for the distribution type
4. add the new class to `lantern.models.item.catalogue.tabs.DataTab._supported_distributions` list
5. if the distribution should use a collapsible information panel, edit the
   `src/lantern/resources/templates/_macros/_tabs/data.html.j2` macros in the [Site Templates](/docs/site.md#templates):
   - create a new macro for the distribution format
   - update the `panel` macro to call the new macro
6. include the new distribution format in`lantern.models.verification.elements.VerificationDistribution`
7. include the new distribution format in [Test Records](#test-records):
   - `tests.resources.records/item_cat_data::record`
   - `tests.resources.records/item_cat_verify::record`
8. update `lantern.models.verification.elements.VerificationDistribution`
9. add a new tests to:
   - `tests.lantern_tests.models.item.catalogue.test_distributions`
   - `tests.lantern_tests.templates.macros.test_tabs.TestDataTab.test_data_info` (if using a collapsible panel)

### Adding catalogue item tabs

> [!CAUTION]
> This section is Work in Progress (WIP) and may not be complete/accurate.

1. create a new class in `lantern.models.item.catalogue.tabs` inheriting from `lantern.models.item.catalogue.tabs.Tab`
   - set the `anchor`, `title`, `icon` properties
   - add tab specific properties and logic
   - create catalogue specif elements or element subclasses in `lantern.models.item.catalogue.elements` as needed
   - set logic for the `enables` property based on relevant tab properties
2. in `lantern.models.item.catalogue.item.ItemCatalogue`:
   - add a private property returning an instance of the tab class
   - call property in `tabs` property
   - update `default_tab_anchor` property if tab is optional and/or should be shown before additional information tab
3. create a new macro in `lantern.resources.templates._macros.tabs` named after the tab anchor
   - ensure the section ID attribute is set correctly for tab navigation to work
   - populate tab macro as needed
   - create additional macros nearby (if one or two), or under `lantern.resources.templates._macros._tabs`
4. run `tailwind` [Development Task](#development-tasks) to update styles (for tab classes to work)
5. update `lantern_tests.models.item.catalogue.test_tabs` to cover new tab class
6. update `lantern_tests.models.item.catalogue.test_item_catalogue.TestItemCatalogue.test_tabs` to include new tab class
7. update `TestItemCatalogue.test_default_tab_anchor` if tab should be shown before additional information tab
8. updates tests within `lantern_tests.templates` as needed

### Adding catalogue licences

> [!CAUTION]
> This section is Work in Progress (WIP) and may not be complete/accurate.

1. update `lantern.models.item.catalogue.enums.Licence`
2. in `src/lantern/resources/templates/_macros/_tabs/licence.html.j2`:
   - create a new macro calling the `licence` macro, named after a lower case version of the Licence enum item
3. create a new test record in `tests.resources.records.item_cat_licence`
4. add test record to:
   - `tests.resources.records.item_cat_collection_all`
   - `tests.resources.stores.fake_records_store.FakeRecordsStore._fake_records`

### Adding site pages

> [!CAUTION]
> This section is Work in Progress (WIP) and may not be complete/accurate.

- ... include in `VerificationExporter.site_pages` list

### Updating styles

> [!IMPORTANT]
> Follow the [Styling Guidelines](/docs/site.md#styling-guidelines) when updating styles.

1. if needed, add styles/rules to `src/lantern/resources/css/main.css.j2`
2. apply classes as necessary to elements in [Templates](/docs/site.md#templates)
3. run the `tailwind` [Development Task](/docs/dev.md#development-tasks) which will:
   - build a temporary [Static Site](/docs/architecture.md#static-site) containing [Test Records](#test-records)
   - run Tailwind compiler against this site, adding or removing classes as needed
   - copy the resulting minified CSS to `src/lantern/resources/css/main.css`
4. run the `build-test-records` or `build-records` [Development Task](/docs/dev.md#development-tasks) to rebuild the
   static site
   - needed as builds reference a local copy of `main.css` that will need refreshing

> [!TIP]
> You can run `uv run task tailwind && uv run task build-test-records` to chain these tasks together.

### Adding development tasks

See the [Taskipy](https://github.com/taskipy/taskipy?tab=readme-ov-file#adding-tasks) documentation.

## Python version

The minimum Python version is 3.11 for consistency with related projects.

## Dependencies

### Vulnerability scanning

The [Safety](https://pypi.org/project/safety/) package checks dependencies for known vulnerabilities.

> [!WARNING]
> As with all security tools, Safety is an aid for spotting common mistakes, not a guarantee of secure code.
> In particular this is using the free vulnerability database, which is updated less frequently than paid options.

Checks are run automatically in [Continuous Integration](#continuous-integration).

> [!TIP]
> To check locally run the `safety` [Development Task](#development-tasks).

### Updating dependencies

- create an issue and switch to branch
- run `uv tree --outdated --depth=1` to list outdated packages
- follow https://docs.astral.sh/uv/concepts/projects/sync/#upgrading-locked-package-versions
- note upgrades in the issue
- review any major/breaking upgrades
- run [Tests](#testing) manually
- commit changes

> [!TIP]
> If playwright is upgraded, update the image used in CI to match the new version.

## Linting

### Ty

[Ty](https://docs.astral.sh/ty/) is used for static type checking in main application Python files (not tests, etc.).
Default options are used. Type checks are run automatically in [Continuous Integration](#continuous-integration) and
the [Pre-Commit Hook](#pre-commit-hook).

<!-- pyml disable md028 -->
> [!NOTE]
> Ty is an experimental tool and may report false positives. Type checking may be removed if it becomes a burden.

> [!TIP]
> To check types manually run the `types` [Development Task](#development-tasks).
<!-- pyml enable md028 -->

### Ruff

[Ruff](https://docs.astral.sh/ruff/) is used to lint and format Python files. Specific checks and config options are
set in [`pyproject.toml`](/pyproject.toml). Linting checks are run automatically in
[Continuous Integration](#continuous-integration) and the [Pre-Commit Hook](#pre-commit-hook).

> [!TIP]
> To check linting manually run the `lint` [Development Task](#development-tasks), for formatting run the `format` task.

### Static security analysis

[Ruff](#ruff) is configured to run [Bandit](https://github.com/PyCQA/bandit), a static analysis tool for Python.

> [!WARNING]
> As with all security tools, Bandit is an aid for spotting common mistakes, not a guarantee of secure code.
> In particular this tool can't check for issues that are only be detectable when running code.

### Markdown

[PyMarkdown](https://pymarkdown.readthedocs.io/en/latest/) is used to lint Markdown files. Specific checks and config
options are set in [`pyproject.toml`](/pyproject.toml). Linting checks are run automatically in
[Continuous Integration](#continuous-integration) and the [Pre-Commit Hook](#pre-commit-hook).

> [!TIP]
> To check linting manually run the `markdown` [Development Task](#development-tasks).

Wide tables will fail rule `MD013` (max line length). Wrap such tables with pragma disable/enable exceptions:

```markdown
<!-- pyml disable md013 -->
| Header | Header |
|--------|--------|
| Value  | Value  |
<!-- pyml enable md013 -->
```

Stacked admonitions will fail rule `MD028` (blank lines in blockquote) as it's ambiguous whether a new blockquote has
started where another element isn't inbetween. Wrap such instances with pragma disable/enable exceptions:

```markdown
<!-- pyml disable md028 -->
> [!NOTE]
> ...

> [!NOTE]
> ...
<!-- pyml enable md028 -->
```

### Editorconfig

For consistency, it's strongly recommended to configure your IDE or other editor to use the
[EditorConfig](https://editorconfig.org/) settings defined in `.editorconfig`.

### Pre-commit hook

A [Pre-Commit](https://pre-commit.com) hook is configured in `.pre-commit-config.yaml`.

To update Pre-Commit and configured hooks:

```shell
% pre-commit autoupdate
```

> [!TIP]
> To run pre-commit checks against all files manually run the `pre-commit` [Development Task](#development-tasks).

## Testing

### Pytest

[pytest](https://docs.pytest.org) with a number of plugins is used for testing the application. Config options are set
in `pyproject.toml`. Tests are defined in the `tests` package.

> [!NOTE]
> Parallel processing is disabled for tests to avoid issues with [HTTP recording](#pytest-recording) by setting the
> `PARALLEL_JOBS` [config option](#pytest-env).

Tests are run automatically in [Continuous Integration](#continuous-integration).

<!-- pyml disable md028 -->
> [!TIP]
> To run tests manually run the `test` [Development Task](#development-tasks).

> [!TIP]
> To run a specific test:
>
> ```shell
> % uv run pytest tests/path/to/test_module.py::<class>.<method>
> ```
<!-- pyml enable md028 -->

### Pytest fast fail

If a test run fails with a `NotImplementedError` exception run the `test-reset` [Development Task](#development-tasks).

This occurs where:

- a test fails and the failed test is then renamed or parameterised options changed
- the reference to the previously failed test has been cached to enable the `--failed-first` runtime option
- the cached reference no longer exists triggering an error which isn't handled by the `pytest-random-order` plugin

Running this task clears Pytest's cache and re-runs all tests, skipping the `--failed-first` option.

### Pytest fixtures

Fixtures SHOULD be defined in `tests.conftest` prefixed with `fx_` to indicate they are a fixture when used in tests.
E.g.:

```python
import pytest

@pytest.fixture()
def fx_foo() -> str:
    """Example test fixture."""
    return 'foo'
```

### Pytest-cov test coverage

[`pytest-cov`](https://pypi.org/project/pytest-cov/) checks test coverage. We aim for 100% coverage but exemptions are
fine with good justification:

- `# pragma: no cover` - for general exemptions
- `# pragma: no branch` - where a conditional branch can never be called

[Continuous Integration](#continuous-integration) will check coverage automatically.

<!-- pyml disable md028 -->
> [!TIP]
> To check coverage manually run the `test-cov` [Development Task](#development-tasks).

> [!TIP]
> To run tests for a specific module locally:
>
> ```shell
> % uv run pytest --cov=lantern.some.module --cov-report=html tests/lantern_tests/some/module
> ```
<!-- pyml enable md028 -->

Where tests are added to ensure coverage, use the `cov` [mark](https://docs.pytest.org/en/7.1.x/how-to/mark.html), e.g:

```python
import pytest

@pytest.mark.cov()
def test_foo():
    assert 'foo' == 'foo'
```

### Pytest-env

[pytest-env](https://pypi.org/project/pytest-env/) sets environment variables used by the [Config](/docs/config.md)
class to fake values when testing. Values are configured in the `[tool.pytest_env]` section of `pyproject.toml`.

### Pytest-recording

[pytest-recording](https://github.com/kiwicom/pytest-recording) is used to mock HTTP calls to provider APIs (ensuring
known values are used in tests).

> [!CAUTION]
> Review recorded responses to check for any sensitive information.

To update a specific test:

```text
% uv run pytest --record-mode=once tests/path/to/test_module.py::<class>::<method>
# E.g.
% uv run pytest --record-mode=once tests/lantern_tests/stores/test_gitlab_store.py::TestGitLabLocalCache::test_fetch_file_commits
```

To incrementally build up a set of related tests (including parameterised tests) use the `new_episodes` recording mode:

```text
% uv run pytest --record-mode=new_episodes tests/path/to/test_module.py::<class>::<method>
```

### Static site template tests

Pytest parameterised tests with [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) are used to
check expected content is returned for each variant of [Static Site Templates](/docs/site.md#item-templates), e.g. with
and without an optional property.

### Playwright tests

[Playwright](https://playwright.dev/) Python tests are used to verify the behaviour of dynamic JavaScript content,
such as switching tabs in items and opening/closing the feedback widget.

To run a specific test file with visible output:

```shell
% uv run pytest --headed tests/lantern_tests/e2e/test_item_e2e.py
```

Playwright tests require a real website to test against, which is provided by the `fx_exporter_static_server` fixture.
This hosts a local [Static Site](/docs/architecture.md#static-site) served from a temporary directory using Python's
simple HTTP server. The site is built by the `fx_exporter_static_site` fixture and contains all
[Test Records](#test-records).

> [!NOTE]
> This local server cannot be used directly in CI. Instead, a Python simple server serving a known (initially empty)
> path in the build directory is started before Pytest runs. The `fx_exporter_static_server` detects the CI environment
> and copies the static site build to this path, then quits, giving an equivalent outcome.

### Test records

To aid in debugging and testing, a set of fake records are included in `tests/resources/records/`. They include:

- example collections and products with only minimal properties set
- example collections and products with all optional properties set
- example items to test supported formatting options in free-text properties
- example items to test supported distribution options and verification types
- example items for each supported licence
- examples of special items, such as physical maps

These records are used within tests but can and should also be used when developing [Templates](/docs/site.md#templates).

A set of test keys are used for signing and encrypting
[Administrative Metadata](/docs/data-model.md#item-administrative-metadata) within test records. These keys are
were generated using `tests.resources.records.admin_keys.testing_keys._make_keys()` and intended as static values
available via [Pytest-Env](#pytest-env) and `tests.conftest._admin_meta_keys` and its related fixture.

> [!TIP]
> An additional `X_ADMIN_METADATA_SIGNING_KEY_PRIVATE` environment variable is set to load the private signing key for
> use signing admin metadata instances for use in tests and test records.

An in-memory [Store](/docs/architecture.md#stores) is provided to load these records for use with
[Exporters](/docs/architecture.md#exporters).

To add a new test record:

> [!CAUTION]
> This section is Work in Progress (WIP) and may not be complete/accurate.

1. create new `tests/resources/records/item_cat_*.py` file or clone from minimal examples
   - records MUST use a unique `file_identifier`
   - the `tests.resources.records.utils.make_record()` method SHOULD be used as a base (properties can be unset later)
2. include the record in the `tests.resources.records.item_cat_collection_all.collection_members` list
3. include the record in the `resources.stores.fake_records_store.FakeRecordsStore._fake_records()` method

> [!TIP]
> Run the `build-test-records` [Development Task](#development-tasks) to export a static site using these records.
>
> Run the `serve` task to host an exported static site, with real or test records, locally.

### Continuous Integration

All commits will trigger Continuous Integration using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.
