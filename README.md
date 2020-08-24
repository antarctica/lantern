# SCAR Antarctic Digital Database (ADD) Metadata Toolbox

Editor, repository and data catalogue for
[SCAR Antarctic Digital Database (ADD) discovery metadata](http://data.bas.ac.uk/collections/e74543c0-4c4e-4b41-aa33-5bb2f67df389/).

## Status

This project is a mature alpha.

This means the core components needed have now been implemented but are subject to considerable change and refactoring.

Between releases major parts of this project may be replaced whilst the project evolves. As major non-core features are
yet to be implemented the shape and scope of this project may change significantly. It is still expected that this
project will grow to cover other MAGIC datasets and products in future, and more widely to act as the seed for a new
BAS wide data catalogue.

The *0.2.0* release has effectively been a complete rewrite of the project to reorganise and reimplement prototype code
in a more structured way. Automated integration tests have been added and the project is now open-sourced.

Some undesirable code from the *0.1.0* release still remains, to workaround issues in other packages until they can be
properly addressed. This code has been moved to a 'Hazardous Materials' (`scar_add_metadata_toolbox.hazmat`) module.

Further information on upcoming changes to this project can be found in the issues and milestones in
[GitLab (internal)](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues).

**Note:** This project is designed to meet an internal need within the
[Mapping and Geographic Information Centre (MAGIC)](https://www.bas.ac.uk/team/magic) at BAS. It has been open-sourced
in case it's of use to others with similar needs.

## Overview

This project is comprised of several components:

1. metadata editor - for maintaining metadata records written as JSON files via the
   [BAS Metadata Library](https://github.com/antarctica/metadata-library)
2. unpublished (working) metadata repository - using an embedded, authenticated PyCSW catalogue
3. published metadata repository - using an embedded, partially-authenticated PyCSW catalogue
4. data catalogue - using a static website

These components map to components 2, 4 and 6 in the draft ADD data workflow
([#139 (internal)](https://gitlab.data.bas.ac.uk/MAGIC/add/issues/139)).

Metadata records are persisted within the the *metadata repositories*, using the ISO 19115-2 (geographic information)
metadata standard.

Access to unpublished records, and the ability to publish/retract records is restricted to restricted to relevant ADD
project members. Once published, records can viewed through the *data catalogue*, which presents them as human readable
items, (such as visualising geographic extents on a map). Manually curated collections provide a means to group items.

The *data catalogue* is rendered as a static website for improved performance, reliability and ease of hosting.
Currently this content is accessed within the existing [BAS data catalogue](https://data.bas.ac.uk).

## Usage

### Metadata editor

The *metadata editor* component of this project is ran on the BAS central workstations using the shared MAGIC user:

```shell
$ ssh geoweb@bslws01.nerc-bas.ac.uk
$ scar-add-metadata-toolbox [command]
```

The editor is configured using a settings file: `/users/geoweb/.config/scar-add-metadata-toolbox/.env`.

### Metadata repositories and data catalogue

The *unpublished repository*, *published repository* and *data catalogue* run as a
[service](http://bsl-nomad-magic-dev-s1.nerc-bas.ac.uk:4646/ui/jobs/scar-add-metadata-toolbox) in the experimental
[MAGIC Nomad cluster](https://gitlab.data.bas.ac.uk/MAGIC/infrastructure/nomad).

Any errors will be automatically reported to [Sentry](#sentry-error-tracking) and relevant individuals alerted by email.

### Workflows

* [adding new records](docs/workflow-adding-records.md)
* [updating existing records](docs/workflow-updating-records.md)
* [adding new collections](docs/workflow-adding-collections.md)
* [updating existing collections](docs/workflow-updating-collections.md)

### Available commands

[Command line reference](docs/command-reference.md)

## Implementation

Flask application using [CSW](#csw) to store [Metadata records](#metadata-records) and display them as [Items](#items)
in [Collections](#collections) rendered as [Jinja templates](#jinja-templates) served as a
[static website](#s3-static-website) within the [BAS data catalogue](https://data.bas.ac.uk).

CSW catalogues are backed by BAS IT provided PostGIS databases, secured using [OAuth](#oauth). Contact forms for
feedback and items in the static catalogue use [Microsoft Power Automate](#feedback-and-contact-forms). Legal policies
use templates from the [Legal Policies](https://gitlab.data.bas.ac.uk/web-apps/legal-policies-templates) project.

### Architecture

This diagram shows the main concepts in this project and how they relate:

![concepts overview](docs/assets/diagrams/concepts.png)

### Metadata records

Metadata records are the content and data within project. Records describe resources, which are typically datasets
within the ADD, e.g. a record might describe the Antarctic Coastline dataset. Records are based on the ISO 19115
metadata standard (specifically 19115-2:2009), which defines an information model for geographic data.

Records are stored/persisted in a records repository (implemented using [CSW](#csw)) or in files for import and export.

A metadata record includes information to answer questions such as:

* what is this dataset?
* what formats is this dataset available in?
* what projection does this dataset use?
* what keywords describe the themes, places, etc. related to this dataset?
* why is this dataset useful?
* who is this dataset for?
* who made this dataset?
* who can I contact with any questions about this dataset?
* when was this dataset created?
* when was it last updated?
* what time period does it cover?
* where does this dataset cover?
* how was this dataset created?
* how can trust the quality of this dataset?
* how can I download or access this dataset?

This metadata is termed 'discovery metadata' (to separate it from metadata for calibration or analysis for example). It
helps users find metadata in catalogues or search engines, and then to help them decide if the data is useful to them.

The information in a metadata record is encoded in a different formats at different stages:

* during editing, records are encoded as JSON, using the
  [BAS Metadata Library](https://github.com/antarctica/metadata-library)'s record configuration
* when stored in a repository, records are encoded as XML using the ISO 19139 standard
* when viewed in the data catalogue, records are encoded in HTML or as (styled) XML

These different formats are used for different reasons:

* JSON is easily understood by machines and is concise to understand and edit by humans
* XML is also machine readable but more suited/mature for complex standards such ISO 19139
* HTML is designed for presenting information to humans, with very flexible formatting options

### Items

Items represent [Metadata records](#metadata-records) but in a form intended for human consumption. They are derived
from [Records](#metadata-records) and are specific to the data catalogue, allowing greater flexibility compared to the
strict rigidity and formality enforced by metadata records.

For example, a resource's coordinate reference system may be defined as `urn:ogc:def:crs:EPSG::3031` in a metadata
record but will be shown as `WGS 84 / Antarctic Polar Stereographic (EPSG:3031)` in items. Both are technically correct
but the descriptive version is easier for a human to understand, at the sake of being less precise and harder for
machines to parse.

As items are derived from records, they are not persisted themselves, except as rendered pages within the data catalogue
static site.

### Collections

Collections are a simple way to group [Items](#items) together based on a shared purpose, theme or topic. They are
specific to the data catalogue and are not based on metadata records.

Collections are stored/persisted in a collections repository (implemented as a JSON file) or in files for import and
export.

They support a limited set of properties compared to records/items:

| Property           | Data Type | Required | Description                                                  |
| ------------------ | --------- | -------- | ------------------------------------------------------------ |
| identifier         | String    | Yes      | UUID                                                         |
| title              | String    | Yes      | Descriptive title                                            |
| topics             | Array     | Yes      | BAS Research Topics associated with collection               |
| topics.*           | String    | Yes      | BAS Research Topic                                           |
| publishers         | Array     | Yes      | Data catalogue publishers associated with collection         |
| publishers.*       | String    | Yes      | Data catalogue publisher                                     |
| summary            | String    | Yes      | Descriptive summary, supports markdown formatting            |
| item_identifiers   | Array     | Yes      | Items associated with collection, specified by their Item ID |
| item_identifiers.* | String    | Yes      | Item ID                                                      |

**Note:** Items in collections will be shown in the order they are listed in the `item_identifiers` property.

For example:

```json
{
    "identifier": "1790c9d5-af77-4a03-9a08-6ba8e83ce748",
    "title": "Operation Tabarin",
    "topics": [
        "Living and Working in Antarctica"
    ],
    "publishers": [
        "BAS Archives Service"
    ],
    "summary": "A secret British Antarctic expedition launched in 1943 during the course of World War II ...",
    "item_identifiers": [
        "82f3fe32-6d6b-4e7a-8256-690ce99fc653",
        "88a22198-36e0-4aff-9099-aae1dfd7baa9",
        "35c6d732-3acc-4044-9c8f-680eed39268a"
    ]
}
```

### OAuth

This project uses OAuth to protect access to the *Unpublished* and *Published* repositories via the
[Microsoft (Azure) identity platform](https://docs.microsoft.com/en-us/azure/active-directory/develop/).

The *Unpublished* and *Published* repositories are registered together as the resource to be protected with different
scopes and roles to authorise users to read, write and publish records. The
[Flask Azure AD OAuth Provider](https://pypi.org/project/flask-azure-oauth/) is used to verify access tokens when CSW
requests are made and enforce these permissions as needed.

The *Metadata editor* is registered as a separate application as a client that will interact with protected resource
(i.e. to read, write and publish records). The
[Microsoft Authentication Library (MSAL) for Python](https://github.com/AzureAD/microsoft-authentication-library-for-python)
library is used to request access tokens using the OAuth device code grant type.

Both applications are registered in the NERC Azure tenancy administered by the
[UKRI/NERC DDaT](https://infohub.ukri.org/corporate-hub/digital-data-and-technology-ddat/) team, currently via the old
[RTS Helpdesk](mailto:rtsservicedesk@nerc.ac.uk).

The [Azure Portal](https://portal.azure.com) is used to assign permissions to applications and users as needed:

* [assigning permissions to users](docs/workflow-permissions-users.md)

### CSW

The *Unpublished* and *Published* repositories are implemented as embedded [PyCSW](http://pycsw.org) servers. The
embedded mode allowing integration with Flask for authentication and authorisation of requests via [OAuth](#oauth).

The CSW transactional profile is used extensively for clients (such as the *Metadata editor* and *Data catalogue*) to
insert, update and delete records programmatically.

The CSW version is fixed to *2.0.2* because it's the latest version supported by
[OWSLib](https://geopython.github.io/OWSLib/), the CSW client used by the *Metadata editor*.

**Note:** Some elements of both the PyCSW server and the OWSLib client have been extended by this project to incorporate
OAuth support. These modifications will be formalised, ideally as upstream contributions, but currently reside within
the 'Hazardous Materials' module as a number of unsightly workarounds are currently needed.

#### Max records limit

Both PyCSW (CSW servers) and OWSLib (CSW clients) have a maximum record of 100 per request.

#### CSW backing databases

CSW servers are backed using PostGIS (PostgreSQL) databases provided by BAS IT (via the central Postgres database
`bsldb`). As PyCSW uses a single table for all records, all servers share the same database and schema, configured
through SQLAlchemy connection strings.

Separate databases are used for each environment (currently only production is used), details are stored in the MAGIC
1Password shared vault. In local development, a local PostGIS database configured in `docker-compose.yml` can be used:

```
postgresql://postgres:password@csw-db/postgres`
```

### Jinja templates

A series of [Jinja2](https://jinja.palletsprojects.com/) templates are used for rendering pages in the *Data catalogue*.

Templates use the [BAS Style Kit Jinja Templates](https://pypi.org/project/bas-style-kit-jinja-templates/) and styled
using the [BAS Style Kit](https://style-kit.web.bas.ac.uk).

### S3 static website

Rendered pages and other assets are hosted through an AWS S3 bucket with static website hosting enabled.

Reverse proxy rules are used to expose content from this static site within the existing/legacy BAS Data Catalogue, DMS.

### Feedback and contact forms

A Microsoft
[Power Automate](https://emea.flow.microsoft.com/manage/environments/Default-b311db95-32ad-438f-a101-7ba061712a4e/flows/97d95c3b-5d40-4358-86a6-979a679a4b7c/details)
Flow is used to process feedback and contact form submissions. Messages support Markdown formatting, converted to HTML
prior to submission. On submitted, Power Automate creates an issue for the message in a relevant GitLab project.

### Sentry error tracking

Errors in this service are tracked with Sentry:

* [Sentry dashboard](https://sentry.io/organizations/antarctica/issues/?project=5197036)
* [GitLab dashboard](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/error_tracking)

Error tracking will be enabled or disabled depending on the environment. It can be manually controlled by setting the
`APP_ENABLE_SENTRY` [Configuration option](#configuration).

### Application logging

Logs for this service are written to *stdout/stderr* as appropriate.

## Configuration

Application configuration options are set in per-environment classes extending a base `Config` class in
`scar_add_metadata_toolbox/config.py`. The active environment is set using the `FLASK_ENV` environment variable.

Configuration options are defined, and documented, using class properties. Some configuration options may optionally be
set at runtime using environment variables. If not set, default values will be used.

| Configuration Option                                | Description                                                      | Allowed Values                     | Example Value                                                   |
| --------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------- | --------------------------------------------------------------- |
| `APP_ENABLE_SENTRY`                                 | Feature flag to enable/disable Sentry error tracking             | true/false                         | `true`                                                          |
| `APP_LOGGING_LEVEL`                                 | Minimum logging level to include in application logs             | debug/info/warning/error/critical  | `warning`                                                       |
| `APP_AUTH_SESSION_FILE_PATH`                        | Path to file used for authentication information                 | valid file path                    | `/home/user/.config/scar_add_metadata_toolbox/auth.json`        |
| `APP_COLLECTIONS_PATH`                              | Path to file used for data catalogue collections                 | valid file path                    | `/home/user/.config/scar_add_metadata_toolbox/collections.json` |
| `APP_SITE_PATH`                                     | Path to directory used for rendered static site content          | valid directory path               | `/home/user/.config/scar_add_metadata_toolbox/_site`            |
| `CSW_ENDPOINT_UNPUBLISHED`                          | CSW endpoint for accessing unpublished catalogue                 | valid URL                          | `http://example.com/csw/unpublished`                            |
| `CSW_ENDPOINT_PUBLISHED`                            | CSW endpoint for accessing published catalogue                   | valid URL                          | `http://example.com/csw/published`                              |
| `CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT`            | Endpoint at which to run unpublished CSW catalogue               | valid URL                          | `http://example.com/csw/unpublished`                            |
| `CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT`              | Endpoint at which to run published CSW catalogue                 | Valid URL                          | `http://example.com/csw/published`                              |
| `CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION` | Connection string for unpublished CSW catalogue backing database | Valid SQLAlchemy connection string | `postgresql://postgres:password@db.example.com/postgres`        |
| `CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION`   | Connection string for published CSW catalogue backing database   | Valid SQLAlchemy connection string | `postgresql://postgres:password@db.example.com/postgres`        |
| `APP_S3_BUCKET`                                     | AWS S3 bucket name used for hosting static website content       | Valid AWS S3 bucket name           | `add-catalogue.data.bas.ac.uk`                                  |

These options are typically set when running this application as a client (metadata editor and data catalogue):

* `APP_LOGGING_LEVEL`
* `APP_AUTH_SESSION_FILE_PATH`
* `APP_COLLECTIONS_PATH`
* `APP_SITE_PATH`
* `CSW_ENDPOINT_UNPUBLISHED`
* `CSW_ENDPOINT_PUBLISHED`
* `APP_S3_BUCKET`

These options are typically set when running this application as a server (metadata repositories):

* `APP_LOGGING_LEVEL`
* `CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT`
* `CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT`
* `CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION`
* `CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION`

## Setup

[Continuous deployment](#continuous-deployment) will configure this application to run on the BAS central workstations
as a Podman container, using an automatically generated launch script and environment variables.

[Continuous deployment](#continuous-deployment) will configure this application to run in the experimental
[MAGIC Nomad cluster](https://gitlab.data.bas.ac.uk/MAGIC/infrastructure/nomad), using an automatically
generated job definition.

See the [Usage](#usage) section for how to use the application.

### PyCSW backing database setup

Backing databases for PyCSW servers require initialisation using the `csw setup` application
[CLI command](docs/command-reference.md#csw-setup) for both the *published* and *unpublished* repositories.

Normally this command will create the required database table, geometry column (if PostGIS is detected) and relevant
indexes. As catalogues only require a single table, multiple can be stored in the same database/schema. However two of
the indexes used (`fts_gin_idx` [full text search] and `wkb_geometry_idx` [binary geometry]) are named non-uniquely,
preventing multiple catalogues being co-located in the same schema.

This appears to be an oversight as all other indexes are made unique by prefixing them with the name of the records
table and doing this manually for these indexes appears to work without issue.

Assuming the *Unpublished catalogue* is setup first, perform these steps *before* setting up the *Published catalogue*:

1. verify that the `records_unpublished` table was created successfully (contains `fts_gin_idx` and `wkb_geometry_idx`
   indexes)
2. alter the affected indexes in the `records_unpublished` table [1]
3. setup the *Published catalogue* `flask csw setup published`
4. alter the affected indexes in the second table [2]

**Note:** These steps will be performed automatically, or mitigated by fixing the upstream PyCSW package, in future.

[1]

```sql
ALTER INDEX fts_gin_idx RENAME TO ix_records_unpublished_fts_gin_indx;
ALTER INDEX wkb_geometry_idx RENAME TO ix_unpublished_wkb_geometry_idx;
```

[2]

```sql
ALTER INDEX fts_gin_idx RENAME TO ix_records_published_fts_gin_indx;
ALTER INDEX wkb_geometry_idx RENAME TO ix_published_wkb_geometry_idx;
```

### Azure permissions

[Terraform](#terraform) will create and configure the relevant Azure application registrations required for using
[OAuth](#oauth) to protect the CSW catalogues. However manual approval by a Tenancy Administrator is needed to grant
the registration representing the *client* role of the application access to the registration for the *server* role.

This has been approved by NERC RTS in [#3](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/3).

### Terraform

Terraform is used for:

* resources required for hosting the *Data catalogue* component as a static website
* resources required for protecting and accessing the *unpublished repository*, *published repository*  components
* a templated job file for Nomad during [Continuous deployment](#continuous-deployment)
* a templated launch script for Podman during [Continuous deployment](#continuous-deployment)

Access to the [BAS AWS account](https://gitlab.data.bas.ac.uk/WSF/bas-aws),
[Terraform remote state](#terraform-remote-state) and NERC Azure tenancy are required to provision these resources.

**Note:** The templated Podman and Nomad runtime files are not included in Terraform state.

```
$ cd provisioning/terraform
$ docker-compose run terraform

$ az login --allow-no-subscriptions

$ terraform init
$ terraform validate
$ terraform fmt
$ terraform apply

$ exit
$ docker-compose down
```

Once provisioned the following steps need to be taken manually:

1. set branding icons (if desired)
2. set [Azure permissions](#azure-permissions)
3. [assign roles](docs/workflow-permissions-users.md) to users and/or groups
4. set `accessTokenAcceptedVersion: 2` in both application registration manifests

**Note:** Assignments are 1:1 between users/groups and roles but there can be multiple assignments. I.e. roles `Foo`
and `Bar` can be assigned to the same user/group by creating two role assignments.

#### Terraform remote state

State information for this project is stored remotely using a
[Backend](https://www.terraform.io/docs/backends/index.html).

Specifically the [AWS S3](https://www.terraform.io/docs/backends/types/s3.html) backend as part of the
[BAS Terraform Remote State](https://gitlab.data.bas.ac.uk/WSF/terraform-remote-state) project.

Remote state storage will be automatically initialised when running `terraform init`. Any changes to remote state will
be automatically saved to the remote backend, there is no need to push or pull changes.

##### Remote state authentication

Permission to read and/or write remote state information for this project is restricted to authorised users. Contact
the [BAS Web & Applications Team](mailto:servicedesk@bas.ac.uk) to request access.

See the [BAS Terraform Remote State](https://gitlab.data.bas.ac.uk/WSF/terraform-remote-state) project for how these
permissions to remote state are enforced.

### Docker image tag expiration policy

The Docker image for this project uses a [Tag expiration policy](#docker-image-expiration-policy) which needs to be
configured manually in [GitLab](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/settings/ci_cd).

* Expiration policy: *enabled*
* Expiration interval: *90 days*
* Expiration schedule: *Every week*
* Number of tags to retain: *10 tag per image name*
* Tags with names matching this regex pattern will expire: `(review.+|build.+)`
* Tags with names matching this regex pattern will be preserved: `release.+`

## Development

```shell
$ git clone https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox
$ cd add-metadata-toolbox
```

### Development environment

A flexible development environment is available for developing this application locally. It can be used in a variety of
ways depending on what is being developed:

* all components, the Flask application, CSW database and static website can be ran locally
    * useful for end-to-end testing
    * useful for testing changes to how data is loaded into the CSW catalogues
* the Flask application can be ran directly, without needing to convert it into a static site
    * useful for iterating on changes to the data catalogue website
* the Flask application can use the production CSW database
    * useful for testing with real-world data

The local development environment is defined using Docker Compose in `./docker-compose.yml`. It consists of:

* an `app` service for running the Flask application as a web application
* an `app-cli` service for running [application commands](docs/command-reference.md)
* a `csw-db` service for storing data added to local CSW catalogues (if used)
* a `web` service for serving a local version of the data catalogue static site (if used)

To create a local development environment:

1. pull docker images: `docker-compose pull` [1]
3. run the Docker Compose stack: `docker-compose up`
    * the Flask application will be available directly at: [http://localhost:9000](http://localhost:9000)
    * the static site will be available at: [http://localhost:9001](http://localhost:9001)
4. run application [Commands](docs/command-reference.md) [2]

To destroy a local development environment:

1. run `docker-compose down`

[1] This requires access to the BAS Docker Registry (part of [gitlab.data.bas.ac.uk](https://gitlab.data.bas.ac.uk)):

```shell
$ docker login docker-registry.data.bas.ac.uk
```

**Note:** You will need to sign-in using your GitLab credentials (your password is set through your GitLab profile) the
first time this is used.

[2] In a new terminal:

```shell
$ docker-compose run app-cli flask [task]
```

#### Development container

A development container image, defined by `./Dockerfile`, is built manually, tagged as `:latest` and hosted in the
private BAS Docker Registry (part of [gitlab.data.bas.ac.uk](https://gitlab.data.bas.ac.uk)):

[docker-registry.data.bas.ac.uk/magic/add-metadata-toolbox](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/container_registry)

It is separate to the [deployment container](#docker-image) and installs both runtime and development
[dependencies](#dependencies) (deployment containers only install runtime dependencies).

If you don't have access to the BAS Docker Register, you can build this image locally using `docker-compose build app`.

### Python version

When upgrading to a new version of Python, ensure the following are also checked and updated where needed:

* `Dockerfile`:
    * base stage image (e.g. `FROM python:3.X-alpine as base` to `FROM python:3.Y-alpine as base`)
    * pre-compiled wheels (e.g. `https://.../linux_x86_64/cp3Xm/lxml-4.5.0-cp3X-cp3X-linux_x86_64.whl` to
     `http://.../linux_x86_64/cp3Ym/lxml-4.5.0-cp3Y-cp3Y-linux_x86_64.whl`)
* `support/docker-packaging/Dockerfile`:
    * base stage image (e.g. `FROM python:3.X-alpine as base` to `FROM python:3.Y-alpine as base`)
    * pre-compiled wheels (e.g. `http://.../linux_x86_64/cp3Xm/lxml-4.5.0-cp3X-cp3X-linux_x86_64.whl` to
     `http://.../linux_x86_64/cp3Ym/lxml-4.5.0-cp3Y-cp3Y-linux_x86_64.whl`)
* `pyproject.toml`
    * `[tool.poetry.dependencies]`
        * `python` (e.g. `python = "^3.X"` to `python = "^3.Y"`)
    * `[tool.black]`
        * `target-version` (e.g. `target-version = ['py3X']` to `target-version = ['py3Y']`)

### Package structure

All code for this project should be defined in the [`scar_add_metadata_toolbox`](scar_add_metadata_toolbox) package,
with the exception of tests.

In brief, this package is comprised of these modules:

* `scar_add_metadata_toolbox` - contains [Flask application](#flask-application)
* `scar_add_metadata_toolbox.classes` - contains classes for concepts (Repositories, Records, Items, Collections)
* `scar_add_metadata_toolbox.commands` - contains Flask blueprints used for CLI commands
* `scar_add_metadata_toolbox.config` - contains [Flask configuration](#flask-configuration)
* `scar_add_metadata_toolbox.csw` - contains classes for [CSW](#csw) servers and clients
* `scar_add_metadata_toolbox.hazmat` - contains ['Hazardous Material' code](#hazardous-materials-module)
* `scar_add_metadata_toolbox.static` - contains static site assets (CSS, JS, etc.)
* `scar_add_metadata_toolbox.templates` - contains [Application templates](#templates)
* `scar_add_metadata_toolbox.utils` - contains various utility/helper methods and classes

#### Hazardous Materials module

Whilst this application has been developed, extended/modified versions of class from 3rd party packages have been
created to address unresolved bugs or add new required functionality. As this code often requires workarounds and hacks
it is ugly, non-standard and against established best practices (such as not to use mocks outside of tests).

In time, these changes and additions are expected to be either incorporated into upstream packages, or if not possible,
into forked packages that we maintain. Until then, this code is kept in a 'Hazardous Materials' (Hazmat) module,
`scar_add_metadata_toolbox.hazmat`, to indicate that it shouldn't be treated like other modules in this project.

Ideally no additional code will be added to this module, however if other changes/extensions need to be made in a
non-clean way then they should be added here, rather than 'polluting' the main package.

### Dependencies

Python dependencies for this project are managed with [Poetry](https://python-poetry.org) in `pyproject.toml`.

Non-code files, such as static files, can also be included in the [Python package](#python-package) using the
`include` key in `pyproject.toml`.

#### Adding new dependencies

To add a new (development) dependency:

```shell
$ docker-compose run app ash
$ poetry add [dependency] (--dev)
```

Then rebuild the [Development container](#development-container) and push to GitLab (GitLab will rebuild other images
automatically as needed):

```shell
$ docker-compose build app
$ docker-compose push app
```

#### Updating dependencies

```shell
$ docker-compose run app ash
$ poetry update
```

Then rebuild the [Development container](#development-container) and push to GitLab (GitLab will rebuild other images
automatically as needed):

```shell
$ docker-compose build app
$ docker-compose push app
```

### Static security scanning

To ensure the security of this API, source code is checked against [Bandit](https://github.com/PyCQA/bandit) for issues
such as not sanitising user inputs or using weak cryptography. Bandit is configured in `.bandit`.

**Warning:** Bandit is a static analysis tool and can't check for issues that are only be detectable when running the
application. As with all security tools, Bandit is an aid for spotting common mistakes, not a guarantee of secure code.

To run checks manually:

```shell
$ docker-compose run app bandit -r .
```

Checks are ran automatically in [Continuous Integration](#continuous-integration).

### Code Style

PEP-8 style and formatting guidelines must be used for this project, with the exception of the 80 character line limit.

[Black](https://github.com/psf/black) is used to ensure compliance, configured in `pyproject.toml`.

Black can be [integrated](https://black.readthedocs.io/en/stable/editor_integration.html) with a range of editors, such
as PyCharm, to perform formatting automatically.

To apply formatting manually:

```shell
$ docker-compose run app black bas_scar_add_metadata_toolbox/
```

To check compliance manually:

```shell
$ docker-compose run app black --check bas_scar_add_metadata_toolbox/
```

Checks are ran automatically in [Continuous Integration](#continuous-integration).

### Flask application

The Flask application representing this project is defined in the
[`scar_add_metadata_toolbox`](/scar_add_metadata_toolbox) package. The application uses the
[application factory](https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/) pattern.

Flask Blueprints are used to logically organise application commands, currently all within the
`scar_add_metadata_toolbox.commands` module. Until this is refactored, additional commands should be registered in the
same module.

### Flask configuration

The Flask application's configuration (`app.config`) is populated from an environment specific class in the
`scar_add_metadata_toolbox.config` module.

New configuration options should be added to the base config class as properties, overridden as needed in environment
sub-classes. Where a configuration should be configurable at runtime it should be read as an environment variable and
documented in the [Configuration](#configuration) section.

### Logging

Use the Flask application's logger, for example:

```python
from flask import current_app

current_app.logger.info('Log message')
```

### File paths

Use Python's [`pathlib`](https://docs.python.org/3.8/library/pathlib.html) library for file paths.

Where displaying a file path to the user, use the absolute form to aid in debugging:

```python
from pathlib import Path

foo_path = Path("foo.txt")
print(f"foo_path is: {str(foo_path.absolute())}")
```

### Templates

Application templates use the Flask application's Jinja environment configured to use general templates from the
[BAS Style Kit Jinja Templates](https://pypi.org/project/bas-style-kit-jinja-templates) package (for layouts, etc.) and
application specific templates from the `scar_add_metadata_toolbox.templates` module.

Styles, components and patterns from the [BAS Style Kit](https://style-kit.web.bas.ac.uk) should be used where possible.
Configuration options for Style Kit Jinja Templates are set in the `scar_add_metadata_toolbox.config` module, including
loading local styles and scripts defined in [`scar_add_metadata_toolbox/static`](scar_add_metadata_toolbox/static).

Application views should inherit from the application layout,
[`app.j2`](scar_add_metadata_toolbox/templates/_layouts/app.j2), and using
[includes](https://jinja.palletsprojects.com/en/2.11.x/templates/#include) and
[macros](https://jinja.palletsprojects.com/en/2.11.x/templates/#macros) to breakdown and reuse content within views is
strongly encouraged.

### Editor support

#### PyCharm

Multiple run/debug configurations are included in the project for debugging and testing:

* *App* runs the Flask application and is useful for debug the server role of this application (e.g. CSW requests)
* *App CLI* runs the Flask application and is useful for debug the client role of this application (e.g. static site
   commands requests) - change the *parameters* option to set which command to run

### Testing

All code in the `scar_add_metadata_toolbox` package must be covered by tests, defined in `tests/`. This project uses
[PyTest](https://docs.pytest.org/en/latest/) which should be ran in a random order using
[pytest-random-order](https://pypi.org/project/pytest-random-order/).

To run tests manually from the command line:

```shell
$ docker-compose run app -e FLASK_ENV=testing app pytest --random-order
```

To run/debug tests using PyCharm, use the included *App (Tests)* run/debug configuration.

Tests are ran automatically in [Continuous Integration](#continuous-integration).

#### Test coverage

[pytest-cov](https://pypi.org/project/pytest-cov/) is used to measure test coverage.

A `.coveragerc` file is used to omit code from the `scar_add_metadata_toolbox.hazmat` module.

To measure coverage manually:

```shell
$ docker-compose run -e FLASK_ENV=testing app pytest --cov=scar_add_metadata_toolbox --cov-fail-under=100 --cov-report=html .
```

[Continuous Integration](#continuous-integration) will check coverage automatically and fail if less than 100%.

#### Continuous Integration

All commits will trigger a Continuous Integration process using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.

## Review apps

To review changes to functionality, commits made in branches will trigger review apps to be created using GitLab's
CI/CD platform, configured in `.gitlab-ci.yml`.

Review apps run as [Nomad services](#nomad-service) only, not as [Command line applications](#command-line-application).

Containers for review apps are built using the [deployment Docker image](#docker-image) but tagged as `review:[slug]`,
where `[slug]` is a reference to the merge request the review app is related to. Images are hosted in the private BAS
Docker Registry (part of [gitlab.data.bas.ac.uk](https://gitlab.data.bas.ac.uk)):

[docker-registry.data.bas.ac.uk/magic/add-metadata-toolbox/deploy](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/container_registry)

### Limitations

* the URL for review apps point to the Nomad job via it's UI, rather than the managed application, as the port number
  for the application is set dynamically and not stored in the Terraform state for the Nomad job
* the application will currently use the production CSW database, therefore records **MUST NOT** be changed by review
  apps, this is currently unenforced but will be when ServiceDesk ticket #42232 is resolved

## Deployment

### Python package

A project Python package is built by [Continuous Delivery](#continuous-deployment), hosted through the private BAS Repo
Server:

[bsl-repoa.nerc-bas.ac.uk/magic/v1/projects/scar-add-metadata-toolbox/latest/dist/](http://bsl-repoa.nerc-bas.ac.uk/magic/v1/projects/scar-add-metadata-toolbox/latest/dist/)

### Docker image

A deployment container image, defined by `./support/docker-packaging/Dockerfile`, is built by
[Continuous Delivery](#continuous-deployment) for releases (Git tags). Images are tagged as `/release:[tag]`, where
`[tag]` is the name of the Git tag a release is related to. Images are hosted in the private BAS Docker Registry (part
of [gitlab.data.bas.ac.uk](https://gitlab.data.bas.ac.uk)):

[docker-registry.data.bas.ac.uk/magic/add-metadata-toolbox/deploy](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/container_registry)

**Note:** All container builds (including those from [Review apps](#review-apps)) are also tagged as `/build:[commit]`,
where `[commit]` is a reference to the Git commit that triggered the image to be built.

#### Docker image expiration policy

An image [expiration policy](https://docs.gitlab.com/ee/user/packages/container_registry/#cleanup-policy) is used to
limit the number of non-release container images that are kept. This policy is set within, and enforced automatically
by, GitLab. See the [Setup section](#docker-image-tag-expiration-policy) for how this is configured.

### Nomad service

The deployment [Docker image](#docker-image) is deployed as a service job in the experimental
[MAGIC Nomad cluster](https://gitlab.data.bas.ac.uk/MAGIC/infrastructure/nomad).

### Command line application

The deployment [Docker image](#docker-image) is made available as a command line application on the BAS central
workstations using Podman. A wrapper shell script is used to mask the `podman run` run command for ease of use.

### Continuous Deployment

All commits will trigger a Continuous Deployment process using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.

## Release procedure

For all releases:

1. create a release branch
2. close release in `CHANGELOG.md`
3. push changes, merge the release branch into `master` and tag with version

## Feedback

The maintainer of this project is the BAS Mapping and Geographic Information Centre (MAGIC), they can be contacted at:
[magic@bas.ac.uk](mailto:magic@bas.ac.uk).

## Issue tracking

This project uses issue tracking, see the
[Issue tracker](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues) for more information.

**Note:** Read & write access to this issue tracker is restricted. Contact the project maintainer to request access.

## License

© UK Research and Innovation (UKRI), 2020, British Antarctic Survey.

You may use and re-use this software and associated documentation files free of charge in any format or medium, under
the terms of the Open Government Licence v3.0.

You may obtain a copy of the Open Government Licence at http://www.nationalarchives.gov.uk/doc/open-government-licence/
