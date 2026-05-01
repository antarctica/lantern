from typing import TypedDict

from jwskate import Jwk

from lantern.config import Config
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys


class ExtraConfig(Config):
    """Additional config options needed for development tasks."""

    def __init__(self, read_dotenv: bool = True) -> None:
        super().__init__(read_dotenv)
        self._extra_prefix = "X_"
        self._none_value = "[**NOT SET**]"

    class ConfigDumpSafe(TypedDict):
        """Types and keys for `dumps_extra`."""

        ADMIN_METADATA_KEYS_SIGNING_KEY_PUBLIC: str
        AGOL_CLIENT_ID: str
        AGOL_CLIENT_SECRET: str

    def dumps_extra(self) -> ConfigDumpSafe:
        """Dump extra config for output to the user with sensitive data redacted."""
        return {
            "ADMIN_METADATA_KEYS_SIGNING_KEY_PUBLIC": self.ADMIN_METADATA_KEYS_RW_SAFE,
            "AGOL_CLIENT_ID": self.AGOL_CLIENT_ID,
            "AGOL_CLIENT_SECRET": self.AGOL_CLIENT_SECRET_SAFE,
        }

    @property
    def ADMIN_METADATA_KEYS_RW(self) -> AdministrationKeys:  # noqa: N802
        """JSON Web Keys for encrypting and signing administrative metadata."""
        return AdministrationKeys(
            encryption_private=Jwk(self._env.json(f"{self._app_prefix}ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE")),
            signing_private=Jwk(self._env.json(f"{self._extra_prefix}ADMIN_METADATA_SIGNING_KEY_PRIVATE")),
        )

    @property
    def ADMIN_METADATA_KEYS_RW_SAFE(self) -> str:  # noqa: N802
        """ADMIN_METADATA_KEYS_RW with value redacted."""
        return self._safe_value if self.ADMIN_METADATA_KEYS_RW.signing_private else ""

    @property
    def AGOL_CLIENT_ID(self) -> str:  # noqa: N802
        """Client ID for ArcGIS Online OAuth developer credential for accessing/updating item metadata."""
        with self._env.prefixed(self._extra_prefix), self._env.prefixed("AGOL_CLIENT_"):
            return self._env.str("ID")

    @property
    def AGOL_CLIENT_SECRET(self) -> str:  # noqa: N802
        """Secret for ArcGIS Online OAuth developer credential for accessing/updating item metadata."""
        with self._env.prefixed(self._extra_prefix), self._env.prefixed("AGOL_CLIENT_"):
            return self._env.str("SECRET")

    @property
    def AGOL_CLIENT_SECRET_SAFE(self) -> str:  # noqa: N802
        """AGOL_CLIENT_SECRET with value redacted."""
        return self._safe_value if self.AGOL_CLIENT_SECRET else ""
