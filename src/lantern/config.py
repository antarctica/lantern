from pathlib import Path
from typing import TypedDict

from environs import Env, EnvError


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

    def validate(self) -> None:
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

    class ConfigDumpSafe(TypedDict):
        """Types for `dumps_safe`."""

        STORE_GITLAB_ENDPOINT: str
        STORE_GITLAB_TOKEN: str
        STORE_GITLAB_PROJECT_ID: str
        STORE_GITLAB_CACHE_PATH: str

    def dumps_safe(self) -> ConfigDumpSafe:
        """Dump config for output to the user with sensitive data redacted."""
        return {
            "STORE_GITLAB_ENDPOINT": self.STORE_GITLAB_ENDPOINT,
            "STORE_GITLAB_TOKEN": self.STORE_GITLAB_TOKEN_SAFE,
            "STORE_GITLAB_PROJECT_ID": self.STORE_GITLAB_PROJECT_ID,
            "STORE_GITLAB_CACHE_PATH": str(self.STORE_GITLAB_CACHE_PATH.resolve()),
        }

    @property
    def STORE_GITLAB_ENDPOINT(self) -> str:
        """Endpoint for GitLab store."""
        with (
            self.env.prefixed(self._app_prefix),
            self.env.prefixed("STORE_GITLAB_"),
        ):
            return self.env.str("ENDPOINT")

    @property
    def STORE_GITLAB_TOKEN(self) -> str:
        """API token for GitLab store."""
        with (
            self.env.prefixed(self._app_prefix),
            self.env.prefixed("STORE_GITLAB_"),
        ):
            return self.env.str("TOKEN")

    @property
    def STORE_GITLAB_TOKEN_SAFE(self) -> str:
        """STORE_GITLAB_TOKEN with value redacted."""
        return self._safe_value if self.STORE_GITLAB_TOKEN else ""

    @property
    def STORE_GITLAB_PROJECT_ID(self) -> str:
        """Project ID for GitLab store."""
        with (
            self.env.prefixed(self._app_prefix),
            self.env.prefixed("STORE_GITLAB_"),
        ):
            return self.env.str("PROJECT_ID")

    @property
    def STORE_GITLAB_CACHE_PATH(self) -> Path:
        """Path to local cache for GitLab store."""
        with (
            self.env.prefixed(self._app_prefix),
            self.env.prefixed("STORE_GITLAB_"),
        ):
            return self.env.path("CACHE_PATH")
