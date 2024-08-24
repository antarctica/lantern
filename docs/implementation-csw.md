# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - Implementation (CSW)

## CSW overview

The [OGC CSW](https://www.ogc.org/standards/cat) standard is used as a protocol and interface for accessing and
managing [Records](/docs/implementation.md#metadata-records) in the *Repository* component.

Separate CSW catalogues are used for Published and unpublished records, using embedded [PyCSW](http://pycsw.org)
servers with Flask routes to allow additional features:

* using [OAuth](/docs/implementation.md#oauth) for [authentication and authorisation](#csw-auth) requests
* optionally using Git for [revision tracking](#csw-revision-tracking) of records in requests

Records are accessed using `getRecords` and `getRecordById` requests. Records are managed using the CSW
transactional profile. These requests can be made using from the Flask CLI, or from other applications, if authorised.

The CSW version is fixed to *2.0.2* because it's the latest version supported by
[OWSLib](https://geopython.github.io/OWSLib/), which is the CSW client used by the Flask CLI.

**Note:** The CSW repositories are considered to be APIs, and so ran as services through the
[BAS API Load Balancer 🛡️](https://gitlab.data.bas.ac.uk/WSF/api-load-balancer) with documentation in the
[BAS API Documentation 🛡️](https://gitlab.data.bas.ac.uk/WSF/api-docs) project.

## CSW package modifications

Some elements of both the PyCSW server and the OWSLib client have been extended by this project to incorporate
OAuth support and fix a variety of issues. These modifications will be formalised, ideally as upstream contributions,
but currently reside within the [Hazardous Materials module](/docs/implementation.md#hazardous-materials-module).

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

## CSW Max records limit

Both PyCSW (CSW server) and OWSLib (CSW client) have a maximum record limit of *100* per request.

## CSW Supported Element Sets

Both PyCSW (CSW server) and OWSLib (CSW client) support the *full* Element Set only.

## CSW backing databases

CSW servers are backed using PostGIS (Postgres) databases - see the [Infrastructure](/docs/infrastructure.md#databases)
documentation for details.

In local development environments, a local PostGIS database configured in `docker-compose.yml` is used.

To test against real data in a non-production environment, a staging database, which is synced from the production
database, can be used. Credentials for this database are stored in the MAGIC 1Password shared vault. This database is
re-synced automatically by BAS IT every Tuesday at 02:00.

## CSW auth

Requests are evaluated as being either 'read' or 'write' based on either the `request` query string parameter, or
elements used in the request body (e.g. `request=GetRecords` or `<csw:Query>` for a read/select request).

These permissions are mapped onto required scopes for each catalogue. Required scopes may be empty to allow anonymous
for read or write.

Where the request type cannot be determined unambiguously it will be rejected.

## CSW revision tracking

CSW servers can optionally use revision tracking, where records modified in a CSW server are tracked as files in a Git
repository. I.e. When a record is inserted, the record is written as files within a Git repo, and updated/deleted later
using an update or delete transactional request.

Revision tracking is only enabled for the *Unpublished*

Revision tracking is designed to protect against accidental changes to records, or set of records if bulk operations
are carried out. Records are stored as:

* ISO 19115 XML (for durability and completeness) and using the
* BAS Metadata Library 19115 JSON (for ease of use and comparison)

Records are written to a Git working copy stored locally. Records are stored using a hashed directory structure based
on the file identifier for each metadata record, under a common 'records/' root directory. For example a record with an
identifier of 'b1a7d1b5-c419-41e7-9178-b1ffd76d5371' will be stored at `records/b1/a7/`. This hashed structure is to
ensure individual directories do not contain large numbers of files, reducing file system performance.

Changes to records are committed on a per-record basis, using the user's identity (from the OAuth token), and pushed
to a remote repository. As this working copy resides on the server side of the application, there should only be a
single committer. Remote repositories are stored in the BAS GitLab instance for each environment:

* [Integration 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-catalogue-records-integration)
* [Production 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-catalogue-records-production)

When enabled, revision tracking is performed after records have been processed (inserted, updated or deleted) and only
if the transaction was successful (prevent changes being committed that aren't present in the related CSW catalogue).
For successful, tracked, transactions the Git commit hash will be returned in a `X-CSW-REVISION-ID` header. If desired,
this can be used to link to the tracked change:

* Integration: `https://gitlab.data.bas.ac.uk/MAGIC/add-catalogue-records-integration/-/commit/{REVISION ID}`
* Production: `https://gitlab.data.bas.ac.uk/MAGIC/add-catalogue-records-production/-/commit/{REVISION ID}`
