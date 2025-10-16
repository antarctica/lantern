from dataclasses import dataclass

from jwskate import JweCompact, Jwk, JwtSigner

from lantern.lib.metadata_library.models.record.elements.administration import Administration
from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.kv import get_kv, set_kv


class AdministrativeMetadataSubjectMismatchError(Exception):
    """Raised when administrative metadata does not relate to discovery metadata for the same resource."""

    pass


class AdministrativeMetadataIntegrityError(Exception):
    """Raised when administrative metadata ID does not match the subject of a JWT."""

    pass


@dataclass(kw_only=True)
class AdministrationKeys:
    """
    Encryption and signing keys for administrative metadata.

    One of the public or private signing key is needed depending on whether metadata needs verification and/or signing.
    """

    encryption_private: Jwk
    signing_public: Jwk | None = None
    signing_private: Jwk | None = None

    def __post_init__(self) -> None:
        """Validate."""
        if self.signing_public is None and self.signing_private is None:
            msg = "Public or private signing_key must be provided."
            raise ValueError(msg) from None
        if self.signing_public is None and self.signing_private is not None:
            self.signing_public = self.signing_private.public_jwk()

    def dumps_json(self) -> dict[str, str]:
        """Dump keys as JSON."""
        keys_json = {
            "encryption_private": self.encryption_private.to_json(),
            "signing_public": self.signing_public.to_json(),
        }
        if self.signing_private:
            keys_json["signing_private"] = self.signing_private.to_json()
        return keys_json


class AdministrationWrapper:
    """
    Wrapper for encrypting/decrypting and signing/verifying Administrative Metadata.

    Administrative metadata is signed and encrypted as a JWT within a JWE using compact serialization.

    The JWT provides integrity protection via signing with an asymmetric key (allowing applications to verify metadata
    without being able to modify it). The JWE wrapper provides confidentiality via encryption with a symmetric key.

    Administrative metadata is included in the JWT using a custom 'pyd' (payload) claim.

    This class checks the metadata ID corresponds to the JWT subject (internal integrity). It does not check admin
    metadata relates to discovery metadata.
    """

    _issuer = "magic.data.bas.ac.uk"
    _audience = "data.bas.ac.uk"
    _lifetime = 3_153_600_000  # 100 years
    _enc_alg = "A256GCM"

    def __init__(self, keys: AdministrationKeys) -> None:
        self._keys = keys

    def encode(self, metadata: Administration) -> str:
        """
        Sign and encrypt metadata.

        The JWT is signed using the private signing key (for anyone to then verify).
        The JWE is encrypted using the public encryption key (for only us to read).
        """
        if self._keys.signing_private is None:
            msg = "Private signing key is required for writing metadata."
            raise ValueError(msg) from None
        signer = JwtSigner(issuer=self._issuer, key=self._keys.signing_private, default_lifetime=self._lifetime)
        token: JweCompact = signer.sign(
            subject=metadata.id, audience=self._audience, extra_claims={"pyd": metadata.dumps_json()}
        ).encrypt(key=self._keys.encryption_private.public_jwk(), enc=self._enc_alg)
        return str(token)

    def decode(self, encrypted_metadata: str) -> Administration:
        """Decrypt and verify metadata."""
        token = JweCompact(encrypted_metadata)
        trusted_token = token.decrypt_jwt(self._keys.encryption_private)
        trusted_token.validate(key=self._keys.signing_public, issuer=self._issuer, audience=self._audience)
        value = Administration.loads_json(trusted_token.claims["pyd"])
        if trusted_token.subject != value.id:
            raise AdministrativeMetadataIntegrityError() from None
        return value


def get_admin(keys: AdministrationKeys, record: Record) -> Administration | None:
    """

    Get administrative metadata for record if available.

    Checks loaded administrative metadata relates to parent discovery metadata record via resource (file) identifier.
    """
    kv = get_kv(record)
    raw_value: str | None = kv.get("administrative_metadata", None)
    if raw_value is None:
        return None

    loader = AdministrationWrapper(keys)
    value = loader.decode(raw_value)
    if value.id != record.file_identifier:
        raise AdministrativeMetadataSubjectMismatchError() from None
    return value


def set_admin(keys: AdministrationKeys, record: Record, admin_meta: Administration) -> None:
    """Set administrative metadata for record."""
    if admin_meta.id != record.file_identifier:
        raise AdministrativeMetadataSubjectMismatchError() from None
    wrapper = AdministrationWrapper(keys=keys)
    token = wrapper.encode(admin_meta)
    set_kv(kv={"administrative_metadata": token}, record=record)
