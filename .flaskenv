## Copy this file to `.flaskenv` and change values as needed
## This file is for public environment variables - see `.env` for private variables
## Entries prefixed by a `#` have a default value that can be changed if needed by removing the `#` comment
## Entries prefixed by a `#!` are set elsewhere (typically because they are application secrets set in .env)

## Feature flags
# APP_ENABLE_FILE_LOGGING=True
# APP_ENABLE_SENTRY=True

# Settings
# APP_LOG_FILE_PATH=/var/log/app/app.log
# APP_AUTH_SESSION_FILE_PATH=~/.config/scar_add_metadata_toolbox/auth.json

## Sentry - Get DSN from https://sentry.io - this value is not a secret
SENTRY_DSN=https://db9543e7b68f4b2596b189ff444438e3@o39753.ingest.sentry.io/5197036

## Azure authentication (Client/Editor) - Get from https://portal.azure.com/
AUTH_CLIENT_TENANCY=https://login.microsoftonline.com/d14c529b-5558-4a80-93b6-7655681e55d6
AUTH_CLIENT_ID=e9f1f826-156f-448f-aa9c-ca44ec35aafb
AUTH_CLIENT_SCOPES="api://d364a396-36a8-4137-a6ef-12996fa39183/Records.Read.All"

## Azure authentication (Server/Catalogue) - Get from https://portal.azure.com
AUTH_SERVER_TENANCY=d14c529b-5558-4a80-93b6-7655681e55d6
AUTH_SERVER_ID=d364a396-36a8-4137-a6ef-12996fa39183

## CSW repository (client)
# APP_CSW_LOG_FILE_PATH=/var/log/app/csw.log
# CSW_ENDPOINT_UNPUBLISHED=http://localhost:9000/csw/unpublished
# CSW_ENDPOINT_PUBLISHED=http://localhost:9000/csw/published

## CSW repository (server)
CSW_UNPUBLISHED_DB_CONNECTION="postgresql://postgres:password@csw-unpub-db/postgres"
CSW_PUBLISHED_DB_CONNECTION="postgresql://postgres:password@csw-pub-db/postgres"

# Static website export
STATIC_BUILD_DIR="./scar_add_metadata_toolbox/build"
S3_BUCKET="add-catalogue.data.bas.ac.uk"
