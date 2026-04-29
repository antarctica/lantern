import os
import pickle
from importlib.metadata import version
from pathlib import Path
from typing import Any
from unittest.mock import PropertyMock

import pytest
from environs.exceptions import EnvError, EnvValidationError
from pytest_mock import MockerFixture

from lantern.config import Config
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys


class TestConfig:
    """Test app config."""

    JWK = '{"kty":"EC","kid":"config_testing_public_key","alg":"ES256","crv":"P-256","x":"nBe5t7mCgi-SWLmVbB9OgYdQBeh3OgymE9xyCsOiy1g","y":"-pGsEOdH-LQc9m8fo3xqwila4z1kdOkQkhBcWUhnAls"}'

    @staticmethod
    def _set_envs(envs: dict) -> dict:
        envs_bck = {}

        for env in envs:
            # backup environment variable if set
            value = os.environ.get(env, None)
            if value is not None:
                envs_bck[env] = value
            # unset environment variable if set
            if env in os.environ:
                del os.environ[env]
            # set environment variable to test value
            if envs[env] is not None:
                os.environ[env] = envs[env]

        return envs_bck

    @staticmethod
    def _unset_envs(envs: dict, envs_bck: dict) -> None:
        # unset environment variable
        for env in envs:
            if env in os.environ:
                del os.environ[env]
        # restore environment variables if set outside of test
        for env in envs:
            if env in envs_bck:
                os.environ[env] = str(envs_bck[env])

    @pytest.mark.cov()
    def test_not_eq(self, fx_config: Config):
        """Cannot compare if non-config instances are equal."""
        assert fx_config != 1

    def test_pickle(self, fx_config: Config):
        """Can pickle and unpickle config."""
        pickled = pickle.dumps(fx_config, pickle.HIGHEST_PROTOCOL)
        result: Config = pickle.loads(pickled)  # noqa: S301
        assert result == fx_config

    def test_version(self):
        """Can get version from package metadata."""
        config = Config()
        assert version("lantern") == config.VERSION

    def test_dumps_safe(self, fx_package_version: str, fx_config: Config):
        """Can export config to a dict safely with sensitive values redacted."""
        redacted_value = "[**REDACTED**]"
        expected: fx_config.ConfigDumpSafe = {
            "NAME": fx_config.NAME,
            "VERSION": fx_package_version,
            "PARALLEL_JOBS": 1,
            "LOG_LEVEL": 20,
            "LOG_LEVEL_NAME": "INFO",
            "SENTRY_DSN": fx_config.SENTRY_DSN,
            "ENABLE_FEATURE_SENTRY": False,  # would be True by default but Sentry disabled in tests
            "SENTRY_ENVIRONMENT": "test",
            "ADMIN_METADATA_KEYS_ENCRYPTION_KEY_PRIVATE": redacted_value,
            "ADMIN_METADATA_KEYS_SIGNING_KEY_PUBLIC": fx_config.ADMIN_METADATA_KEYS.signing_public.to_json(
                compact=True
            ),
            "STORE_GITLAB_ENDPOINT": "https://gitlab.example.com",
            "STORE_GITLAB_TOKEN": redacted_value,
            "STORE_GITLAB_PROJECT_ID": "1234",
            "STORE_GITLAB_DEFAULT_BRANCH": "main",
            "STORE_GITLAB_CACHE_PATH": str(fx_config.STORE_GITLAB_CACHE_PATH),
            "TEMPLATES_CACHE_BUST_VALUE": fx_config.TEMPLATES_CACHE_BUST_VALUE,
            "TEMPLATES_PLAUSIBLE_ID": "x",
            "TEMPLATES_ITEM_MAPS_ENDPOINT": "https://embedded-maps.data.bas.ac.uk/v1",
            "TEMPLATES_ITEM_CONTACT_ENDPOINT": "https://example.com/contact",
            "TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY": "x",
            "TEMPLATES_ITEM_VERSIONS_ENDPOINT": "https://example.com",
            "SITE_UNTRUSTED_S3_BUCKET_TESTING": "x",
            "SITE_UNTRUSTED_S3_BUCKET_LIVE": "x",
            "SITE_UNTRUSTED_S3_ACCESS_ID": "x",
            "SITE_UNTRUSTED_S3_ACCESS_SECRET": redacted_value,
            "SITE_TRUSTED_RSYNC_HOST": "x",
            "SITE_TRUSTED_RSYNC_BASE_PATH_TESTING": str(fx_config.SITE_TRUSTED_RSYNC_BASE_PATH_TESTING),
            "SITE_TRUSTED_RSYNC_BASE_PATH_LIVE": str(fx_config.SITE_TRUSTED_RSYNC_BASE_PATH_LIVE),
            "BASE_URL_TESTING": "https://example.com",
            "BASE_URL_LIVE": "https://example.com",
        }

        output = fx_config.dumps_safe()
        assert output == expected
        assert len(output["STORE_GITLAB_CACHE_PATH"]) > 0
        assert len(output["TEMPLATES_CACHE_BUST_VALUE"]) > 0

    def test_validate(self, fx_config: Config):
        """Can validate config where the configuration is OK."""
        fx_config.validate()

    @pytest.mark.parametrize(
        "envs",
        [
            (
                {
                    "LANTERN_ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE": None,
                    "LANTERN_ADMIN_METADATA_SIGNING_KEY_PUBLIC": "x",
                }
            ),
            (
                {
                    "LANTERN_ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE": "x",
                    "LANTERN_ADMIN_METADATA_SIGNING_KEY_PUBLIC": None,
                }
            ),
            (
                {
                    "LANTERN_STORE_GITLAB_ENDPOINT": None,
                    "LANTERN_STORE_GITLAB_TOKEN": "x",
                    "LANTERN_STORE_GITLAB_PROJECT_ID": "x",
                    "LANTERN_STORE_GITLAB_DEFAULT_BRANCH": "x",
                    "LANTERN_STORE_GITLAB_CACHE_PATH": "x",
                }
            ),
            (
                {
                    "LANTERN_STORE_GITLAB_ENDPOINT": "x",
                    "LANTERN_STORE_GITLAB_TOKEN": None,
                    "LANTERN_STORE_GITLAB_PROJECT_ID": "x",
                    "LANTERN_STORE_GITLAB_DEFAULT_BRANCH": "x",
                    "LANTERN_STORE_GITLAB_CACHE_PATH": "x",
                }
            ),
            (
                {
                    "LANTERN_STORE_GITLAB_ENDPOINT": "x",
                    "LANTERN_STORE_GITLAB_TOKEN": "x",
                    "LANTERN_STORE_GITLAB_PROJECT_ID": None,
                    "LANTERN_STORE_GITLAB_DEFAULT_BRANCH": "x",
                    "LANTERN_STORE_GITLAB_CACHE_PATH": "x",
                }
            ),
            (
                {
                    "LANTERN_STORE_GITLAB_ENDPOINT": "x",
                    "LANTERN_STORE_GITLAB_TOKEN": "x",
                    "LANTERN_STORE_GITLAB_PROJECT_ID": "x",
                    "LANTERN_STORE_GITLAB_DEFAULT_BRANCH": None,
                    "LANTERN_STORE_GITLAB_CACHE_PATH": "x",
                }
            ),
            (
                {
                    "LANTERN_STORE_GITLAB_ENDPOINT": "x",
                    "LANTERN_STORE_GITLAB_TOKEN": "x",
                    "LANTERN_STORE_GITLAB_PROJECT_ID": "x",
                    "LANTERN_STORE_GITLAB_DEFAULT_BRANCH": "x",
                    "LANTERN_STORE_GITLAB_CACHE_PATH": None,
                }
            ),
            (
                {
                    "LANTERN_TEMPLATES_PLAUSIBLE_ID": None,
                    "LANTERN_TEMPLATES_ITEM_CONTACT_ENDPOINT": "x",
                    "LANTERN_TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY": "x",
                    "LANTERN_TEMPLATES_ITEM_VERSIONS_ENDPOINT": "x",
                }
            ),
            (
                {
                    "LANTERN_TEMPLATES_PLAUSIBLE_ID": "x",
                    "LANTERN_TEMPLATES_ITEM_CONTACT_ENDPOINT": None,
                    "LANTERN_TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY": "x",
                    "LANTERN_TEMPLATES_ITEM_VERSIONS_ENDPOINT": "x",
                }
            ),
            (
                {
                    "LANTERN_TEMPLATES_PLAUSIBLE_ID": "x",
                    "LANTERN_TEMPLATES_ITEM_CONTACT_ENDPOINT": "x",
                    "LANTERN_TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY": None,
                    "LANTERN_TEMPLATES_ITEM_VERSIONS_ENDPOINT": "x",
                }
            ),
            (
                {
                    "LANTERN_TEMPLATES_PLAUSIBLE_ID": "x",
                    "LANTERN_TEMPLATES_ITEM_CONTACT_ENDPOINT": "x",
                    "LANTERN_TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY": "x",
                    "LANTERN_TEMPLATES_ITEM_VERSIONS_ENDPOINT": None,
                }
            ),
            (
                {
                    "LANTERN_SITE_UNTRUSTED_S3_BUCKET_TESTING": None,
                    "LANTERN_SITE_UNTRUSTED_S3_BUCKET_LIVE": "x",
                    "LANTERN_SITE_UNTRUSTED_S3_ACCESS_ID": "x",
                    "LANTERN_SITE_UNTRUSTED_S3_ACCESS_SECRET": "x",
                }
            ),
            (
                {
                    "LANTERN_SITE_UNTRUSTED_S3_BUCKET_TESTING": "x",
                    "LANTERN_SITE_UNTRUSTED_S3_BUCKET_LIVE": None,
                    "LANTERN_SITE_UNTRUSTED_S3_ACCESS_ID": "x",
                    "LANTERN_SITE_UNTRUSTED_S3_ACCESS_SECRET": "x",
                }
            ),
            (
                {
                    "LANTERN_SITE_UNTRUSTED_S3_BUCKET_TESTING": "x",
                    "LANTERN_SITE_UNTRUSTED_S3_BUCKET_LIVE": "x",
                    "LANTERN_SITE_UNTRUSTED_S3_ACCESS_ID": None,
                    "LANTERN_SITE_UNTRUSTED_S3_ACCESS_SECRET": "x",
                }
            ),
            (
                {
                    "LANTERN_SITE_UNTRUSTED_S3_BUCKET_TESTING": "x",
                    "LANTERN_SITE_UNTRUSTED_S3_BUCKET_LIVE": "x",
                    "LANTERN_SITE_UNTRUSTED_S3_ACCESS_ID": "x",
                    "LANTERN_SITE_UNTRUSTED_S3_ACCESS_SECRET": None,
                }
            ),
            (
                {
                    "LANTERN_SITE_TRUSTED_RSYNC_HOST": None,
                    "LANTERN_SITE_TRUSTED_RSYNC_BASE_PATH_TESTING": "x",
                    "LANTERN_SITE_TRUSTED_RSYNC_BASE_PATH_LIVE": "x",
                }
            ),
            (
                {
                    "LANTERN_SITE_TRUSTED_RSYNC_HOST": "x",
                    "LANTERN_SITE_TRUSTED_RSYNC_BASE_PATH_TESTING": None,
                    "LANTERN_SITE_TRUSTED_RSYNC_BASE_PATH_LIVE": "x",
                }
            ),
            (
                {
                    "LANTERN_SITE_TRUSTED_RSYNC_HOST": "x",
                    "LANTERN_SITE_TRUSTED_RSYNC_BASE_PATH_TESTING": "x",
                    "LANTERN_SITE_TRUSTED_RSYNC_BASE_PATH_LIVE": None,
                }
            ),
            ({"LANTERN_BASE_URL_TESTING": "x", "LANTERN_BASE_URL_LIVE": None}),
            ({"LANTERN_BASE_URL_TESTING": None, "LANTERN_BASE_URL_LIVE": "x"}),
        ],
    )
    def test_validate_missing_required_option(self, envs: dict):
        """Cannot validate where a required provider or exporter config option is missing."""
        envs_bck = self._set_envs(envs)
        config = Config(read_dotenv=False)

        with pytest.raises(EnvError):
            config.validate()

        self._unset_envs(envs, envs_bck)

    def test_validate_invalid_logging_level(self):
        """Cannot validate where the logging level is invalid."""
        envs = {"LANTERN_LOG_LEVEL": "INVALID"}
        envs_bck = self._set_envs(envs)
        config = Config(read_dotenv=False)

        with pytest.raises(EnvValidationError):
            _ = config.LOG_LEVEL

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize("value", ["0", "-2", "INVALID"])
    def test_validate_invalid_parallel_value(self, value: int | str):
        """Cannot validate where the parallel processing jobs value is invalid."""
        envs = {"LANTERN_PARALLEL_JOBS": value}
        envs_bck = self._set_envs(envs)
        config = Config(read_dotenv=False)

        with pytest.raises(EnvValidationError):
            _ = config.PARALLEL_JOBS

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize("env", ["LANTERN_STORE_GITLAB_CACHE_PATH"])
    def test_validate_invalid_path(self, env: str):
        """Cannot validate where a required path is invalid."""
        envs: dict = {env: str(Path(__file__).resolve())}
        envs_bck = self._set_envs(envs)
        config = Config(read_dotenv=False)

        with pytest.raises(EnvValidationError):
            config.validate()

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        ("property_name", "expected", "sensitive"),
        [
            ("PARALLEL_JOBS", 2, False),
            ("STORE_GITLAB_ENDPOINT", "https://example.com", False),
            ("STORE_GITLAB_TOKEN", "x", True),
            ("STORE_GITLAB_PROJECT_ID", "x", False),
            ("STORE_GITLAB_DEFAULT_BRANCH", "x", False),
            ("STORE_GITLAB_CACHE_PATH", Path("x").resolve(), False),
            ("TEMPLATES_PLAUSIBLE_ID", "x", False),
            ("TEMPLATES_ITEM_CONTACT_ENDPOINT", "https://example.com", False),
            ("TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY", "x", False),
            ("TEMPLATES_ITEM_VERSIONS_ENDPOINT", "https://example.com", False),
            ("SITE_UNTRUSTED_S3_BUCKET_TESTING", "x", False),
            ("SITE_UNTRUSTED_S3_BUCKET_LIVE", "x", False),
            ("SITE_UNTRUSTED_S3_ACCESS_ID", "x", False),
            ("SITE_UNTRUSTED_S3_ACCESS_SECRET", "x", True),
            ("SITE_TRUSTED_RSYNC_HOST", "x", False),
            ("SITE_TRUSTED_RSYNC_BASE_PATH_TESTING", Path("x"), False),
            ("SITE_TRUSTED_RSYNC_BASE_PATH_LIVE", Path("x"), False),
            ("BASE_URL_TESTING", "https://example.com", False),
            ("BASE_URL_LIVE", "https://example.com", False),
        ],
    )
    def test_configurable_property(self, property_name: str, expected: Any, sensitive: bool):
        """
        Can access configurable properties.

        Note: `ENABLE_FEATURE_SENTRY`, `SENTRY_ENVIRONMENT` and `ADMIN_METADATA_KEYS` are not tested here.
        """
        envs = {f"LANTERN_{property_name}": str(expected)}
        envs_bck = self._set_envs(envs)
        config = Config()

        assert getattr(config, property_name) == expected
        if sensitive:
            assert getattr(config, f"{property_name}_SAFE") == config._safe_value

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize("property_name", ["STORE_GITLAB_TOKEN", "SITE_UNTRUSTED_S3_ACCESS_SECRET"])
    def test_redacted_property(self, mocker: MockerFixture, property_name: str):
        """Can only get redacted value where secret values have a value."""
        for has_value in [True, False]:
            value = "x" if has_value else None
            expected = "[**REDACTED**]" if has_value else ""
            config = Config()
            mocker.patch.object(type(config), property_name, new_callable=PropertyMock, return_value=value)

            assert getattr(config, f"{property_name}_SAFE") == expected

    def test_admin_metadata_keys(self, fx_config: Config):
        """Can get administration metadata keys assembled from multiple environment variables."""
        envs = {
            "LANTERN_ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE": str(self.JWK),
            "ADMIN_METADATA_SIGNING_KEY_PUBLIC": str(self.JWK),
        }
        envs_bck = self._set_envs(envs)
        config = Config()

        assert isinstance(config.ADMIN_METADATA_KEYS, AdministrationKeys)

        self._unset_envs(envs, envs_bck)
