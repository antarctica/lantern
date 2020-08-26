import os
import json
from base64 import urlsafe_b64decode

from typing import Dict, Optional
from pathlib import Path

# noinspection PyPackageRequirements
from awscli.clidriver import create_clidriver
from jinja2 import PrefixLoader, PackageLoader
from werkzeug.utils import import_string

from scar_add_metadata_toolbox.config import Config
from scar_add_metadata_toolbox.csw import CSWServer


def _create_app_config() -> Config:
    """
    Create a Flask application configuration object

    Creates an instance of the relevant Config class defined in `config.py` based on the application environment
    (e.g. in production, the ProductionConfig class).

    :rtype Config
    :return: Flask config object
    """
    return import_string(f"scar_add_metadata_toolbox.config.{str(os.environ['FLASK_ENV']).capitalize()}Config")()


def _create_app_jinja_loader() -> PrefixLoader:
    """
    Create a Jinja environment's template sources

    Creates a Jinja prefix loader to load shared and application specific templates together. A prefix (namespace) is
    used to select which set of templates to use. Templates are loaded from relevant Python modules

    :rtype PrefixLoader
    :return: Jinja prefix loader
    """
    return PrefixLoader(
        {
            "app": PackageLoader("scar_add_metadata_toolbox"),
            "bas_style_kit": PackageLoader("bas_style_kit_jinja_templates"),
        }
    )


def _create_csw_repositories(repositories_config: dict) -> Dict[str, CSWServer]:
    """
    Create application CSW servers

    Creates CSW servers (catalogues/repositories) used in the server/catalogue component of this application.

    The arrangement of servers used is designed to provide the catalogues needed for the MirrorRepository class.

    :rtype dict
    :param repositories_config: dictionary of configurations for CSW servers, keyed by MirrorRepository class reference
    :return:
    """
    _repositories = {}
    for repository_name, repository_config in repositories_config.items():
        _repositories[repository_name] = CSWServer(config=repository_config)
    return _repositories


def aws_cli(*cmd) -> None:
    """
    AWS CLI python bindings

    Creates an instance of the AWS CLI that can be used via Python. This allows convenience commands like `s3 sync`,
    rather than needing to implement this ourselves using the underlying boto (AWS Python SDK) methods.

    Source: https://github.com/boto/boto3/issues/358#issuecomment-372086466
    """
    old_env = dict(os.environ)
    try:
        env = os.environ.copy()
        env["LC_CTYPE"] = "en_US.UTF"
        os.environ.update(env)
        exit_code = create_clidriver().main(*cmd)
        if exit_code > 0:
            raise RuntimeError(f"AWS CLI exited with code {exit_code}")
    finally:
        os.environ.clear()
        os.environ.update(old_env)


class AppAuthToken:
    """
    Azure auth token

    This class serves two main purposes:

    1. enabling easier access to access tokens returned in auth requests from the Microsoft Authentication Library
    2. persisting auth information to a local file for situations where this application is ran statelessly
    """

    def __init__(self, session_file_path: Path):
        """
        :type session_file_path Path
        :param session_file_path: Path to the file used to persist auth information
        """
        self.session_file_path = session_file_path
        self._payload = None

    @property
    def access_token_bearer_insecure(self) -> str:
        """
        Return the name of the user identified in the access token

        This is a convenience method to return the name of the user an access token is issued for. This method avoids
        having to fetch signing key sets to authenticate tokens etc. where the claims shown don't have an
        impact on security (e.g. greeting messages).

        WARNING: This method is insecure as it does not validate it's claims are authentic, or that the token is still
        valid. This method therefore MUST NOT be used in a secure context (e.g. determining if a user has access to a
        resource or action). A full JWT library MUST be used instead in such circumstances.

        :rtype str
        :return: Name of the user in access token (or '*unknown*')
        """
        try:
            access_token_parts = self.access_token.split(".")
            access_token_payload = urlsafe_b64decode(access_token_parts[1].encode() + b"===").decode()
            access_token_claims = json.loads(access_token_payload)
            return f"{access_token_claims['given_name']} {access_token_claims['family_name']}"
        except KeyError:
            return "*unknown*"

    @property
    def access_token(self) -> Optional[str]:
        """
        OAuth access token

        As defined by Azure: https://docs.microsoft.com/en-us/azure/active-directory/develop/access-tokens

        This application uses V2 access tokens.

        None is returned if an access token isn't set so that this class is compatible with the OWSLib Authentication
        class, which defaults credentials to None if not set (i.e. unauthenticated).

        :rtype str or None
        :return: access token
        """
        try:
            return self.payload["access_token"]
        except KeyError:
            return None

    @property
    def payload(self) -> dict:
        """
        Azure device flow response payload

        Payload returned by the Azure OAuth device flow via the Microsoft Authentication Library Public Client object.

        This includes tokens (access, refresh, id) and metadata (expiration times) for various purposes.

        When read, the payload is loaded from a JSON file.

        :rtype dict
        :return: Azure device flow response payload
        """
        self._payload = self._load()
        return self._payload

    @payload.setter
    def payload(self, payload: dict):
        """
        Azure device flow response payload

        When set, the payload is saved to a JSON file.

        :type payload dict
        :param payload: Azure device flow response payload
        """
        self._payload = payload
        self._dump()

    @payload.deleter
    def payload(self):
        """
        Azure device flow response payload

        When deleted, the stored payload file is removed.
        """
        self._payload = None
        self.session_file_path.unlink()

    def _load(self) -> dict:
        """
        Loads payload information from a JSON encoded file

        :rtype dict
        :returns Azure device flow response payload
        """
        try:
            with open(str(self.session_file_path), "r") as auth_file:
                return json.load(auth_file)
        except FileNotFoundError:
            return {}

    def _dump(self) -> None:
        """
        Saves payload information to a file encoded as JSON
        """
        self.session_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(self.session_file_path), "w") as auth_file:
            json.dump(self._payload, auth_file, indent=4)
