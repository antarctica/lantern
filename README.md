# SCAR Antarctic Digital Database (ADD) Metadata Toolbox

Prototype editor, repository and catalogue for 
[SCAR Antarctic Digital Database (ADD) discovery metadata](http://data.bas.ac.uk/collections/e74543c0-4c4e-4b41-aa33-5bb2f67df389/).

**Note:** This project is designed for internal use within MAGIC, but is offered to anyone with similar needs.

## Status

**This project is a prototype with a significant number of sharp and pointy edges. It has not been thoroughly tested and 
may break without warning or in unexpected ways. Code quality and organisation is currently very low.**

These limitations will be addressed in the near future as this project develops into a prototype for other discovery 
metadata records. Parts of this project may also be used for widely, such as in the new BAS wide data catalogue.

See the milestones and issues in this project on GitLab (internal) for more information.

## Overview

This project is a monolithic (Python Flask) application comprised of several components:

1. metadata editor - using a JSON file for each record implementing the 
[BAS Metadata Library](https://github.com/antarctica/metadata-library) record configuration for ISO 19115
2. unpublished (working) metadata repository - using an embedded, authenticated PyCSW catalogue
3. published metadata repository - using an embedded, partially-authenticated PyCSW catalogue
4. data catalogue - using a static website

These components map to components 2, 4 and 6 in the draft ADD data workflow 
([#139 (internal)](https://gitlab.data.bas.ac.uk/MAGIC/add/issues/139)).

At a high level, the *metadata editor* and *data catalogue* components are both clients of the *metdata repositories*.
Components communicate using CSW (including the transactional profile) with records encoded using ISO 19139.

All of the *unpublished repository* and the transactional parts of the *published repository* are authenticated using
OAuth (currently using Azure Active Directory). Access control is used to restrict access to draft/in-progress records 
held in the *unpublished repository* (to *authors*), and to restrict who can publish/retract records to/form the 
*published repository* (to *editors*).

Records in the *published repository* can be viewed through the *data catalogue* which transforms records into human 
readable items. These items are designed to make discovery metadata easy to find and understand (such as visualising 
geographic extents on a map). Manually defined collections provide a limited means to group items together.

An export process is used to save item and collection pages as pre-rendered HTML files that are served from a static
website. This content can be accessed through the existing [BAS data catalogue](https://data.bas.ac.uk) using 
reverse-proxying.

In the future:

* the *unpublished/published* repositories will be ran as standalone applications, in time as part of the 
[BAS CSW (internal)](https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/bas-csw) project
* the *data catalogue* will be incorporated into the new 
[BAS data catalogue (internal)](https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-catalogue) project

## Usage

This project runs in a container. See the [Setup](#setup) section for setup instructions.

If running on the BAS central workstations:

```shell
$ ssh geoweb@bslws01.nerc-bas.ac.uk
$ add-metadata-toolbox [command]
```

Configuration, logs and data input or output are stored in /users/geoweb/.config/add-metadata-toolbox/.

If any errors occur they will be reported to Sentry and relevant individuals alerted by email.

**Note:** This application does not work on the central workstations yet.

### Workflow: Adding a new record

Follow this workflow to publish metadata about a new dataset.

**Note:** You will need *author* rights to import new metadata records and *editor* rights to publish them for others 
to see.

This sequence diagram shows how the overall process to import and publish a new record:

[![](https://mermaid.ink/img/eyJjb2RlIjoic2VxdWVuY2VEaWFncmFtXG4gICUlIHVzaW5nIGNvbmZpZ3VyYXRpb246XG4gICUlIFwic2VxdWVuY2VcIjogeyBcInNob3dTZXF1ZW5jZU51bWJlcnNcIjogdHJ1ZSwgXCJtaXJyb3JBY3RvcnNcIjogZmFsc2UgfVxuXG4gIGF1dG9udW1iZXJcbiAgXG4gIHBhcnRpY2lwYW50IEEgYXMgQXV0aG9yXG4gIHBhcnRpY2lwYW50IFUgYXMgVW5wdWJsaXNoZWQgUmVwb3NpdG9yeVxuICBwYXJ0aWNpcGFudCBQIGFzIFB1Ymxpc2hlZCBSZXBvc2l0b3J5XG4gIHBhcnRpY2lwYW50IEMgYXMgRGF0YSBDYXRhbG9ndWVcbiAgcGFydGljaXBhbnQgViBhcyBWaXNpdG9yc1xuXG5cdEEtPj5VOiBJbXBvcnQgcmVjb3JkXG4gIFUtPj5QOiBQdWJsaXNoIHJlY29yZFxuICBDLT4-UDogUmVhZCByZWNvcmRcbiAgVi0-PkM6IFZpZXcgaXRlbSIsIm1lcm1haWQiOnsidGhlbWUiOiJkZWZhdWx0Iiwic2VxdWVuY2UiOnsic2hvd1NlcXVlbmNlTnVtYmVycyI6dHJ1ZSwibWlycm9yQWN0b3JzIjpmYWxzZX19LCJ1cGRhdGVFZGl0b3IiOmZhbHNlfQ)](https://mermaid-js.github.io/mermaid-live-editor/#/edit/eyJjb2RlIjoic2VxdWVuY2VEaWFncmFtXG4gICUlIHVzaW5nIGNvbmZpZ3VyYXRpb246XG4gICUlIFwic2VxdWVuY2VcIjogeyBcInNob3dTZXF1ZW5jZU51bWJlcnNcIjogdHJ1ZSwgXCJtaXJyb3JBY3RvcnNcIjogZmFsc2UgfVxuXG4gIGF1dG9udW1iZXJcbiAgXG4gIHBhcnRpY2lwYW50IEEgYXMgQXV0aG9yXG4gIHBhcnRpY2lwYW50IFUgYXMgVW5wdWJsaXNoZWQgUmVwb3NpdG9yeVxuICBwYXJ0aWNpcGFudCBQIGFzIFB1Ymxpc2hlZCBSZXBvc2l0b3J5XG4gIHBhcnRpY2lwYW50IEMgYXMgRGF0YSBDYXRhbG9ndWVcbiAgcGFydGljaXBhbnQgViBhcyBWaXNpdG9yc1xuXG5cdEEtPj5VOiBJbXBvcnQgcmVjb3JkXG4gIFUtPj5QOiBQdWJsaXNoIHJlY29yZFxuICBDLT4-UDogUmVhZCByZWNvcmRcbiAgVi0-PkM6IFZpZXcgaXRlbSIsIm1lcm1haWQiOnsidGhlbWUiOiJkZWZhdWx0Iiwic2VxdWVuY2UiOnsic2hvd1NlcXVlbmNlTnVtYmVycyI6dHJ1ZSwibWlycm9yQWN0b3JzIjpmYWxzZX19LCJ1cGRhdGVFZGl0b3IiOmZhbHNlfQ)

1. a JSON file containing the items metadata is imported into the *unpublished repository*
2. the record is published from *unpublished repository* to the *published repository*
3. the *data catalogue* reads records from the *published repository* to create item pages
4. visitors can then access item pages through the *data catalogue*

Steps:

1. create a metadata record using the 
   [interim guidance (internal)](https://gitlab.data.bas.ac.uk/MAGIC/add/issues/146#note_49157) for the BAS Metadata 
   Library record configuration
2. [Sign-in](#auth-sign-in) to the editor application
3. [Import](#records-import) the metadata record from its JSON file, which will add it to the unpublished repository
4. [Publish](#records-publish) the metadata record, which will copy it from the *unpublished* to *published* repository
5. [Export](#export) the data catalogue, which will read metadata records from the *published* repository and save them
   as static HTML content
6. [Publish](#publish) the data catalogue, which will upload the exported catalogue to a static website for others to 
   access

### Command reference

#### `version`

Reports the current application version.

#### `export`

Saves the *data catalogue* component to a static site that can then be published using the [`publish`](#publish) 
command.

```json
$ flask export
...
Successfully exported static site to scar_add_metadata_toolbox/build
```

**Note:** This command will replace any content already in the build directory `scar_add_metadata_toolbox/build`. This 
means if a record no longer exists in the latest export for example it will be removed from the static site.

**Note:** You will see warnings like the example below about missing URL generators, you can safely ignore these:

```
/usr/local/virtualenvs/scar_add_metadata_toolbox/lib/python3.8/site-packages/flask_frozen/__init__.py:199: MissingURLGeneratorWarning: Nothing frozen for endpoints csw_server_published, csw_server_unpublished. Did you forget a URL generator?
  return set(page.url for page in self.freeze_yield())
```

#### `publish`

Uploads an export of the *data catalogue* component (generated using the [`export`](#export))command) to a static 
website.

```shell
$ flask publish
...
Successfully published static site to https://add-catalogue.data.bas.ac.uk
```

**Note:** This command will replace any content already in the static site. This means if a record no longer exists in 
the latest export for example it will be removed from the static site.

**Note:** This command will reference an internal website rather than `data.bas.ac.uk`, this is not a mistake, reverse
proxying is used to make it look like this website part of `data.bas.ac.uk` whereas it is actually separate.

#### `auth sign-in`

Identifies the user of the editor application to allow them access to the *unpublished* repository and, if applicable, 
permission to [`records publish`](#records-publish) records into the *published* repository.

You will login by entering a code given by this application into a website. Once signed-in you return to the application
to complete the sign-in process. You will sign-in using your NERC Active Directory account (the account used for 
accessing your email).

**Note:** Your account will need to configured to sign into this application, contact @felnne to set this up.

Once signed-in your session will last for 1 hour, after which you will need to [`auth sign-out`](#auth-sign-out) and 
sign-in again. You can use the [`auth check`](#auth-check) command to check if your sign-in session is still active.

An access token, which allows the editor to act as you in a limited way, and includes your name, is stored locally as a 
file.

```shell
$ flask auth sign-in
To sign into this application, use a web browser to open the page 'https://microsoft.com/devicelogin' and enter this code: 'DAR5P9L53'
Once you've signed in, press any key to continue, or press [ctrl + c] twice to abort ...
Sign-in successful, hello Felix
For reference, your login details have been saved to /root/.config/scar_add_metadata_toolbox/auth.json
```

#### `auth sign-out`

Having run [`auth sign-in`](#auth-sign-in), this command will remove the local file containing your access token, 
clearing your identity, either to allow another user to sign-in, or to run sign-in again if your session expires.

```shell
$ flask auth sign-out
Are you sure you want to sign-out? [y/N]: y
Sign-out successful
```

#### `auth check`

Having run [`auth sign-in`](#auth-sign-in), this command will confirm whether the access token stored locally is still 
valid.

```shell
$ flask auth sign-check
You are signed in as Felix (felnne@bas.ac.uk)
```

#### `records list`

Queries the *unpublished* and *published* repositories using CSW GetRecords requests and lists the metadata records 
they contain.

Because all metadata records in the *published repository* should also exist in the *unpublished repository*, the 
results are formatted to indicate whether each record is published or unpublished.

```shell
$ flask records list
# where a record is unpublished
List of ADD metadata records:
* 33d5a2d4-66d8-46be-82c8-404664b21455 - High resolution vector polygons of the Antarctic coastline - Unpublished
# where a record is published
List of ADD metadata records:
* 33d5a2d4-66d8-46be-82c8-404664b21455 - High resolution vector polygons of the Antarctic coastline - Published
```

#### `records import`

Loads a metadata record encoded using the [BAS Metadata Library](https://github.com/antarctica/metadata-library) record 
configuration in a JSON file, re-encodes the record as an ISO 19115-2 XML record and inserts, or updates, the record 
in the *Unpublished repository* using a CSW transactional insert request. The file to import needs to be available 
locally.

The `/file_identifier` property is used to determine if a record is new, and should be inserted, or has already been 
imported and should be updated. If any other properties are different in the imported record they will be updated.

**WARNING!** Once updated, a record cannot be reverted to its previous state, unless a backup of the previous version 
has been made using [`records export`](#records-export).

Once imported, the record can be verified using the [`records list`](#records-list) command.

```shell
$ flask records import
[?] What is the path to the file containing the record you would like to import?: /usr/src/app/records/coast-polygon-high.json
Importing metadata record from file /usr/src/app/records/coast-polygon-high.json
# Inserting a record
Loaded record 33d5a2d4-66d8-46be-82c8-404664b21455 - High resolution vector polygons of the Antarctic coastline
Successfully added record [33d5a2d4-66d8-46be-82c8-404664b21455].
# Updating a record
A record with ID [33d5a2d4-66d8-46be-82c8-404664b21455] already exists - do you want to update it with this import? [y/N]: y
Successfully updated record [33d5a2d4-66d8-46be-82c8-404664b21455].
```

#### `records export`

Saves a metadata record held in the *Unpublished repository*, encoded as ISO 19115-2 in XML using a CSW GetRecordByID 
request, re-encodes the record using the [BAS Metadata Library](https://github.com/antarctica/metadata-library) record 
configuration in JSON, and saves the record into a local file.

This command is intended to be used to backup records, for example as a precaution before updating a record using 
[`records import`](#records-import) or removing a record using [`records remove`](#records-remove).

```shell
$ flask records export
[?] Which record would like to export?: * 33d5a2d4-66d8-46be-82c8-404664b21455 - High resolution vector polygons of the Antarctic coastline
 > * 33d5a2d4-66d8-46be-82c8-404664b21455 - High resolution vector polygons of the Antarctic coastline

[?] Which directory would like to export this record into?: /tmp
Successfully exported record 33d5a2d4-66d8-46be-82c8-404664b21455 - High resolution vector polygons of the Antarctic coastline to /tmp/ADD-metadata-record-33d5a2d4-66d8-46be-82c8-404664b21455-2020-05-06T22:49:02.687447.json
```

#### `records remove`

Remove a metadata record from the *Unpublished repository* using a CSW transactional delete request.

**WARNING!** Once removed a record cannot be restored unless unless a backup of the record has been made using  
[`records export`](#records-export).

```shell
$ flask records remove
[?] Which record would like to remove?: * 33d5a2d4-66d8-46be-82c8-404664b21455 - High resolution vector polygons of the Antarctic coastline
 > * 33d5a2d4-66d8-46be-82c8-404664b21455 - High resolution vector polygons of the Antarctic coastline

Are you sure you want to remove record [33d5a2d4-66d8-46be-82c8-404664b21455] 'High resolution vector polygons of the Antarctic coastline'? [y/N]: y 
Successfully removed record [33d5a2d4-66d8-46be-82c8-404664b21455].
```

#### `records publish`

Copy a metadata record from the *Unpublished* to the *Published* repository using a CSW GetRecordByID and CSW 
transactional insert request. Publishing the record. If needed, the record can be retracted later using 
[`records retract`](#records-retract).

```shell
$ flask records publish
[?] Which record would like to publish?: * 33d5a2d4-66d8-46be-82c8-404664b21455 - High resolution vector polygons of the Antarctic coastline
 > * 33d5a2d4-66d8-46be-82c8-404664b21455 - High resolution vector polygons of the Antarctic coastline
Successfully published record [33d5a2d4-66d8-46be-82c8-404664b21455].
```

#### `records retract`

Remove a metadata record from the *Published repository* using a CSW transactional delete request. Retracting the 
record. The record can be re-published later using [`records publish`](#records-publish).

```shell
$ flask records retract
[?] Which record would like to retract?: * 33d5a2d4-66d8-46be-82c8-404664b21455 - High resolution vector polygons of the Antarctic coastline
 > * 33d5a2d4-66d8-46be-82c8-404664b21455 - High resolution vector polygons of the Antarctic coastline
Successfully retracted record [33d5a2d4-66d8-46be-82c8-404664b21455].
```

## Implementation

Flask application using [CSW](#csw) to store [Metadata records](#metadata-records) and Jinja templates using the 
[BAS Style Kit](https://style-kit.web.bas.ac.uk) to display records as [Items](#items) and [Collections](#collections) 
in a data catalogue served as a static website. 

CSW catalogues are backed by local Postgres databases and secured using [OAuth](#oauth). The data catalogue output is 
captured as a static website using the [Frozen Flask](#frozen-flask) extension and uploaded to 
an S3 static website. Routes have been configured in the BAS General Load Balancer to reverse proxy path prefixes in 
this static site within the main [BAS data catalogue](https://data.bas.ac.uk).

### Metadata records

Metadata records are the content and data within project. Records describe resources, which are typically datasets 
within the ADD, e.g. a record might describe the Antarctic Coastline dataset. Records are based on the ISO 19115 
metadata standard, which defines an information model for geographic data.

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
  [BAS Metadata Library](https://github.com/antarctica/metadata-library) record configuration
* when stored in a repository, records are encoded as XML using the ISO 19139 standard
* when viewed in the data catalogue, records are encoded in HTML

These different formats are used for different reasons:

* JSON, and the Metadata Library configuration, is easily understood by machines and is concise to understand and edit
* XML, and ISO 19139, is also machine readable but focused on interoperability between components and providers through 
  its very rigid structure
* HTML is designed for presenting information to humans, with very flexible formatting options

### Items

Items represent [Metadata records](#metadata-records) but in a form intended for human consumption and to give greater
flexibility than rigidity and formality enforced by a metadata record.

For example, a resource's coordinate reference system is described as `urn:ogc:def:crs:EPSG::3031` in the metadata 
record but as `WGS 84 / Antarctic Polar Stereographic (EPSG:3031)`. Both are technically correct but the URN code is
not very useful to a human whereas the descriptive version is not as easy for a machine to understand.

### Collections

Collections are a simple way to group [Items](#items) together based on a shared purpose, theme or topic. They are not 
based on metadata records and support a very limited set of properties.

### OAuth

This project uses OAuth to protect access to the *Unpublished* and *Published* repositories, using the 
[Microsoft (Azure) identity platform](https://docs.microsoft.com/en-us/azure/active-directory/develop/).

The *Unpublished* and *Published* repositories are registered together as the resource to be protected with different 
scopes and roles to authorise users to read, write and publish records within the resource. The  
[Flask Azure AD OAuth Provider](https://pypi.org/project/flask-azure-oauth/) is used to verify access tokens and enforce
these permissions when requests are made to the repositories.

The *Metadata editor* (and possibly other applications in the future) is registered as another application as a client
that will interact with protected resource (i.e. to read, write and publish records). The 
[Microsoft Authentication Library (MSAL) for Python](https://github.com/AzureAD/microsoft-authentication-library-for-python)
library is used to request access tokens using the OAuth device code grant type, as terminal applications can't use 
redirects.

The [Azure Portal](https://portal.azure.com) is used to assign permissions to applications and users as needed.
 
### CSW

The *Unpublished* and *Published* repositories are implemented as embedded [PyCSW](http://pycsw.org) servers. The 
embedded mode allowing integration with Flask for authentication and authorisation of requests via [OAuth](#oauth).

The CSW transactional profile is used extensively for clients (such as the *Metadata editor* and *Data catalogue*) to 
insert, update and delete records programmatically.

The CSW version is fixed to *2.0.2* because it's the latest version supported by 
[OWSLib](https://geopython.github.io/OWSLib/), the CSW client used by the *Metadata editor*.

**Note:** Some elements of both the PyCSW server and the OWSLib client have been extended by this project to incorporate
OAuth support. These modifications will be formalised, ideally as upstream contributions.

### Frozen flask

The [Frozen flask](https://pythonhosted.org/Frozen-Flask/) extension is used to convert a dynamic Flask application 
into a static website. This allows the content of the *Data catalogue* component to be hosted separately from the 
underlying Flask application.

It uses generator functions to iterate through all valid items in dynamic routes and saves their output, along with 
static resources into a directory for hosting using relative URL references between pages.

Generators are used for all routes we wish to export, notably: items, collections and records.

### Configuration

Configuration options are set within `scar_add_metadata_toolbox/config.py`.

All [Options](#configuration-options) are defined in a `Config` base class, with per-environment sub-classes overriding
and extending these options as needed. The active configuration is set using the `FLASK_ENV` environment variable.

Most options can be [Set using environment variables or files](#setting-configuration-options).

| Option                               | Required | Data Type (Cast)    | Source      |  Allowed Values                                                                                                      | Default Value                                                | Example Value                                                            | Description                                                                                                                                   | Notes                        |
| ------------------------------------ | -------- | ------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `FLASK_APP`                          | Yes      | String              | OS          | Valid [`FLASK_APP`](https://flask.palletsprojects.com/en/1.1.x/cli/#application-discovery) value                     | `manage.py`                                                  | `manage.py`                                                              | See [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/cli/#application-discovery)                                              | -                            |
| `FLASK_ENV`                          | Yes      | String              | OS          | Name of a configuration class in `config.py` (written as `production` for the `ProductionConfig` class for example)  | `production`                                                 | `production`                                                             | See [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/config/#environment-and-debug-features)                                  | -                            |
| `DEBUG`                              | No       | Boolean             | Internal    | `True`/`False`                                                                                                       | Depends on environment                                       | `True`                                                                   | See [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/config/#DEBUG)                                                           | -                            |
| `TESTING`                            | No       | Boolean             | Internal    | `True`/`False`                                                                                                       | Depends on environment                                       | `True`                                                                   | See [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/config/#TESTING)                                                         | -                            |
| `NAME`                               | No       | String              | Internal    | `scar-add-metadata-toolbox`                                                                                          | `scar-add-metadata-toolbox`                                  | `scar-add-metadata-toolbox`                                              | Used for self reporting                                                                                                                       | -                            |
| `LOGGING_LEVEL`                      | No       | Logging Level       | Internal    | Valid [Python logging level](https://docs.python.org/3/library/logging.html#logging-levels)                          | Depends on environment                                       | `logging.WARNING`                                                        | See [Python documentation](https://docs.python.org/3/library/logging.html#logging-levels)                                                     | -                            |
| `LOG_FORMAT`                         | No       | String              | Internal    | Valid [Python Log Formatter Format](https://docs.python.org/3/library/logging.html#logging.Formatter.format)         | See `Config` class                                           | See `Config` class                                                       | See [Python documentation](https://docs.python.org/3/library/logging.html#logging.Formatter.format)                                           | -                            |
| `LOG_FILE_PATH`                      | No       | Path                | `.flaskenv` | Valid file path, the file does not need to already exist                                                             | `/var/log/app/app.log`                                       | `/var/log/app/app.log`                                                   | Path to application log file, if enabled                                                                                                      | Set by `APP_LOG_FILE_PATH`   |
| `APP_ENABLE_SENTRY`                  | No       | Boolean             | `.flaskenv` | `True`/`False`                                                                                                       | Depends on environment                                       | `True`                                                                   | Feature flag for [Error reporting](#error-reporting)                                                                                          | -                            |
| `APP_ENABLE_FILE_LOGGING`            | No       | Boolean             | `.flaskenv` | `True`/`False`                                                                                                       | `False`                                                      | `False`                                                                  | Feature flag for writing [Application Logs](#logging) to a file in addition to standard out                                                   | -                            |
| `SENTEY_DSN`                         | Yes      | String              | `.flaskenv` | [Sentry DSN](https://docs.sentry.io/error-reporting/quickstart/?platform=python#configure-the-sdk) for this project  | `https://c69a62ee2262460f9bc79c4048ba764f@sentry.io/1832548` | `https://c69a62ee2262460f9bc79c4048ba764f@sentry.io/1832548`             | Sentry [Data Source Name](https://docs.sentry.io/error-reporting/quickstart/?platform=python#configure-the-sdk)                               | This value is not a secret   |
| `APP_AUTH_SESSION_FILE_PATH`         | No       | String              | `.flaskenv` | Valid file path, the file does not need to already exist                                                             | `~/.config/scar_add_metadata_toolbox/auth.json`              | `~/.config/scar_add_metadata_toolbox/auth.json`                          | File in which the access token and other authentication metadata will be stored between command runs                                          | -                            |
| `AUTH_CLIENT_SCOPES`                 | Yes      | List[String]        | `.flaskenv` | Valid list of scopes defined in the Azure application identified by `AZURE_OAUTH_APPLICATION_ID`                     | Empty List                                                   | `api://8643fd87-cca5-4e56-bc81-46af208ef260/Records.Read.All`            | List of required scopes defined in the the Azure application identified by `AZURE_OAUTH_APPLICATION_ID`                                       | -                            |
| `AUTH_CLIENT_TENANCY`                | Yes      | String              | `.flaskenv` | ID of the tenancy the Azure application identified by `AUTH_CLIENT_ID` is registered                                 | None                                                         | `https://login.microsoftonline.com/3a6d68fc-5a35-4f40-b45d-2268000031a4` | ID of the tenancy the Azure application identified by `AUTH_CLIENT_ID` is registered                                                          | -                            |
| `AUTH_CLIENT_ID`                     | Yes      | String              | `.flaskenv` | ID of the Azure application that represents the *Metadata editor* component                                          | None                                                         | `8643fd87-cca5-4e56-bc81-46af208ef260`                                   | ID of the Azure application that represents the *Metadata editor* component                                                                   | -                            |
| `AZURE_OAUTH_TENANCY`                | Yes      | String              | `.flaskenv` | ID of the tenancy the Azure application identified by `AZURE_OAUTH_APPLICATION_ID` is registered                     | None                                                         | `2fa3a3af-89e1-439d-af27-838c6874fac1`                                   | ID of the tenancy the Azure application identified by `AZURE_OAUTH_APPLICATION_ID` is registered                                              | Set by `AUTH_SERVER_TENANCY` |
| `AZURE_OAUTH_APPLICATION_ID`         | Yes      | String              | `.flaskenv` | ID of the Azure application that represents the *Unpublished* and *Published* repository components                  | None                                                         | `https://login.microsoftonline.com/3a6d68fc-5a35-4f40-b45d-2268000031a4` | ID of the Azure application that represents the *Unpublished* and *Published* repository components                                           | Set by `AUTH_SERVER_ID`      |
| `AZURE_OAUTH_CLIENT_APPLICATION_IDS` | Yes      | List[String]        | Internal    | ID of an Azure application                                                                                           | Empty List                                                   | `8643fd87-cca5-4e56-bc81-46af208ef260`                                   | A list of client (Azure) applications that are authorised to use the application identified by `AZURE_OAUTH_APPLICATION_ID`                   | [self.AUTH_CLIENT_ID]        |
| `CSW_ENDPOINT_UNPUBLISHED`           | Yes      | String              | `.flaskenv` | Valid URL                                                                                                            | `http://app:9000/csw/unpublished`                            | `http://app:9000/csw/unpublished`                                        | URL of the CSW endpoint representing the *Unpublished* repository component                                                                   | -                            |
| `CSW_ENDPOINT_PUBLISHED`             | Yes      | String              | `.flaskenv` | Valid URL                                                                                                            | `http://app:9000/csw/published`                              | `http://app:9000/csw/published`                                          | URL of the CSW endpoint representing the *Published* repository component                                                                     | -                            |
| `CSW_CONFIG_UNPUBLISHED`             | Yes      | PyCSW Configuration | Internal    | [PyCSW configuration](https://docs.pycsw.org/en/2.4.2/configuration.html) as a Python dictionary                     | -                                                            | -                                                                        | Configuration for the *Unpublished* repository component                                                                                      | -                            |
| `CSW_CONFIG_PUBLISHED`               | Yes      | PyCSW Configuration | Internal    | [PyCSW configuration](https://docs.pycsw.org/en/2.4.2/configuration.html) as a Python dictionary                     | -                                                            | -                                                                        | Configuration for the *Published* repository component                                                                                        | -                            |
| `STATIC_BUILD_DIR`                   | Yes      | Path                | `.flaskenv` | Valid directory path, the directory does not need to exist                                                           | None                                                         | `./scar_add_metadata_toolbox/build`                                      | Path to where the *Data Catalogue* component will be exported as a static site                                                                | =                            |
| `S3_BUCKET`                          | Yes      | String              | `.flaskenv` | Valid S3 bucket name                                                                                                 | None                                                         | `add-catalogue.data.bas.ac.uk`                                           | Name of the S3 bucket that will host the exported *Data Catalogue* static site                                                                | -                            |
| `BSK_TEMPLATES`                      | Yes      | String              | Internal    | [BAS Style Kit Jinja Templates configuration](https://github.com/antarctica/bas-style-kit-jinja-templates#variables) | -                                                            | -                                                                        | [BAS Style Kit Jinja Templates](https://github.com/antarctica/bas-style-kit-jinja-templates) configuration for the *Data Catalogue* component | -                            | 

All Options are set as strings and cast to relevant data type. See 
[Setting configuration options](#setting-configuration-options) for more information.

Flask also has a number of
[builtin configuration options](https://flask.palletsprojects.com/en/1.1.x/config/#builtin-configuration-values).

#### Setting configuration options

Variable configuration options can be set using environment variables or environment files:

| Source                   | Priority | Purpose                     | Notes                                     |
| ------------------------ | -------- | --------------------------- | ----------------------------------------- |
| Internal                 | 1st      | Fixed variables             | These variables can be changed at runtime | 
| OS environment variables | 2nd      | General/Runtime             | -                                         |
| `.env`                   | 3rd      | Secret/private variables    | Not used in this project                  |
| `.flaskenv`              | 4th      | Non-secret/public variables | Generate by copying `.flaskenv.example`   |

**Note:** these sources are a
[Flask convention](https://flask.palletsprojects.com/en/1.1.x/cli/#environment-variables-from-dotenv).

### Error tracking

Errors in this service are tracked with Sentry:

* [Sentry dashboard](https://sentry.io/organizations/antarctica/issues/?project=5197036)
* [GitLab dashboard](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/error_tracking)

Error tracking will be enabled or disabled depending on the environment. It can be manually controlled by setting the
`APP_ENABLE_SENTRY` [Configuration option](#configuration).

### Logging

Logs for this service are written to *stdout* and, optionally, a log file (`/var/log/app/app.py` by default).

File based logging is controlled by the `APP_ENABLE_FILE_LOGGING` and `APP_LOG_FILE_PATH` 
[Configuration option](#configuration).

**Note:** The value of `APP_LOG_FILE_PATH` must be writable by this application.

## Setup

The application for this project runs as a Docker container.

Once setup, see the [Usage](#usage) section for how to use and run the application.

**Note:** This project can currently only run locally. In future it will also run on the BAS central workstations using 
Podman. For this you will need access to the private BAS Docker Registry (part of 
[gitlab.data.bas.ac.uk](https://gitlab.data.bas.ac.uk)) and for IT to enable Podman in your user account. Unless noted, 
`docker` commands listed here can be replaced with `podman`.

```shell
$ docker login docker-registry.data.bas.ac.uk
$ docker pull docker-registry.data.bas.ac.uk/magic/add-metadata-toolbox/deploy:stable
```

**Note:** [Other image tags](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/container_registry) are available 
if you want to run pre-release versions of this project.

Before you can run the container, you will need to create a runtime directory that will live outside of the container.
Any local files, such as Metadata records for importing or that are generated by exporting will also be saved here, as
well as any required [Configuration files](#configuration). 

```shell
$ mkdir -p ~/.config/add-metadata-toolbox
```

### Optional wrapper script

**Note:** This is not yet available.

If using podman, a wrapper script, `support/container-wrapper/podman-wrapper.sh`, is available to make running the
container easier.

To use, copy this script and enable it to be executed:

```shell
$ mkdir ~/bin
# copy `support/container-wrapper/podman-wrapper.sh` as `~/bin/add-metadata-toolbox`
$ chmod +x ~/bin/add-metadata-toolbox
```

Then ensure `~/bin` is part of the user's path (use `echo $PATH` to check), if it isn't edit the user's shell to include
it (these instructions assume the bash shell and the absolute path to the user's home directory is `/home/foo`):

```shell
$ vi ~/.bash_rc
# add `export PATH="/home/foo/bin:$PATH" then save the file and reload the user's shell
```

You should now be able to run `add-metadata-toolbox` to run the container and application it contains.

### Terraform

Terraform is used to provision resources required for hosting the *Data catalogue* component as a static website.

Access to the [BAS AWS account](https://gitlab.data.bas.ac.uk/WSF/bas-aws) is needed to provision these resources.

**Note:** This provisioning should have already been performed (and applies globally). If changes are made to this 
provisioning it only needs to be applied once.

```shell
# start terraform inside a docker container
$ cd provisioning/terraform
$ docker-compose run terraform
# setup terraform
$ terraform init
# apply changes
$ terraform validate
$ terraform fmt
$ terraform apply
# exit container
$ exit
$ docker-compose down
```

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

### Azure Active Directory

Two Azure application registrations need to be created in the *BAS Web & Applications Active Directory* in Azure through 
the [Azure Portal](https://portal.azure.com). The [First registration](#registration-1-data-catalogue-component),
represents the *Data Catalogue* component, the [Second](#registration-2-metadata-editor-component) represents the 
*Metadata editor* component.

Global Administrator permissions in the *BAS Web & Applications Active Directory* tenancy are needed to provision these 
resources.

**Note:** This provisioning should have already been performed (and applies globally). If changes are made to this 
provisioning it only needs to be applied once.

#### Registration 1 - Data Catalogue component

* name: `Antarctic Digital Database (ADD) - Metadata Catalogue`
* supported account types: *Accounts in this organisational directory only*

Once registered, edit the application:

* Manage -> Token configuration:
    * *Add optional claim*
        * Token type: *Access*
        * Claim:
            * *email*
            * *given_name*
            * *family_name*
* Manage -> Expose an API:
    * Application ID URI: `api://[application id]`
    * Scopes defined by this API -> *Add a scope*
        * Scope name: `Records.Read.All`
        * Who can consent: *Admins Only*
        * Admin consent display name: `Read all catalogue records`
        * Admin consent description: `Allow reading all catalogue records`
        * User consent display name: N/A
        * User consent description: N/A
        * State: enabled
* Manage -> Manifest:
    * `accessTokenAcceptedVersion`: `2`
    * `appRoles`: [1]

Set users that are allowed to update records in the catalogue:

* Overview -> managed Application in local directory (link) -> Users and groups:
    * *Add user*
        * Users: *[User]*
        * Role: *Records.ReadWrite.All*

Set users that are allowed to publish records from the unpublished to published catalogue:

* Overview -> managed Application in local directory (link) -> Users and groups:
    * *Add user*
        * Users: As Applicable
        * Role: *Records.Publish.All*

**Note:** Assignments are 1:1 between user:role but there can be multiple user:role assignments. I.e. to assign both the
*Records.ReadWrite.All* and *Records.Publish.All* roles create two role assignments with the same user.

[1] Application roles:

```json
{
    "allowedMemberTypes": [
        "User"
    ],
    "description": "Change all metadata records.",
    "displayName": "Records.ReadWrite.All",
    "id": "b7baedc2-bde7-4723-a9b3-edd021843cd1",
    "isEnabled": true,
    "lang": null,
    "origin": "Application",
    "value": "Records.ReadWrite.All"
},
{
    "allowedMemberTypes": [
        "User"
    ],
    "description": "Publish all metadata records.",
    "displayName": "Records.Publish.All",
    "id": "f4ab9b0a-21dd-4ac8-a6f0-178388bef98d",
    "isEnabled": true,
    "lang": null,
    "origin": "Application",
    "value": "Records.Publish.All"
}
```

#### Registration 2 - Metadata Editor component

* name: `Antarctic Digital Database (ADD) - Metadata Editor`
* supported account types: *Accounts in this organisational directory only*
* redirect URI: `https://login.microsoftonline.com/common/oauth2/nativeclient`

Once registered, edit the application:

* Manage -> Branding:
    * Homepage: `https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox`
* Manage -> API Permissions:
    * *Add a permission*
        * *My APIs* -> *Antarctic Digital Database (ADD) - Metadata Catalogue* -> *Records.Read.All*
* Manage -> Authentication:
    * *Advanced settings* -> *Default client type* -> Treat application as a public client: *Yes*
    * *Grant admin consent for [Tenancy]*

## Development

```shell
$ git clone https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox
$ cd add-metadata-toolbox
```

### Development environment

The `:latest` container image is used for developing this project. It can run locally using Docker and Docker Compose:

```shell
$ docker login docker-registry.data.bas.ac.uk
$ docker-compose pull app
```

Then create/configure required [Configuration files](#configuration):

```shell
$ cp .flaskenv.example .flaskenv
```

To run/test application commands:

```shell
$ docker-compose run app flask [task]
```

[1] You will need access to the private BAS Docker Registry (part of
[gitlab.data.bas.ac.uk](https://gitlab.data.bas.ac.uk)) to pull this image. If you don't, you can build the relevant
image/tag locally instead.

### Code Style

PEP-8 style and formatting guidelines must be used for this project, with the exception of the 80 character line limit.

[Black](https://github.com/psf/black) is used to ensure compliance, configured in `pyproject.toml`.

Black can be [integrated](https://black.readthedocs.io/en/stable/editor_integration.html#pycharm-intellij-idea) with a 
range of editors, such as PyCharm, to perform formatting automatically.

To apply formatting manually:

```shell
$ docker-compose run app black bas_scar_add_metadata_toolbox/
```

To check compliance manually:

```shell
$ docker-compose run app black --check bas_scar_add_metadata_toolbox/
```

Checks are ran automatically in [Continuous Integration](#continuous-integration).

### Python version

When upgrading to a new version of Python, ensure the following are also checked and updated where needed:

* `Dockerfile`:
    * base stage image (e.g. `FROM python:3.X-alpine as base` to `FROM python:3.Y-alpine as base`)
    * pre-compiled wheels (e.g. `https://.../linux_x86_64/cp3Xm/lxml-4.5.0-cp3X-cp3X-linux_x86_64.whl` to
     `http://.../linux_x86_64/cp3Ym/lxml-4.5.0-cp3Y-cp3Y-linux_x86_64.whl`)
* `provisioning/docker/Dockerfile`:
    * base stage image (e.g. `FROM python:3.X-alpine as base` to `FROM python:3.Y-alpine as base`)
    * pre-compiled wheels (e.g. `http://.../linux_x86_64/cp3Xm/lxml-4.5.0-cp3X-cp3X-linux_x86_64.whl` to
     `http://.../linux_x86_64/cp3Ym/lxml-4.5.0-cp3Y-cp3Y-linux_x86_64.whl`)
* `pyproject.toml`
    * `[tool.poetry.dependencies]`
        * `python` (e.g. `python = "^3.X"` to `python = "^3.Y"`)
    * `[tool.black]`
        * `target-version` (e.g. `target-version = ['py3X']` to `target-version = ['py3Y']`)

### Dependencies

Python dependencies for this project are managed with [Poetry](https://python-poetry.org) in `pyproject.toml`.

The development container image installs both runtime and development dependencies. Deployment images only install
runtime dependencies.

Non-code files, such as static files, can also be included in the [Python package](#python-package) using the
`include` key in `pyproject.toml`.

To add a new (development) dependency:

```shell
$ docker-compose run app ash
$ poetry add [dependency] (--dev)
```

Then rebuild the development container and push to GitLab (GitLab will rebuild other images automatically as needed):

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

### Logging

Use the Flask default logger. For example:

```python
app.logger.info('Log message')
```

When outside of a route/command use `current_app`:

```python
from flask import current_app

current_app.logger.info('Log message')
```

### File paths

Use Python's [`pathlib`](https://docs.python.org/3.8/library/pathlib.html) library for managing file paths.

Where displaying a file path to the user ensure it is always absolute to aid in debugging:

```python
from pathlib import Path

foo_path = Path("foo.txt")
print(f"foo_path is: {str(foo_path.absolute())}")
```

### Editor support

#### PyCharm

A run/debug configuration, *App*, is included in the project.

### Testing

Automated tests are not yet used in this project.

#### Continuous Integration

All commits will trigger a Continuous Integration process using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.

## Deployment

### Python package

This project is distributed as a Python package, hosted in [PyPi](https://pypi.org/project/scar-add-metadata-toolbox).

Source and binary packages are built and published automatically using
[Poetry](https://python-poetry.org/docs/cli/#publish) in [Continuous Delivery](#continuous-deployment).

Package versions are determined automatically using the `support/python-packaging/parse_version.py` script.

### Docker image

The project [Python package](#python-package) is available as a Docker/OCI image, hosted in the private BAS Docker
Registry (part of [gitlab.data.bas.ac.uk](https://gitlab.data.bas.ac.uk)).

[Continuous Delivery](#continuous-deployment) will automatically:

* build a `/deploy:latest` image for commits to the *master* branch
* build a `/deploy:release-stable` and `/deploy:release-[release]` image for tags
* deploy new images to the BAS central workstations (by running `podman pull [image]` from the workstations)

**Note:** Images are not yet deployed to the BAS central workstations.

### Continuous Deployment

All commits will trigger a Continuous Deployment process using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.

## Release procedure

For all releases:

1. create a release branch
2. close release in `CHANGELOG.md`
3. push changes, merge the release branch into `master` and tag with version

## Feedback

The maintainer of this project is the BAS Mapping and Geographic Information Centre (MAGIC), they can be contacted at:
[servicedesk@bas.ac.uk](mailto:servicedesk@bas.ac.uk).

## Issue tracking

This project uses issue tracking, see the
[Issue tracker](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues) for more information.

**Note:** Read & write access to this issue tracker is restricted. Contact the project maintainer to request access.

## License

© UK Research and Innovation (UKRI), 2020, British Antarctic Survey.

You may use and re-use this software and associated documentation files free of charge in any format or medium, under
the terms of the Open Government Licence v3.0.

You may obtain a copy of the Open Government Licence at http://www.nationalarchives.gov.uk/doc/open-government-licence/
