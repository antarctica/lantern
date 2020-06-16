import logging
import os

import simplejson as json
import pkg_resources

from typing import Dict
from pathlib import Path

from flask.cli import load_dotenv
from msal import PublicClientApplication
from sentry_sdk.integrations.flask import FlaskIntegration
from str2bool import str2bool

from bas_style_kit_jinja_templates import BskTemplates


class Config:
    """
    Flask configuration base class

    Includes a mixture of static and dynamic configuration options. Dynamic objects are typically set from environment
    variables (set directly or through environment files).

    See the project README for configuration option details.
    """

    ENV = os.environ.get("FLASK_ENV")
    DEBUG = False
    TESTING = False

    NAME = "scar-add-metadata-toolbox"

    LOGGING_LEVEL = logging.WARNING

    def __init__(self):
        load_dotenv()

        self.APP_ENABLE_FILE_LOGGING = str2bool(os.environ.get("APP_ENABLE_FILE_LOGGING")) or False
        self.APP_ENABLE_SENTRY = str2bool(os.environ.get("APP_ENABLE_SENTRY")) or True

        self.LOG_FORMAT = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
        self.LOG_FILE_PATH = Path(os.environ.get("APP_LOG_FILE_PATH") or "/var/log/app/app.log")

        self.SENTRY_DSN = os.environ.get("SENTRY_DSN") or None

        self.APP_AUTH_SESSION_FILE_PATH = Path.home().joinpath(".config/scar_add_metadata_toolbox/auth.json")
        if "APP_AUTH_SESSION_FILE_PATH" in os.environ:
            self.APP_AUTH_SESSION_FILE_PATH = Path(os.environ.get("APP_AUTH_SESSION_FILE_PATH"))
        self.AUTH_CLIENT_SCOPES = []
        if "AUTH_CLIENT_SCOPES" in os.environ:
            self.AUTH_CLIENT_SCOPES = str(os.environ.get("AUTH_CLIENT_SCOPES")).split(" ")
        self.AUTH_CLIENT_TENANCY = os.environ.get("AUTH_CLIENT_TENANCY") or None
        self.AUTH_CLIENT_ID = os.environ.get("AUTH_CLIENT_ID") or None

        self.AZURE_OAUTH_TENANCY = os.environ.get("AUTH_SERVER_TENANCY") or None
        self.AZURE_OAUTH_APPLICATION_ID = os.environ.get("AUTH_SERVER_ID") or None
        self.AZURE_OAUTH_CLIENT_APPLICATION_IDS = [self.AUTH_CLIENT_ID]

        self.CSW_ENDPOINT_UNPUBLISHED = os.environ.get("CSW_ENDPOINT_UNPUBLISHED") or "http://app:9000/csw/unpublished"
        self.CSW_ENDPOINT_PUBLISHED = os.environ.get("CSW_ENDPOINT_PUBLISHED") or "http://app:9000/csw/published"

        self.CSW_CONFIG_UNPUBLISHED = {
            "server": {
                "url": os.environ.get("CSW_ENDPOINT_UNPUBLISHED") or "http://app:9000/csw/unpublished",
                "mimetype": "application/xml; charset=UTF-8",
                "encoding": "UTF-8",
                "language": "en-GB",
                "maxrecords": "100",
                "loglevel": "DEBUG",
                "logfile": os.environ.get("APP_CSW_LOG_FILE_PATH") or "/var/log/app/csw-unpublished.log",
                "pretty_print": "true",
                "gzip_compresslevel": "8",
                "domainquerytype": "list",
                "domaincounts": "false",
                "profiles": "apiso",
            },
            "manager": {"transactions": "true", "allowed_ips": "*.*.*.*",},
            "metadata:main": {
                "identification_title": "Internal CSW (Unpublished)",
                "identification_abstract": "Internal PyCSW OGC CSW server for unpublished records",
                "identification_keywords": "catalogue, discovery, metadata",
                "identification_keywords_type": "theme",
                "identification_fees": "None",
                "identification_accessconstraints": "None",
                "provider_name": "British Antarctic Survey",
                "provider_url": "https://www.bas.ac.uk/",
                "contact_name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                "contact_position": "Technical Contact",
                "contact_address": "British Antarctic Survey, Madingley Road, High Cross",
                "contact_city": "Cambridge",
                "contact_stateorprovince": "Cambridgeshire",
                "contact_postalcode": "CB30ET",
                "contact_country": "United Kingdom",
                "contact_phone": "+44(0) 1223 221400",
                "contact_email": "magic @ bas.ac.uk",
                "contact_url": "https://www.bas.ac.uk/team/magic",
                "contact_hours": "07:00 - 19:00",
                "contact_instructions": "During hours of service on weekdays. Best efforts support only.",
                "contact_role": "pointOfContact",
            },
            "repository": {"database": os.environ.get("CSW_UNPUBLISHED_DB_CONNECTION"), "table": "records_unpublished"},
            "metadata:inspire": {
                "enabled": "true",
                "languages_supported": "eng",
                "default_language": "eng",
                "date": "YYYY-MM-DD",
                "gemet_keywords": "Utility and governmental services",
                "conformity_service": "notEvaluated",
                "contact_name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                "contact_email": "magic@bas.ac.uk",
                "temp_extent": "YYYY-MM-DD/YYYY-MM-DD",
            },
        }
        self.CSW_CONFIG_PUBLISHED = {
            "server": {
                "url": os.environ.get("CSW_ENDPOINT_PUBLISHED") or "http://app:9000/csw/published",
                "mimetype": "application/xml; charset=UTF-8",
                "encoding": "UTF-8",
                "language": "en-GB",
                "maxrecords": "100",
                "loglevel": "DEBUG",
                "logfile": os.environ.get("APP_CSW_LOG_FILE_PATH") or "/var/log/app/csw-published.log",
                "pretty_print": "true",
                "gzip_compresslevel": "8",
                "domainquerytype": "list",
                "domaincounts": "false",
                "profiles": "apiso",
            },
            "manager": {"transactions": "true", "allowed_ips": "*.*.*.*",},
            "metadata:main": {
                "identification_title": "Internal CSW (Published)",
                "identification_abstract": "Internal PyCSW OGC CSW server for published records",
                "identification_keywords": "catalogue, discovery, metadata",
                "identification_keywords_type": "theme",
                "identification_fees": "None",
                "identification_accessconstraints": "None",
                "provider_name": "British Antarctic Survey",
                "provider_url": "https://www.bas.ac.uk/",
                "contact_name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                "contact_position": "Technical Contact",
                "contact_address": "British Antarctic Survey, Madingley Road, High Cross",
                "contact_city": "Cambridge",
                "contact_stateorprovince": "Cambridgeshire",
                "contact_postalcode": "CB30ET",
                "contact_country": "United Kingdom",
                "contact_phone": "+44(0) 1223 221400",
                "contact_email": "magic @ bas.ac.uk",
                "contact_url": "https://www.bas.ac.uk/team/magic",
                "contact_hours": "07:00 - 19:00",
                "contact_instructions": "During hours of service on weekdays. Best efforts support only.",
                "contact_role": "pointOfContact",
            },
            "repository": {"database": os.environ.get("CSW_PUBLISHED_DB_CONNECTION"), "table": "records_published"},
            "metadata:inspire": {
                "enabled": "true",
                "languages_supported": "eng",
                "default_language": "eng",
                "date": "YYYY-MM-DD",
                "gemet_keywords": "Utility and governmental services",
                "conformity_service": "notEvaluated",
                "contact_name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                "contact_email": "magic@bas.ac.uk",
                "temp_extent": "YYYY-MM-DD/YYYY-MM-DD",
            },
        }

        self.STATIC_BUILD_DIR = os.environ.get("STATIC_BUILD_DIR") or "./build"
        self.STATIC_BUILD_DIR = Path(self.STATIC_BUILD_DIR)
        self.S3_BUCKET = os.environ.get("S3_BUCKET")

        self.BSK_TEMPLATES = BskTemplates()
        self.BSK_TEMPLATES.site_title = "BAS Data Catalogue"
        self.BSK_TEMPLATES.site_description = (
            "Discover data, services and records held by the British Antarctic Survey and UK Polar Data Centre"
        )
        self.BSK_TEMPLATES.bsk_site_nav_brand_text = "BAS Data Catalogue"
        # TODO: Waiting for fix
        # self.BSK_TEMPLATES.bsk_site_development_phase = "experimental"
        self.BSK_TEMPLATES.bsk_site_development_phase = "alpha"
        self.BSK_TEMPLATES.bsk_site_feedback_href = "/feedback"
        self.BSK_TEMPLATES.bsk_site_footer_policies_cookies_href = "/legal/cookies"
        self.BSK_TEMPLATES.bsk_site_footer_policies_copyright_href = "/legal/copyright"
        self.BSK_TEMPLATES.bsk_site_footer_policies_privacy_href = "/legal/privacy"
        # TODO: Waiting for fix
        # self.BSK_TEMPLATES.site_analytics["id"] = "UA-64130716-19"
        self.BSK_TEMPLATES.site_styles.append(
            {
                "href": "https://cdn.web.bas.ac.uk/libs/font-awesome-pro/5.13.0/css/all.min.css",
                "integrity": "sha256-DjbUjEiuM4tczO997cVF1zbf91BC9OzycscGGk/ZKks=",
            }
        )
        self.BSK_TEMPLATES.site_scripts.append(
            {
                "href": "https://browser.sentry-cdn.com/5.15.4/bundle.min.js",
                "integrity": "sha384-Nrg+xiw+qRl3grVrxJtWazjeZmUwoSt0FAVsbthlJ5OMpx0G08bqIq3b/v0hPjhB",
            }
        )
        self.BSK_TEMPLATES.site_scripts.append(
            {
                "href": "https://cdn.web.bas.ac.uk/libs/jquery-sticky-tabs/1.2.0/jquery.stickytabs.js",
                "integrity": "sha256-JjbqQErDTc0GyOlDQLEgyqoC6XR6puR0wIJFkoHp9Fo=",
            }
        )
        self.BSK_TEMPLATES.site_styles.append({"href": "/static/css/app.css"})
        self.BSK_TEMPLATES.site_scripts.append({"href": "/static/js/app.js"})

    # noinspection PyPep8Naming
    @property
    def VERSION(self) -> str:
        return "Unknown"

    # noinspection PyPep8Naming
    @property
    def SENTRY_CONFIG(self) -> Dict:
        return {
            "dsn": self.SENTRY_DSN,
            "integrations": [FlaskIntegration()],
            "environment": self.ENV,
            "release": f"{self.NAME}@{self.VERSION}",
        }

    # noinspection PyPep8Naming
    @property
    def CLIENT_AUTH(self):
        return PublicClientApplication(client_id=self.AUTH_CLIENT_ID, authority=self.AUTH_CLIENT_TENANCY)

    # noinspection PyPep8Naming
    @property
    def CLIENT_AUTH_TOKEN(self):
        client_auth_token = None

        if self.APP_AUTH_SESSION_FILE_PATH.exists():
            with open(str(self.APP_AUTH_SESSION_FILE_PATH), "r") as auth_file:
                client_auth_token = json.load(auth_file)

        return client_auth_token


