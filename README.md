# SCAR Antarctic Digital Database (ADD) Metadata Toolbox

Repository and Catalogue for
[SCAR Antarctic Digital Database (ADD) discovery metadata](http://data.bas.ac.uk/collections/e74543c0-4c4e-4b41-aa33-5bb2f67df389/).

## Status

This project is a mature alpha.

This means core, required, components have been implemented but are subject to considerable change and refactoring.

Between releases major parts of this project may be replaced/rewritten. As major non-core features are yet to be 
implemented, the shape and scope of this project may change significantly.

In time, this project will grow to cover other MAGIC datasets, products and activities. It may also be used as the seed 
for a new BAS wide Data Catalogue.

Further information on upcoming changes to this project can be found in the issues and milestones in
[GitLab (internal)](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues).

**Note:** This project is designed to meet an internal need within the
[Mapping and Geographic Information Centre (MAGIC)](https://www.bas.ac.uk/team/magic) at the British Antarctic Survey.
It has been open-sourced in case it's of use to others with similar needs.

## Overview

This project is made up of a:

1. Repository, for storing metadata records, acts as a source of truth
2. Catalogue, for displaying metadata records, acts as a discovery tool

These components map to components 4 and 6 in the draft ADD data workflow
([#139 (internal)](https://gitlab.data.bas.ac.uk/MAGIC/add/issues/139)).

Metadata records use the [ISO 19115](https://metadata-standards.data.bas.ac.uk/standard/iso-19115/) metadata standard.
The [OGC Catalogue Services for the Web (CSW)] standard is used to provide the *Repository* component, allowing records
to be added, accessed, updated and deleted. Records can be either published (available publicly) or unpublished. 
Access to any unpublished records, and the ability to publish/retract records, is restricted to relevant ADD project 
members.

Once published, records can be viewed through the *Catalogue* component, a static website, which presents records as 
human-readable items (with geographic extents visualised on a map for example). Manually curated collections provide a 
basic way to group items into sets. The Catalogue is part of the current/legacy BAS Data Catalogue, known as the
[Discovery Metadata System (DMS)](https://data.bas.ac.uk), which is in the process of being replaced.

## Usage

### Workflows

* [adding new records](docs/workflow-adding-records.md)
* [updating existing records](docs/workflow-updating-records.md)
* [adding new collections](docs/workflow-adding-collections.md)
* [updating existing collections](docs/workflow-updating-collections.md)

### Available commands

[Command line reference](docs/command-reference.md)

## Implementation

Flask application using [CSW](#csw) to store [Metadata records](#metadata-records), and display them as [Items](#items),
in [Collections](#collections), rendered using [Jinja templates](#jinja-templates), served as a
[static website](#s3-static-website) within the [BAS Discovery Metadata System (DMS)](https://data.bas.ac.uk) website.
A command line interface is used to setup components, manage records and build/publish the static site.

CSW catalogues are backed by PostGIS databases and secured using [OAuth](#oauth). Contact forms for feedback and items 
in the static site use [Microsoft Power Automate](#feedback-and-contact-forms). Legal policies use templates from the
[Legal Policies](https://gitlab.data.bas.ac.uk/web-apps/legal-policies-templates) project.

[Static site](#website-metrics) and [item download](#download-metrics) are tracked using 
[Google Analytics Event Tracking](https://developers.google.com/analytics/devguides/collection/analyticsjs/events).
Application errors are tracked using [Sentry](#sentry-error-tracking).

### Architecture

This diagram shows the main concepts in this project and how they relate:

![concepts overview](docs/assets/diagrams/concepts.png)

### Metadata records

Metadata records are the content and data within this project. Records describe resources, which are typically datasets
within the ADD, e.g. a record might describe the Antarctic Coastline dataset. Records are based on the ISO 19115
metadata standard (specifically 19115-2:2009), which defines an information model and XML encoding for geographic data.

Records are stored/persisted in a records repository (implemented using [CSW](#csw)). Records are imported or 
exported (for editing) as files.

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
helps users find metadata in catalogues or search engines, and then helps them decide if the data is useful to them.

The information in a metadata record is encoded in a different formats at different stages:

* when imported/exported (during editing), records are encoded as JSON, using the
  [BAS Metadata Library](https://github.com/antarctica/metadata-library) record configuration
* when stored in a repository, records are encoded as XML using the ISO 19139 encoding standard
* when viewed in the data catalogue, records are encoded in freeform HTML or as (styled) standardised XML

These different formats are used for different reasons:

* JSON is concise/accessible enough to be understood by humans for editing
* XML is proscribed by the ISO 19139 standard
* HTML is the defacto standard for web content

### Items

Items are derived from [Records](#metadata-records) but with greater flexibility to make them more intuitive for humans.
Whereas Records prioritise strictness and formality, using complex standards, Items prioritise readability and 
understanding by humans.

For example, a resource's coordinate reference system may be defined as `urn:ogc:def:crs:EPSG::3031` in a Record
and as `WGS 84 / Antarctic Polar Stereographic (EPSG:3031)` in an equivalent Item. The Record's definition is 
precise and unambiguous (and therefore more interoperable), whereas the Item definition is less complex and more
descriptive (and therefore more understandable to a human).

As items are derived from records, they are not persisted themselves, except as rendered pages within the static site.

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

OAuth is used to protect access to actions or information (unpublished Records) within the *Repository* component. 
The [Microsoft (Azure) identity platform](https://docs.microsoft.com/en-us/azure/active-directory/develop/) is used to 
define roles/scopes for restricted actions or information, and to assign these to users/groups. The
[Flask Azure AD OAuth Provider](https://pypi.org/project/flask-azure-oauth/) is used to enforce these permissions 
within the Flask application.

Two Azure OAuth applications (application registrations) are defined for this:

1. a server application, representing the Repository
2. a client application, representing a user accessing or modifying records within the Repository

The server app registration defines the roles/scopes that exist (reading records, updating records, etc.). These are 
then assigned to users and groups, who use them through the client app registration to read/update records, etc.

The Flask application represents both of these app registrations. The CLI acts as the client, and the CSW catalogues as
the server.

Both Azure applications are registered in the NERC Azure tenancy administered by the
[UKRI/NERC DDaT](https://infohub.ukri.org/corporate-hub/digital-data-and-technology-ddat/) team. 
[Terraform](#terraform) is used to define and provision these applications.

The [Azure Portal](https://portal.azure.com) is used to assign permissions to applications and users as needed:

* [assigning permissions to users](docs/workflow-permissions-users.md)

### CSW

The [OGC CSW](https://www.ogc.org/standards/cat) standard is used as a protocol and interface for accessing and 
managing records in the *Repository* component.

Separate CSW catalogues are used for Published and unpublished records, using embedded [PyCSW](http://pycsw.org) 
servers to allow integration with Flask for authentication and authorisation of requests via [OAuth](#oauth).

Records are accessed using `getRecords` and `getRecordById` requests. Records are managed using the CSW 
transactional profile. These requests can be made using from the Flask CLI, or from other applications, if authorised. 

The CSW version is fixed to *2.0.2* because it's the latest version supported by
[OWSLib](https://geopython.github.io/OWSLib/), the CSW client used by the Flask CLI.

**Note:** The CSW repositories are considered to be APIs, and so ran as services through the
[BAS API Load Balancer](https://gitlab.data.bas.ac.uk/WSF/api-load-balancer) (internal) with documentation in the
[BAS API Documentation](https://gitlab.data.bas.ac.uk/WSF/api-docs) project (internal).

#### CSW package modifications

Some elements of both the PyCSW server and the OWSLib client have been extended by this project to incorporate
OAuth support and fix a variety of issues. These modifications will be formalised, ideally as upstream contributions, 
but currently reside within the [Hazardous Materials module](#hazardous-materials-module).

These modifications are:

* PyCSW:
  * hex-encoding - see https://github.com/geopython/pycsw/issues/576 for details
  * allowing stdout for logging
* OWSlib:
  * adding token authentication type
  * adding GSS and GSR namespaces (used in ISO 19115-2 records)
  * working around records as strings (decode to bytes)
  * working around records with additional schema location attribute (remove)
  * working around XPath queries that result in trailing element tags

#### CSW Max records limit

Both PyCSW (CSW servers) and OWSLib (CSW clients) have a maximum record of 100 per request.

#### CSW backing databases

CSW servers are backed using PostGIS (PostgreSQL) databases. In production, these are provided by BAS IT (via the 
central Postgres database `bsldb`). Credentials for this database are stored in the MAGIC 1Password shared vault. 

In local development environments, a local PostGIS database configured in `docker-compose.yml` is used.

To test against real data in a non-production environment, a staging database, which is synced from the production 
database, can be used. Credentials for this database are stored in the MAGIC 1Password shared vault. This database is
re-synced automatically by BAS IT every Tuesday at 02:00. 

### Jinja templates

A series of [Jinja2](https://jinja.palletsprojects.com/) templates are used for rendering pages in the *Catalogue* 
component.

Templates use the [BAS Style Kit Jinja Templates](https://pypi.org/project/bas-style-kit-jinja-templates/) which use 
the [BAS Style Kit](https://style-kit.web.bas.ac.uk).

### S3 static website

Rendered pages and other assets are hosted through an AWS S3 bucket with static website hosting enabled. Separate 
production and staging buckets are available to preview changes. [Terraform](#terraform) is used to define and 
provision these buckets.

Rules within the BAS General Load Balancer, managed by IT, are used to reverse proxy content from these S3 static sites 
to appear as part of the current/legacy BAS Discovery Metadata System (DMS).

### Downloads Proxy 

To support [tracking downloads](#download-metrics) of items, a proxy service is used, which redirects download URLs
defined in Records/Items to a real location. This redirection is used to increase the chances downloads are tracked, 
by making the real location of items less obvious, and harder to share/use directly.

E.g. A download URL such as `https://data.bas.ac.uk/downloads/123`, where `123` is a unique identifier, will be 
resolved by this Proxy to a URL such as `https://example.com/dataset.gpkg` (it's real location).

The Downloads Proxy is a very simple AWS Lambda function. When a request is made (using a download URL), the unique 
identifier is looked up in a JSON file. This returns an object containing the real download URL, and metadata on the
item the download relates to, and it's file type (to track downloads by item and by file format).

Entries in this file are managed manually. The JSON file looks like this:

```json
{
  "123": {
    "item_id": "abc",
    "transfer_option_format": "gpkg",
    "transfer_option_location": "https://example.com/data/example1.gpkg"
  },
  "345": {
    "item_id": "def",
    "transfer_option_format": "gpkg",
    "transfer_option_location": "https://example.com/data/example2.gpkg"
  }
}
```

The Lambda function, and JSON file, are managed within the AWS Console as part of the BAS AWS account.

[bas-add-data-catalogue-downloads-metrics function](https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions/bas-add-data-catalogue-downloads-metrics?tab=code).

At some point this Proxy will be more integrated into this project, though it may not be implemented in the same form.

### Feedback and contact forms

A Microsoft
[Power Automate](https://emea.flow.microsoft.com/manage/environments/Default-b311db95-32ad-438f-a101-7ba061712a4e/flows/97d95c3b-5d40-4358-86a6-979a679a4b7c/details)
Flow is used to process feedback and contact form submissions. Messages support Markdown formatting, converted to HTML
prior to submission. On submitted, Power Automate creates an issue for the message in a relevant GitLab project.

### Website metrics

Metrics for viewing item/collection web pages, and tabs within pages, are tracked as events within Google 
Analytics.

[Events report](https://analytics.google.com/analytics/web/#/report/content-event-overview/a64130716w100162930p104062219/).

### Download metrics

To support tracking downloads of item artefacts, a [Downloads Proxy](#downloads-proxy) service is used. This service
logs events within Google Analytics. See the [Website Metrics](#website-metrics) section for how to access event 
reports.

For download metrics to be recorded, download URLs (i.e. https://data.bas.ac.uk/downloads/123`) must be used.
It doesn't matter if the URL is accessed through a data catalogue item page, or if the link is shared directly, 
downloads will still be recorded.

These download metrics are not foolproof however. If a user shares the real file after downloading it, or is determined 
enough to discover the real URL and share that, the tracking can be bypassed.

### Sentry error tracking

Errors in this service are tracked with Sentry:

* [Sentry dashboard](https://sentry.io/organizations/antarctica/issues/?project=5197036)
* [GitLab dashboard](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/error_tracking)

Error tracking will be enabled or disabled depending on the environment. It can be manually controlled by setting the
`APP_ENABLE_SENTRY` [Configuration option](#configuration).

### Application logging

Logs for this service are written to *stdout/stderr* as appropriate.

### Hazardous Materials module

In order to implement the [CSW package modifications](#csw-package-modifications), the `pycsw` and `owslib` packages
have been vendored into this application, meaning their source code, and their dependencies, have been added within 
this project.

As this code is third party, and hasn't been vetted or integrated into this project, it is held in a *hazmat* 
(Hazardous Materials) module, `scar_add_metadata_toolbox.hazmat`. This module is exempt from 
[Code Linting](#code-linting), [Testing](#testing) and [Test Coverage](#test-coverage) rules.

The eventual aim is to remove these packages from this project, however this will depend on whether these packages 
are used in the longer term (see [#194](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/194)), and 
if so, whether the changes made to them in this project, could be integrated into their upstream projects.

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

These options are typically set when running this application as a client (CLI):

* `APP_LOGGING_LEVEL`
* `APP_AUTH_SESSION_FILE_PATH`
* `APP_COLLECTIONS_PATH`
* `APP_SITE_PATH`
* `CSW_ENDPOINT_UNPUBLISHED`
* `CSW_ENDPOINT_PUBLISHED`
* `APP_S3_BUCKET`

These options are typically set when running this application as a server (CSW catalogues):

* `APP_LOGGING_LEVEL`
* `CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT`
* `CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT`
* `CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION`
* `CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION`

## Setup

To setup this project as an en-user (to manage and publish records), create a 
[Development Environment](#development-environment).

See the [Usage](#usage) section for how to use the application.

To setup a new production/stage deployment of this project as a server, see the [BAS IT](#bas-it) section.

### Terraform

Terraform is used for:

* resources required for protecting and accessing the *Repository* components
* resources required for hosting the *Catalogue* component as a static website

Access to the [BAS AWS account](https://gitlab.data.bas.ac.uk/WSF/bas-aws),
[Terraform remote state](#terraform-remote-state) and NERC Azure tenancy are required to provision these resources.

```shell
$ cd provisioning/terraform
$ docker compose run terraform

$ az login --allow-no-subscriptions

$ terraform init
$ terraform validate
$ terraform fmt
$ terraform apply

$ exit
$ docker compose down
```

**Note:** The `terraform apply` step will need to be taken in stages for Azure application registrations. See the notes 
in `provisioning/terraform/54-azure_app_registrations.tf` for details.

Once provisioned, the following steps need to be taken manually:

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

### Azure permissions

[Terraform](#terraform) will create and configure the relevant Azure application registrations required for using
[OAuth](#oauth) to protect the CSW catalogues. However manual approval by a Tenancy Administrator is needed to grant
the registration representing the *client* role of the application access to the registration for the *server* role.

This has been approved by NERC RTS in 
[#3 (Internal)](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/3).

### BAS IT

Manually request a new application to be deployed from the BAS IT ServiceDesk using the
[request template](http://ictdocs.nerc-bas.ac.uk/wiki/index.php/Provisioning_Process#Template_ServiceDesk_request).

See [#44](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/44) for an example.

Manually request a new PostGIS database for the CSW catalogue backing databases from the BAS IT ServiceDesk and 
[setup](#pycsw-backing-database-setup) when provisioned.

Manually [add a new service](https://gitlab.data.bas.ac.uk/WSF/api-load-balancer#adding-a-new-service) and related
[documentation](https://gitlab.data.bas.ac.uk/WSF/api-docs#adding-a-new-service-service-version).

See [#60](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/60) for an example.

### PyCSW backing database setup

Backing databases for PyCSW servers require initialisation using the `csw setup` application
[CLI command](docs/command-reference.md#csw-setup) for both the *published* and *unpublished* repositories.

**Note:** Backing databases must use the PostgreSQL engine with the PostGIS extension enabled.

Normally this command will create the required database table, geometry column and relevant indexes. As catalogues only
require a single table, multiple can be stored in the same database/schema. However, two of the indexes used
(`fts_gin_idx` [full text search] and `wkb_geometry_idx` [binary geometry]) are named non-uniquely, preventing multiple
catalogues being co-located in the same schema.

This appears to be an oversight, as all other indexes are made unique by prefixing them with the name of the records
table, and doing this manually for these indexes appears to work without issue. To workaround this issue, you will need
to manually modify the indexes of catalogue tables once they've been setup.

Assuming the *Unpublished catalogue* is setup first, perform these steps *before* setting up the *Published catalogue*:

1. verify that the `records_unpublished` table was created successfully (contains `fts_gin_idx` and `wkb_geometry_idx`
   indexes)
2. alter the affected indexes in the `records_unpublished` table [1]
3. setup the *Published catalogue* `flask csw setup published`
4. alter the affected indexes in the second table [2]

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

## Development

### Development environment

Once setup, a development environment can be used to:

* run all components locally:
  * useful for end-to-end testing
  * useful for testing changes to how data is loaded into CSW catalogues
* use real data but generate a local static site:
  * useful for iterating changes to static website templates
  * NOT YET SUPPORTED - see [#200](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/200)
* use real data:
  * useful for managing records (i.e. for ADD releases)
  * NOT YET SUPPORTED - see [#201](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/201)

Git, [Poetry](https://python-poetry.org) and [Docker Desktop](https://www.docker.com/products/docker-desktop) are 
required to set up a local development environment of this project.

**Note:** If you use [Pyenv](https://github.com/pyenv/pyenv), this project sets a local Python version for consistency.

```shell
# clone from the BAS GitLab instance if possible
$ git clone https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox.git

# setup virtual environment
$ cd add-metadata-toolbox
$ poetry install

# pull docker containers
$ docker compose pull
```

To run all components locally:

```shell
# start local Postgres database for CSW and Nginx for static website
$ docker compose up

# start flask application as a server (it will automatically use the local postgres database)
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development poetry run flask

# Run flask CLI commands
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development poetry run flask [command]
```

See the [Command Reference](docs/command-reference.md) for how to use the CLI. Where `flask` is written, replace this
with `FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development poetry run flask`.

When built, a local static site can be accessed from [http://localhost:9000](http://localhost:9000).

### Package structure

All code for this project should be defined in the `scar_add_metadata_toolbox` package, with the exception of tests.

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

### Code Style

PEP-8 style and formatting guidelines must be used for this project, except the 80 character line limit.
[Black](https://github.com/psf/black) is used for formatting, configured in `pyproject.toml` and enforced as part of
[Python code linting](#code-linting).

Black can be integrated with a range of editors, such as
[PyCharm](https://black.readthedocs.io/en/stable/integrations/editors.html#pycharm-intellij-idea), to apply formatting
automatically when saving files.

To apply formatting manually:

```shell
$ poetry run black src/ tests/
```

### Code Linting

[Flake8](https://flake8.pycqa.org) and various extensions are used to lint Python files. Specific checks, and any
configuration options, are documented in the `./.flake8` config file.

To check files manually:

```shell
$ poetry run flake8 src/ tests/
```

Checks are run automatically in [Continuous Integration](#continuous-integration).

### Dependencies

Python dependencies for this project are managed with [Poetry](https://python-poetry.org) in `pyproject.toml`.

Non-code files, such as static files, can also be included in the [Python package](#python-package) using the
`include` key in `pyproject.toml`.

#### Adding new dependencies

To add a new (development) dependency:

```shell
$ poetry add [dependency] (--dev)
```

Then update the Docker image used for CI/CD builds and push to the BAS Docker Registry (which is provided by GitLab):

```shell
$ docker build -f gitlab-ci.Dockerfile -t docker-registry.data.bas.ac.uk/magic/add-metadata-toolbox:latest .
$ docker push docker-registry.data.bas.ac.uk/magic/add-metadata-toolbox:latest
```

#### Updating dependencies

```shell
$ poetry update
```

See the instructions above to update the Docker image used in CI/CD.

#### Dependency vulnerability checks

The [Safety](https://pypi.org/project/safety/) package is used to check dependencies against known vulnerabilities.

**IMPORTANT!** As with all security tools, Safety is an aid for spotting common mistakes, not a guarantee of secure
code. In particular this is using the free vulnerability database, which is updated less frequently than paid options.

This is a good tool for spotting low-hanging fruit in terms of vulnerabilities. It isn't a substitute for proper
vetting of dependencies, or a proper audit of potential issues by security professionals. If in any doubt you MUST seek
proper advice.

Checks are run automatically in [Continuous Integration](#continuous-integration).

To check locally:

```shell
$ poetry export --without-hashes -f requirements.txt | poetry run safety check --full-report --stdin
```

#### Dependencies for vendored dependencies 

...

### Static security scanning

To ensure the security of this API, source code is checked against [Bandit](https://github.com/PyCQA/bandit)
and enforced as part of [Code linting](#code-linting).

**Warning:** Bandit is a static analysis tool and can't check for issues that are only be detectable when running the
application. As with all security tools, Bandit is an aid for spotting common mistakes, not a guarantee of secure code.

To check manually:

```shell
$ poetry run bandit -r src/ tests/
```

Checks are run automatically in [Continuous Integration](#continuous-integration).

### Flask application

The Flask application representing this project is defined in the `scar_add_metadata_toolbox` package. The 
application uses the [application factory](https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/) pattern.

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

Where displaying a file path to the user, use the absolute/resolved form to aid in debugging.

### Templates

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

### Testing

All code in the `scar_add_metadata_toolbox` package must be covered by tests, defined in `tests/`. This project uses
[PyTest](https://docs.pytest.org/en/latest/) which should be ran in a random order using
[pytest-random-order](https://pypi.org/project/pytest-random-order/).

To run tests manually from the command line:

```shell
$ FLASK_ENV=testing poetry run pytest --random-order
```

To run tests manually using PyCharm, use the included *App (Tests)* run/debug configuration.

Tests are ran automatically in [Continuous Integration](#continuous-integration).

#### Test coverage

[pytest-cov](https://pypi.org/project/pytest-cov/) is used to measure test coverage.

A `.coveragerc` file is used to omit code from the `scar_add_metadata_toolbox.hazmat` module.

To measure coverage manually:

```shell
$ FLASK_ENV=testing poetry run pytest --cov=scar_add_metadata_toolbox --cov-config=.coveragerc --cov-fail-under=100 --cov-report=html .
```

[Continuous Integration](#continuous-integration) will check coverage automatically and fail if less than 100%.

#### Continuous Integration

All commits will trigger a Continuous Integration process using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.

## Deployment

### Python package

This project is distributed as a Python package, hosted in ...

Source and binary packages are built and published automatically using
[Poetry](https://python-poetry.org) in [Continuous Deployment](#continuous-deployment).

**Note:** Except for tagged releases, Python packages built in CD will use `0.0.0` as a version to indicate they are
not formal releases.

### BAS IT service

The deployment [Python package](#python-package) is deployed as a WSGI application via BAS IT using an Ansible playbook:
[`/playbooks/magic/add-metadata-toolbox.yml`](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/playbooks/magic/add-metadata-toolbox.yml) (internal)

Variables for this application are set in:
[`/group_vars/magic/add-metadata-toolbox.yml`](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/group_vars/magic/add-metadata-toolbox.yml) (internal)

Environment variables used by this application are set in:
[`/playbooks/magic/add-metadata-toolbox.yml`](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/playbooks/magic/add-metadata-toolbox.yml) (internal)

This application is deployed to a development, staging and production environment. Hosts for each environment are listed
in the relevant Ansible inventory in:
[`/inventory/magic/`](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/tree/master/inventory/magic) (internal)

**Note:** The process to run/update this playbook/variables is still under development (see
[#44](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/44) (internal) for background). Currently
either needs to be requested through the [IT ServiceDesk](mailto:servicedesk@bas.ac.uk).

#### Key paths

Key files/directories within this deployed application are:

* `/etc/httpd/sites/10-add-metadata-toolbox.conf`: Apache virtual host
* `/var/opt/wsgi/.virtualenvs/add-metadata-toolbox`: Python virtual environment
* `/var/www/add-metadata-toolbox/app.py`: Application entrypoint script
* `/var/log/httpd/access_log.add_metadata_toolbox`: Apache virtual host access log
* `/var/log/httpd/error_log.add_metadata_toolbox`: Apache/Application error/log file

#### SSH access

| Environment | SSH Access     | Sudo | Access   |
| ----------- | -------------- | ---- | -------- |
| Development | Yes            | Yes  | `felnne` |
| Staging     | Yes (for logs) | No   | `felnne` |
| Production  | Yes (for logs) | No   | `felnne` |

Currently access to the servers for each environment is bespoke but should be standardised in future, see
[#100](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/100) for more information.

#### Flask CLI

To use the Flask CLI:

```shell
$ ssh [server]
$ sudo su
$ . [path to virtual environment]/bin/activate
$ export FLASK_APP=scar_add_metadata_toolbox
$ export FLASK_ENV=production
$ flask [command]
$ deactivate
$ exit
$ exit
```

### API Service

The CSW Catalogues are deployed as a service within the BAS API Load Balancer, backed by the production
[BAS IT service](#bas-it-service).

#### API Documentation

Usage documentation for this API service is held in `docs/api/` and currently
[manually](https://gitlab.data.bas.ac.uk/WSF/api-docs#adding-a-service-manually) published using these service paths:

* `s3://bas-api-docs-content-testing/services/data/metadata/add/csw/`
* `s3://bas-api-docs-content/services/data/metadata/add/csw/`

### Continuous Deployment

All commits will trigger a Continuous Deployment process using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.

## Release procedure

For all releases:

1. create a release branch
2. close release in `CHANGELOG.md`
3. push changes, merge the release branch into `main` and tag with version
4. create a ServiceDesk request to deploy the new package version (and change/add environment variables if needed)
5. re-deploy API documentation if needed

## Feedback

The maintainer of this project is the BAS Mapping and Geographic Information Centre (MAGIC), they can be contacted at:
[magic@bas.ac.uk](mailto:magic@bas.ac.uk).

## Issue tracking

This project uses issue tracking, see the
[Issue tracker](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues) for more information.

**Note:** Read & write access to this issue tracker is restricted. Contact the project maintainer to request access.

## License

Copyright (c) 2020-2022 UK Research and Innovation (UKRI), British Antarctic Survey.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
