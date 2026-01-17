import logging
from hashlib import sha1
from importlib.metadata import version
from pathlib import Path
from typing import TypedDict

from environs import Env, EnvError, EnvValidationError
from jwskate import Jwk

from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys


class ConfigurationError(Exception):
    """Raised for configuration validation errors."""

    pass


# noinspection PyPep8Naming
class Config:
    """Application configuration."""

    def __init__(self, read_env: bool = True) -> None:
        """Create Config instance and load options from possible .env file."""
        self._app_prefix = "LANTERN_"
        self._app_package = "lantern"
        self._safe_value = "[**REDACTED**]"

        self.env = Env()
        if read_env:
            self.env.read_env()

    def __getstate__(self) -> dict:
        """
        Support pickling by removing unsupported attributes.

        Environs instances cannot be pickled.
        """
        state = self.__dict__.copy()
        del state["env"]
        return state

    def __setstate__(self, state: dict) -> None:
        """Restore unsupported attributes when unpickling."""
        self.__dict__.update(state)
        self.env = Env()

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Config):
            return NotImplemented
        return self.dumps_safe() == other.dumps_safe() and self.ADMIN_METADATA_KEYS == other.ADMIN_METADATA_KEYS

    def validate(self) -> None:
        """
        Validate configuration.

        This validation is basic/limited. E.g. We check that credentials aren't empty, not that they work.

        Note: Logging level is validated at the point of access by environs automatically.

        If invalid a ConfigurationError is raised.
        """
        required = [
            "ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE",
            "ADMIN_METADATA_SIGNING_KEY_PUBLIC",
            "STORE_GITLAB_ENDPOINT",
            "STORE_GITLAB_TOKEN",
            "STORE_GITLAB_PROJECT_ID",
            "STORE_GITLAB_BRANCH",
            "STORE_GITLAB_CACHE_PATH",
            "TEMPLATES_PLAUSIBLE_DOMAIN",
            "TEMPLATES_ITEM_CONTACT_ENDPOINT",
            "TEMPLATES_ITEM_VERSIONS_ENDPOINT",
            "TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY",
            "EXPORT_PATH",
            "AWS_S3_BUCKET",
            "AWS_ACCESS_ID",
            "AWS_ACCESS_SECRET",
            "VERIFY_SHAREPOINT_PROXY_ENDPOINT",
            "VERIFY_SAN_PROXY_ENDPOINT",
        ]
        directories = ["STORE_GITLAB_CACHE_PATH", "EXPORT_PATH"]

        for prop in required:
            attr = prop
            if prop == "ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE" or prop == "ADMIN_METADATA_SIGNING_KEY_PUBLIC":
                attr = "ADMIN_METADATA_KEYS"
            try:
                _ = getattr(self, attr)
            except EnvError as e:
                msg = f"{prop} must be set."
                raise ConfigurationError(msg) from e

        for prop in directories:
            if Path(getattr(self, prop)).exists() and not Path(getattr(self, prop)).is_dir():
                msg = f"{prop} must be a directory."
                raise ConfigurationError(msg)

    class ConfigDumpSafe(TypedDict):
        """Types and keys for `dumps_safe`."""

        NAME: str
        VERSION: str
        PARALLEL_JOBS: int
        LOG_LEVEL: int
        LOG_LEVEL_NAME: str
        SENTRY_DSN: str
        ENABLE_FEATURE_SENTRY: bool
        SENTRY_ENVIRONMENT: str
        ADMIN_METADATA_KEYS_ENCRYPTION_KEY_PRIVATE: str
        ADMIN_METADATA_KEYS_SIGNING_KEY_PUBLIC: str
        STORE_GITLAB_ENDPOINT: str
        STORE_GITLAB_TOKEN: str
        STORE_GITLAB_PROJECT_ID: str
        STORE_GITLAB_BRANCH: str
        STORE_GITLAB_CACHE_PATH: str
        TEMPLATES_CACHE_BUST_VALUE: str
        TEMPLATES_PLAUSIBLE_DOMAIN: str
        TEMPLATES_ITEM_MAPS_ENDPOINT: str
        TEMPLATES_ITEM_CONTACT_ENDPOINT: str
        TEMPLATES_ITEM_VERSIONS_ENDPOINT: str
        TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY: str
        BASE_URL: str
        EXPORT_PATH: str
        AWS_S3_BUCKET: str
        AWS_ACCESS_ID: str
        AWS_ACCESS_SECRET: str
        VERIFY_SHAREPOINT_PROXY_ENDPOINT: str
        VERIFY_SAN_PROXY_ENDPOINT: str

    def dumps_safe(self) -> ConfigDumpSafe:
        """Dump config for output to the user with sensitive data redacted."""
        return {
            "NAME": self.NAME,
            "VERSION": self.VERSION,
            "PARALLEL_JOBS": self.PARALLEL_JOBS,
            "LOG_LEVEL": self.LOG_LEVEL,
            "LOG_LEVEL_NAME": self.LOG_LEVEL_NAME,
            "SENTRY_DSN": self.SENTRY_DSN,
            "ENABLE_FEATURE_SENTRY": self.ENABLE_FEATURE_SENTRY,
            "SENTRY_ENVIRONMENT": self.SENTRY_ENVIRONMENT,
            "ADMIN_METADATA_KEYS_ENCRYPTION_KEY_PRIVATE": self.ADMIN_METADATA_KEYS_ENCRYPTION_KEY_PRIVATE_SAFE,
            "ADMIN_METADATA_KEYS_SIGNING_KEY_PUBLIC": self.ADMIN_METADATA_KEYS.signing_public.to_json(compact=True),
            "STORE_GITLAB_ENDPOINT": self.STORE_GITLAB_ENDPOINT,
            "STORE_GITLAB_TOKEN": self.STORE_GITLAB_TOKEN_SAFE,
            "STORE_GITLAB_PROJECT_ID": self.STORE_GITLAB_PROJECT_ID,
            "STORE_GITLAB_BRANCH": self.STORE_GITLAB_BRANCH,
            "STORE_GITLAB_CACHE_PATH": str(self.STORE_GITLAB_CACHE_PATH.resolve()),
            "TEMPLATES_CACHE_BUST_VALUE": self.TEMPLATES_CACHE_BUST_VALUE,
            "TEMPLATES_PLAUSIBLE_DOMAIN": self.TEMPLATES_PLAUSIBLE_DOMAIN,
            "TEMPLATES_ITEM_MAPS_ENDPOINT": self.TEMPLATES_ITEM_MAPS_ENDPOINT,
            "TEMPLATES_ITEM_CONTACT_ENDPOINT": self.TEMPLATES_ITEM_CONTACT_ENDPOINT,
            "TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY": self.TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY,
            "TEMPLATES_ITEM_VERSIONS_ENDPOINT": self.TEMPLATES_ITEM_VERSIONS_ENDPOINT,
            "BASE_URL": self.BASE_URL,
            "EXPORT_PATH": str(self.EXPORT_PATH.resolve()),
            "AWS_S3_BUCKET": self.AWS_S3_BUCKET,
            "AWS_ACCESS_ID": self.AWS_ACCESS_ID,
            "AWS_ACCESS_SECRET": self.AWS_ACCESS_SECRET_SAFE,
            "VERIFY_SHAREPOINT_PROXY_ENDPOINT": self.VERIFY_SHAREPOINT_PROXY_ENDPOINT,
            "VERIFY_SAN_PROXY_ENDPOINT": self.VERIFY_SAN_PROXY_ENDPOINT,
        }

    @property
    def NAME(self) -> str:
        """Application name."""
        return self._app_package

    @property
    def VERSION(self) -> str:
        """
        Application version.

        Read from package metadata.
        """
        return version(self.NAME)

    @property
    def PARALLEL_JOBS(self) -> int:
        """Number of parallel jobs to use for relevant tasks."""
        with self.env.prefixed(self._app_prefix):
            return self.env.int("PARALLEL_JOBS", 1)

    @property
    def LOG_LEVEL(self) -> int:
        """Logging level."""
        with self.env.prefixed(self._app_prefix):
            try:
                return self.env.log_level("LOG_LEVEL", logging.WARNING)
            except EnvValidationError as e:
                msg = "LOG_LEVEL is invalid."
                raise ConfigurationError(msg) from e

    @property
    def LOG_LEVEL_NAME(self) -> str:
        """Logging level name."""
        return logging.getLevelName(self.LOG_LEVEL)

    @property
    def SENTRY_DSN(self) -> str:
        """Connection string for Sentry monitoring."""
        return "https://7ee10f6777ab8ec05ffe8b84c4c3039e@o39753.ingest.us.sentry.io/4507147658919936"

    @property
    def ENABLE_FEATURE_SENTRY(self) -> bool:
        """Controls whether Sentry monitoring is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.bool("ENABLE_FEATURE_SENTRY", True)

    @property
    def SENTRY_ENVIRONMENT(self) -> str:
        """Controls whether Sentry monitoring is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.str("SENTRY_ENVIRONMENT", "development")

    @property
    def ADMIN_METADATA_KEYS(self) -> AdministrationKeys:
        """JSON Web Keys for decrypting and verifying administrative metadata."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("ADMIN_METADATA_"):
            return AdministrationKeys(
                encryption_private=Jwk(self.env.json("ENCRYPTION_KEY_PRIVATE")),
                signing_public=Jwk(self.env.json("SIGNING_KEY_PUBLIC")),
            )

    @property
    def ADMIN_METADATA_KEYS_ENCRYPTION_KEY_PRIVATE_SAFE(self) -> str:
        """ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE with value redacted."""
        return self._safe_value if self.ADMIN_METADATA_KEYS.encryption_private else ""

    @property
    def STORE_GITLAB_ENDPOINT(self) -> str:
        """Endpoint for GitLab store."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("STORE_GITLAB_"):
            return self.env.str("ENDPOINT")

    @property
    def STORE_GITLAB_TOKEN(self) -> str:
        """API token for GitLab store."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("STORE_GITLAB_"):
            return self.env.str("TOKEN")

    @property
    def STORE_GITLAB_TOKEN_SAFE(self) -> str:
        """STORE_GITLAB_TOKEN with value redacted."""
        return self._safe_value if self.STORE_GITLAB_TOKEN else ""

    @property
    def STORE_GITLAB_PROJECT_ID(self) -> str:
        """Project ID for GitLab store."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("STORE_GITLAB_"):
            return self.env.str("PROJECT_ID")

    @property
    def STORE_GITLAB_BRANCH(self) -> str:
        """Branch name for GitLab store."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("STORE_GITLAB_"):
            return self.env.str("BRANCH")

    @property
    def STORE_GITLAB_CACHE_PATH(self) -> Path:
        """Path to local cache for GitLab store."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("STORE_GITLAB_"):
            return self.env.path("CACHE_PATH").resolve()

    @property
    def TEMPLATES_CACHE_BUST_VALUE(self) -> str:
        """
        Value to append to URLs for static assets to ensure current versions are used.

        Set to the first 7 characters of app version SHA1 hash. E.g. `main.css?v=f053ddb` for version 0.1.0.
        """
        return sha1(f"v{self.VERSION}".encode()).hexdigest()[:7]  # noqa: S324

    @property
    def TEMPLATES_PLAUSIBLE_DOMAIN(self) -> str:
        """Plausible site/domain name."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("TEMPLATES_"):
            return self.env("PLAUSIBLE_DOMAIN")

    @property
    def TEMPLATES_ITEM_MAPS_ENDPOINT(self) -> str:
        """Base URL for Embedded Maps Service to generate extent maps in items extent tab."""
        return "https://embedded-maps.data.bas.ac.uk/v1"

    @property
    def TEMPLATES_ITEM_CONTACT_ENDPOINT(self) -> str:
        """Endpoint for contact form in items contact tab."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("TEMPLATES_"), self.env.prefixed("ITEM_"):
            return self.env("CONTACT_ENDPOINT")

    @property
    def TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY(self) -> str:
        """Site key for public facing Cloudflare Turnstile bot protection widget."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("TEMPLATES_"), self.env.prefixed("ITEM_"):
            return self.env("CONTACT_TURNSTILE_KEY")

    @property
    def TEMPLATES_ITEM_VERSIONS_ENDPOINT(self) -> str:
        """
        Base URL for viewing item revisions.

        I.e. The URL to the Git repository where item record revisions are stored.
        """
        with self.env.prefixed(self._app_prefix), self.env.prefixed("TEMPLATES_"), self.env.prefixed("ITEM_"):
            return self.env("VERSIONS_ENDPOINT")

    @property
    def BASE_URL(self) -> str:
        """Root URL for site output."""
        return f"https://{self.AWS_S3_BUCKET}"

    @property
    def EXPORT_PATH(self) -> Path:
        """Path to site output."""
        with self.env.prefixed(self._app_prefix):
            return self.env.path("EXPORT_PATH").resolve()

    @property
    def AWS_S3_BUCKET(self) -> str:
        """S3 bucket for site output."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("AWS_"):
            return self.env("S3_BUCKET")

    @property
    def AWS_ACCESS_ID(self) -> str:
        """ID for AWS IAM access key used to manage content in AWS_S3_BUCKET."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("AWS_"):
            return self.env("ACCESS_ID")

    @property
    def AWS_ACCESS_SECRET(self) -> str:
        """Secret for AWS IAM access key used to manage content in AWS_S3_BUCKET."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("AWS_"):
            return self.env("ACCESS_SECRET")

    @property
    def AWS_ACCESS_SECRET_SAFE(self) -> str:
        """AWS_ACCESS_SECRET with value redacted."""
        return self._safe_value if self.AWS_ACCESS_SECRET else ""

    @property
    def VERIFY_SHAREPOINT_PROXY_ENDPOINT(self) -> str:
        """Endpoint for checking SharePoint hosted downloads in verification jobs."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("VERIFY_"):
            return self.env("SHAREPOINT_PROXY_ENDPOINT")

    @property
    def VERIFY_SAN_PROXY_ENDPOINT(self) -> str:
        """Endpoint for checking SAN references in verification jobs."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("VERIFY_"):
            return self.env("SAN_PROXY_ENDPOINT")
