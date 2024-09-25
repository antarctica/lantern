# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - Development

## Development environment

Requirements:

* Python 3.9 ([pyenv](https://github.com/pyenv/pyenv) recommended)
* [Poetry](https://python-poetry.org/docs/#installation) (1.8+)
* Git (`brew install git`)
* Postgres with PostGIS extension (`brew install postgis`)
* Pre-commit (`pipx install pre-commit`)

Clone project:

```
$ git clone https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox.git
$ cd add-metadata-toolbox
```

Install project:

```
$ poetry install
```

Create database and enable extensions:

```
$ createdb add-toolbox-dev
$ psql -d add-toolbox-dev -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

Set configuration as per the [Configuration](/docs/config.md) documentation:

```
$ cp .env.example .env
```

Install pre-commit hooks:

```
$ pre-commit install
```

## Running CLI commands

### Running all components locally

Useful for:

* end-to-end testing
* testing changes to how data is loaded into CSW catalogues

```shell
# Start the Flask application as a server (it will use the local postgres database by default)
$ FLASK_APP=scar_add_metadata_toolbox poetry run flask run --port 5050

# In another terminal; Run Flask CLI commands as a client (see quick start section below)
$ FLASK_APP=scar_add_metadata_toolbox poetry run flask [command]

# In another terminal; Run a simple web server for the static site
$ poetry run python -m http.server 9000 --directory _site
```

See the [CLI Reference](/docs/cli-reference.md) for how to use the CLI. Where `flask` is written, replace this with
the command example above.

When built, the local static site can be accessed from [http://localhost:9000](http://localhost:9000).

Quick start (example):

```shell
$ FLASK_APP=scar_add_metadata_toolbox poetry run flask csw setup db unpublished
# follow steps in setup documentation for fixing indexes in CSW backing DB
$ FLASK_APP=scar_add_metadata_toolbox poetry run flask csw setup db published
$ FLASK_APP=scar_add_metadata_toolbox poetry run flask csw setup repo unpublished
$ FLASK_APP=scar_add_metadata_toolbox poetry run flask auth sign-in
$ FLASK_APP=scar_add_metadata_toolbox poetry run flask records import --publish path/to/some-example-record.json
$ FLASK_APP=scar_add_metadata_toolbox poetry run flask site build
# (after example-record updated)
$ FLASK_APP=scar_add_metadata_toolbox poetry run flask records import --publish --allow-update --allow-republish path/to/some-example-record.json
$ FLASK_APP=scar_add_metadata_toolbox poetry run flask site build
```

### Building a local static site with production data

Useful for developing and testing changes to static website templates.

See the [CLI Reference](/docs/cli-reference.md) for how to use the CLI. Where `flask` is written, replace this
with:

```shell
# Run Flask CLI commands as a client, with remote server
$ FLASK_APP=scar_add_metadata_toolbox CSW_ENDPOINT_UNPUBLISHED=https://api.bas.ac.uk/data/metadata/add/csw/v1/unpublished CSW_ENDPOINT_PUBLISHED=https://api.bas.ac.uk/data/metadata/add/csw/v1/published poetry run flask [command]
```

When built, and in another terminal, run:

```
$ poetry run python -m http.server 9000 --directory _site
```

The local static site can then be accessed from [http://localhost:9000](http://localhost:9000).

### Using a local client and local server with a remote database

Useful for testing with real data but where changes to the server application are being developed or tested.

```shell
# Start the Flask application as a server (using the production database)
$ FLASK_APP=scar_add_metadata_toolbox CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION=xxx CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION=xxx CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_REMOTE_URL=https://gitlab.data.bas.ac.uk/MAGIC/add-catalogue-records-production.git poetry run flask run --port 5050

# In another terminal; Run Flask CLI commands as a client
$ FLASK_APP=scar_add_metadata_toolbox poetry run flask [command]
```

Where the value for `CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION` and
`CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION` is the relevant database connection string (staging or production).
See the [Infrastructure](/docs/infrastructure.md#databases) documentation for details.

The `CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_REMOTE_URL` variable is set to the production repo as if
production data is being modified it should be tracked in the production repo too.

**Note:** If the staging database is used, the `CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_REMOTE_URL` should not be changed.

See the [CLI Reference](/docs/cli-reference.md) for how to use the CLI. Where `flask` is written, replace this with
the command example above.

When built, the local static site can be accessed from [http://localhost:9000](http://localhost:9000).

## Contributing

All changes except minor tweaks (typos, comments, etc.) MUST:

- be associated with an issue (either directly or by reference)
- be included in the [Change Log](/CHANGELOG.md)

Conventions:

- all deployable code should be contained in the `scar-add-metadata-toolbox` package
- use `Path.resolve()` if displaying or logging file/directory paths
- use logging to record how actions progress, using the Flask logger
  - (e.g. `current_app.logger.info('Log message')`)

## Python version

The Python version is limited to 3.9 due to the BAS IT deployment environment.

## Dependencies

Python dependencies for this project are managed with [Poetry](https://python-poetry.org) in `pyproject.toml`.

Non-code files, such as static files, can also be included in the [Python package](/docs/deploy.md#python-package)
using the `include` key in `pyproject.toml`.

### Adding new dependencies

To add a new (development) dependency:

```shell
$ poetry add (--group dev) [dependency]
```

The [CI container](#ci-container) will be rebuilt by GitLab automatically whenever dependencies change.

### Vulnerability scanning

The [Safety](https://pypi.org/project/safety/) package is used to check dependencies against known vulnerabilities.

**WARNING!** As with all security tools, Safety is an aid for spotting common mistakes, not a guarantee of secure code.
In particular this is using the free vulnerability database, which is updated less frequently than paid options.

Checks are run automatically in [Continuous Integration](#continuous-integration). To check locally:

```
$ poetry run safety scan
```

### Listing outdated dependencies

To list out of date dependencies:

```shell
$ poetry show --outdated
```

**Note:** This will include non-primary dependencies (i.e. not those listed directly in `pyproject.toml`), which should
normally be ignored.

**Note:** To find out why a dependency is required, run `poetry show [package]`.

### Updating dependencies

To update packages within their allowed constraints:

```shell
$ poetry update
```

The [CI container](#ci-container) will be rebuilt by GitLab automatically whenever dependencies change.

To update dependencies to their latest versions:

1. [List outdated dependencies](#listing-outdated-dependencies)
2. review this list against version constraints in `pyproject.toml` and against change logs for each package
3. for packages that are ok to update to their latest versions, update the version constraint in `pyproject.toml`
4. perform an update as listed above

**Note:** If a dependency cannot be updated due to a conflict with another package or Python version, pin the version
as needed and append a comment to explain which package is blocking further updates, e.g.:

```python
  # pinned because >= 0.3.2 requires Python > 3.6
```

### Updating minimum Python version [WIP]

As dependencies drop support for older Python versions, pressure will build to increase the minimum Python version
required for this package (e.g. from `3.6` to `3.8`). When this pressure becomes too great (e.g. due to incompatibility
with OS packages, security vulnerabilities, etc.), the minimum Python version should be increased.

Suggested upgrade steps:

1. upgrade to new Python version but keeping the same dependency versions (except `pyproj` and backports)
1. address any code incompatibilities due to backports
1. upgrade dependencies to their latest versions, as per the [Updating dependencies](#updating-dependencies) section

For step (1):

1. if using `pyenv`, switch to the latest patch release of new Python version (e.g. 3.8.15)
1. in `poetry.toml` change `python` dependency to new Python version (e.g. `^3.8`)
1. re-create the virtual environment to check all dependencies install correctly (`rm -rf .venv && poetry install`)
1. run application [Tests](#pytest) manually
1. update the base image used in the [CI container](#ci-container) to the new Python version (e.g. `python:3.8-alpine`)
1. check whether the [`pyproj`](#upgrading-pyproj-dependency) dependency can be updated

### Upgrading `pyproj` dependency

The [pyproj](https://pyproj4.github.io/pyproj/stable/index.html) dependency depends on the version of the
[`PROJ`](https://proj.org) library installed. Special care should therefore be taken to ensure the version of *pyproj*
required by this package supports the version of *PROJ* library available on target platforms.

The *pyproj* website documents the minimum version of PROJ and Python required for each release. For example version
3.4.0 requires:

* Python 3.8
* PROJ 8.2

For development, in addition to local development environments (where it's assumed any version requirements can be met),
the [CI Container](#ci-container) needs to be checked. This container uses the Alpine Python base image corresponding
to the minimum Python version used by the package.

Newer Alpine releases are used for newer versions of Python, and newer versions of PROJ are packaged for newer versions
of Alpine. Care therefore needs to be taken if the version of Python used is old. To check the version of PROJ
available within this container image:

```
$ docker run -it --rm docker-registry.data.bas.ac.uk/magic/add-metadata-toolbox/ci-cd:latest ash
$ proj -v
proj_create: unrecognized format / unknown name
Rel. 9.0.0, March 1st, 2022
<proj>:
projection initialization failure
cause: Invalid PROJ string syntax
program abnormally terminated
```

If these dependencies can be satisfied for all target platforms, it is safe to upgrade the `pyproj` dependency.

### Updating `bas-metadata-libray` dependency

Special care should be taken when the `bas-metadata-library` switches to a new
[Record Configuration Version](https://github.com/antarctica/metadata-library?tab=readme-ov-file#supported-configuration-versions).

**Note:** When this is not the case this dependency can be upgraded like any other and this section skipped.

To upgrade, a multi-stage process should be followed to manage the rate of change. At each stage, application tests
should be re-run to ensure regressions are not introduced. Additional (edge) test cases may need to be added to the
test suite as real world testing/deployment uncovers unforeseen regressions.

Suggested upgrade steps:

1. upgrade the Pip dependency for the Metadata Library to the new version (`poetry update bas-metadata-library`):
    * this will usually mean all MetadataRecord classes will use the new config version internally
    * where a new MetadataRecordConfig class is returned it should be downgraded to the old version
    * where a new MetadataRecordConfig class is required as input, it should be upgraded from the old version
    * the `Record.load()`, `Record.dump()` & `Record.dumps()` and `Repository.retrieve_record()` &
      `Repository.retrieve_records()` methods will need to be updated
    * usually calling the relevant `upgrade_from_vX_config()` or `downgrade_to_vX_config()` methods is enough to
      migrate between configuration versions, additional tweaks may be needed depending on the config schema changes
2. use new Metadata Configuration classes natively:
    * this means all references to the old MetadataRecordConfig class should be removed
    * this also means uses of the `upgrade_from_vX_config()` or `downgrade_to_vX_config()` methods should be removed
    * change properties in the `Record` and `Item` classes to be compatible with the new config schema, whilst
      preserving the form of returned information as far as possible [1]
    * update tests to use the new MetadataRecordConfig class
    * update test record configurations to be compatible with the new config schema
3. use new or changed properties from the new config schema:
    * this will depend on the nature of the new schema, but usually means adding new properties to the `Record` or
      `Item` classes, or changing existing properties to include additional or different information
    * these changes can then be surfaced in templates or other outputs
    * each change should use a dedicated feature branch to make changes more atomic and easier to review
    * suitable tests should be added or extended to ensure test coverage and to prevent future regressions
    * where relevant, other refactoring should be considered if large changes are made

[1]

For example, An existing property such as *lineage* is changed from a string to an object, to support new,
additional, configuration properties. To illustrate in pseudocode:

* going from: `lineage: '...'`
* to: `lineage: {statement: '...', additional_property: '...'}`.

In step (2) of the schedule above, the existing `Record.lineage()` Python property (or `Item.lineage()` property
depending on the class) should be changed to read from `config.lineage.statement` rather than `config.lineage`. This
preserves the existing interface of the Python property and ignores new features from the new config schema.

Later in step (3), the `Record.lineage()` or `Item.lineage()` Python property can be amended to return both
properties, or new properties added for the additional property if that makes more sense.

## Linting

### Ruff

[Ruff](https://docs.astral.sh/ruff/) is used to lint and format Python files. Specific checks and config options are
set in [`pyproject.toml`](/pyproject.toml). Linting checks are run automatically in
[Continuous Integration](#continuous-integration).

To check linting locally:

```
$ poetry run ruff check src/ tests/
```

To run and check formatting locally:

```
$ poetry run ruff format src/ tests/
$ poetry run ruff format --check src/ tests/
```

### Static security analysis

Ruff is configured to run [Bandit](https://github.com/PyCQA/bandit), a static analysis tool for Python.

**WARNING!** As with all security tools, Bandit is an aid for spotting common mistakes, not a guarantee of secure code.
In particular this tool can't check for issues that are only be detectable when running code.

### Editorconfig

For consistency, it's strongly recommended to configure your IDE or other editor to use the
[EditorConfig](https://editorconfig.org/) settings defined in [`.editorconfig`](/.editorconfig).

### Pre-commit hook

A set of [Pre-Commit](https://pre-commit.com) hooks are configured in
[`.pre-commit-config.yaml`](/.pre-commit-config.yaml). These checks must pass to make a commit.

To run pre-commit checks manually:

```
$ pre-commit run --all-files
```

## Testing

### Pytest

[pytest](https://docs.pytest.org) with a number of plugins is used to test the application. Config options are set in
[`pyproject.toml`](../pyproject.toml). Tests checks are run automatically in
[Continuous Integration](#continuous-integration).

Tests for the application are defined in the
[`tests/scar_add_metadata_toolbox_tests`](/tests/scar_add_metadata_toolbox_tests) module.

To run tests locally:

```shell
$ poetry run pytest
```

### Pytest fixtures

Fixtures should be defined in [conftest.py](/tests/conftest.py), prefixed with `fx_` to indicate they are a fixture,
e.g.:

```python
import pytest

@pytest.fixture()
def fx_test_foo() -> str:
    """Example of a test fixture."""
    return 'foo'
```

#### Fixture helper

The [`create_runner()`](/tests/conftest.py) method helps common patching of auth and CSW server and/or client classes.

This method:

- patches [CSW auth](/docs/implementation-csw.md#csw-auth) to accept locally signed access tokens or simulate an error
  acquiring a token from Entra
- patches the CSW Server class with a configurable mock (that either responds successfully or raises an exception)
- patches the CSW Client class with a configurable mock (that either responds successfully or raises an exception)
- updates app config to use a temporary directory for storing the MSAL / client auth cache
- updates app config to use a temporary directory for the static site build output
- can be configured to return a Flask app, a Flask test HTTP client or Flask test CLI runner as needed

### Pytest-cov test coverage

[`pytest-cov`](https://pypi.org/project/pytest-cov/) checks test coverage. We aim for 100% coverage but exemptions are fine with good justification:

- `# pragma: no cover` - for general exemptions
- `# pragma: no branch` - where a conditional branch can never be called

The [`[tool.coverage]`](/pyproject.toml) section omits code from the
[Hazmat](/docs/implementation.md#hazardous-materials-module) module.

[Continuous Integration](#continuous-integration) will check coverage automatically and fail if less than 99%.

To run tests with coverage locally:

```
$ poetry run pytest --cov --cov-report=html
```

Where tests are added to ensure coverage, use the `cov` [mark](https://docs.pytest.org/en/7.1.x/how-to/mark.html), e.g:

```python
import pytest

@pytest.mark.cov()
def test_foo():
    assert 'foo' == 'foo'
```

### Continuous Integration

All commits will trigger Continuous Integration using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.

#### CI container

To improve performance, CI jobs use a Docker container defined by a [`Dockerfile`](/support/ci-cd/Dockerfile)) that
pre-installs project [Dependencies](#dependencies). GitLab manages this container, automatically updating it if these
dependencies change. The container image is stored in the project
[Docker Registry 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/container_registry).

### Test Records

To ensure components such as Repository, Record, Item and Collection classes work correctly, a number of valid and
intentionally invalid, [Metadata Record](/docs/implementation.md#metadata-records) configurations are held within the
tests for this project.

Test record configurations are defined in `tests/scar_add_metadata_toolbox/records.py`, and are used to ensure
components such as the Repository, Record, Item and Collection classes work correctly. These include a range of record
types, classes of records, and ways records can be invalid.

These records are accessed through a fake/mocked CSW Server instance, which returns record configurations as XML from
static files held in `tests/scar_add_metadata_toolbox/resources/csw/records/`. These static files need to be kept
in-sync with the record configurations defined in `records.py` using this Python command:

```shell
$ cd tests/scar_add_metadata_toolbox_tests
$ poetry run python -c "from records import make_csw_test_records; make_csw_test_records()"
```

## Flask application

The Flask application representing this project is defined in the `scar_add_metadata_toolbox` package. The
application uses the [application factory](https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/) pattern.

Flask Blueprints are used to logically organise application commands, currently all within the
`scar_add_metadata_toolbox.commands` module. Until this is refactored, additional commands should be registered in the
same module.

## Flask configuration

The Flask application's configuration (`app.config`) is populated from an environment specific class in the
`scar_add_metadata_toolbox.config` module.

New configuration options should be added to the base config class as properties, overridden as needed in environment
subclasses. Where a configuration should be configurable at runtime it should be read as an environment variable and
documented in the [Configuration](/docs/config.md) documentation.

## Templates

Application templates use the Flask application's Jinja environment configured to use general templates from the
[BAS Style Kit Jinja Templates](https://pypi.org/project/bas-style-kit-jinja-templates) package (for layouts, etc.) and
application specific templates from the `scar_add_metadata_toolbox.templates` module.

Styles, components and patterns from the [BAS Style Kit](https://style-kit.web.bas.ac.uk) should be used where possible.
Configuration options for Style Kit Jinja Templates are set in the `scar_add_metadata_toolbox.config` module, including
loading local styles and scripts defined in `scar_add_metadata_toolbox.static`.

Application views should inherit from the application layout, `scar_add_metadata_toolbox.templates/_layouts/app.j2`,
and using [includes](https://jinja.palletsprojects.com/en/2.11.x/templates/#include) and
[macros](https://jinja.palletsprojects.com/en/2.11.x/templates/#macros) to breakdown and reuse content within views is
strongly encouraged.

## Downloads Proxy source

Source code for the [Downloads Proxy](/docs/implementation-downloads-proxy.md) is contained in a single JavaScript
(Node.js) module, `/support/downloads-proxy/index.js`. This module is composed of a set of JS functions with two AWS
Lambda event handler entrypoints for the read and write Lambda functions (i.e. both Lambda functions read from the same
source file but use different entrypoint methods).

Lambda event handlers receive event and context information as per the
[Lambda documentation](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html#http-api-develop-integrations-lambda.proxy-format).

The Lambda function execution environment has access to the Node.js standard library and the AWS JavaScript SDK.

See the [Downloads Proxy Deployment](/docs/deploy.md#downloads-proxy-deployment) subsection for information on
releasing changes to the Download Proxy code.
