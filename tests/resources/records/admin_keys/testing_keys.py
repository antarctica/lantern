import os
import tomllib
from pathlib import Path

from environs import Env
from jwskate import Jwk

from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys


def _make_keys(base_path: Path) -> None:
    """Generate keys."""
    signing_key_private = Jwk.generate(alg="ES256", kid="magic_metadata_testing_signing_key")
    signing_key_public = signing_key_private.public_jwk()
    encryption_key_private = Jwk.generate(
        alg="ECDH-ES+A128KW", crv="P-256", kid="magic_metadata_testing_encryption_key"
    )

    keys = [
        (
            "Signing Key (private)",
            signing_key_private,
            base_path / "signing_key_private.json",
            "X_ADMIN_METADATA_SIGNING_KEY_PRIVATE",
        ),
        (
            "Signing Key (public)",
            signing_key_public,
            base_path / "signing_key_public.json",
            "LANTERN_ADMIN_METADATA_SIGNING_KEY_PUBLIC",
        ),
        (
            "Encryption Key",
            encryption_key_private,
            base_path / "encryption_key_private.json",
            "LANTERN_ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE",
        ),
    ]
    for key in keys:
        label, jwk, path, env_var = key
        if path.exists():
            print(f"{label} exists at: '{path.resolve()}'")
        else:
            with path.open("w") as f:
                f.write(jwk.to_json(indent=2))
                print(f"{label} written to: '{path.resolve()}'")
            env_value = jwk.to_json(compact=True).replace('"', '\\"')
            print("Set in pyproject.toml 'tool.pytest_env' section as:")
            print(f'{env_var} = "{env_value}"')


def _find_pyproject_path() -> Path | None:
    """Try and find pyproject.toml file."""
    path = Path(__file__).parent
    for parent in [path, *list(path.parents)]:
        pyproject = parent / "pyproject.toml"
        if pyproject.exists():
            return pyproject
    return None


def _load_pytest_env() -> None:
    """Adapted from pytest_env plugin to load env values from pyproject.toml."""
    allow_list = [
        "LANTERN_ADMIN_METADATA_SIGNING_KEY_PUBLIC",
        "X_ADMIN_METADATA_SIGNING_KEY_PRIVATE",
        "LANTERN_ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE",
    ]
    pyproject_path = _find_pyproject_path()
    if pyproject_path and pyproject_path.exists():
        with pyproject_path.open("rb") as file_handler:
            config = tomllib.load(file_handler)
            if "tool" in config and "pytest_env" in config["tool"]:
                for key, entry in config["tool"]["pytest_env"].items():
                    if key not in allow_list:
                        continue
                    value = str(entry["value"]) if isinstance(entry, dict) else str(entry)
                    os.environ[key] = value


def load_keys() -> AdministrationKeys:
    """Load keys from env variables."""
    _load_pytest_env()
    env = Env()

    keys = AdministrationKeys(
        signing_public=Jwk(env.json("LANTERN_ADMIN_METADATA_SIGNING_KEY_PUBLIC")),
        signing_private=Jwk(env.json("X_ADMIN_METADATA_SIGNING_KEY_PRIVATE")),
        encryption_private=Jwk(env.json("LANTERN_ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE")),
    )

    if keys.encryption_private.kid != "magic_metadata_testing_encryption_key":
        msg = "Incorrect encryption key loaded, check pytest_env values are loaded."
        raise ValueError(msg) from None
    if keys.signing_private.kid != "magic_metadata_testing_signing_key":
        msg = "Incorrect signing key loaded, check pytest_env values are loaded."
        raise ValueError(msg) from None

    return keys


def main() -> None:
    """Entrypoint."""
    base_path = Path(__file__).parent
    _make_keys(base_path)


if __name__ == "__main__":
    main()
