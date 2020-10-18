---
title: SCAR ADD CSW - Usage
---

## General information

This API provides access to records  the 
[SCAR ADD Data Catalogue](http://data.bas.ac.uk/collections/e74543c0-4c4e-4b41-aa33-5bb2f67df389/) using the 
[OGC CSW](https://www.ogc.org/standards/cat) standard (Open Geospatial Consortium, Catalogue Service for the Web).

This can be used to search/filter and retrieve records in their raw ISO 19115 form. If authenticated, this API can also
be used to create, update or delete records.

This API is part of the [SCAR ADD Metadata Toolbox](https://github.com/antarctica/scar-add-metadata-toolbox) project.

### Support

Limited, best effort, support only is offered for this API. 

Contact the [BAS Service Desk](mailto:servicedesk@bas.ac.uk) in the first instance.

### Information handling

This API is provided by the [British Antarctic Survey (BAS)](https://www.bas.ac.uk) on behalf of the 
[Scientific Committee on Antarctic Research (SCAR)](https://www.scar.org). BAS is part of 
[UK Research and Innovation (URKI)](https://www.ukri.org), who are the legal operator of this service.

Reasonable policies and technical measures are in place to ensure information in this API is held and transferred 
securely. Where third parties are used to operate this API, they are used for a necessary task with measures in place 
to ensure they are used appropriately and securely.

Third party services used by this API are:

* Sentry - for monitoring API errors, which may include API responses

[Seek support](#support) if you have any questions about how information is used by this API is used or managed. If you 
do not receive a prompt reply, you can contact the [BAS Freedom of Information Officer](mailto:foi@bas.ac.uk) directly.

### Security disclosures

[Seek support](#support) to disclose any security concerns with this API. Contact us first for instructions if you need 
to report any sensitive information.

### Versioning policy

This API is versioned. An API version must be specified as a URL prefix (e.g. `/v1`).

Only the latest, stable, API version is supported. When a new version is released, all previous versions are deprecated 
to allow clients time to move to a supported version. After a period of time, deprecated versions are retired and no 
longer accessible.

## Technical information

### Standards support

This API implements [OGC CSW 2.0.2](http://portal.opengeospatial.org/files/?artifact_id=20555), including the 
transactional profile for modifying records.

#### CSW Output Schemas

Only the `http://www.isotc211.org/2005/gmd` (ISO 19115/19139) output schema is officially supported by this API.
 
### Content Types

This API officially supports the `text/xml` content type only for both requests and responses.

This API supports UTF-8 character encoding only, unless stated otherwise.

### Errors

Errors covered by the CSW standard, will use the relevant form specified by the standard.

Other errors will be returned in a logical but non-standardised form.

**Note:** Authentication errors will currently use a `application/json` content type. This is a considered a bug and 
will addressed in future versions of this API.

### Request IDs

All requests will include a `X-Request-ID` header to aid in debugging requests through different components.

If desired, a custom request ID can be specified by the client which will be used instead of, or in addition to, the
automatically generated value.

**Note:** In some cases a client specified value will be ignored, you **MUST NOT** rely on this value being returned.

**Note:** This header **MAY** include multiple values (multiple Request IDs) separated by a `,` and possible whitespace.

### Authentication and authorisation

Parts of this API require authentication and suitable authorisation to access. This will be highlighted in the 
[Usage](#usage) section where it applies.

## Usage

### Base path

All API requests should use `https://api.bas.ac.uk/data/metadata/add/csw/v1` as a base path.

### Authenticating requests

Where an API request is authenticated/authorised, an `Authorization` header containing a bearer token must be specified.

E.g. `Authorisation: Bearer [token]`

Bearer tokens are OAuth access tokens issued by Microsoft Azure's OAuth endpoints using a supported code flow. Clients
must be registered before they can make authenticated/authorised requests.

Contact [Support](#support) for registering new clients or for information on how to request access tokens.

### Resources

This API consists of a single resource, [Catalogues](#catalogues).

#### Catalogues

Catalogues represent CSW instances. The ADD Data Catalogue includes two catalogues:

* Published (`published`) - containing published records available to the public
* Unpublished (`unpublished`) - containing draft records restricted to ADD project staff

CSW requests must target a catalogue using a path prefix, e.g. `/published`, followed by a valid CSW request.

E.g. `https://api.bas.ac.uk/data/metadata/add/csw/v1/published?service=CSW&request=GetCapabilities"`

Parts of this require require authentication and authorisation:

* transactional requests (in either catalogue) are authenticated and restricted to ADD project staff
* requests to read records in the unpublished catalogue are authenticated and restricted to ADD project staff
