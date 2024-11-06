# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - Implementation (Downloads Proxy)

To support [tracking downloads](/docs/implementation.md#download-metrics) of items, a proxy service is used. This proxy
intercepts requests to download files, returning a 302 temporary redirect to the item download. Redirection is used to
increase, but not ensure, the chances downloads are tracked, by making the real location of items less obvious, and
harder to share/use directly.

When a request is made (using a download URL), an [AWS Lambda function](#downloads-proxy-lambda-functions) looks up
the distribution option identifier (termed an [Artefact lookup](#downloads-proxy-artefacts-lookup-schema) item) in a
JSON file (stored in a S3 bucket).

For example, requesting a download URL such as `https://data.bas.ac.uk/download/123`, where `123` is the identifier
for a distribution option (artefact lookup) within an item, will return a 302 redirect with a URL to its real location,
`https://example.com/dataset.gpkg`.

## Downloads proxy Lambda functions

The Downloads Proxy is a set of AWS Lambda functions using Node.js defined in `support/downloads-proxy/index.js`.

There are two functions used for reading and writing [Artefact Lookups](#downloads-proxy-artefacts-lookup-schema).
In addition, there are two independent environments, *staging* and *production*. Each environment uses a separate S3
bucket, with object versioning, containing a separate code package and artefact lookups JSON file. The Lambda endpoint
for each environment is reverse proxied to appear as part of the BAS Data Catalogue (`data.bas.ac.uk`) using the BAS
General Load Balancer.

Access to use Lambda functions that can modify state (the write functions) is restricted. AWS Customer Managed IAM
polices are defined by this project to assign permissions to use these functions to suitable AWS IAM principles
(users or roles).

**WARNING!** Some or all lookup items in the staging environment MAY be removed at anytime.

See the [Infrastructure](/docs/infrastructure.md#downloads-proxy) documentation for specific resources.

See the [relevant](/docs/dev.md#downloads-proxy-source) development subsection for information on the source code for these
functions.

See the [Terraform](/docs/setup.md#terraform) setup subsection for information on how to provision the resources for
these functions, including IAM policies.

See the [BAS API Load Balancer](/docs/setup.md#bas-api-load-balancer) setup subsection for information on how to set
up reverse proxying for these functions.

## Downloads proxy artefacts lookup schema

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
is published as part of the `https://metadata-resources.data.bas.ac.uk` website at:

https://metadata-resources.data.bas.ac.uk/scar-add-metadata-toolbox-downloads-proxy-schemas/v1/artefact-lookups-v1.json

A complete JSON file, with a single artefact lookup item, looks like this:

```json
{
  "$id": "https://example.com/lookup.json",
  "$schema": "https://metadata-resources.data.bas.ac.uk/scar-add-metadata-toolbox-downloads-proxy-schemas/v1/artefact-lookups-v1.json",
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

## Registering downloads proxy artefacts lookup items

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
