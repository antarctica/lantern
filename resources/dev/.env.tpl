LANTERN_LOG_LEVEL="INFO"  # normally INFO
LANTERN_PARALLEL_JOBS="-1"  # normally -1 (all CPUs)

LANTERN_ENABLE_FEATURE_SENTRY="false"  # normally false
LANTERN_SENTRY_ENVIRONMENT="development"  # normally development

LANTERN_ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE="op://Shared/MAGIC administrative metadata encryption key/private-jwk-escaped"
LANTERN_ADMIN_METADATA_SIGNING_KEY_PUBLIC="op://Shared/MAGIC administrative metadata signing key/public-jwk-escaped"

LANTERN_STORE_GITLAB_ENDPOINT="op://Infrastructure/SCAR ADD Metadata Toolbox - GitLab Store/GitLab Instance/password"
LANTERN_STORE_GITLAB_PROJECT_ID="op://Infrastructure/SCAR ADD Metadata Toolbox - GitLab Store/Project ID/project_id"
LANTERN_STORE_GITLAB_TOKEN=""  # populate with personal access token for GitLab bot user with 'api' scopes
LANTERN_STORE_GITLAB_BRANCH="main"
LANTERN_STORE_GITLAB_CACHE_PATH=".cache"

LANTERN_TEMPLATES_PLAUSIBLE_ID="op://Infrastructure/SCAR ADD Metadata Toolbox - Plausible site/password"
LANTERN_TEMPLATES_ITEM_CONTACT_ENDPOINT="op://Infrastructure/SCAR ADD Metadata Toolbox - Power Automate item enquires/password"
LANTERN_TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY="op://Infrastructure/SCAR ADD Metadata Toolbox - Cloudflare Turnstile Captcha/username"
LANTERN_TEMPLATES_ITEM_VERSIONS_ENDPOINT="op://Infrastructure/SCAR ADD Metadata Toolbox - GitLab Store/GitLab Project Web URL/web_url"

LANTERN_SITE_UNTRUSTED_S3_BUCKET_TESTING="op://Infrastructure/rnv7zb3jzviwsvziknpxicvqaq/password"  # testing
LANTERN_SITE_UNTRUSTED_S3_BUCKET_LIVE="op://Infrastructure/hksogwx7zqx3ct2jr36cshoqpy/password"  # production
LANTERN_SITE_UNTRUSTED_S3_ACCESS_ID=""  # populate with per-user/instance IAM credentials
LANTERN_SITE_UNTRUSTED_S3_ACCESS_SECRET=""  # populate with per-user/instance IAM credentials

LANTERN_SITE_TRUSTED_RSYNC_HOST=""  # populate with SSH config entry or leave blank to use local file system
LANTERN_SITE_TRUSTED_RSYNC_BASE_PATH_TESTING="{{ op://Infrastructure/SCAR ADD Metadata Toolbox - SAN sync/content-path }}/testing"
LANTERN_SITE_TRUSTED_RSYNC_BASE_PATH_LIVE="{{ op://Infrastructure/SCAR ADD Metadata Toolbox - SAN sync/content-path }}/live"
#LANTERN_SITE_TRUSTED_RSYNC_HOST=""  # for local stack
#LANTERN_SITE_TRUSTED_RSYNC_BASE_PATH_TESTING="./resources/dev/apache/run/cat/testing"  # for local stack

LANTERN_VERIFY_SHAREPOINT_PROXY_ENDPOINT="op://Infrastructure/SCAR ADD Metadata Toolbox - SharePoint proxy URL/password"
LANTERN_VERIFY_SAN_PROXY_ENDPOINT="op://Infrastructure/SCAR ADD Metadata Toolbox - SAN proxy URL/password"

LANTERN_BASE_URL_TESTING="https://data.bas.ac.uk"
LANTERN_BASE_URL_LIVE="https://data-testing.data.bas.ac.uk"

# Dev tasks
X_ADMIN_METADATA_SIGNING_KEY_PRIVATE="op://Shared/MAGIC administrative metadata signing key/private-jwk-escaped"
X_AGOL_CLIENT_ID="op://Infrastructure/l6srwxde4bj3e3tiwegsixocyq/username"
X_AGOL_CLIENT_SECRET="op://Infrastructure/l6srwxde4bj3e3tiwegsixocyq/credential"
