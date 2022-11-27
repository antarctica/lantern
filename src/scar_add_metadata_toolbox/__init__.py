from http import HTTPStatus

from authlib.integrations.flask_oauth2 import current_token
from flask import Flask, request, Response, url_for
from flask_azure_oauth import FlaskAzureOauth
from markupsafe import escape
from werkzeug.exceptions import NotFound

from scar_add_metadata_toolbox.classes import MirrorRepository
from scar_add_metadata_toolbox.commands import (
    auth_commands_blueprint,
    csw_commands_blueprint,
    record_commands_blueprint,
    site_commands_blueprint,
)
from scar_add_metadata_toolbox.csw import (
    CSWAmbiguousRequestError,
    CSWAuthInsufficientError,
    CSWAuthMissingError,
    CSWDatabaseNotInitialisedError,
    CSWUnknownRequestError,
    CSWUnmappedRequestError,
)
from scar_add_metadata_toolbox.utils import (
    _create_app_config,
    _create_app_jinja_loader,
    _create_csw_repositories,
    AppAuthToken,
)


def create_app():  # noqa: C901
    """
    Application factory

    This app object:
    * loads configuration from the `config` class (based on the `FLASK_ENV` environment variable)
    * creates instances of important classes such as authentication and metadata records
    * defines a `version` CLI command for debugging the package version installed
    * registers additional CLI commands from blueprints, for use when this app is run as a client
    * defines a route for handling CSW requests, for use when this is run as a server

    :rtype Flask
    :return: application object
    """
    app = Flask(__name__)

    app.config.from_object(_create_app_config())
    app.jinja_loader = _create_app_jinja_loader()

    auth = FlaskAzureOauth()
    auth.init_app(app)
    app.auth_token = AppAuthToken(session_file_path=app.config["AUTH_SESSION_FILE_PATH"])

    app.repositories = _create_csw_repositories(repositories_config=app.config["CSW_SERVERS_CONFIG"])
    app.config["CSW_CLIENTS_CONFIG"]["unpublished"]["client_config"]["auth"] = {"token": app.auth_token.access_token}
    app.config["CSW_CLIENTS_CONFIG"]["published"]["client_config"]["auth"] = {"token": app.auth_token.access_token}
    app.records = MirrorRepository(
        unpublished_repository_config=app.config["CSW_CLIENTS_CONFIG"]["unpublished"],
        published_repository_config=app.config["CSW_CLIENTS_CONFIG"]["published"],
    )

    app.register_blueprint(record_commands_blueprint)
    app.register_blueprint(site_commands_blueprint)
    app.register_blueprint(csw_commands_blueprint)
    app.register_blueprint(auth_commands_blueprint)

    @app.cli.command("version")
    def version():
        """Show application version."""
        print(f"{app.config['NAME']} version: {app.config['VERSION']}")

    @app.errorhandler(NotFound)
    def handle_bad_request(e):
        return Response(response="Not Found.", status=HTTPStatus.NOT_FOUND)

    @app.route("/meta/health/v1")
    def health():
        return {
            "status": "pass",
            "version": 1,
            "releaseId": app.config["VERSION"],
            "description": "Server side endpoints for the SCAR Antarctic Digital Database (ADD) Metadata Toolbox.",
            "links": {
                "self": url_for(endpoint="health", _external=True),
                "about": "https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox",
                "describedBy": f"https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/"
                f"v{app.config['VERSION']}/README.md",
            },
        }

    @app.route("/csw/<string:catalogue>", methods=["HEAD", "GET", "POST"])
    @auth(optional=True)
    def csw_catalogue(catalogue: str):
        try:
            return app.repositories[escape(catalogue)].process_request(request=request, token=current_token)
        except KeyError:
            return Response(response="Catalogue not found.", status=HTTPStatus.NOT_FOUND)
        except CSWDatabaseNotInitialisedError:
            return Response(response="Catalogue not yet available.", status=HTTPStatus.INTERNAL_SERVER_ERROR)
        except CSWUnknownRequestError:
            return Response(response="Request/operation information missing.", status=HTTPStatus.BAD_REQUEST)
        except CSWAmbiguousRequestError:
            return Response(
                response="Request/operation information specified in multiple forms.", status=HTTPStatus.BAD_REQUEST
            )
        except CSWUnmappedRequestError:
            return Response(
                response="Request/operation cannot be evaluated / not supported.", status=HTTPStatus.BAD_REQUEST
            )
        except CSWAuthMissingError:
            return Response(response="Missing authorisation token.", status=HTTPStatus.UNAUTHORIZED)
        except CSWAuthInsufficientError:
            return Response(response="Insufficient authorisation token.", status=HTTPStatus.FORBIDDEN)

    return app
