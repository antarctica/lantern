import logging
import os
from importlib.metadata import version
from pathlib import Path

from bas_style_kit_jinja_templates import BskTemplates
from flask.cli import load_dotenv
from platformdirs import user_config_dir
from str2bool import str2bool


class Config:
    """
    Flask/App configuration base class.

    Configuration options are mostly set using class properties and are typically hard-coded. A limited number of
    options can be set at runtime using environment variables (set directly or through an `.env` file).
    """

    ENV = os.environ.get("FLASK_ENV")
    DEBUG = False
    TESTING = False

    LOG_FORMAT = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"

    # Used as defaults for values that can be set at runtime
    _APP_ENABLE_SENTRY = True
    _LOGGING_LEVEL = logging.WARNING

    def __init__(self) -> None:
        load_dotenv()

        self._app_org = "BAS"
        self._app_package = "scar-add-metadata-toolbox"
        self._app_config = Path(user_config_dir(appauthor=self._app_org, appname=self._app_package))

        """
        APP_ENABLE_SENTRY - Whether to enable Sentry error reporting

        If true errors and uncaught exceptions will be reported to Sentry. A default value is set on an per-environment
        basis (off in development/testing) by overriding the attribute, however it can be also be set at runtime.
        """
        self.APP_ENABLE_SENTRY = str2bool(os.environ.get("APP_ENABLE_SENTRY") or str(self._APP_ENABLE_SENTRY))

    # noinspection PyPep8Naming
    @property
    def NAME(self) -> str:
        """
        Application/Package name.

        :rtype str
        :return: Application name
        """
        return self._app_package

    # noinspection PyPep8Naming
    @property
    def VERSION(self) -> str:
        """
        Application version.

        Taken from the package where possible, otherwise a generic placeholder is used.

        :rtype str
        :return: Application version
        """
        return "Unknown"

    # noinspection PyPep8Naming
    @property
    def LOGGING_LEVEL(self) -> int:
        """
        Application logging level.

        Python logging module logging level. If set at runtime, the level set as a descriptive string is mapped to the
        relevant numeric level using the logging level enumeration.

        :rtype int
        :return: Application logging level
        """
        if "APP_LOGGING_LEVEL" in os.environ:  # pragma: no cover
            if os.environ.get("APP_LOGGING_LEVEL") == "debug":
                return logging.DEBUG
            if os.environ.get("APP_LOGGING_LEVEL") == "info":
                return logging.INFO
            if os.environ.get("APP_LOGGING_LEVEL") == "warning":
                return logging.WARNING
            if os.environ.get("APP_LOGGING_LEVEL") == "error":
                return logging.ERROR
            if os.environ.get("APP_LOGGING_LEVEL") == "critical":
                return logging.CRITICAL

        return self._LOGGING_LEVEL

    # noinspection PyPep8Naming
    @property
    def SENTRY_CONFIG(self) -> dict:
        """
        Sentry runtime configuration.

        Returns empty config if `APP_ENABLE_SENTRY` is False which disables Sentry.

        Note: Sentry DSN values are not sensitive.
        """
        if not self.APP_ENABLE_SENTRY:
            return {}

        return {
            "dsn": "https://db9543e7b68f4b2596b189ff444438e3@o39753.ingest.sentry.io/5197036",
            "environment": self.ENV,
            "release": self.VERSION,
        }

    # noinspection PyPep8Naming
    @property
    def BSK_TEMPLATES(self) -> BskTemplates:
        """
        BAS Style Kit Jinja2 templates configuration.

        Sets relevant configuration options for setting application identity, primary navigation, analytics and
        required CSS styles and JavaScript.

        :rtype BskTemplates
        :return: BAS Style Kit Jinja2 templates configuration
        """
        bsk_templates = BskTemplates()
        bsk_templates.site_title = "BAS Data Catalogue"
        bsk_templates.site_description = (
            "Discover data, services and records held by the British Antarctic Survey and UK Polar Data Centre"
        )
        bsk_templates.bsk_site_nav_brand_text = "BAS Data Catalogue"
        bsk_templates.bsk_site_development_phase = "alpha"
        bsk_templates.bsk_site_feedback_href = "/feedback"
        bsk_templates.bsk_site_footer_policies_cookies_href = "/legal/cookies"
        bsk_templates.bsk_site_footer_policies_copyright_href = "/legal/copyright"
        bsk_templates.bsk_site_footer_policies_privacy_href = "/legal/privacy"
        bsk_templates.site_analytics["id"] = "UA-64130716-19"
        bsk_templates.site_styles.append(
            {
                "href": "https://cdn.web.bas.ac.uk/libs/font-awesome-pro/5.13.0/css/all.min.css",
                "integrity": "sha256-DjbUjEiuM4tczO997cVF1zbf91BC9OzycscGGk/ZKks=",
            }
        )
        bsk_templates.site_scripts.append(
            {
                "href": "https://browser.sentry-cdn.com/5.15.4/bundle.min.js",
                "integrity": "sha384-Nrg+xiw+qRl3grVrxJtWazjeZmUwoSt0FAVsbthlJ5OMpx0G08bqIq3b/v0hPjhB",
            }
        )
        bsk_templates.site_scripts.append(
            {
                "href": "https://cdn.web.bas.ac.uk/libs/jquery-sticky-tabs/1.2.0/jquery.stickytabs.js",
                "integrity": "sha256-JjbqQErDTc0GyOlDQLEgyqoC6XR6puR0wIJFkoHp9Fo=",
            }
        )
        bsk_templates.site_scripts.append(
            {
                "href": "https://cdn.web.bas.ac.uk/libs/markdown-it/11.0.0/js/markdown-it.min.js",
                "integrity": "sha256-3mv+NUxFuBg26MtcnuN2X37WUxuGunWCCiG2YCSBjNc=",
            }
        )
        bsk_templates.site_styles.append({"href": "/static/css/app.css"})
        bsk_templates.site_scripts.append({"href": "/static/js/app.js"})

        return bsk_templates

    # noinspection PyPep8Naming
    @property
    def CSW_CLIENTS_CONFIG(self) -> dict:
        """
        CSW clients config.

        Configuration for CSW clients used in application Repository class instances. See Repository class for details
        on required/available options. This arrangement of configuration options is intended for use with the
        application MirrorRepository class instance.

        :rtype dict
        :return: CSW clients config
        """
        return {
            "unpublished": {"client_config": {"endpoint": os.environ.get("CSW_ENDPOINT_UNPUBLISHED")}},
            "published": {"client_config": {"endpoint": os.environ.get("CSW_ENDPOINT_PUBLISHED")}},
        }

    # noinspection PyPep8Naming
    @property
    def CSW_SERVERS_CONFIG(self) -> dict:
        """
        CSW servers config.

        Configuration for CSW servers/repositories used in CSWServer class instances. See CSWServer class for details on
        required/available options. This arrangement of configuration options is intended for use with the application
        CSWServer class instances set by `scar_add_metadata_toolbox.utils._create_csw_repositories` method.

        :rtype dict
        :return: CSW servers config
        """
        return {
            "unpublished": {
                "endpoint": os.environ.get("CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT"),
                "title": "Internal CSW (Unpublished)",
                "abstract": "Internal PyCSW OGC CSW server for unpublished records",
                "database_connection_string": os.environ.get("CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION"),
                "database_table": "records_unpublished",
                "auth_required_scopes_read": ["BAS.MAGIC.ADD.Records.ReadWrite.All"],
                "auth_required_scopes_write": ["BAS.MAGIC.ADD.Records.ReadWrite.All"],
                "tracking_enabled": True,
                "tracking_working_dir": os.environ.get("CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_WORKING_DIR"),
                "tracking_remote_url": os.environ.get("CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_REMOTE_URL"),
                "tracking_branch": "main",
                "tracking_gitlab_pat": os.environ.get("CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_GITLAB_TOKEN"),
            },
            "published": {
                "endpoint": os.environ.get("CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT"),
                "title": "Internal CSW (Published)",
                "abstract": "Internal PyCSW OGC CSW server for published records",
                "database_connection_string": os.environ.get("CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION"),
                "database_table": "records_published",
                "auth_required_scopes_read": [],
                "auth_required_scopes_write": ["BAS.MAGIC.ADD.Records.Publish.All"],
            },
        }

    # noinspection PyPep8Naming
    @property
    def ENTRA_AUTH_CLIENT_ID(self) -> str:
        """
        Entra application (server).

        Entra app registration ID for the registration representing the server/catalogue component of this application.

        Note: This value is not sensitive.
        """
        return "8b45581e-1b2e-4b8c-b667-e5a1360b6906"

    # noinspection PyPep8Naming
    @property
    def ENTRA_AUTH_OIDC_ENDPOINT(self) -> str:
        """
        Entra OIDC endpoint (server).

        OIDC endpoint for tenancy containing the registration representing the server/catalogue component of this
        application.

        Note: This value is not sensitive.
        """
        return "https://login.microsoftonline.com/b311db95-32ad-438f-a101-7ba061712a4e/v2.0/.well-known/openid-configuration"

    # noinspection PyPep8Naming
    @property
    def MSAL_AUTH_CACHE_PATH(self) -> Path:
        """
        MSAL token cache path.

        Path to a sentinel file MSAL should create for an encrypted token cache.
        """
        return Path(os.environ.get("APP_AUTH_CACHE") or self._app_config / "auth_cache.bin")

    # noinspection PyPep8Naming
    @property
    def MSAL_SCOPES(self) -> list[str]:
        """
        Entra scopes (client).

        List of scopes requested in OAuth authorisation requests to Entra (i.e. sign-in requests).

        These should be scopes always required by this application, rather than scopes needed for specific/privileged
        actions, as these are typically conferred on specific users and will be included as roles in access tokens.

        This scope is very general and is effectively static. Other scopes, needed for publishing records for example,
        are granted to specific users as roles (which the Flask Entra Auth provider treats as scopes).

        Note: These values are not sensitive.
        """
        return ["api://8bfe65d3-9509-4b0a-acd2-8ce8cdc0c01e/BAS.MAGIC.ADD.Access"]

    # noinspection PyPep8Naming
    @property
    def MSAL_CLIENT_ID(self) -> str:
        """
        Entra application (client).

        Entra app registration ID for the registration representing the client/editor component of this application.

        Note: This value is not sensitive.
        """
        return "91c284e7-6522-4eb4-9943-f4ec08e98cb9"

    # noinspection PyPep8Naming
    @property
    def MSAL_TENANCY(self) -> str:
        """
        Entra tenancy (client).

        Entra tenancy containing the Entra app registration representing the client/editor component of this application.

        Note: This value is not sensitive.
        """
        return "b311db95-32ad-438f-a101-7ba061712a4e"

    # noinspection PyPep8Naming
    @property
    def SITE_PATH(self) -> Path:
        """
        Path to the directory used to store generated static site content.

        The contents of this directory should be considered ephemeral and under the exclusive control this application.

        :rtype Path
        :return Site content path
        """
        return Path(os.environ.get("APP_SITE_PATH") or self._app_config / "site")

    # noinspection PyPep8Naming
    @property
    def S3_BUCKET(self) -> str:
        """
        Name of the AWS S3 bucket used to host static site content.

        :rtype str
        :return: S3 bucket name
        """
        return os.environ.get("APP_S3_BUCKET")


