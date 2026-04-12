import logging
from hashlib import sha1
from importlib.metadata import version
from pathlib import Path
from typing import TypedDict

from environs import Env, ValidationError
from jwskate import Jwk
from marshmallow import validate

from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys


class Config:
    """
    Application configuration using environment variables.

    Properties are validated on access, see `validate()` for details and/or how to force checks.
    """

    def __init__(self, read_dotenv: bool = True) -> None:
        """Create Config instance and load options from possible .env file."""
        self._app_prefix = "LANTERN_"
        self._app_package = "lantern"
        self._safe_value = "[**REDACTED**]"
        self._none_value = "[**NOT SET**]"

        self._env = Env()
        if read_dotenv:
            self._env.read_env()

    def __getstate__(self) -> dict:
        """
        Support pickling by removing unsupported attributes.

        Environs instances cannot be pickled.
        """
        state = self.__dict__.copy()
        del state["_env"]
        return state

    def __setstate__(self, state: dict) -> None:
        """Restore unsupported attributes when unpickling."""
        self.__dict__.update(state)
        self._env = Env()

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Config):
            return NotImplemented
        return self.dumps_safe() == other.dumps_safe() and self.ADMIN_METADATA_KEYS == other.ADMIN_METADATA_KEYS

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
        TEMPLATES_PLAUSIBLE_ID: str
        TEMPLATES_ITEM_MAPS_ENDPOINT: str
        TEMPLATES_ITEM_CONTACT_ENDPOINT: str
        TEMPLATES_ITEM_VERSIONS_ENDPOINT: str
        TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY: str
        SITE_UNTRUSTED_S3_BUCKET_TESTING: str
        SITE_UNTRUSTED_S3_BUCKET_LIVE: str
        SITE_UNTRUSTED_S3_ACCESS_ID: str
        SITE_UNTRUSTED_S3_ACCESS_SECRET: str
        SITE_TRUSTED_RSYNC_HOST: str
        SITE_TRUSTED_RSYNC_BASE_PATH_TESTING: str
        SITE_TRUSTED_RSYNC_BASE_PATH_LIVE: str
        BASE_URL_TESTING: str
        BASE_URL_LIVE: str

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
            "TEMPLATES_PLAUSIBLE_ID": self.TEMPLATES_PLAUSIBLE_ID,
            "TEMPLATES_ITEM_MAPS_ENDPOINT": self.TEMPLATES_ITEM_MAPS_ENDPOINT,
            "TEMPLATES_ITEM_CONTACT_ENDPOINT": self.TEMPLATES_ITEM_CONTACT_ENDPOINT,
            "TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY": self.TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY,
            "TEMPLATES_ITEM_VERSIONS_ENDPOINT": self.TEMPLATES_ITEM_VERSIONS_ENDPOINT,
            "SITE_UNTRUSTED_S3_BUCKET_TESTING": self.SITE_UNTRUSTED_S3_BUCKET_TESTING,
            "SITE_UNTRUSTED_S3_BUCKET_LIVE": self.SITE_UNTRUSTED_S3_BUCKET_LIVE,
            "SITE_UNTRUSTED_S3_ACCESS_ID": self.SITE_UNTRUSTED_S3_ACCESS_ID,
            "SITE_UNTRUSTED_S3_ACCESS_SECRET": self.SITE_UNTRUSTED_S3_ACCESS_SECRET_SAFE,
            "SITE_TRUSTED_RSYNC_HOST": self.SITE_TRUSTED_RSYNC_HOST,
            "SITE_TRUSTED_RSYNC_BASE_PATH_TESTING": str(self.SITE_TRUSTED_RSYNC_BASE_PATH_TESTING),
            "SITE_TRUSTED_RSYNC_BASE_PATH_LIVE": str(self.SITE_TRUSTED_RSYNC_BASE_PATH_LIVE),
            "BASE_URL_TESTING": self.BASE_URL_TESTING,
            "BASE_URL_LIVE": self.BASE_URL_LIVE,
        }

    def validate(self) -> None:
        """
        Prompt config validation.

        Trigger validation of all properties by trying to access them.

        Undefined required properties will raise `environs.exceptions.EnvError`.

        Invalid property values will raise a `environs.exceptions.EnvValidationError` (a `EnvError` subclass).

        Validation is set on each property, using a combination of default environs/marshmallow and custom validators.
        Validation is basic/limited, for example we check credentials aren't empty, not that they work.
        """
        self.dumps_safe()

    @staticmethod
    def _opt_path_validator(n: Path) -> None:
        """If path exists, it must be a directory."""
        if n.exists() and not n.is_dir():
            msg = "Must be a directory."
            raise ValidationError(msg)

    @staticmethod
    def _parallel_validator(n: int) -> None:
        """Must be a positive integer or -1."""
        # Accept integers >= 0 or the sentinel -1. Reject other values.
        if not (type(n) is int and (n > 0 or n == -1)):
            msg = "Must be a positive integer or -1."
            raise ValidationError(msg)

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
        with self._env.prefixed(self._app_prefix):
            return self._env.int("PARALLEL_JOBS", default=1, validate=self._parallel_validator)

    @property
    def LOG_LEVEL(self) -> int:
        """Logging level."""
        with self._env.prefixed(self._app_prefix):
            return self._env.log_level("LOG_LEVEL", default=logging.WARNING)

    @property
    def LOG_LEVEL_NAME(self) -> str:
        """Logging level name."""
        return logging.getLevelName(self.LOG_LEVEL)

    @property
    def SENTRY_DSN(self) -> str:
        """
        Connection string for Sentry monitoring.

        This value is not sensitive.
        """
        return "https://7ee10f6777ab8ec05ffe8b84c4c3039e@o39753.ingest.us.sentry.io/4507147658919936"

    @property
    def ENABLE_FEATURE_SENTRY(self) -> bool:
        """Controls whether Sentry monitoring is used."""
        with self._env.prefixed(self._app_prefix):
            return self._env.bool("ENABLE_FEATURE_SENTRY", default=True)

    @property
    def SENTRY_ENVIRONMENT(self) -> str:
        """Controls whether Sentry monitoring is used."""
        with self._env.prefixed(self._app_prefix):
            return self._env.str("SENTRY_ENVIRONMENT", default="development")

    @property
    def ADMIN_METADATA_KEYS(self) -> AdministrationKeys:
        """
        JSON Web Keys for decrypting and verifying administrative metadata.

        Keys are cached JWKs for performance. Use setter if changing keys (for tests etc.).
        """
        if "_admin_metadata_keys" in self.__dict__:
            return self.__dict__["_admin_metadata_keys"]
        with self._env.prefixed(self._app_prefix), self._env.prefixed("ADMIN_METADATA_"):
            keys = AdministrationKeys(
                encryption_private=Jwk(self._env.json("ENCRYPTION_KEY_PRIVATE")),
                signing_public=Jwk(self._env.json("SIGNING_KEY_PUBLIC")),
            )
            self.__dict__["_admin_metadata_keys"] = keys
            return keys

    @property
    def ADMIN_METADATA_KEYS_ENCRYPTION_KEY_PRIVATE_SAFE(self) -> str:
        """ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE with value redacted."""
        return self._safe_value if self.ADMIN_METADATA_KEYS.encryption_private else ""

    @property
    def STORE_GITLAB_ENDPOINT(self) -> str:
        """Endpoint for GitLab store."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("STORE_GITLAB_"):
            return self._env.str("ENDPOINT", validate=validate.URL())

    @property
    def STORE_GITLAB_TOKEN(self) -> str:
        """API token for GitLab store."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("STORE_GITLAB_"):
            return self._env.str("TOKEN")

    @property
    def STORE_GITLAB_TOKEN_SAFE(self) -> str:
        """STORE_GITLAB_TOKEN with value redacted."""
        return self._safe_value if self.STORE_GITLAB_TOKEN else ""

    @property
    def STORE_GITLAB_PROJECT_ID(self) -> str:
        """Project ID for GitLab store."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("STORE_GITLAB_"):
            return self._env.str("PROJECT_ID")

    @property
    def STORE_GITLAB_BRANCH(self) -> str:
        """Branch name for GitLab store."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("STORE_GITLAB_"):
            return self._env.str("BRANCH")

    @property
    def STORE_GITLAB_CACHE_PATH(self) -> Path:
        """Path to local cache for GitLab store."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("STORE_GITLAB_"):
            return self._env.path("CACHE_PATH", validate=self._opt_path_validator).resolve()

    @property
    def TEMPLATES_CACHE_BUST_VALUE(self) -> str:
        """
        Value to append to URLs for static assets to ensure current versions are used.

        Set to the first 7 characters of app version SHA1 hash. E.g. `main.css?v=f053ddb` for version 0.1.0.
        """
        return sha1(f"v{self.VERSION}x".encode()).hexdigest()[:7]  # noqa: S324

    @property
    def TEMPLATES_PLAUSIBLE_ID(self) -> str:
        """Plausible site/domain name."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("TEMPLATES_"):
            return self._env.str("PLAUSIBLE_ID")

    @property
    def TEMPLATES_ITEM_MAPS_ENDPOINT(self) -> str:
        """Base URL for Embedded Maps Service to generate extent maps in items extent tab."""
        return "https://embedded-maps.data.bas.ac.uk/v1"

    @property
    def TEMPLATES_ITEM_CONTACT_ENDPOINT(self) -> str:
        """Endpoint for contact form in items contact tab."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("TEMPLATES_"), self._env.prefixed("ITEM_"):
            return self._env.str("CONTACT_ENDPOINT", validate=validate.URL())

    @property
    def TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY(self) -> str:
        """Site key for public facing Cloudflare Turnstile bot protection widget."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("TEMPLATES_"), self._env.prefixed("ITEM_"):
            return self._env.str("CONTACT_TURNSTILE_KEY")

    @property
    def TEMPLATES_ITEM_VERSIONS_ENDPOINT(self) -> str:
        """
        Base URL for viewing item revisions.

        I.e. The URL to the Git repository where item record revisions are stored.
        """
        with self._env.prefixed(self._app_prefix), self._env.prefixed("TEMPLATES_"), self._env.prefixed("ITEM_"):
            return self._env.str("VERSIONS_ENDPOINT", validate=validate.URL())

    @property
    def SITE_UNTRUSTED_S3_BUCKET_TESTING(self) -> str:
        """Target S3 bucket for untrusted site content (testing environment)."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("SITE_UNTRUSTED_S3_"):
            return self._env.str("BUCKET_TESTING")

    @property
    def SITE_UNTRUSTED_S3_BUCKET_LIVE(self) -> str:
        """Target S3 bucket for untrusted site content (live environment)."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("SITE_UNTRUSTED_S3_"):
            return self._env.str("BUCKET_LIVE")

    @property
    def SITE_UNTRUSTED_S3_ACCESS_ID(self) -> str:
        """ID for AWS IAM access key used to manage content in SITE_UNTRUSTED_S3_BUCKET."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("SITE_UNTRUSTED_S3_"):
            return self._env.str("ACCESS_ID")

    @property
    def SITE_UNTRUSTED_S3_ACCESS_SECRET(self) -> str:
        """Secret for AWS IAM access key used to manage content in SITE_UNTRUSTED_S3_BUCKET."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("SITE_UNTRUSTED_S3_"):
            return self._env.str("ACCESS_SECRET")

    @property
    def SITE_UNTRUSTED_S3_ACCESS_SECRET_SAFE(self) -> str:
        """SITE_UNTRUSTED_S3_ACCESS_SECRET with value redacted."""
        return self._safe_value if self.SITE_UNTRUSTED_S3_ACCESS_SECRET else ""

    @property
    def SITE_TRUSTED_RSYNC_HOST(self) -> str:
        """Target host for trusted site content."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("SITE_TRUSTED_RSYNC_"):
            return self._env.str("HOST")

    @property
    def SITE_TRUSTED_RSYNC_BASE_PATH_TESTING(self) -> Path:
        """Target path for trusted site content (testing environment)."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("SITE_TRUSTED_RSYNC_"):
            return self._env.path("BASE_PATH_TESTING")

    @property
    def SITE_TRUSTED_RSYNC_BASE_PATH_LIVE(self) -> Path:
        """Target path for trusted site content (live environment)."""
        with self._env.prefixed(self._app_prefix), self._env.prefixed("SITE_TRUSTED_RSYNC_"):
            return self._env.path("BASE_PATH_LIVE")

    @property
    def BASE_URL_TESTING(self) -> str:
        """
        Catalogue base URL (Testing environment).

        Can be a reverse proxied endpoint. Must be a fully qualified URL.
        """
        with self._env.prefixed(self._app_prefix), self._env.prefixed("BASE_URL_"):
            return self._env.str("TESTING", validate=validate.URL())

    @property
    def BASE_URL_LIVE(self) -> str:
        """
        Catalogue hosting base URL (Live environment).

        Can be a reverse proxied endpoint. Must be a fully qualified URL.
        """
        with self._env.prefixed(self._app_prefix), self._env.prefixed("BASE_URL_"):
            return self._env.str("LIVE", validate=validate.URL())
