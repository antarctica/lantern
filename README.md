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

1. Repository, for storing metadata records, acting as a source of truth
2. Catalogue, for displaying metadata records, acting as a discovery tool

These components map to components 4 and 6 in the draft ADD data workflow
([#139 (internal)](https://gitlab.data.bas.ac.uk/MAGIC/add/issues/139)).

Metadata records use the [ISO 19115](https://metadata-standards.data.bas.ac.uk/standard/iso-19115/) metadata standard.
The [OGC Catalogue Services for the Web (CSW)] standard is used to provide the *Repository* component, allowing records
to be added, accessed, updated and deleted. Records can be either published (available publicly) or unpublished. 
Access to any unpublished records, and the ability to publish/retract records, is restricted to relevant ADD project 
members.

Once published, records can be viewed through the *Catalogue* component, a static website, which presents published 
records as human-readable items (with geographic extents visualised on a map for example). Manually curated collections 
provide a basic way to group items into sets. This Catalogue is part of the current/legacy BAS Data Catalogue, known as 
the [Discovery Metadata System (DMS)](https://data.bas.ac.uk), which is in the process of being replaced.

## Usage

### Workflows

* [adding new records](docs/workflow-adding-records.md)
* [updating existing records](docs/workflow-updating-records.md)

### Available commands

[Command line reference](docs/command-reference.md)

### Registering download proxy items

See the [Registering Download Proxy Artefact Lookup Items](#registering-downloads-proxy-artefacts-lookup-items) section.

## Implementation

### Implementation Overview

Flask application:

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

Static website:

* is hosted in AWS S3 and reverse proxied as part of the [`data.bas.ac.uk`](https://data.bas.ac.uk) domain
* web maps are hosted using [Esri](#esri-web-maps)
* contact forms for feedback and items are processed using [Microsoft Power Automate](#feedback-and-contact-forms)
* legal policies use templates from the 
  [Legal Policies](https://gitlab.data.bas.ac.uk/web-apps/legal-policies-templates) project
* uses [Sentry](#sentry-error-tracking) for frontend error tracking

### Architecture

This diagram shows the main concepts in this project and how they relate:

![concepts overview](docs/assets/diagrams/concepts.png)

### Metadata records

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

### Items

Items are derived from Records using any hierarchy level except 'collection' (which is represented by 
[Collections](#collections)). Whereas Records prioritise strictness and being unambiguous, Items prioritise readability 
and understanding by humans.

Items are specific to this Data Catalogue, and can infer and present information in ways that general representations
are unable to (e.g. by recognising and reformatting commonly used projections, vocabularies or contacts). 

As Items are derived from Records, they are not persisted themselves, except as rendered pages within the static site.

### Collections

Collections are a simple way to group [Items](#items) together based on a shared purpose, theme or topic. Like Items, 
collections are derived from Records using the 'collection' hierarchy level.

As Collections are derived from Records, they are not persisted themselves, except as rendered pages within the static 
site.

**Note:** Currently, Collections can only include Items from this Data Catalogue, rather than external resources.

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

### Sentry error tracking

Backend and frontend errors in this service are tracked with Sentry:

* [Sentry dashboard](https://sentry.io/organizations/antarctica/issues/?project=5197036)
* [GitLab dashboard](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/error_tracking)

Backend error tracking will be enabled or disabled depending on the environment. It can be manually controlled by 
setting the `APP_ENABLE_SENTRY` [Configuration option](#configuration).

### Application logging

Logs for this service are written to *stdout/stderr* as appropriate.

### Health checks

A check for the Flask application is available to determine the health of the server side application (CSV endpoints).

It is available at `/meta/health/v1` and uses the draft 
[Health Check Response Format for HTTP APIs](https://inadarei.github.io/rfc-healthcheck) RFC structure.

**Note:** This endpoint is tested or designed for high frequency checks (i.e. more than every 10 seconds). 

It is intended for use in monitoring systems, and to verify the deployed version of the service. It is currently a very 
basic check, without verifying things like database connectivity.

Example request/response:

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

#### Application logging (BAS IT)

When deployed as a BAS IT service, application logs are captured by Apache, and written to a log files. See  
[Key Paths](#key-paths) section for location. Log files are rotated weekly at ≈03:00 (day unknown).

**Note:** When logs are rotated the Flask application will be restarted.

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

### CSW

The [OGC CSW](https://www.ogc.org/standards/cat) standard is used as a protocol and interface for accessing and 
managing [Records](#metadata-records) in the *Repository* component.

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

Both PyCSW (CSW server) and OWSLib (CSW client) have a maximum record limit of *100* per request.

#### CSW Supported Element Sets

Both PyCSW (CSW server) and OWSLib (CSW client) support the *full* Element Set only.

#### CSW backing databases

CSW servers are backed using PostGIS (Postgres) databases. In production, these are provided by BAS IT (via the 
central Postgres database `bsldb`). Credentials for this database are stored in the MAGIC 1Password shared vault. 

In local development environments, a local PostGIS database configured in `docker-compose.yml` is used.

To test against real data in a non-production environment, a staging database, which is synced from the production 
database, can be used. Credentials for this database are stored in the MAGIC 1Password shared vault. This database is
re-synced automatically by BAS IT every Tuesday at 02:00. 

#### CSW auth

Requests are evaluated as being either 'read' or 'write' based on either the `request` query string parameter, or
elements used in the request body (e.g. `request=GetRecords` or `<csw:Query>` for a read/select request).

These permissions are mapped onto required scopes for each catalogue. Required scopes may be empty to allow anonymous 
for read or write.

Where the request type cannot be determined unambiguously it will be rejected.

### Jinja templates

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

### S3 static website

Rendered templates and other static assets are hosted through an AWS S3 bucket with static website hosting enabled. 
Separate production and integration buckets are available to preview changes. [Terraform](#terraform) is used to define 
and provision these buckets.

Rules within the BAS General Load Balancer, managed by IT, are used to reverse proxy content from these S3 static sites 
to appear as part of the production and testing current/legacy BAS Discovery Metadata System (DMS).

### ESRI web maps

To display the spatial extent of Items, an ESRI web map is included in the page template for Items. This web map 
uses:

* the [ESRI ArcGIS API for JavaScript](https://developers.arcgis.com/javascript/latest/) as a mapping framework
* [ESRI ArcGIS Online](https://www.arcgis.com/index.html) for mapping layers

#### ESRI API key

Accessing content from ArcGIS Online requires an API key from the ESRI 
[ArcGIS Developers](https://developers.arcgis.com) platform. This API key is treated as an application secret, and 
must be set as an environment variable when building the static site.

Once built, this key will be embedded in page content, and visible to end-users accessing the static site. This is 
considered safe providing some 
[precautions](https://developers.arcgis.com/documentation/mapping-apis-and-services/security/security-best-practices/#api-key-security)
are taken.

The API key used for this project is stored in the MAGIC 1Password shared vault as the *SCAR ADD Metadata Toolbox - 
ESRI ArcGIS API key* item.

### Feedback and contact forms

A Microsoft
[Power Automate](https://emea.flow.microsoft.com/manage/environments/Default-b311db95-32ad-438f-a101-7ba061712a4e/flows/97d95c3b-5d40-4358-86a6-979a679a4b7c/details)
Flow is used to process feedback and contact form submissions. Messages support Markdown formatting, converted to HTML
prior to submission. On submission, Power Automate creates an issue for the message in a relevant GitLab project.

### Website metrics

**Note:** Website metrics are not currently collected. See 
[#292](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/292) for more information.

### Download metrics

**Note:** Download metrics are not currently collected. See 
[#246](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/246) for more information.

### Downloads Proxy 

To support [tracking downloads](#download-metrics) of items, a proxy service is used. This proxy intercepts requests to 
download files, returning a 302 temporary redirect to the item download. Redirection is used to increase, but not 
ensure, the chances downloads are tracked, by making the real location of items less obvious, and harder to share/use 
directly.

When a request is made (using a download URL), an [AWS Lambda function](#downloads-proxy-lambda-functions) looks up 
the distribution option identifier (termed an [Artefact lookup](#downloads-proxy-artefacts-lookup-schema) item) in a 
JSON file (stored in a S3 bucket).

For example, requesting a download URL such as `https://data.bas.ac.uk/download/123`, where `123` is the identifier 
for a distribution option (artefact lookup) within an item, will return a 302 redirect with a URL to its real location,
`https://example.com/dataset.gpkg`.

#### Downloads proxy Lambda functions

The Downloads Proxy is a set of AWS Lambda functions using NodeJS defined in `support/downloads-proxy/index.js`. 

There are two functions used for reading and writing [Artefact Lookups](#downloads-proxy-artefacts-lookup-schema).
In addition, there are two independent environments, *staging* and *production*. Each environment uses a separate S3
bucket, with object versioning, containing a separate code package and artefact lookups JSON file. The Lambda endpoint 
for each environment is reverse proxied to appear as part of the BAS Data Catalogue (`data.bas.ac.uk`) using the BAS 
General Load Balancer.

Access to use Lambda functions that can modify state (the write functions) is restricted. AWS Customer Managed IAM 
polices are defined by this project to assign permissions to use these functions to suitable AWS IAM principles 
(users or roles).

**WARNING!** Some or all lookup items in the staging environment MAY be removed at anytime.

* Staging instance:
  * S3 bucket (AWS Console): `https://s3.console.aws.amazon.com/s3/buckets/add-catalogue-downloads-proxy-stage?region=eu-west-1&tab=objects`
  * Lambda function (Read, AWS Console): `https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions/add-catalogue-downloads-proxy-stage`
  * Lambda function (Read, HTTP Endpoint): `https://vp3wuemex36unyzbzx76g4pnce0henks.lambda-url.eu-west-1.on.aws/`
  * Lambda function (Write, AWS Console): `https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions/add-catalogue-downloads-proxy-write-stage`
  * Lambda function (Write, HTTP Endpoint): `https://zrpqdlufnfqcmqmzppwzegosvu0rvbca.lambda-url.eu-west-1.on.aws/`
  * Lambda function (Read, Reverse Proxied HTTP Endpoint, Staging Catalogue): `https://data-testing.data.bas.ac. uk/download-testing/`
  * Lambda endpoint (Read, Reverse Proxied HTTP Endpoint, Production Catalogue): `https://data.bas.ac. uk/download-testing/`
  * Artefact lookups file: `s3://add-catalogue-downloads-proxy-stage/lookups.json`
  * Lambda function (Write, IAM Customer Managed policy): `BAS-ADD-Catalogue-Downloads-Proxy-Function-Write-Staging`
* Production instance:
  * S3 bucket (AWS Console): `https://s3.console.aws.amazon.com/s3/buckets/add-catalogue-downloads-proxy-prod?region=eu-west-1&tab=objects`
  * Lambda function (Read, AWS Console): `https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions/add-catalogue-downloads-proxy-prod`
  * Lambda endpoint (Read, HTTP Endpoint): `https://v7lyval5auv7hnqd75rsdhfi640wvpet.lambda-url.eu-west-1.on.aws/`
  * Lambda function (Write, AWS Console): `https://eu-west-1.console.aws.amazon.com/lambda/home?
    region=eu-west-1#/functions/add-catalogue-downloads-proxy-write-prod`
  * Lambda function (Write, HTTP Endpoint): `https://dvej4gdfa333uci4chyhkxj3wq0fkxrs.lambda-url.eu-west-1.on.aws/`
  * Lambda function (Read, Reverse Proxied HTTP Endpoint, Staging Catalogue): `https://data-testing.data.bas.ac.uk/download/`
  * Lambda function (Read, Reverse Proxied HTTP Endpoint, Production Catalogue): `https://data.bas.ac.uk/download/`
  * Artefact lookups file: `s3://add-catalogue-downloads-proxy-prod/lookups.json`
  * Lambda function (Write, IAM Customer Managed policy): `BAS-ADD-Catalogue-Downloads-Proxy-Function-Write-Production`

See the [relevant](#downloads-proxy-source) development subsection for information on the source code for these 
functions. 

See the [Terraform](#terraform) setup subsection for information on how to provision the resources for 
these functions, including IAM policies.

See the [BAS API Load Balancer](#bas-api-load-balancer) setup subsection for information on how to set up reverse 
proxying for these functions.

#### Downloads proxy artefacts lookup schema

The Downloads Proxy reads information about artefacts that can be downloaded from a JSON file stored in an S3 bucket.
This JSON file can be [Updated](#registering-downloads-proxy-artefacts-lookup-items) as needed to include new artefact 
lookups or amend existing entries. The structure of this file consists of an object, the keys of which are artefact 
IDs, and values are an artefact lookup item.

An artefact lookup item is an object with these properties:

| Property       | Data Type | Required | Example                                |
|----------------|-----------|----------|----------------------------------------|
| `artefact_id`  | String    | Yes      | '758ab069-46d7-47b7-82d4-1905ed155a54' |
| `resource_id`  | String    | Yes      | 'beaa0a4e-e452-4087-b4f5-eb2b8246dedb' |
| `media_type`   | String    | Yes      | 'application/geopackage+sqlite3'       |
| `origin_uri`   | String    | Yes      | 'https://example.com/dataset.gpkg'     |

This structure is formally described by a JSON Schema in `support/downloads/proxy/artefact-lookups-v1.json`, which 
is published as part of the [BAS Metadata Standards](https://metadata-standards.data.bas.ac.uk) website at:

https://metadata-standards.data.bas.ac.uk/scar-add-metadata-toolbox-downloads-proxy-schemas/v1/artefact-lookups-v1.json

A complete JSON file, with a single artefact lookup item, looks like this:

```json
{
  "$id": "https://example.com/lookup.json",
  "$schema": "https://metadata-standards.data.bas.ac.uk/scar-add-metadata-toolbox-downloads-proxy-schemas/v1/artefact-lookups-v1.json",
  "artefacts": {
    "a16faf66-3ed1-46e5-8f53-2ef398d86b3f": {
      "artefact_id": "758ab069-46d7-47b7-82d4-1905ed155a54",
      "resource_id": "beaa0a4e-e452-4087-b4f5-eb2b8246dedb",
      "media_type": "application/geopackage+sqlite3",
      "origin_uri": "https://example.com/dataset.gpkg"
    }
  }
}
```

#### Registering downloads proxy artefacts lookup items

Individual artefact lookup items can be added through a Lambda function. 

**Note:** Bulk additions, or changes/removals of existing lookup items can be made by updating the relevant JSON file 
via the AWS S3 API. This is out of scope for this guide.

Requests to these Lambda functions require authentication using the
[AWS Signature Version 4](https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html) algorithm.

Generating this signature requires an AWS IAM principle (user or role) with the relevant IAM policy assigned, see the
[Downloads proxy Lambda functions](#downloads-proxy-lambda-functions) section for references and more information.

When called:

* an HTTP `204 No Content` status will be returned if the new lookup item is added successfully
* an HTTP `409 Conflict` status will be returned if the artefact ID in the lookup item is already registered
* other HTTP errors (in the `4xx` or `5xx` range), may be returned if an error occurs

Reference (using the command line):

```shell
# with AWSCuRL installed and AWS credentials configured (`brew install awscurl awscli`, then `aws configure`)
$ awscurl --region eu-west-1 --service lambda --access_key $AWS_ACCESS_KEY_ID --secret_key $AWS_SECRET_ACCESS_KEY '[Lambda function (Write, HTTP Endpoint)]' --request POST --header 'Content-Type: application/json' --data $'{"artefact_id": "[Artefact ID]", "resource_id": "[Resource ID]", "media_type": "[Media Type]", "origin_uri": "[Origin URI]"}'
```

Example (using the command line, for a fake artefact/resource using the staging environment):

```shell
$ awscurl --region eu-west-1 --service lambda --access_key xxx --secret_key xxx 'https://zrpqdlufnfqcmqmzppwzegosvu0rvbca.lambda-url.eu-west-1.on.aws/' --request POST --header 'Content-Type: application/json' --data $'{"artefact_id": "758ab069-46d7-47b7-82d4-1905ed155a54", "resource_id": "beaa0a4e-e452-4087-b4f5-eb2b8246dedb", "media_type": "application/geopackage+sqlite3", "origin_uri": "https://example.com/dataset.gpkg"}'
```

Reference (using Python):

```python
import requests
from requests_auth_aws_sigv4 import AWSSigV4  # `pip install requests-auth-aws-sigv4`

lookup_item = {
    'artefact_id': '[Artefact ID]',
    'resource_id': '[Resource ID]',
    'media_type': '[Media Type]',
    'origin_uri': '[Origin URI]'
}
lambda_endpoint = 'https://zrpqdlufnfqcmqmzppwzegosvu0rvbca.lambda-url.eu-west-1.on.aws/'

r = requests.post(url=lambda_endpoint, json=lookup_item, auth=AWSSigV4('lambda'))
r.raise_for_status()
print(r.status_code)
```

Example (using Python, for a fake artefact/resource using the staging environment):

```python
import requests
from requests_auth_aws_sigv4 import AWSSigV4

lookup_item = {
    'artefact_id': '758ab069-46d7-47b7-82d4-1905ed155a54',
    'resource_id': 'beaa0a4e-e452-4087-b4f5-eb2b8246dedb',
    'media_type': 'application/geopackage+sqlite3',
    'origin_uri': 'https://example.com/dataset.gpkg'
}
lambda_endpoint = 'https://zrpqdlufnfqcmqmzppwzegosvu0rvbca.lambda-url.eu-west-1.on.aws/'

r = requests.post(url=lambda_endpoint, json=lookup_item, auth=AWSSigV4('lambda'))
r.raise_for_status()
print(r.status_code)
```

#### Resetting staging downloads proxy lookup items

Periodically, lookup items in the staging environment should be reset on the production environment to clear out 
temporary or invalid lookup items added when developing integrations or in other testing.

This involves copying the lookup file from the production environment to the staging environment.

**Note:** Lookup files are versioned using S3 object versioning. If needed, this can be used to recover overwritten 
staging lookup items.

```shell
# with the AWS CLI installed and configured with appropriate credentials
$ aws s3 cp s3://add-catalogue-downloads-proxy-prod/lookups.json s3://add-catalogue-downloads-proxy-stage/lookups.json
```

## Configuration

Application configuration options are set in per-environment classes extending a base `Config` class in
`scar_add_metadata_toolbox/config.py`. The active environment is set using the `FLASK_ENV` environment variable.

Configuration options are defined, and documented, using class properties. Some configuration options may optionally be
set at runtime using environment variables. If not set, default values will be used.

| Configuration Option                                | Description                                                           | Allowed Values                     | Example Value                                            |
|-----------------------------------------------------|-----------------------------------------------------------------------|------------------------------------|----------------------------------------------------------|
| `APP_ENABLE_SENTRY`                                 | Feature flag to enable/disable Sentry error tracking                  | True/False                         | `true`                                                   |
| `APP_LOGGING_LEVEL`                                 | Minimum logging level to include in application logs                  | debug/info/warning/error/critical  | `warning`                                                |
| `APP_AUTH_SESSION_FILE_PATH`                        | Path to file used for authentication information                      | Valid file path                    | `/home/user/.config/scar_add_metadata_toolbox/auth.json` |
| `APP_SITE_PATH`                                     | Path to directory used for rendered static site content               | Valid directory path               | `/home/user/.config/scar_add_metadata_toolbox/_site`     |
| `CSW_ENDPOINT_UNPUBLISHED`                          | CSW endpoint for accessing unpublished catalogue                      | Valid URL                          | `http://example.com/csw/unpublished`                     |
| `CSW_ENDPOINT_PUBLISHED`                            | CSW endpoint for accessing published catalogue                        | Valid URL                          | `http://example.com/csw/published`                       |
| `CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT`            | Endpoint at which to run unpublished CSW catalogue                    | Valid URL                          | `http://example.com/csw/unpublished`                     |
| `CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT`              | Endpoint at which to run published CSW catalogue                      | Valid URL                          | `http://example.com/csw/published`                       |
| `CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION` | Connection string for unpublished CSW catalogue backing <br/>database | Valid SQLAlchemy connection string | `postgresql://postgres:password@db.example.com/postgres` |
| `CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION`   | Connection string for published CSW catalogue backing <br/>database   | Valid SQLAlchemy connection string | `postgresql://postgres:password@db.example.com/postgres` |
| `APP_S3_BUCKET`                                     | AWS S3 bucket name used for hosting static website content            | Valid AWS S3 bucket name           | `add-catalogue.data.bas.ac.uk`                           |
| `APP_ESRI_API_KEY`                                  | API Key for using [ESRI ArcGIS JavaScript client](#esri-api-key)      | Valid ESRI API key                 | `AAPK...qo`                                              |

These options are typically set when running this application as a client (CLI):

* `APP_LOGGING_LEVEL`
* `APP_AUTH_SESSION_FILE_PATH`
* `APP_COLLECTIONS_PATH`
* `APP_SITE_PATH`
* `CSW_ENDPOINT_UNPUBLISHED`
* `CSW_ENDPOINT_PUBLISHED`
* `APP_S3_BUCKET`
* `APP_ESRI_API_KEY`

These options are typically set when running this application as a server (CSW catalogues):

* `APP_LOGGING_LEVEL`
* `CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT`
* `CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT`
* `CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION`
* `CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION`

## Setup

To set up this project as an en-user (to manage and publish records), create a 
[Development Environment](#development-environment).

See the [Usage](#usage) section for how to use the application.

To set up a new production/stage deployment of this project as a server, see the [BAS IT](#bas-it) section.

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
in `provisioning/terraform/56-azure_app_registrations.tf` for details.

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
[OAuth](#oauth) to protect the CSW catalogues. 

Manual approval by a Tenancy Administrator (UKRI) is needed to grant the registration representing the *client* role 
of the application access to the registration for the *server* role.

This has been approved by NERC RTS in 
[#3 (Internal)](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/3).

### BAS IT

#### Flask application setup

Manually request a new application to be deployed from the BAS IT ServiceDesk using the
[request template](http://ictdocs.nerc-bas.ac.uk/wiki/index.php/Provisioning_Process#Template_ServiceDesk_request).
See [#44](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/44) for an example.

#### Postgres database

Manually request a new PostGIS database for the [CSW backing databases](#csw-backing-databases) from the BAS IT
ServiceDesk and run required [setup](#pycsw-backing-database-setup) when provisioned.

#### BAS General Load Balancer

Manually request entries are set up in the BAS General Load Balancer for:

1. Data Catalogue [static site](#s3-static-website) URLs:
    * for both the production and testing URLs (`data.bas.ac.uk`, `data-testing.data.bas.ac.uk`):
    * the paths to request are the top-level directories within the static site (e.g. `/items/`)
    * the [Health Check](#health-checks) can be used in HAProxy, providing the check frequency is lowered to 10 seconds
2. the [Downloads proxy](#downloads-proxy) instance endpoints:
    * (see [#242](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/242) for an example)
    * **Note:** ensure HAProxy health checks are disabled for this service, as it will incur a cost

### BAS API Load Balancer

Manually [add a new service](https://gitlab.data.bas.ac.uk/WSF/api-load-balancer#adding-a-new-service) and related
[documentation](https://gitlab.data.bas.ac.uk/WSF/api-docs#adding-a-new-service-service-version) for the CSW, health 
check and other server side endpoints. See [#60](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/60) 
for an example.

### Nagios checks

Request URL checks are setup in the [PDC Nagios instance](https://gitlab.data.bas.ac.uk/nagios/config/bslnagios) for:

* the [Health Check](#health-checks) endpoint
* a CSW GetCapabilities request for the published catalogue
* one of the legal policy pages within the static site

See  for an example request for these checks.

### PyCSW backing database setup

Backing databases for PyCSW servers require initialisation using the `csw setup` application
[CLI command](docs/command-reference.md#csw-setup) for both the *published* and *unpublished* repositories.

**Note:** Backing databases must use the Postgres engine with the PostGIS extension enabled.

Normally this command will create the required database table, geometry column and relevant indexes. As catalogues only
require a single table, multiple can be stored in the same database/schema. However, two of the indexes used
(`fts_gin_idx` [full text search] and `wkb_geometry_idx` [binary geometry]) are named non-uniquely, preventing multiple
catalogues being co-located in the same schema.

This appears to be an oversight, as all other indexes are made unique by prefixing them with the name of the records
table, and doing this manually for these indexes appears to work without issue. To work around this issue, you will need
to manually modify the indexes of catalogue tables once they've been set up.

Assuming the *Unpublished catalogue* is set up first, perform these steps *before* setting up the *Published catalogue*:

1. verify that the `records_unpublished` table was created successfully (contains `fts_gin_idx` and `wkb_geometry_idx`
   indexes)
2. alter the affected indexes in the `records_unpublished` table [1]
3. set up the *Published catalogue* `flask csw setup published`
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

### ESRI ArcGIS

ESRI ArcGIS is used for the [web maps](#esri-web-maps) within the catalogue static site.

Access to the [BAS ESRI tenancy](https://gitlab.data.bas.ac.uk/MAGIC/esri) is required to provision these resources.

To generate an ESRI ArcGIS developer API key:

1. login to https://developers.arcgis.com/api-keys/
2. click *New API Key*:
      1. title: `SCAR ADD Metadata Toolbox`
      2. description: `Embedded maps shown within the ADD Data Catalogue for extent information.`
3. from the *Location Services* section of the page for the new API key:
     1. choose *Configure Services*
     2. disable the *Geocoding (not stored)* option if enabled
     3. note: the *Basemaps* service is always enabled
4. copy the API key and paste into a 1Password password item with the name 'SCAR ADD Metadata Toolbox - ESRI ArcGIS API 
   key'

## Development

### Development environment

Git, [Poetry](https://python-poetry.org) [1.2+] and [Docker Compose](https://docs.docker.com/compose/) are required to 
set up a local development environment of this project.

```shell
# clone from the BAS GitLab instance if possible
$ git clone https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox.git

# setup virtual environment
$ cd add-metadata-toolbox
$ poetry install

# pull docker containers
$ docker compose pull
```

#### Running all components locally

Useful for:

* end-to-end testing
* testing changes to how data is loaded into CSW catalogues

```shell
$ cd add-metadata-toolbox

# Start the local Postgres database for CSW, and Nginx for the local static website
$ docker compose up

# In another terminal; Start the Flask application as a server (it will use the local postgres database by default)
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development poetry run flask run

# In another terminal; Run Flask CLI commands as a client
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development poetry run flask [command]
```

See the [Command Reference](docs/command-reference.md) for how to use the CLI. Where `flask` is written, replace this
with `FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development poetry run flask`.

When built, the local static site can be accessed from [http://localhost:9000](http://localhost:9000).

Quick start (example):

```shell
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development poetry run flask csw setup unpublished 
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development poetry run flask csw setup published 
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development poetry run flask auth sign-in
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development poetry run flask records import --publish ~/some-example-record.json
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development APP_ESRI_API_KEY=xxx poetry run flask site build
# (after example-record updated)
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development poetry run flask records import --publish --allow-update --allow-republish ~/some-example-record.json
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development APP_ESRI_API_KEY=xxx poetry run flask site build
```

Where the value for `APP_ESRI_API_KEY` is the 'SCAR ADD Metadata Toolbox - ESRI ArcGIS API key' item in the shared 
vault in the MAGIC 1Password account.

#### Building a local static site with production data

Useful for developing and testing changes to static website templates.

```shell
$ cd add-metadata-toolbox

# Start the local Postgres database for CSW [not used], and Nginx for the local static website
$ docker compose up
```

See the [Command Reference](docs/command-reference.md) for how to use the CLI. Where `flask` is written, replace this
with:

```shell
# Run Flask CLI commands as a client, with remote server
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development CSW_ENDPOINT_UNPUBLISHED=https://api.bas.ac.uk/data/metadata/add/csw/v1/unpublished CSW_ENDPOINT_PUBLISHED=https://api.bas.ac.uk/data/metadata/add/csw/v1/published poetry run flask [command]
```

When built, the local static site can be accessed from [http://localhost:9000](http://localhost:9000).

If building the static site, include the `APP_ESRI_API_KEY` environment variable as well, using the 'SCAR ADD Metadata 
Toolbox - ESRI ArcGIS API key' item in the MAGIC shared vault in 1Password as the value.

**Note:** to use the remote server in the staging environment instead, use this command for `flask` commands:

```shell
# Run Flask CLI commands as a client, with remote server
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development CSW_ENDPOINT_UNPUBLISHED=http://add-metadata-toolbox.bslmagf-staging.nerc-bas.ac.uk/csw/unpublished CSW_ENDPOINT_PUBLISHED=http://add-metadata-toolbox.bslmagf-staging.nerc-bas.ac.uk/csw/published poetry run flask [command]
```

#### Using a local client and local server with a remote database

Useful for testing with real data but where changes to the server application are being developed or tested.

```shell
$ cd add-metadata-toolbox

# Start the local Postgres database for CSW [not used], and Nginx for the local static website
$ docker compose up

# In another terminal; Start the Flask application as a server (using the production database)
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION=postgresql://pycsw_production:xxx@bsldb.nerc-bas.ac.uk/pycsw_production CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION=postgresql://pycsw_production:xxx@bsldb.nerc-bas.ac.uk/pycsw_production poetry run flask run

# In another terminal; Run Flask CLI commands as a client
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development poetry run flask [command]
```

Where `xxx` should be replaced with real credentials from the *MAGIC CSW [Prod]* entry in the shared vault in the 
MAGIC 1Password.

See the [Command Reference](docs/command-reference.md) for how to use the CLI. Where `flask` is written, replace this
with `FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development poetry run flask`.

When built, the local static site can be accessed from [http://localhost:9000](http://localhost:9000).

If building the static site, include the `APP_ESRI_API_KEY` environment variable as well, using the 'SCAR ADD Metadata 
Toolbox - ESRI ArcGIS API key' item in the MAGIC shared vault in 1Password as the value.

**Note:** to use the database staging environment instead, use this command for starting the Flask application as a
server:

```shell
# In another terminal; Start the Flask application as a server (using the production database)
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=development CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION=postgresql://pycsw_staging:xxx@bsldb.nerc-bas.ac.uk/pycsw_staging CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION=postgresql://pycsw_staging:xxx@bsldb.nerc-bas.ac.uk/pycsw_staging poetry run flask run
```

Where `xxx` should be replaced with real credentials from the *MAGIC CSW [Staging]* entry in the MAGIC 1Password.

### Package structure

All code for this project should be defined in the `scar_add_metadata_toolbox` package, within the `src/` directory, 
except for:

* [Tests](#testing)
* the [Downloads Proxy](#downloads-proxy)

In brief, this package comprises these modules:

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
configuration options, are documented in the `[tool.flake8]` section of `pyproject.toml`.

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

#### Listing outdated dependencies

To list out of date dependencies:

```shell
$ poetry show --outdated
```

**Note:** This will include non-primary dependencies (i.e. not those listed directly in `pyproject.toml`), which should
normally be ignored.

**Note:** To find out why a dependency is required, run `poetry show [package]`.

#### Updating dependencies

To update packages within their allowed constraints:

```shell
$ poetry update
```

After updating, see the instructions above to update the Docker image used in CI/CD.

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

#### Updating minimum Python version [WIP]

As dependencies drop support for older Python versions, pressure will build to increase the minimum Python version 
required for this package (e.g. from `3.6` to `3.8`). When this pressure becomes too great (e.g. due to incompatibility 
with OS packages, security vulnerabilities, etc.), the minimum Python version should be increased.

Suggested upgrade steps:

1. upgrade to new Python version but keeping the same dependency versions (except `pyproj` and backports)
2. address any code incompatibilities due to backports
3. upgrade dependencies to their latest versions, as per the [Updating dependencies](#updating-dependencies) section

In more detail for step 1:

1. in `poetry.toml` change special `python` dependency to new Python version (e.g. `^3.8`)
2. if using `pyenv`, switch to the latest patch release of new Python version (e.g. 3.8.15)
3. re-create the virtual environment to check all dependencies install correctly [1]
4. run application tests manually
5. update the base image used in `gitlab-ci.Dockerfile` to match the new Python version (e.g. `python:3.8-alpine`)
6. rebuild the `gitlab-ci.Dockerfile` (the Docker image used for CI/CD builds) [2]
7. check whether the [`pyproj`](#upgrading-pyproj-dependency) dependency can be updated 
8. push the updated container to the BAS Docker Registry [3]

[1]

```
$ rm -rf .venv 
$ poetry install
```

[2]

```
$ docker build -f gitlab-ci.Dockerfile -t docker-registry.data.bas.ac.uk/magic/add-metadata-toolbox:latest .
```

[3]

```
$ docker push docker-registry.data.bas.ac.uk/magic/add-metadata-toolbox:latest
``` 

1. change any packages that are pinned in `poetry.toml` due to Python version to their latest major versions
2. run `poetry upgrade` to upgrade dependencies

#### Upgrading `pyproj` dependency

The [pyproj](https://pyproj4.github.io/pyproj/stable/index.html) dependency depends on the version of the 
[`PROJ`](https://proj.org) library installed. Special care should therefore be taken to ensure the version of *pyproj*
required by this package supports the version of *PROJ* library available on target platforms. 

The *pyproj* website documents the minimum version of PROJ and Python required for each release. For example version
3.4.0 requires:

* Python 3.8
* PROJ 8.2

For development, in addition to local development environments (where it's assumed any version requirements can be met),
the container used for CI/CD in GitLab needs to be checked. This container is defined in `gitlab-ci.Dockerfile` and 
used the Alpine Python base image corresponding to the minimum Python version used by the package. Newer Alpine 
releases are used for newer versions of Python, and newer versions of PROJ are packaged for newer versions of Alpine. 
Care therefore needs to be taken if the version of Python used is old. To check the version of PROJ available within 
this container image:

```
$ docker run -it --rm docker-registry.data.bas.ac.uk/magic/add-metadata-toolbox:latest ash
$  proj -v
proj_create: unrecognized format / unknown name
Rel. 9.0.0, March 1st, 2022
<proj>: 
projection initialization failure
cause: Invalid PROJ string syntax
program abnormally terminated
```

If these dependencies can be satisfied for all target platforms, it is safe to upgrade the `pyproj` dependency.

#### Updating `bas-metadata-libray` dependency

Special care should be taken when the `bas-metadata-library` switches to a new 
[record configuration version](https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-library#supported-configuration-versions).

**Note:** When this is not the case, and the record configuration has not changed, this dependency can be upgraded like 
any other and this section skipped.

To upgrade, a multi-stage process should be followed to manage the rate of change. At each stage application tests 
should be re-run to ensure regressions are not introduced. Additional (edge) test cases may need to be added to the 
test suite as real world testing/deployment uncovers unforeseen regressions.

Suggested upgrade steps:

1. upgrade the Pip dependency for the Metadata Library to the new version:
    * this will usually mean all MetadataRecord classes will use the new config version internally
    * where a new MetadataRecordConfig class is returned it should be downgraded to the old version
    * where a new MetadataRecordConfig class is required as input, it should be upgraded from the old version
    * the `Record.dump()`, `Record.dumps()`, `Repository.retrieve_record()` and `Repository.retrieve_records()` methods 
      all interact with MetadataRecordConfig class instances and will need to be updated
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
subclasses. Where a configuration should be configurable at runtime it should be read as an environment variable and
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

All code in the `scar_add_metadata_toolbox` package must be covered by tests, defined in the 
`scar_add_metadata_toolbox_tests` package within the `tests/` directory.

This project uses [PyTest](https://docs.pytest.org/en/latest/) as a framework. Tests should always be run in a random 
order using [pytest-random-order](https://pypi.org/project/pytest-random-order/).

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
$ FLASK_ENV=testing poetry run pytest --random-order --cov=scar_add_metadata_toolbox --cov-config=.coveragerc --cov-fail-under=100 --cov-report=html .
```

[Continuous Integration](#continuous-integration) will check coverage automatically and fail if less than 100%.

#### Continuous Integration

All commits will trigger a Continuous Integration process using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.

#### Test Records

To ensure components such as Repository, Record, Item and Collection classes work correctly, a number of valid and 
intentionally invalid, [Metadata Record](#metadata-records) configurations are held within the tests for this project.

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

### Downloads Proxy source

Source code for the [Downloads Proxy](#downloads-proxy) is contained in a single JavaScript (NodeJS) module, `.
/support/downloads-proxy/index.js`. This module is composed of a set of JS functions with two AWS Lambda event handler 
entrypoints for the read and write Lambda functions (i.e. both Lambda functions read from the same source file but 
use different entrypoint methods).

Lambda event handlers receive event and context information as per the 
[Lambda documentation](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html#http-api-develop-integrations-lambda.proxy-format).

The Lambda function execution environment has access to the NodeJS standard library and the AWS JavaScript SDK.

See the [Downloads Proxy Deployment](#downloads-proxy-deployment) subsection for information on releasing changes to 
the Download Proxy code.

## Deployment

### Python package

This project is distributed as a Python package, hosted in the 
[BAS GitLab Python Registry](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/packages).

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

#### Deployment process

To deploy a new version of the Python package to the IT managed service:

1. create an issue in the 
   [Station Data Management](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/issues) GitLab project
    * this should link to the new release (in this project) being deployed
    * for an example see: https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/issues/62
2. create a merge request from this issue and update:
    * the [`scar_add_metadata_toolbox_version`](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/group_vars/magic/add-metadata-toolbox.yml#L16) 
      group variable to the new release
3. push change to branch and deploy to the development instance, using a pre-setup
   [BAS IT Ansible Deployment Environment](#bas-it-ansible-deployment-environment) [1]

[1]

```shell
# ssh into deployment environment
$ cd ./ansible
$ workon venv
$ git fetch origin
$ git checkout -b $BRANCH origin/$BRANCH
$ invoke ansible -e dev magic/add-metadata-toolbox
```

#### BAS IT Ansible deployment environment

To set up a deployment environment from which to run BAS IT Ansible deployments in a VM:

**Note:** Deployment environments are shared between projects, a pre-setup environment may already be available.

1. create a new virtual machine (CentOS is recommended)
2. set up a user with sudo access, and who's public key is registered in GitLab (to allow cloning projects)
3. install required software [1]
4. configure software [2]

[1]

```shell
# update existing software first
$ yum update
$ shutdown -r now

# install software
$ yum install epel-release python-virtualenvwrapper git libffi-devel gcc
```

[2]

```shell
$ echo 'export WORKON_HOME=$HOME/.virtualenvs' >> ~/.bashrc
$ echo 'source /usr/bin/virtualenvwrapper.sh' >> ~/.bashrc
# restart shell

$ git clone git@gitlab.data.bas.ac.uk:station-data-management/ansible.git
$ cd ansible
$ mkvirtualenv -a . venv
$ venv/bin/activate
(venv) $ pip install --upgrade pip
(venv) $ pip install -r requirements.txt --index-url http://bsl-repoa/pdc/halley/pip --trusted-host bsl-repoa
(venv) $ echo '[Secret]' > $/.vault_magic.password
```

Where: `[Secret]` is from the 'Ansible Vault - BAS IT (MAGIC Dev)' entry in 1Password.

#### Key paths

Key files/directories within this deployed application are:

* `/etc/httpd/sites/10-add-metadata-toolbox.conf`: Apache virtual host
* `/var/opt/wsgi/.virtualenvs/add-metadata-toolbox`: Python virtual environment
* `/var/www/add-metadata-toolbox/app.py`: Application entrypoint script
* `/var/log/httpd/access_log.add_metadata_toolbox`: Apache virtual host access log
* `/var/log/httpd/error_log.add_metadata_toolbox`: Apache/Application error/log file

#### SSH access

| Environment | SSH Access     | Sudo | Access   |
|-------------|----------------|------|----------|
| Development | Yes            | Yes  | `felnne` |
| Staging     | Yes (for logs) | No   | `felnne` |
| Production  | Yes (for logs) | No   | `felnne` |

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

### Downloads proxy deployment

When [Source Code](#downloads-proxy-source) for the [Downloads Proxy](#downloads-proxy) is updated, it needs to be
packaged into a zip archive for deployment via [Terraform](#terraform).

**Note:** Terraform will automatically deploy either zip archive if its file hash changes. Therefore, only update the 
archives of Download Proxy environments you wish to update. I.e. don't update the production archive if changes are 
still being tested.

To package the source code into a deployment package for the staging environment:

```shell
$ cd support/downloads-proxy/
$ zip -u downloads-proxy-stage.zip index.js
```

To package the source code into a deployment package for the production environment:

```shell
$ cd support/downloads-proxy/
$ zip -u downloads-proxy-prod.zip index.js
```

To deploy changes, plan and apply the [Terraform](#terraform) configuration.

### Downloads proxy JSON Schema deployment

The JSON Schema used for the [Downloads Proxy](#downloads-proxy-artefacts-lookup-schema) is distributed through the BAS 
Metadata Standards website, alongside other related schemas from other projects.

**Note:** These instructions assume the JSON Schema is version 1. Replace `v1` if this version is different (e.g. `v3`).

To deploy the latest Downloads Proxy JSON Schema for use within the *staging* environment of the BAS Metadata 
Standards website:

```shell
# with the AWS CLI installed and configured with appropriate credentials
$ aws s3 cp ./support/downloads-proxy/artefact-lookups-v1.json s3://metadata-standards-testing.data.bas.ac.uk/scar-add-metadata-toolbox-downloads-proxy-schemas/v1/artefact-lookups-v1.json
```

To deploy the latest Downloads Proxy JSON Schema for use within the *production* environment of the BAS Metadata 
Standards website:

```shell
# with the AWS CLI installed and configured with appropriate credentials
$ aws s3 cp ./support/downloads-proxy/artefact-lookups-v1.json s3://metadata-standards.data.bas.ac.uk/scar-add-metadata-toolbox-downloads-proxy-schemas/v1/artefact-lookups-v1.json
```

### Continuous Deployment

All commits will trigger a Continuous Deployment process using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.

## Release procedure

For all releases:

1. create an [Issue](#issue-tracking) using the *release* template

**Note:** To update the release template, edit `./gitlab/issue_templates/release.md`. 

Usually you will then want to deploy the new release:

1. create an [Issue](#issue-tracking) using the *deployment* template

**Note:** To update the release template, edit `./gitlab/issue_templates/deployment.md`.

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
