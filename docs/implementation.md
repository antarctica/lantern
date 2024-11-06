# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - Implementation

## Implementation Overview

A Flask application:

* using [CSW](#csw) to store [Metadata records](#metadata-records)
* interpreted as [Items](#items) in [Collections](#collections)
* rendered using [Jinja templates](#jinja-templates)
* served as a [static website](#s3-static-website) within the [`data.bas.ac.uk`](https://data.bas.ac.uk) website
* providing a CLI to set up components, manage records and build/publish the static site
* backend errors are tracked using [Sentry](#sentry-error-tracking)
* providing a [health endpoint](#health-checks) for monitoring application state

[CSW catalogues](#csw):

* are reverse proxied as a route in Flask
* are backed by PostGIS databases
* are secured using [OAuth](#oauth)
* optionally track changes made to records using [Revision Tracking](/docs/implementation-csw.md#csw-revision-tracking)

A Static website:

* hosted on AWS S3 and reverse proxied as part of [`data.bas.ac.uk`](https://data.bas.ac.uk)
* web maps are hosted using the [BAS Embedded Maps Service](#extent-maps)
* contact forms for feedback and items are processed using [Microsoft Power Automate](#feedback-and-contact-forms)
* legal policies use templates from the
  [Legal Policies 🛡️](https://gitlab.data.bas.ac.uk/web-apps/legal-policies-templates) project
* uses [Sentry](#sentry-error-tracking) for frontend error tracking

## Architecture

This diagram shows the high level concepts in this project and how they relate:

![concepts overview](/docs/assets/diagrams/concepts.png)

## Metadata records

Metadata records are the content and data within this project. Records describe resources, which are typically datasets
within the ADD, e.g. a record might describe the Antarctic Coastline dataset. Other types of records might describe
[Collections](#collections) of related records, or other resource such as map products.

Records in this catalogue aim to provide *discovery metadata*, which allows users to find and evaluate whether a
resource is useful to them (i.e. does it cover the right area?, has it been updated recently?, how was it made?, etc.).
This metadata is separate it from metadata for calibration or analysis for example.

Records are based on the [ISO 19115](https://metadata-standards.data.bas.ac.uk/standard/iso-19115-19139/) metadata
standard, which defines an information model (*19115-2:2009*), and XML encoding (*19139-2:2012*), for geographic data.

Records are stored/persisted in a records' repository (implemented using [CSW](#csw)). Records are imported and
exported (for editing) as files, or inserted/updated via the CSW transactional profile by other services.

The information in a metadata record is encoded in a different formats at different stages:

* when imported/exported (during editing), records are encoded as JSON, using the
  [BAS Metadata Library](https://github.com/antarctica/metadata-library) record configuration
* when stored in a repository, records are encoded as XML using the ISO 19139 encoding standard
* when viewed in the data catalogue, records are encoded in bespoke HTML

These different formats are used for different reasons:

* JSON is concise/accessible enough to be understood by humans for editing
* XML is proscribed by the ISO 19139 standard
* HTML is the de-facto standard for web content

### Minimum record requirements

In addition to the properties required by the ISO 19115 standard, the Catalogue requires these properties to be set in
all records:

1. `file_identifier` so records can be distinguished without relying on a value that may change or not be unique
1. `hierarchy_level` so records can be distinguished between [Items](#items) and [Collections](#collections) [2]
1. `identifier` as per [1], so that the Catalogue can determine whether a record is part of the Catalogue or not
1. `identifier.contacts[role='pointOfContact']` so the _contact_ item tab displays a point of contact

[1]

* identifier: `file_identifier`
* href: `https://data.bas.ac.uk/items/{file_identifier}`
* namespace: `data.bas.ac.uk`

## Items

Items are derived from Records using any hierarchy level except 'collection' (which is represented by
[Collections](#collections)). Whereas Records prioritise strictness and being unambiguous, Items prioritise readability
and understanding by humans.

Items are specific to this Data Catalogue, and can infer and present information in ways that general representations
are unable to (e.g. by recognising and reformatting commonly used projections, vocabularies or contacts).

As Items are derived from Records, they are not persisted themselves, except as rendered pages within the static site.

## Collections

Collections are a simple way to group [Items](#items) together based on a shared purpose, theme or topic. Like Items,
collections are derived from Records using the 'collection' hierarchy level.

As Collections are derived from Records, they are not persisted themselves, except as rendered pages within the static
site.

**Note:** Currently, Collections can only include Items from this Data Catalogue, rather than external resources.

## Configuration

See [Configuration](/docs/config.md) documentation.

## OAuth

OAuth is used to protect access to actions or information (unpublished Records) within the *Repository* component.
The [Microsoft Entra identity platform](https://learn.microsoft.com/en-us/entra/identity/) is used to define
roles/scopes for restricted actions or information, and to assign these to users/groups. The
[Flask Entra Auth](https://pypi.org/project/flask-entra-auth/) extension is used to enforce these permissions within
the Flask application.

Two Entra OAuth applications (application registrations) are defined for this:

1. a server application, representing the Repository
2. a client application, representing a user accessing or modifying records within the Repository

The Flask application represents both of these app registrations. The CLI acts as the client, and the CSW catalogues as
the server.

See the [Infrastructure](/docs/infrastructure.md#entra-app-registrations) documentation for specific resources.
[Terraform](/docs/setup.md#terraform) is used to define and provision these resources.

The server app registration defines the roles/scopes that exist (reading records, updating records, etc.). These are
then assigned to users and groups, who use them through the client app registration to read/update records, etc.:

* [assigning permissions to users](/docs/workflow-permissions-users.md)

## Sentry error tracking

Backend and frontend errors in this service are tracked with Sentry:

* [Sentry dashboard 🔒](https://sentry.io/organizations/antarctica/issues/?project=5197036)

Backend error tracking will be enabled or disabled depending on the environment. It can be manually controlled by
setting the `APP_ENABLE_SENTRY` [Configuration option](#configuration).

## Application logging

Logs for this service are written to *stdout/stderr* as appropriate for capture by underlying runtime environments.

When deployed as a [BAS IT service](/docs/deploy.md#bas-it-ansible), logs are captured by Apache and written to a log
files. Log files are rotated weekly at ≈03:00 (day unknown).

**Note:** When logs are rotated the Flask application will be restarted.

## Health checks

Two endpoints are available to check the health of the static site and Flask application respectively:

* static site: `/static/txt/heartbeat.txt`
* Flask app / CSW endpoints: `/meta/health/v1`

The static site health check is a simple file that is copied into the static site when built.

The Flask/CSW health check uses the draft
[Health Check Response Format for HTTP APIs](https://inadarei.github.io/rfc-healthcheck) RFC structure.

**Note:** This endpoint is not rated for high frequency checks and should not be checked more than every 10 seconds.

Both endpoints are intended for use in monitoring systems, where a non-200 status code can be interpreted as a failure.
The Flask endpoint can also be used to verify the deployed version of the service. Both checks are currently very basic.

Example request/response (static site):

```
$ curl "https://www.example.com/static/txt/heartbeat.txt"
```

```
badump, badump
```

Example request/response (Flask route):

```
$ curl "https://example.com/meta/health/v1" -H 'Accept: application/json'
```

```json
{
  "description": "Server side endpoints for the SCAR Antarctic Digital Database (ADD) Metadata Toolbox.",
  "links": {
    "about": "https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox",
    "describedBy": "https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/vN/A/README.md",
    "self": "https://example.com/meta/health/v1"
  },
  "releaseId": "0.6.0",
  "status": "pass",
  "version": 1
}
```

## Hazardous Materials module

In order to implement the [CSW package modifications](/docs/implementation-csw.md#csw-package-modifications), the
`pycsw` and `owslib` packages have been vendored into this application, meaning their source code, and their
dependencies, have been added within this project.

As this code is third party, and hasn't been vetted or integrated into this project, it is held in a *hazmat*
(Hazardous Materials) module, `scar_add_metadata_toolbox.hazmat`. This module is exempt from
[Code Linting](/docs/dev.md#linting), [Testing](/docs/dev.md#testing) and
[Test Coverage](/docs/dev.md#pytest-cov-test-coverage) rules.

The eventual aim is to remove these packages from this project, however this will depend on whether these packages
are used in the longer term (see
[MAGIC/add-metadata-toolbox#194 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/194)), and
if so, whether the changes made to them in this project, could be integrated into their upstream projects.

## CSW

See [CSW](/docs/implementation-csw.md) documentation.

## Jinja templates

A series of [Jinja2](https://jinja.palletsprojects.com/) templates are used for rendering pages, including
[Items](#items), [Collections](#collections) from the *Catalogue* component. Templates use the
[BAS Style Kit Jinja Templates](https://pypi.org/project/bas-style-kit-jinja-templates/), which in turn implements the
[BAS Style Kit](https://style-kit.web.bas.ac.uk).

Templates are stored in the `scar_add_metadata_toolbox.templates` module and organised into:

* `_layouts`: base page designs, currently using the
  [Standard Page](https://github.com/antarctica/bas-style-kit-jinja-templates#layouts) layout from the BAS Style Kit
* `_views`: designs for specific pages or types of content, such as the feedback and legal pages and Items
* `_includes`: components of a page that may be content specific (specific tabs within Item pages), or shared

For example, the template used for Item pages is a view which inherits from the application layout and combines a
number of includes to define a page structure with a fixed header and a series of tabs, each with their own content.

## S3 static website

Rendered templates and other static assets are hosted through an AWS S3 bucket with static website hosting enabled.
Separate production and integration buckets are available to preview changes. [Terraform](/docs/setup.md#terraform) is
used to define and provision these buckets.

Rules within the BAS General Load Balancer, managed by IT, are used to reverse proxy content from these S3 static sites
to appear as part of the production and testing current/legacy BAS Discovery Metadata System (DMS).

## Extent maps

To visualise the spatial extent of Items, a map is included using the
[BAS Embedded Maps](https://github.com/antarctica/embedded-maps).

## Feedback and contact forms

A Microsoft
[Power Automate 🔒](https://emea.flow.microsoft.com/manage/environments/Default-b311db95-32ad-438f-a101-7ba061712a4e/flows/97d95c3b-5d40-4358-86a6-979a679a4b7c/details)
Flow is used to process feedback and contact form submissions. Messages support Markdown formatting, converted to HTML
prior to submission. On submission, Power Automate creates an issue for the message in a relevant GitLab project.

## Website metrics

**Note:** Website metrics are not currently collected. See
[MAGIC/add-metadata-toolbox#416 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/416) for more
information.

## Download metrics

**Note:** Download metrics are not currently collected. See
[MAGIC/add-metadata-toolbox#292 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/292) for more
information.

## Downloads Proxy

See [Downloads Proxy](/docs/implementation-downloads-proxy.md) documentation.
