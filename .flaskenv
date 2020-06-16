## Copy this file to `.flaskenv` and change values as needed
## This file is for public environment variables - see `.env` for private variables
## Entries prefixed by a `#` have a default value that can be changed if needed by removing the `#` comment
## Entries prefixed by a `#!` are set elsewhere (typically because they are application secrets set in .env)

## Feature flags
# APP_ENABLE_FILE_LOGGING=False
# APP_ENABLE_SENTRY=True

# Settings
# APP_LOG_FILE_PATH=/var/log/app/app.log
# APP_AUTH_SESSION_FILE_PATH=~/.config/scar_add_metadata_toolbox/auth.json

## Sentry - Get DSN from https://sentry.io - this value is not a secret
SENTRY_DSN=https://db9543e7b68f4b2596b189ff444438e3@o39753.ingest.sentry.io/5197036

## Azure authentication (Client/Editor) - Get from https://portal.azure.com/
AUTH_CLIENT_TENANCY=https://login.microsoftonline.com/b311db95-32ad-438f-a101-7ba061712a4e
AUTH_CLIENT_ID=91c284e7-6522-4eb4-9943-f4ec08e98cb9
AUTH_CLIENT_SCOPES=api://8bfe65d3-9509-4b0a-acd2-8ce8cdc0c01e/BAS.MAGIC.ADD.Access

## Azure authentication (Server/Catalogue) - Get from https://portal.azure.com
AUTH_SERVER_TENANCY=b311db95-32ad-438f-a101-7ba061712a4e
AUTH_SERVER_ID=8b45581e-1b2e-4b8c-b667-e5a1360b6906

## CSW repository (client)
# APP_CSW_LOG_FILE_PATH=/var/log/app/csw.log
# CSW_ENDPOINT_UNPUBLISHED=http://localhost:9000/csw/unpublished
# CSW_ENDPOINT_PUBLISHED=http://localhost:9000/csw/published

## CSW repository (server)
#! CSW_UNPUBLISHED_DB_CONNECTION
#! CSW_PUBLISHED_DB_CONNECTION

# Static website export
STATIC_BUILD_DIR="./scar_add_metadata_toolbox/build"
S3_BUCKET="add-catalogue-integration.data.bas.ac.uk"
