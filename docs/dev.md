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

```
% git clone https://gitlab.data.bas.ac.uk/MAGIC/lantern-exp.git
% cd lantern-exp/
% pre-commit install
% uv sync --all-groups
% uv run playwright install
```

## Development tasks

[Taskipy](https://github.com/taskipy/taskipy?tab=readme-ov-file#general) is used to define development tasks, such as
running tests and rebuilding site styles. These tasks are akin to NPM scripts or similar concepts.

Run `uv run task --list` for available commands.

Run `uv run task [task]` to run a specific task.

See [Adding development tasks](#adding-development-tasks) for how to add new tasks.

> [!TIP]
> If offline, use `uv run --offline task ...` to avoid lookup errors trying to the unconstrained build system
> requirements in `pyproject.toml`, which is a [Known Issue](https://github.com/astral-sh/uv/issues/5190) within UV.

## Contributing

All changes except minor tweaks (typos, comments, etc.) MUST:

- be associated with an issue (either directly or by reference)
- be included in the [Change Log](/CHANGELOG.md)

Conventions:

- all deployable code should be contained in the `lantern` package
- use `Path.resolve()` if displaying or logging file/directory paths
- use logging to record how actions progress, using the app logger (`logger = logging.getLogger('app')`)
- extensions to third party dependencies should be:
  - created in `lantern.lib`
  - documented in [Libraries](/docs/libraries.md)
  - tested in `tests.lib_tests/`

## Python version

The Python version is limited to 3.11 for consistency with related projects.

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
- follow https://docs.astral.sh/uv/concepts/projects/sync/#upgrading-locked-package-versions
- note upgrades in the issue
- review any major/breaking upgrades
- run [Tests](#testing) manually
- commit changes

## Linting

### Ruff

[Ruff](https://docs.astral.sh/ruff/) is used to lint and format Python files. Specific checks and config options are
set in [`pyproject.toml`](/pyproject.toml). Linting checks are run automatically in
[Continuous Integration](#continuous-integration).

> [!TIP]
> To check linting manually run the `lint` [Development Task](#development-tasks), for formatting run the `format` task.

### Static security analysis

[Ruff](#ruff) is configured to run [Bandit](https://github.com/PyCQA/bandit), a static analysis tool for Python.

> [!WARNING]
> As with all security tools, Bandit is an aid for spotting common mistakes, not a guarantee of secure code.
> In particular this tool can't check for issues that are only be detectable when running code.

### Editorconfig

For consistency, it's strongly recommended to configure your IDE or other editor to use the
[EditorConfig](https://editorconfig.org/) settings defined in `.editorconfig`.

### Pre-commit hook

A [Pre-Commit](https://pre-commit.com) hook is configured in `.pre-commit-config.yaml`.

> [!TIP]
> To run pre-commit checks against all files manually run the `pre-commit` [Development Task](#development-tasks).

## Testing

### Pytest

[pytest](https://docs.pytest.org) with a number of plugins is used for testing the application. Config options are set
in `pyproject.toml`. Tests are defined in the `tests` package.

Tests are run automatically in [Continuous Integration](#continuous-integration).

> [!TIP]
> To run tests manually run the `test` [Development Task](#development-tasks).

> [!TIP]
> To run a specific test:
>
> ```
> % uv run pytest tests/path/to/test_module.py::<class>.<method>
> ```

> [!TIP]
> If a test run fails with a `NotImplementedError` exception run the `test-reset` [Development Task](#development-tasks).
>
> This occurs where:
>
> - a test fails and the failed test is then renamed or parameterised options changed
> - the reference to the previously failed test has been cached to enable the `--failed-first` runtime option
> - the cached reference no longer exists triggering an error which isn't handled by the `pytest-random-order` plugin
>
> Running this task clears Pytest's cache and re-runs all tests, skipping the `--failed-first` option.

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

> [!TIP]
> To check coverage manually run the `test-cov` [Development Task](#development-tasks).

> [!TIP]
> To run tests for a specific module locally:
>
> ```
> % uv run pytest --cov=lantern.some.module --cov-report=html tests/lantern_tests/some/module
> ```

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

To (re-)record all responses:

```
% uv run pytest --record-mode=all
```

**Note:** Review recorded responses to check for any sensitive information.

To update a specific test:

```
% uv run pytest --record-mode=once tests/path/to/test_module.py::<class>.<method>
```

To incrementally build up a set of related tests (including parameterised tests) use the `new_episodes` recording mode:

```
% uv run pytest --record-mode=new_episodes tests/path/to/test_module.py::<class>.<method>
```

#### Pytest-recording binary data

To update a pytest-recording response that contains binary data (e.g. a `.tar.gz` archive) in a captured response:

1. set the binary content and output filename in `./tests/scripts/decode_binary_response.py` and run
2. update the output file as needed (e.g. extract the output, update as needed and re-compress [1])
3. set the input filename in `./tests/scripts/encode_binary_response.py` and run
4. copy the output string back into the pytest-recording response

[1] To compress a `foo` directory as `bar.tar.gz`:

```shell
tar -czvf 'bar.tar.gz' 'foo'
```

### Playwright tests

[Playwright](https://playwright.dev/) Python tests are used to verify the behaviour of dynamic JavaScript content,
such as switching tabs in items and opening/closing the feedback widget.

To run a specific test file with visible output:

```
% uv run pytest --headed tests/lantern_tests/e2e/test_item_e2e.py
```

### Static site template tests

Pytest parameterised tests with [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) are used to
check expected content is returned for each variant of [Static Site Templates](/docs/site.md#item-templates), e.g. with
and without an optional property.

### Test records

To aid in debugging and testing, a set of fake records are included in `tests/resources/records/`. They include:

- example collections and products with only minimal properties set
- example collections and products with all optional properties set
- example items to test formatting free-text properties
- example items with all supported distribution options
- example items for each supported licence
- example special items, such as physical maps

These records are used within tests but can and should also be used when developing template changes etc.

An in-memory [Store](/docs/architecture.md#stores) is provided containing these test/fake records.

> [!TIP]
> Run the `build-test-records` [Development Task](#development-tasks) to export a static site using these records.
>
> Run the `serve` task to host an exported static site, with real or test records, locally.

### Continuous Integration

All commits will trigger Continuous Integration using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.

## Adding configuration options

In the `lantern.Config` class:

- define a new property
- add property to `ConfigDumpSafe` typed dict
- add property to `dumps_safe()` method
- if needed, add logic to `validate()` method

In the [Configuration](/docs/config.md) documentation:

- add to [Options Table](/docs/config.md#config-options) in alphabetical order
- if needed, add a subsection to explain the option in more detail
- if configurable, update the `.env.tpl` template and existing `.env` file
- if configurable, update the `[tool.pytest_env]` section in `pyproject.toml`

In the `tests.lantern_tests.config` module:

- update the expected response in the `test_dumps_safe` method
- if validated, update the `test_validate` (valid) method and add new `test_validate_` (invalid) tests
- update or create other tests as needed

## Adding development tasks

See the [Taskipy](https://github.com/taskipy/taskipy?tab=readme-ov-file#adding-tasks) documentation.

## Updating styles

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
