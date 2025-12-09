import os
import pickle
from importlib.metadata import version
from pathlib import Path
from typing import Any
from unittest.mock import PropertyMock

import pytest
from pytest_mock import MockerFixture

from lantern.config import Config, ConfigurationError


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

    def test_pickle(self, fx_config: Config, mocker: MockerFixture):
        """Config can be pickled and unpickled."""
        result = pickle.dumps(fx_config, pickle.HIGHEST_PROTOCOL)
        config = pickle.loads(result)  # noqa: S301
        assert config.dumps_safe() == fx_config.dumps_safe()

    def test_version(self):
        """Version is read from package metadata."""
        config = Config()
        assert version("lantern") == config.VERSION

    def test_dumps_safe(self, fx_package_version: str, fx_config: Config):
        """
        Config can be exported to a dict with sensitive values redacted.

        `EXPORTER_DATA_CATALOGUE_SENTRY_SRC` uses a real value for e2e tests.
        """
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
            "ADMIN_METADATA_SIGNING_KEY_PUBLIC": fx_config.ADMIN_METADATA_SIGNING_KEY_PUBLIC.to_json(compact=True),
            "ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE": redacted_value,
            "STORE_GITLAB_ENDPOINT": "https://gitlab.example.com",
            "STORE_GITLAB_TOKEN": redacted_value,
            "STORE_GITLAB_PROJECT_ID": "1234",
            "STORE_GITLAB_BRANCH": "main",
            "STORE_GITLAB_CACHE_PATH": str(fx_config.STORE_GITLAB_CACHE_PATH),
            "TEMPLATES_CACHE_BUST_VALUE": fx_config.TEMPLATES_CACHE_BUST_VALUE,
            "TEMPLATES_SENTRY_SRC": "https://js.sentry-cdn.com/7ee10f6777ab8ec05ffe8b84c4c3039e.min.js",
            "TEMPLATES_PLAUSIBLE_DOMAIN": "x",
            "TEMPLATES_ITEM_MAPS_ENDPOINT": "https://embedded-maps.data.bas.ac.uk/v1",
            "TEMPLATES_ITEM_CONTACT_ENDPOINT": "https://example.com/contact",
            "TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY": "x",
            "TEMPLATES_ITEM_VERSIONS_ENDPOINT": "x",
            "BASE_URL": "https://x",
            "EXPORT_PATH": str(fx_config.EXPORT_PATH),
            "AWS_S3_BUCKET": "x",
            "AWS_ACCESS_ID": "x",
            "AWS_ACCESS_SECRET": redacted_value,
            "VERIFY_SHAREPOINT_PROXY_ENDPOINT": "x",
            "VERIFY_SAN_PROXY_ENDPOINT": "x",
        }

        _signing_key_public = "ADMIN_METADATA_SIGNING_KEY_PUBLIC"
        output = fx_config.dumps_safe()
        # noinspection PyUnresolvedReferences
        output[_signing_key_public] = output[_signing_key_public].to_json(compact=True)

        assert output == expected
        assert len(output["EXPORT_PATH"]) > 0
        assert len(output["STORE_GITLAB_CACHE_PATH"]) > 0
        assert len(output["TEMPLATES_CACHE_BUST_VALUE"]) > 0

    def test_validate(self, fx_config: Config):
        """Valid configuration is ok."""
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
                    "LANTERN_STORE_GITLAB_BRANCH": "x",
                    "LANTERN_STORE_GITLAB_CACHE_PATH": "x",
                }
            ),
            (
                {
                    "LANTERN_STORE_GITLAB_ENDPOINT": "x",
                    "LANTERN_STORE_GITLAB_TOKEN": None,
                    "LANTERN_STORE_GITLAB_PROJECT_ID": "x",
                    "LANTERN_STORE_GITLAB_BRANCH": "x",
                    "LANTERN_STORE_GITLAB_CACHE_PATH": "x",
                }
            ),
            (
                {
                    "LANTERN_STORE_GITLAB_ENDPOINT": "x",
                    "LANTERN_STORE_GITLAB_TOKEN": "x",
                    "LANTERN_STORE_GITLAB_PROJECT_ID": None,
                    "LANTERN_STORE_GITLAB_BRANCH": "x",
                    "LANTERN_STORE_GITLAB_CACHE_PATH": "x",
                }
            ),
            (
                {
                    "LANTERN_STORE_GITLAB_ENDPOINT": "x",
                    "LANTERN_STORE_GITLAB_TOKEN": "x",
                    "LANTERN_STORE_GITLAB_PROJECT_ID": "x",
                    "LANTERN_STORE_GITLAB_BRANCH": None,
                    "LANTERN_STORE_GITLAB_CACHE_PATH": "x",
                }
            ),
            (
                {
                    "LANTERN_STORE_GITLAB_ENDPOINT": "x",
                    "LANTERN_STORE_GITLAB_TOKEN": "x",
                    "LANTERN_STORE_GITLAB_PROJECT_ID": "x",
                    "LANTERN_STORE_GITLAB_BRANCH": "x",
                    "LANTERN_STORE_GITLAB_CACHE_PATH": None,
                }
            ),
            (
                {
                    "LANTERN_TEMPLATES_PLAUSIBLE_DOMAIN": None,
                    "LANTERN_TEMPLATES_ITEM_CONTACT_ENDPOINT": "x",
                    "LANTERN_TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY": "x",
                    "LANTERN_TEMPLATES_ITEM_VERSIONS_ENDPOINT": "x",
                }
            ),
            (
                {
                    "LANTERN_TEMPLATES_PLAUSIBLE_DOMAIN": "x",
                    "LANTERN_TEMPLATES_ITEM_CONTACT_ENDPOINT": None,
                    "LANTERN_TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY": "x",
                    "LANTERN_TEMPLATES_ITEM_VERSIONS_ENDPOINT": "x",
                }
            ),
            (
                {
                    "LANTERN_TEMPLATES_PLAUSIBLE_DOMAIN": "x",
                    "LANTERN_TEMPLATES_ITEM_CONTACT_ENDPOINT": "x",
                    "LANTERN_TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY": None,
                    "LANTERN_TEMPLATES_ITEM_VERSIONS_ENDPOINT": "x",
                }
            ),
            (
                {
                    "LANTERN_TEMPLATES_PLAUSIBLE_DOMAIN": "x",
                    "LANTERN_TEMPLATES_ITEM_CONTACT_ENDPOINT": "x",
                    "LANTERN_TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY": "x",
                    "LANTERN_TEMPLATES_ITEM_VERSIONS_ENDPOINT": None,
                }
            ),
            ({"LANTERN_EXPORT_PATH": None}),
            ({"LANTERN_AWS_S3_BUCKET": None, "LANTERN_AWS_ACCESS_ID": "x", "LANTERN_AWS_ACCESS_SECRET": "x"}),
            ({"LANTERN_AWS_S3_BUCKET": "x", "LANTERN_AWS_ACCESS_ID": None, "LANTERN_AWS_ACCESS_SECRET": "x"}),
            ({"LANTERN_AWS_S3_BUCKET": "x", "LANTERN_AWS_ACCESS_ID": "x", "LANTERN_AWS_ACCESS_SECRET": None}),
            ({"LANTERN_VERIFY_SHAREPOINT_PROXY_ENDPOINT": None, "LANTERN_VERIFY_SAN_PROXY_ENDPOINT": "x"}),
            ({"LANTERN_VERIFY_SHAREPOINT_PROXY_ENDPOINT": "x", "LANTERN_VERIFY_SAN_PROXY_ENDPOINT": None}),
        ],
    )
    def test_validate_missing_required_option(self, envs: dict):
        """Validation fails where a required provider or exporter config option is missing."""
        envs_bck = self._set_envs(envs)

        config = Config(read_env=False)

        with pytest.raises(ConfigurationError):
            config.validate()

        self._unset_envs(envs, envs_bck)

    def test_validate_invalid_logging_level(self):
        """Validation fails where logging level is invalid."""
        envs = {"LANTERN_LOG_LEVEL": "INVALID"}
        envs_bck = self._set_envs(envs)

        config = Config(read_env=False)

        with pytest.raises(ConfigurationError):
            _ = config.LOG_LEVEL

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize("env", ["LANTERN_STORE_GITLAB_CACHE_PATH", "LANTERN_EXPORT_PATH"])
    def test_validate_invalid_path(self, env: str):
        """Validation fails where required path is invalid."""
        envs = {env: str(Path(__file__).resolve())}
        envs_bck = self._set_envs(envs)

        config = Config(read_env=False)

        with pytest.raises(ConfigurationError):
            config.validate()

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        ("property_name", "expected", "sensitive"),
        [
            ("PARALLEL_JOBS", 2, False),
            ("ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE", JWK, True),
            ("ADMIN_METADATA_SIGNING_KEY_PUBLIC", JWK, False),
            ("STORE_GITLAB_ENDPOINT", "x", False),
            ("STORE_GITLAB_TOKEN", "x", True),
            ("STORE_GITLAB_PROJECT_ID", "x", False),
            ("STORE_GITLAB_BRANCH", "x", False),
            ("STORE_GITLAB_CACHE_PATH", Path("x").resolve(), False),
            ("TEMPLATES_PLAUSIBLE_DOMAIN", "x", False),
            ("TEMPLATES_ITEM_CONTACT_ENDPOINT", "x", False),
            ("TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY", "x", False),
            ("TEMPLATES_ITEM_VERSIONS_ENDPOINT", "x", False),
            ("EXPORT_PATH", Path("x").resolve(), False),
            ("AWS_S3_BUCKET", "x", False),
            ("AWS_ACCESS_ID", "x", False),
            ("AWS_ACCESS_SECRET", "x", True),
            ("VERIFY_SHAREPOINT_PROXY_ENDPOINT", "x", False),
            ("VERIFY_SAN_PROXY_ENDPOINT", "x", False),
        ],
    )
    def test_configurable_property(self, property_name: str, expected: Any, sensitive: bool):
        """
        Configurable properties can be accessed.

        Note: `ENABLE_FEATURE_SENTRY` and `SENTRY_ENVIRONMENT` are not tested here.
        """
        envs = {f"LANTERN_{property_name}": str(expected)}
        envs_bck = self._set_envs(envs)
        config = Config()

        assert getattr(config, property_name) == expected
        if sensitive:
            assert getattr(config, f"{property_name}_SAFE") == config._safe_value

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize("property_name", ["STORE_GITLAB_TOKEN", "AWS_ACCESS_SECRET"])
    def test_redacted_property(self, mocker: MockerFixture, property_name: str):
        """Redacted values only return value if secret value has value."""
        for has_value in [True, False]:
            value = "x" if has_value else None
            expected = "[**REDACTED**]" if has_value else ""
            config = Config()
            mocker.patch.object(type(config), property_name, new_callable=PropertyMock, return_value=value)

            assert getattr(config, f"{property_name}_SAFE") == expected