class ProductionConfig(Config):  # pragma: no cover
    """
    Flask configuration for Production environments

    Note: This method is excluded from test coverage as its meaning would be undermined.
    """

    def __init__(self):
        super().__init__()
        self.APP_ENABLE_FILE_LOGGING = str2bool(os.environ.get("APP_ENABLE_FILE_LOGGING")) or True

    # noinspection PyPep8Naming
    @property
    def VERSION(self) -> str:
        return pkg_resources.require("scar-add-metadata-toolbox")[0].version


class DevelopmentConfig(Config):  # pragma: no cover
    """
    Flask configuration for (local) Development environments

    Note: This method is excluded from test coverage as its meaning would be undermined.
    """

    DEBUG = True

    LOGGING_LEVEL = logging.INFO

    def __init__(self):
        super().__init__()
        self.APP_ENABLE_SENTRY = str2bool(os.environ.get("APP_ENABLE_SENTRY")) or False

    # noinspection PyPep8Naming
    @property
    def VERSION(self) -> str:
        return "N/A"

    @property
    def SENTRY_CONFIG(self) -> Dict:
        _config = super().SENTRY_CONFIG
        _config["server_name"] = "Local container"

        return _config


class TestingConfig(Config):
    """
    Flask configuration for Testing environments
    """

    DEBUG = True
    TESTING = True

    LOGGING_LEVEL = logging.DEBUG

    def __init__(self):
        super().__init__()
        self.APP_ENABLE_FILE_LOGGING = False
        self.APP_ENABLE_SENTRY = False

    # noinspection PyPep8Naming
    @property
    def VERSION(self) -> str:
        return "N/A"
