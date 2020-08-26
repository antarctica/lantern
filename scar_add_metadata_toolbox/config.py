import logging
import os

from typing import Dict, List
from pathlib import Path

from importlib_metadata import version
from flask.cli import load_dotenv
from msal import PublicClientApplication
from sentry_sdk.integrations.flask import FlaskIntegration
from str2bool import str2bool

from bas_style_kit_jinja_templates import BskTemplates


class Config:
    """
    Flask/App configuration base class

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
    _COLLECTIONS_PATH = Path.home().joinpath(".config/scar_add_metadata_toolbox/collections.json")
    _AUTH_SESSION_FILE_PATH = Path.home().joinpath(".config/scar_add_metadata_toolbox/auth.json")
    _SITE_PATH = Path.home().joinpath(".config/scar_add_metadata_toolbox/_site")

    def __init__(self):
        load_dotenv()

        """
        APP_ENABLE_SENTRY - Whether to enable Sentry error reporting
        
        If true errors and uncaught exceptions will be reported to Sentry. A default value is set on an per-environment 
        basis (off in development/testing) by overriding the attribute, however it can be also be set at runtime.
        """
        self.APP_ENABLE_SENTRY = str2bool(os.environ.get("APP_ENABLE_SENTRY") or self._APP_ENABLE_SENTRY)

        """
        AUTH_SESSION_FILE_PATH - Path to the file used to store authentication information
        
        When ran as a CLI using containers, this application becomes stateless. Therefore user auth information (access 
        token etc.) needs to persisted elsewhere, in this case as a file written to the path set by this config option.
        
        Note: As this file stores authentication information its contents should be considered sensitive, meaning 
        restricted read/write permissions should be set for example. Note that as OAuth is used for authentication, no
        long-lived credentials (e.g. passwords) will be stored in this file.
        """
        self.AUTH_SESSION_FILE_PATH = Path(os.environ.get("APP_AUTH_SESSION_FILE_PATH") or self._AUTH_SESSION_FILE_PATH)

    # noinspection PyPep8Naming
    @property
    def NAME(self) -> str:
        """
        Application/Package name

        :rtype str
        :return: Application name
        """
        return "scar-add-metadata-toolbox"

    # noinspection PyPep8Naming
    @property
    def VERSION(self) -> str:
        """
        Application version

        Taken from the package where possible, otherwise a generic placeholder is used.

        :rtype str
        :return: Application version
        """
        return "Unknown"

    # noinspection PyPep8Naming
    @property
    def LOGGING_LEVEL(self) -> int:
        """
        Application logging level

        Python logging module logging level. If set at runtime, the level set as a descriptive string is mapped to the
        relevant numeric level using the logging level enumeration.

        :rtype int
        :return: Application logging level
        """
        if "APP_LOGGING_LEVEL" in os.environ:  # pragma: no cover
            if os.environ.get("APP_LOGGING_LEVEL") == "debug":
                return logging.DEBUG
            elif os.environ.get("APP_LOGGING_LEVEL") == "info":
                return logging.INFO
            elif os.environ.get("APP_LOGGING_LEVEL") == "warning":
                return logging.WARNING
            elif os.environ.get("APP_LOGGING_LEVEL") == "error":
                return logging.ERROR
            elif os.environ.get("APP_LOGGING_LEVEL") == "critical":
                return logging.CRITICAL

        return self._LOGGING_LEVEL

    # noinspection PyPep8Naming
    @property
    def SENTRY_CONFIG(self) -> Dict:
        """
        Sentry runtime configuration

        Settings used for Sentry, typically reusing other config options. Only relevant if `APP_ENABLE_SENTRY` is True.

        :rtype dict
        :return: Sentry runtime configuration
        """
        return {
            "dsn": "https://db9543e7b68f4b2596b189ff444438e3@o39753.ingest.sentry.io/5197036",
            "integrations": [FlaskIntegration()],
            "environment": self.ENV,
            "release": f"{self.NAME}@{self.VERSION}",
        }

    # noinspection PyPep8Naming
    @property
    def BSK_TEMPLATES(self) -> BskTemplates:
        """
        BAS Style Kit Jinja2 templates configuration

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
    def COLLECTIONS_CONFIG(self) -> dict:
        """
        Collections config

        Configuration for application Collections class instance. See Collections class for details on configuration on
        required/available options

        :rtype dict
        :return: Collections config
        """
        return {"collections_path": Path(os.environ.get("APP_COLLECTIONS_PATH") or self._COLLECTIONS_PATH)}

    # noinspection PyPep8Naming
    @property
    def CSW_CLIENTS_CONFIG(self) -> dict:
        """
        CSW clients config

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
        CSW servers config

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
    def AZURE_OAUTH_TENANCY(self) -> str:
        """
        Azure tenancy (server)

        Tenancy ID for the Azure app registration representing the server/catalogue component of this application.

        Note: This value is not sensitive.

        :rtype str
        :return: Azure tenancy ID
        """
        return "b311db95-32ad-438f-a101-7ba061712a4e"

    # noinspection PyPep8Naming
    @property
    def AZURE_OAUTH_APPLICATION_ID(self) -> str:
        """
        Azure application (server)

        Azure app registration ID for the registration representing the server/catalogue component of this application.

        Note: This value is not sensitive.

        :rtype str
        :return: Azure app registration ID
        """
        return "8b45581e-1b2e-4b8c-b667-e5a1360b6906"

    # noinspection PyPep8Naming
    @property
    def AZURE_OAUTH_CLIENT_APPLICATION_IDS(self) -> List[str]:
        """
        Azure approved applications (server)

        List of of Azure app registrations ID for applications/services (clients) trusted/approved to use the
        server/catalogue component of this application.

        This list automatically includes the app registration representing the client/editor component of this
        application, in addition to these services:

        * 3b864b8d-a6b8-44c1-8468-16f455e5eb4f = BAS Nagios (for uptime/availability monitoring)

        Note: These values are not sensitive.

        :rtype list
        :return: List of approved Azure app registration IDs
        """
        return [self.AUTH_CLIENT_ID, "3b864b8d-a6b8-44c1-8468-16f455e5eb4f"]

    # noinspection PyPep8Naming
    @property
    def AUTH_CLIENT_SCOPES(self) -> List[str]:
        """
        Azure scopes (client)

        List of scopes requested in OAuth authorisation requests to Azure (i.e. sign-in requests).

        These should be scopes always required by this application, rather than scopes needed for specific/privileged
        actions, as these are typically conferred on specific users and will be included as roles in access tokens.

        This scope is very general and is effectively static. Other scopes, needed for publishing records for example,
        are granted to specific users as roles (which the Flask Azure OAuth provider treats as scopes).

        Note: These values are not sensitive.

        :rtype list
        :return: OAuth authorisation request scopes
        """
        return ["api://8bfe65d3-9509-4b0a-acd2-8ce8cdc0c01e/BAS.MAGIC.ADD.Access"]

    # noinspection PyPep8Naming
    @property
    def AUTH_CLIENT_ID(self) -> str:
        """
        Azure application (client)

        Azure app registration ID for the registration representing the client/editor component of this application.

        Note: This value is not sensitive.

        :rtype str
        :return: Azure app registration ID
        """
        return "91c284e7-6522-4eb4-9943-f4ec08e98cb9"

    # noinspection PyPep8Naming
    @property
    def AUTH_CLIENT_TENANCY(self) -> str:
        """
        Azure tenancy (client)

        Tenancy endpoint for the Azure app registration representing the client/editor component of this application.

        Note: This value is not sensitive.

        :rtype str
        :return: Azure tenancy endpoint
        """
        return "https://login.microsoftonline.com/b311db95-32ad-438f-a101-7ba061712a4e"

    # noinspection PyPep8Naming
    @property
    def CLIENT_AUTH(self) -> PublicClientApplication:
        """
        Azure auth provider (client)

        Uses the Microsoft Authentication Library (MSAL) for Python to simplify requesting access tokens from Azure.

        This is used for the client/editor component of this application, which is considered a 'public' client as this
        application runs on the user's device, and therefore isn't confidential.

        Note: The Flask Azure OAuth provider is used for the server/catalogue component, instantiated in the
        application factor method.

        :rtype PublicClientApplication
        :return: Microsoft Authentication Library Public Client application
        """
        return PublicClientApplication(client_id=self.AUTH_CLIENT_ID, authority=self.AUTH_CLIENT_TENANCY)

    # noinspection PyPep8Naming
    @property
    def SITE_PATH(self) -> Path:
        """
        Path to the directory used to store generated static site content

        The contents of this directory should be considered ephemeral and under the exclusive control this application.

        :rtype Path
        :return Site site content path
        """
        return Path(os.environ.get("APP_SITE_PATH") or self._SITE_PATH)

    # noinspection PyPep8Naming
    @property
    def S3_BUCKET(self) -> str:
        return os.environ.get("APP_S3_BUCKET")


class ProductionConfig(Config):  # pragma: no cover
    """
    Flask configuration for Production environments

    Note: This method is excluded from test coverage as its meaning would be undermined.
    """

    # noinspection PyPep8Naming
    @property
    def VERSION(self) -> str:
        return version("scar-add-metadata-toolbox")


class DevelopmentConfig(Config):  # pragma: no cover
    """
    Flask configuration for (local) Development environments

    Note: This method is excluded from test coverage as its meaning would be undermined.
    """

    DEBUG = True

    _APP_ENABLE_SENTRY = False
    _LOGGING_LEVEL = logging.INFO
    _COLLECTIONS_PATH = Path(f"./collections.json")
    _AUTH_SESSION_FILE_PATH = Path("./auth.json")
    _SITE_PATH = Path("./_site")

    def __init__(self):
        """
        Use this method to override property values defined in the config base class.

        For this class, values will typically be local services to ensure production data is not inadvertently modified.
        """
        super().__init__()

        if "CSW_ENDPOINT_UNPUBLISHED" not in os.environ:
            os.environ["CSW_ENDPOINT_UNPUBLISHED"] = "http://app:9000/csw/unpublished"
        if "CSW_ENDPOINT_PUBLISHED" not in os.environ:
            os.environ["CSW_ENDPOINT_PUBLISHED"] = "http://app:9000/csw/published"
        if "CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT" not in os.environ:
            os.environ["CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT"] = "http://app:9000/csw/unpublished"
        if "CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT" not in os.environ:
            os.environ["CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT"] = "http://app:9000/csw/published"

        if "CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION" not in os.environ:
            os.environ[
                "CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION"
            ] = "postgresql://postgres:password@db/postgres"
        if "CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION" not in os.environ:
            os.environ["CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION"] = "postgresql://postgres:password@db/postgres"

    # noinspection PyPep8Naming
    @property
    def VERSION(self) -> str:
        return "N/A"

    @property
    def S3_BUCKET(self) -> str:
        if "S3_BUCKET" in os.environ:
            return os.environ["S3_BUCKET"]
        return "add-catalogue-integration.data.bas.ac.uk"


class TestingConfig(DevelopmentConfig):
    """
    Flask configuration for Testing environments
    """

    TESTING = True

    _LOGGING_LEVEL = logging.DEBUG

    def __init__(self):
        """
        Use this method to override property values defined in the config base class.

        For this class, values will typically be generic or intentionally wrong to ensure components are mocked
        correctly or production data is not inadvertently modified.
        """
        super().__init__()

        os.environ["CSW_ENDPOINT_UNPUBLISHED"] = "http://example.com/csw/unpublished"
        os.environ["CSW_ENDPOINT_PUBLISHED"] = "http://example.com/csw/published"
        os.environ["CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT"] = "http://example.com/csw/unpublished"
        os.environ["CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT"] = "http://example.com/csw/published"

        os.environ[
            "CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION"
        ] = "postgresql://postgres:password@example/postgres"
        os.environ[
            "CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION"
        ] = "postgresql://postgres:password@example/postgres"

        os.environ["S3_BUCKET"] = "example"
