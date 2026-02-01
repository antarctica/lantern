from pathlib import Path
from typing import TypedDict

from environs import EnvError
from jwskate import Jwk

from lantern.config import Config
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys


class ExtraConfig(Config):
    """Additional config options needed for tasks."""

    def __init__(self, read_env: bool = True) -> None:
        super().__init__(read_env)
        self._extra_prefix = "X_"
        self._none_value = "[**NOT SET**]"

    class ConfigDumpSafe(TypedDict):
        """Types and keys for `dumps_extra`."""

        ADMIN_METADATA_KEYS_SIGNING_KEY_PUBLIC: str
        TRUSTED_UPLOAD_HOST: str
        TRUSTED_UPLOAD_PATH: str

    def dumps_extra(self) -> ConfigDumpSafe:
        """Dump extra config for output to the user with sensitive data redacted."""
        _trusted_host: str = self.TRUSTED_UPLOAD_HOST if self.TRUSTED_UPLOAD_HOST is not None else self._none_value
        return {
            "ADMIN_METADATA_KEYS_SIGNING_KEY_PUBLIC": self.ADMIN_METADATA_KEYS_RW_SAFE,
            "TRUSTED_UPLOAD_HOST": _trusted_host,
            "TRUSTED_UPLOAD_PATH": str(self.TRUSTED_UPLOAD_PATH.resolve()),
        }

    @property
    def ADMIN_METADATA_KEYS_RW(self) -> AdministrationKeys:  # noqa: N802
        """JSON Web Keys for encrypting and signing administrative metadata."""
        return AdministrationKeys(
            encryption_private=Jwk(self.env.json(f"{self._app_prefix}ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE")),
            signing_private=Jwk(self.env.json(f"{self._extra_prefix}ADMIN_METADATA_SIGNING_KEY_PRIVATE")),
        )

    @property
    def ADMIN_METADATA_KEYS_RW_SAFE(self) -> str:  # noqa: N802
        """ADMIN_METADATA_KEYS_RW with value redacted."""
        return self._safe_value if self.ADMIN_METADATA_KEYS_RW.signing_private else ""

    @property
    def TRUSTED_UPLOAD_HOST(self) -> str | None:  # noqa: N802
        try:
            with self.env.prefixed(self._extra_prefix):
                return self.env.str("TRUSTED_UPLOAD_HOST")
        except EnvError:
            return None

    @property
    def TRUSTED_UPLOAD_PATH(self) -> Path:  # noqa: N802
        with self.env.prefixed(self._extra_prefix):
            return self.env.path("TRUSTED_UPLOAD_PATH")
