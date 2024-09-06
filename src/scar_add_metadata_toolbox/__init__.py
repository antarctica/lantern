import contextlib
from http import HTTPStatus

import sentry_sdk
from flask import Flask, Response, request, url_for
from flask_entra_auth.resource_protector import FlaskEntraAuth
from markupsafe import escape
from werkzeug.exceptions import NotFound

from scar_add_metadata_toolbox.classes import MirrorRepository
from scar_add_metadata_toolbox.client_auth import MsalFlask, MsalFlaskNoAccountError, MsalTokenAcquisitionError
from scar_add_metadata_toolbox.commands import (
    auth_commands_blueprint,
    csw_commands_blueprint,
    record_commands_blueprint,
    site_commands_blueprint,
)
from scar_add_metadata_toolbox.config import Config
from scar_add_metadata_toolbox.csw import (
    CSWAmbiguousRequestError,
    CSWAuthInsufficientError,
    CSWAuthMissingError,
    CSWDatabaseNotInitialisedError,
    CSWTrackingRepositoryNotInitialisedError,
    CSWUnknownRequestError,
    CSWUnmappedRequestError,
    RecordNotFoundError,
)
from scar_add_metadata_toolbox.utils import (
    _build_item,
    _build_record,
    _create_app_jinja_loader,
    _create_csw_repositories,
)


def create_app() -> Flask:  # noqa: C901
    """
    Application factory.

    This app object:
    * loads configuration from the `config` class
    * creates instances of important classes such as authentication and metadata records
    * defines a `version` CLI command for debugging the package version installed
    * registers additional CLI commands from blueprints, for use when this app is run as a client
    * defines a route for handling CSW requests, for use when this is run as a server
    """
    app = Flask(__name__)
    app.config.from_object(Config())

    sentry_sdk.init(app.config["SENTRY_CONFIG"])

    # noinspection PyPropertyAccess
    app.jinja_loader = _create_app_jinja_loader()

    auth = FlaskEntraAuth()
    auth.init_app(app)

    msal = MsalFlask()
    msal.init_app(app)

    # noinspection PyUnusedLocal
    access_token = None
    with contextlib.suppress(MsalFlaskNoAccountError, MsalTokenAcquisitionError):
        access_token = app.msal.access_token

    app.repositories = _create_csw_repositories(repositories_config=app.config["CSW_SERVERS_CONFIG"])
    app.config["CSW_CLIENTS_CONFIG"]["unpublished"]["client_config"]["auth"] = {"token": access_token}
    app.config["CSW_CLIENTS_CONFIG"]["published"]["client_config"]["auth"] = {"token": access_token}
    app.records = MirrorRepository(
        unpublished_repository_config=app.config["CSW_CLIENTS_CONFIG"]["unpublished"],
        published_repository_config=app.config["CSW_CLIENTS_CONFIG"]["published"],
    )

    app.register_blueprint(record_commands_blueprint)
    app.register_blueprint(site_commands_blueprint)
    app.register_blueprint(csw_commands_blueprint)
    app.register_blueprint(auth_commands_blueprint)

    @app.cli.command("version")
    def version() -> None:
        """Show application version."""
        print(f"{app.config['NAME']} version: {app.config['VERSION']}")

    # noinspection PyUnusedLocal
    @app.errorhandler(NotFound)
    def handle_bad_request(e: Exception) -> Response:
        return Response(response="Not Found.", status=HTTPStatus.NOT_FOUND)

    @app.route("/meta/health/v1")
    def health() -> dict:
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
    @app.auth(optional=True)
    def csw_catalogue(catalogue: str) -> Response:
        try:
            return app.repositories[escape(catalogue)].process_request(request=request, token=app.auth.current_token)
        except KeyError:
            return Response(response="Catalogue not found.", status=HTTPStatus.NOT_FOUND)
        except CSWDatabaseNotInitialisedError:
            return Response(response="Catalogue DB not yet available.", status=HTTPStatus.INTERNAL_SERVER_ERROR)
        except CSWTrackingRepositoryNotInitialisedError:
            return Response(response="Catalogue Repo not yet available.", status=HTTPStatus.INTERNAL_SERVER_ERROR)
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

    @app.route("/site/build", methods=["POST"])
    @app.auth(["BAS.MAGIC.ADD.Records.Publish.All"])
    def build_item() -> Response:
        try:
            record_id = request.args["item"]

            record = app.records.retrieve_record(record_id)
            _build_record(record)
            _build_item(record)

            return Response(status=HTTPStatus.CREATED)
        except CSWDatabaseNotInitialisedError:
            return Response(response="Internal server error.", status=HTTPStatus.INTERNAL_SERVER_ERROR)
        except RecordNotFoundError:
            return Response(response="Record not found.", status=HTTPStatus.NOT_FOUND)
        except KeyError:
            return Response(response="Parameter 'item' missing.", status=HTTPStatus.BAD_REQUEST)

    return app
