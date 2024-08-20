# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - HTTP API reference

## Endpoints

### `/site/build?item=<record_id>`

Build the record XML and item pages for a record.

Equivalent to running the CLI commands `flask site build-record <record_id>` and `flask site build-item <record_id>`.

**Note**: This endpoint requires authentication and the `BAS.MAGIC.ADD.Records.Publish.All` scope.

#### Parameters

- `item`: The ID of the record

#### Reponses

- `201 Created`: The pages were built successfully
- `400 Bad Request`: The item parameter was not specified
- `401 Unauthorized`: The client does not have the `BAS.MAGIC.ADD.Records.Publish.All` scope
- `403 Forbidden`: The client is not authenticated
- `404 Not Found`: The record with the specified ID was not found
- `500 Internal Server Error`: There was an error accessing the CSW or generating the pages
