LANTERN_LOG_LEVEL="INFO"  # normally INFO
LANTERN_PARALLEL_JOBS="-1"  # normally -1 (all CPUs)

LANTERN_ENABLE_FEATURE_SENTRY="false"  # normally false
LANTERN_SENTRY_ENVIRONMENT="development" # normally development

LANTERN_ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE="op://Shared/MAGIC administrative metadata encryption key/private-jwk-escaped"
LANTERN_ADMIN_METADATA_SIGNING_KEY_PUBLIC="op://Shared/MAGIC administrative metadata signing key/public-jwk-escaped"

LANTERN_STORE_GITLAB_ENDPOINT="op://Infrastructure/SCAR ADD Metadata Toolbox - GitLab Store/GitLab Instance/password"
LANTERN_STORE_GITLAB_PROJECT_ID="op://Infrastructure/SCAR ADD Metadata Toolbox - GitLab Store/Project ID/project_id"
LANTERN_STORE_GITLAB_TOKEN=""  # populate with per-user token with 'developer' role and 'api' scopes
LANTERN_STORE_GITLAB_BRANCH="main"
LANTERN_STORE_GITLAB_CACHE_PATH=".cache"

LANTERN_TEMPLATES_PLAUSIBLE_DOMAIN="op://Infrastructure/SCAR ADD Metadata Toolbox - Plausible domain/password"
LANTERN_TEMPLATES_ITEM_CONTACT_ENDPOINT="op://Infrastructure/SCAR ADD Metadata Toolbox - Power Automate item enquires/password"
LANTERN_TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY="op://Shared/SCAR ADD Metadata Toolbox - Cloudflare Turnstile Captcha/username"
LANTERN_TEMPLATES_ITEM_VERSIONS_ENDPOINT="op://Infrastructure/SCAR ADD Metadata Toolbox - GitLab Store/GitLab Project Web URL/web_url"

LANTERN_EXPORT_PATH="./export"
LANTERN_AWS_ACCESS_ID="" # populate with per-user/instance IAM credentials
LANTERN_AWS_ACCESS_SECRET="" # populate with per-user/instance IAM credentials
LANTERN_AWS_S3_BUCKET="op://Infrastructure/rnv7zb3jzviwsvziknpxicvqaq/password"  # integration
#LANTERN_AWS_S3_BUCKET="op://Infrastructure/hksogwx7zqx3ct2jr36cshoqpy/password"  # production

LANTERN_VERIFY_SHAREPOINT_PROXY_ENDPOINT="op://Infrastructure/SCAR ADD Metadata Toolbox - SharePoint proxy URL/password"
