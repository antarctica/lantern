from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from jwskate import JweCompact, JwtSigner
from tasks._config import ExtraConfig

# Troubleshooting task to check administration metadata keys work.


def encode(keys: AdministrationKeys, cleartext: str) -> str:
    """
    Sign and encrypt value.

    The JWT is signed using the private signing key (for anyone to then verify).
    The JWE is encrypted using the public encryption key (for only us to read).
    """
    if keys.signing_private is None:
        msg = "Private signing key is required."
        raise ValueError(msg) from None
    signer = JwtSigner(issuer="x", key=keys.signing_private, default_lifetime=3_153_600_000)
    token: JweCompact = signer.sign(subject="x", audience="x", extra_claims={"pyd": cleartext}).encrypt(
        key=keys.encryption_private.public_jwk(), enc="A256GCM"
    )
    return str(token)


def decode(keys: AdministrationKeys, ciphertext: str) -> str:
    """Decrypt and verify value."""
    token = JweCompact(ciphertext)
    trusted_token = token.decrypt_jwt(keys.encryption_private)
    trusted_token.validate(key=keys.signing_public, issuer="x", audience="x")
    return trusted_token.claims["pyd"]


def main() -> None:
    """Entrypoint."""
    config = ExtraConfig()
    keys = config.ADMIN_METADATA_KEYS_RW
    value = "x"

    ciphertext = encode(keys, value)
    result = decode(keys, ciphertext)
    if value != result:
        msg = f"'{result} != '{value}' (result, expected)"
        raise ValueError(msg) from None


if __name__ == "__main__":
    main()
