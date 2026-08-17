LANTERN_LOG_LEVEL="INFO"  # normally INFO
LANTERN_PARALLEL_JOBS="-1"  # normally -1 (all CPUs), use '1' for debugging

LANTERN_ENABLE_FEATURE_SENTRY="false"  # normally false
LANTERN_SENTRY_ENVIRONMENT="development"  # normally development

LANTERN_ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE="op://Shared/jyo6njigjexbqpbchbkd34cygm/private-jwk-escaped"
LANTERN_ADMIN_METADATA_SIGNING_KEY_PUBLIC="op://Shared/4gwxzflv3bxl7dqcwexrmqi6kq/public-jwk-escaped"

LANTERN_STORE_GITLAB_ENDPOINT="op://Infrastructure/kbzuiol2d74f4s7wwmd7k3zlci/GitLab Instance/instance"
LANTERN_STORE_GITLAB_PROJECT_ID="op://Infrastructure/kbzuiol2d74f4s7wwmd7k3zlci/Project ID/project_id"
LANTERN_STORE_GITLAB_TOKEN=""  # populate with personal access token for GitLab bot user with 'api' scopes
LANTERN_STORE_GITLAB_DEFAULT_BRANCH="main"
LANTERN_STORE_GITLAB_CACHE_PATH=".cache"

## For local stack
#LANTERN_STORE_GITLAB_ENDPOINT="https://gitlab.dev.orb.local"
#LANTERN_STORE_GITLAB_PROJECT_ID="1"
#LANTERN_STORE_GITLAB_TOKEN=""  # 'local-env' PAT for @lantern_bot

LANTERN_STORE_ALGOLIA_APP_ID="op://Infrastructure/hqm2s5h7zjuxljy7owrkzefyke/Application ID/password"
LANTERN_STORE_ALGOLIA_WRITE_API_KEY="op://Infrastructure/hqm2s5h7zjuxljy7owrkzefyke/Backend API Key/password"

## For local stack
#LANTERN_STORE_ALGOLIA_APP_ID=""
#LANTERN_STORE_ALGOLIA_WRITE_API_KEY=""
#LANTERN_TEMPLATES_ALGOLIA_APP_ID=""
#LANTERN_TEMPLATES_ALGOLIA_SEARCH_API_KEY=""

LANTERN_TEMPLATES_PLAUSIBLE_ID="op://Infrastructure/uinr3ials23ryj2smslejztma4/password"
LANTERN_TEMPLATES_ITEM_CONTACT_ENDPOINT="op://Infrastructure/imzpqox4tlppecoui63532fcri/password"
LANTERN_TEMPLATES_TURNSTILE_KEY="op://Infrastructure/s7zzm3hqsq4qs5aidqyqbce2qq/username"
LANTERN_TEMPLATES_ITEM_VERSIONS_ENDPOINT="op://Infrastructure/kbzuiol2d74f4s7wwmd7k3zlci/GitLab Project Web URL/web_url"
LANTERN_TEMPLATES_ALGOLIA_APP_ID="op://Infrastructure/hqm2s5h7zjuxljy7owrkzefyke/Application ID/password"
LANTERN_TEMPLATES_ALGOLIA_SEARCH_API_KEY="op://Infrastructure/hqm2s5h7zjuxljy7owrkzefyke/Frontend API Key/password"

LANTERN_SITE_UNTRUSTED_AWS_ACCESS_ID=""  # populate with per-user/instance IAM credentials
LANTERN_SITE_UNTRUSTED_AWS_ACCESS_SECRET=""  # populate with per-user/instance IAM credentials
LANTERN_SITE_UNTRUSTED_CLOUDFRONT_DIST_LIVE="op://Infrastructure/u4f4no3n7colgagsb4fcztregm/password"
LANTERN_SITE_UNTRUSTED_S3_BUCKET_TESTING="op://Infrastructure/rnv7zb3jzviwsvziknpxicvqaq/password"
LANTERN_SITE_UNTRUSTED_S3_BUCKET_LIVE="op://Infrastructure/rmhzzt5pk4wdamj2ecpguxhfc4/password"

LANTERN_SITE_TRUSTED_RSYNC_HOST=""  # populate with SSH config entry or leave blank to use local file system
LANTERN_SITE_TRUSTED_RSYNC_BASE_PATH_TESTING="{{ op://Infrastructure/l2whnxwdbixs3xypq5ja6w6gr4/content-path }}/testing"
LANTERN_SITE_TRUSTED_RSYNC_BASE_PATH_LIVE="{{ op://Infrastructure/l2whnxwdbixs3xypq5ja6w6gr4/content-path }}/live"

## For local stack
#LANTERN_SITE_TRUSTED_RSYNC_HOST=""
#LANTERN_SITE_TRUSTED_RSYNC_BASE_PATH_TESTING="./resources/dev/apache/run/cat/testing"
#LANTERN_SITE_TRUSTED_RSYNC_BASE_PATH_LIVE="./resources/dev/apache/run/cat/live"

LANTERN_CHECKS_TRUSTED_USERNAME="op://Employee/qdewrgvwjf3pwxygkli5jkswtq/username"
LANTERN_CHECKS_TRUSTED_PASSWORD="op://Infrastructure/hnanekrypud5jyamuilznjsv4y/password"
LANTERN_CHECKS_MAGIC_PRODUCTS_TENANT_ID="op://Infrastructure/tsuxet4wmrwdthy43rhiotkf2y/tenancy-id"
LANTERN_CHECKS_MAGIC_PRODUCTS_CLIENT_ID="op://Infrastructure/tsuxet4wmrwdthy43rhiotkf2y/username"
LANTERN_CHECKS_MAGIC_PRODUCTS_CLIENT_SECRET="op://Infrastructure/tsuxet4wmrwdthy43rhiotkf2y/password"
LANTERN_CHECKS_MAGIC_PRODUCTS_CLIENT_SECRET_ID="op://Infrastructure/tsuxet4wmrwdthy43rhiotkf2y/secret-id"
LANTERN_CHECKS_MAGIC_PRODUCTS_CLIENT_SECRET_EXP="op://Infrastructure/tsuxet4wmrwdthy43rhiotkf2y/secret-exp"

LANTERN_BASE_URL_TESTING="https://data-testing.data.bas.ac.uk"
LANTERN_BASE_URL_LIVE="https://data.bas.ac.uk"

# Dev tasks
X_ADMIN_METADATA_SIGNING_KEY_PRIVATE="op://Shared/4gwxzflv3bxl7dqcwexrmqi6kq/private-jwk-escaped"
X_AGOL_CLIENT_ID="op://Infrastructure/l6srwxde4bj3e3tiwegsixocyq/username"
X_AGOL_CLIENT_SECRET="op://Infrastructure/l6srwxde4bj3e3tiwegsixocyq/credential"
