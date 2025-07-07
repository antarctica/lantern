import logging
from importlib.metadata import version
from pathlib import Path
from typing import TypedDict

from environs import Env, EnvError, EnvValidationError


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

    def validate(self) -> None:  # noqa: C901
        """
        Validate configuration.

        This validation is basic/limited. E.g. We check that credentials aren't empty, not that they work.

        Note: Logging level is validated at the point of access by environs automatically.

        If invalid a ConfigurationError is raised.
        """
        try:
            _ = self.STORE_GITLAB_ENDPOINT
        except EnvError as e:
            msg = "STORE_GITLAB_ENDPOINT must be set."
            raise ConfigurationError(msg) from e

        try:
            _ = self.STORE_GITLAB_TOKEN
        except EnvError as e:
            msg = "STORE_GITLAB_TOKEN must be set."
            raise ConfigurationError(msg) from e

        try:
            _ = self.STORE_GITLAB_PROJECT_ID
        except EnvError as e:
            msg = "STORE_GITLAB_PROJECT_ID must be set."
            raise ConfigurationError(msg) from e

        try:
            _ = self.STORE_GITLAB_CACHE_PATH
        except EnvError as e:
            msg = "STORE_GITLAB_CACHE_PATH must be set."
            raise ConfigurationError(msg) from e
        if Path(self.STORE_GITLAB_CACHE_PATH).exists() and not Path(self.STORE_GITLAB_CACHE_PATH).is_dir():
            msg = "STORE_GITLAB_CACHE_PATH must be a directory."
            raise ConfigurationError(msg)

        try:
            _ = self.TEMPLATES_PLAUSIBLE_DOMAIN
        except EnvError as e:
            msg = "TEMPLATES_PLAUSIBLE_DOMAIN must be set."
            raise ConfigurationError(msg) from e

        try:
            _ = self.TEMPLATES_ITEM_CONTACT_ENDPOINT
        except EnvError as e:
            msg = "TEMPLATES_ITEM_CONTACT_ENDPOINT must be set."
            raise ConfigurationError(msg) from e

        try:
            _ = self.EXPORT_PATH
        except EnvError as e:
            msg = "EXPORT_PATH must be set."
            raise ConfigurationError(msg) from e
        if Path(self.EXPORT_PATH).exists() and not Path(self.EXPORT_PATH).is_dir():
            msg = "EXPORT_PATH must be a directory."
            raise ConfigurationError(msg)

        try:
            _ = self.AWS_S3_BUCKET
        except EnvError as e:
            msg = "AWS_S3_BUCKET must be set."
            raise ConfigurationError(msg) from e

        try:
            _ = self.AWS_ACCESS_ID
        except EnvError as e:
            msg = "AWS_ACCESS_ID must be set."
            raise ConfigurationError(msg) from e

        try:
            _ = self.AWS_ACCESS_SECRET
        except EnvError as e:
            msg = "AWS_ACCESS_SECRET must be set."
            raise ConfigurationError(msg) from e

    class ConfigDumpSafe(TypedDict):
        """Types and keys for `dumps_safe`."""

        VERSION: str
        LOG_LEVEL: int
        LOG_LEVEL_NAME: str
        SENTRY_DSN: str
        ENABLE_FEATURE_SENTRY: bool
        SENTRY_ENVIRONMENT: str
        STORE_GITLAB_ENDPOINT: str
        STORE_GITLAB_TOKEN: str
        STORE_GITLAB_PROJECT_ID: str
        STORE_GITLAB_CACHE_PATH: str
        TEMPLATES_SENTRY_SRC: str
        TEMPLATES_PLAUSIBLE_DOMAIN: str
        TEMPLATES_ITEM_MAPS_ENDPOINT: str
        TEMPLATES_ITEM_CONTACT_ENDPOINT: str
        EXPORT_PATH: str
        AWS_S3_BUCKET: str
        AWS_ACCESS_ID: str
        AWS_ACCESS_SECRET: str

    def dumps_safe(self) -> ConfigDumpSafe:
        """Dump config for output to the user with sensitive data redacted."""
        return {
            "VERSION": self.VERSION,
            "LOG_LEVEL": self.LOG_LEVEL,
            "LOG_LEVEL_NAME": self.LOG_LEVEL_NAME,
            "SENTRY_DSN": self.SENTRY_DSN,
            "ENABLE_FEATURE_SENTRY": self.ENABLE_FEATURE_SENTRY,
            "SENTRY_ENVIRONMENT": self.SENTRY_ENVIRONMENT,
            "STORE_GITLAB_ENDPOINT": self.STORE_GITLAB_ENDPOINT,
            "STORE_GITLAB_TOKEN": self.STORE_GITLAB_TOKEN_SAFE,
            "STORE_GITLAB_PROJECT_ID": self.STORE_GITLAB_PROJECT_ID,
            "STORE_GITLAB_CACHE_PATH": str(self.STORE_GITLAB_CACHE_PATH.resolve()),
            "TEMPLATES_SENTRY_SRC": self.TEMPLATES_SENTRY_SRC,
            "TEMPLATES_PLAUSIBLE_DOMAIN": self.TEMPLATES_PLAUSIBLE_DOMAIN,
            "TEMPLATES_ITEM_MAPS_ENDPOINT": self.TEMPLATES_ITEM_MAPS_ENDPOINT,
            "TEMPLATES_ITEM_CONTACT_ENDPOINT": self.TEMPLATES_ITEM_CONTACT_ENDPOINT,
            "EXPORT_PATH": str(self.EXPORT_PATH.resolve()),
            "AWS_S3_BUCKET": self.AWS_S3_BUCKET,
            "AWS_ACCESS_ID": self.AWS_ACCESS_ID,
            "AWS_ACCESS_SECRET": self.AWS_ACCESS_SECRET_SAFE,
        }

    @property
    def VERSION(self) -> str:
        """
        Application version.

        Read from package metadata.
        """
        return version(self._app_package)

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
        return "https://db9543e7b68f4b2596b189ff444438e3@o39753.ingest.us.sentry.io/5197036"

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
    def STORE_GITLAB_CACHE_PATH(self) -> Path:
        """Path to local cache for GitLab store."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("STORE_GITLAB_"):
            return self.env.path("CACHE_PATH").resolve()

    @property
    def TEMPLATES_SENTRY_SRC(self) -> str:
        """Sentry dynamic CDN script."""
        return "https://js.sentry-cdn.com/57698b6483c7ac43b7c9c905cdb79943.min.js"

    @property
    def TEMPLATES_PLAUSIBLE_DOMAIN(self) -> str:
        """Plausible site/domain name."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("TEMPLATES_"):
            return self.env("PLAUSIBLE_DOMAIN")

    @property
    def TEMPLATES_ITEM_MAPS_ENDPOINT(self) -> str:
        """Endpoint for Embedded Maps Service to generate extent maps in items extent tab."""
        return "https://embedded-maps.data.bas.ac.uk/v1"

    @property
    def TEMPLATES_ITEM_CONTACT_ENDPOINT(self) -> str:
        """Endpoint for contact form in items contact tab."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("TEMPLATES_"), self.env.prefixed("ITEM_"):
            return self.env("CONTACT_ENDPOINT")

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