class ProductionConfig(Config):  # pragma: no cover
    """
    Flask configuration for Production environments.

    Note: This method is excluded from test coverage as its meaning would be undermined.
    """

    # noinspection PyPep8Naming
    @property
    def VERSION(self) -> str:
        """Application version."""
        return version("scar-add-metadata-toolbox")


class DevelopmentConfig(Config):  # pragma: no cover
    """
    Flask configuration for (local) Development environments.

    Note: This method is excluded from test coverage as its meaning would be undermined.
    """

    DEBUG = True

    _APP_ENABLE_SENTRY = False
    _LOGGING_LEVEL = logging.INFO
    _AUTH_SESSION_FILE_PATH = Path("./auth.json")

    def __init__(self) -> None:
        """
        Use this method to override property values defined in the config base class.

        For this class, values will typically be local services to ensure production data is not inadvertently modified.
        """
        super().__init__()

        if "CSW_ENDPOINT_UNPUBLISHED" not in os.environ:
            os.environ["CSW_ENDPOINT_UNPUBLISHED"] = "http://localhost:5000/csw/unpublished"
        if "CSW_ENDPOINT_PUBLISHED" not in os.environ:
            os.environ["CSW_ENDPOINT_PUBLISHED"] = "http://localhost:5000/csw/published"
        if "CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT" not in os.environ:
            os.environ["CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT"] = "http://localhost:5000/csw/unpublished"
        if "CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT" not in os.environ:
            os.environ["CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT"] = "http://localhost:5000/csw/published"

        if "CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION" not in os.environ:
            os.environ["CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION"] = (
                "postgresql://postgres:password@localhost/postgres"
            )
        if "CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION" not in os.environ:
            os.environ["CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION"] = (
                "postgresql://postgres:password@localhost/postgres"
            )

        if "CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_WORKING_DIR" not in os.environ:
            os.environ["CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_WORKING_DIR"] = str(Path("./_record_revisions"))
        if "CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_REMOTE_URL" not in os.environ:
            os.environ["CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_REMOTE_URL"] = (
                "https://gitlab.data.bas.ac.uk/felnne/add-catalogue-integration-records.git"
            )

        if "APP_S3_BUCKET" not in os.environ:
            os.environ["APP_S3_BUCKET"] = "add-catalogue-integration.data.bas.ac.uk"

    # noinspection PyPep8Naming
    @property
    def VERSION(self) -> str:
        """Application version."""
        return "N/A"


class TestingConfig(DevelopmentConfig):
    """Flask configuration for Testing environments."""

    TESTING = True

    _LOGGING_LEVEL = logging.DEBUG

    def __init__(self) -> None:
        """
        Use this method to override property values defined in the config base class.

        For this class, values will typically be generic or intentionally wrong to ensure components are mocked
        correctly or production data is not inadvertently modified.
        """
        super().__init__()

        os.environ["CSW_ENDPOINT_UNPUBLISHED"] = "https://example.com/csw/unpublished"
        os.environ["CSW_ENDPOINT_PUBLISHED"] = "https://example.com/csw/published"
        os.environ["CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT"] = "https://example.com/csw/unpublished"
        os.environ["CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT"] = "https://example.com/csw/published"

        os.environ["CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION"] = (
            "postgresql://postgres:password@example/postgres"
        )
        os.environ["CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION"] = (
            "postgresql://postgres:password@example/postgres"
        )

        os.environ["S3_BUCKET"] = "example"
