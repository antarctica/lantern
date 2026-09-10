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

        DEPOSIT_TENANT_ID: str
        DEPOSIT_CLIENT_ID: str
        DEPOSIT_CLIENT_SECRET: str
        DEPOSIT_SITE_ID: str
        DEPOSIT_LIBRARY_NAME: str
        DEPOSIT_PROXY_URL: str | None

    def dumps_extra(self) -> ConfigDumpSafe:
        """Dump extra config for output to the user with sensitive data redacted."""
        return {
            "ADMIN_METADATA_KEYS_SIGNING_KEY_PUBLIC": self.ADMIN_METADATA_KEYS_RW_SAFE,
            "AGOL_CLIENT_ID": self.AGOL_CLIENT_ID,
            "AGOL_CLIENT_SECRET": self.AGOL_CLIENT_SECRET_SAFE,
            "DEPOSIT_TENANT_ID": self.DEPOSIT_TENANT_ID,
            "DEPOSIT_CLIENT_ID": self.DEPOSIT_CLIENT_ID,
            "DEPOSIT_CLIENT_SECRET": self.DEPOSIT_CLIENT_SECRET_SAFE,
            "DEPOSIT_SITE_ID": self.DEPOSIT_SITE_ID,
            "DEPOSIT_LIBRARY_NAME": self.DEPOSIT_LIBRARY_NAME,
            "DEPOSIT_PROXY_URL": self.DEPOSIT_PROXY_URL,
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

    @property
    def DEPOSIT_TENANT_ID(self) -> str:  # noqa: N802
        """Tenant ID for MAGIC resources Entra app registration for depositing file artefacts."""
        with self._env.prefixed(self._extra_prefix), self._env.prefixed("DEPOSIT_"):
            return self._env.str("TENANT_ID")

    @property
    def DEPOSIT_CLIENT_ID(self) -> str:  # noqa: N802
        """Client ID for MAGIC resources Entra app registration for depositing file artefacts."""
        with self._env.prefixed(self._extra_prefix), self._env.prefixed("DEPOSIT_"):
            return self._env.str("CLIENT_ID")

    @property
    def DEPOSIT_CLIENT_SECRET(self) -> str:  # noqa: N802
        """Secret for MAGIC resources Entra app registration for depositing file artefacts."""
        with self._env.prefixed(self._extra_prefix), self._env.prefixed("DEPOSIT_"):
            return self._env.str("CLIENT_SECRET")

    @property
    def DEPOSIT_CLIENT_SECRET_SAFE(self) -> str:  # noqa: N802
        """DEPOSIT_CLIENT_SECRET with value redacted."""
        return self._safe_value if self.DEPOSIT_CLIENT_SECRET else ""

    @property
    def DEPOSIT_SITE_ID(self) -> str:  # noqa: N802
        """ID for the MAGIC resources SharePoint site for depositing file artefacts."""
        with self._env.prefixed(self._extra_prefix), self._env.prefixed("DEPOSIT_"):
            return self._env.str("SITE_ID")

    @property
    def DEPOSIT_LIBRARY_NAME(self) -> str:  # noqa: N802
        """Library name within the MAGIC resources SharePoint site for depositing file artefacts."""
        with self._env.prefixed(self._extra_prefix), self._env.prefixed("DEPOSIT_"):
            return self._env.str("LIBRARY_NAME")

    @property
    def DEPOSIT_GROUPS_MAPPING(self) -> dict[str, list[str]]:  # noqa: N802
        r"""
        Mapping of well-known group aliases to group ID(s) URL compatible with the MAGIC resources SharePoint site.

        Structured as a JSON encoded object where keys are aliases and values are lists of group IDs.
        E.g. `X_DEPOSIT_GROUPS_MAPPING="{\"x\": [\"123\"]}"`, which is returned as `{'x': ['123']}`.
        """
        with self._env.prefixed(self._extra_prefix), self._env.prefixed("DEPOSIT_"):
            raw = self._env.json("GROUPS_MAPPING", {})
            if not isinstance(raw, dict):
                msg = "Group mapping MUST be a dict."
                raise TypeError(msg) from None
            return raw

    @property
    def DEPOSIT_PROXY_URL(self) -> str | None:  # noqa: N802
        """Optional base URL for MAGIC resources SharePoint access proxy for accessing unrestricted file artefacts."""
        with self._env.prefixed(self._extra_prefix), self._env.prefixed("DEPOSIT_"):
            return self._env.str("PROXY_URL", None)
