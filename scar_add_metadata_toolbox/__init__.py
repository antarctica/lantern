from authlib.integrations.flask_oauth2 import current_token
from flask import Flask, request, Response
from flask_azure_oauth import FlaskAzureOauth
from markupsafe import escape

from scar_add_metadata_toolbox.classes import MirrorRepository, Collections
from scar_add_metadata_toolbox.commands import (
    record_commands_blueprint,
    collections_commands_blueprint,
    site_commands_blueprint,
    auth_commands_blueprint,
    seeding_commands_blueprint,
    csw_commands_blueprint,
)
from scar_add_metadata_toolbox.csw import (
    CSWDatabaseNotInitialisedException,
    CSWAuthMissingException,
    CSWAuthInsufficientException,
)
from scar_add_metadata_toolbox.utils import (
    _create_app_config,
    _create_app_jinja_loader,
    _create_csw_repositories,
    AppAuthToken,
)


def create_app():
    """
    Application factory

    This application uses the application factory pattern [1].

    In addition to various routes and commands (registered directly or via blueprints), the app object includes
    instances of important classes such as authentication and metadata records/collections. Application configuration
    is loaded from the `config` class.

    :return:
    """
    app = Flask(__name__)

    app.config.from_object(_create_app_config())
    app.jinja_loader = _create_app_jinja_loader()

    auth = FlaskAzureOauth()
    auth.init_app(app)
    app.auth_token = AppAuthToken(session_file_path=app.config["AUTH_SESSION_FILE_PATH"])

    app.repositories = _create_csw_repositories(repositories_config=app.config["CSW_SERVERS_CONFIG"])
    app.collections = Collections(config=app.config["COLLECTIONS_CONFIG"])
    app.config["CSW_CLIENTS_CONFIG"]["unpublished"]["client_config"]["auth"] = {"token": app.auth_token.access_token}
    app.config["CSW_CLIENTS_CONFIG"]["published"]["client_config"]["auth"] = {"token": app.auth_token.access_token}
    app.records = MirrorRepository(
        unpublished_repository_config=app.config["CSW_CLIENTS_CONFIG"]["unpublished"],
        published_repository_config=app.config["CSW_CLIENTS_CONFIG"]["published"],
    )

    app.register_blueprint(record_commands_blueprint)
    app.register_blueprint(collections_commands_blueprint)
    app.register_blueprint(site_commands_blueprint)
    app.register_blueprint(csw_commands_blueprint)
    app.register_blueprint(auth_commands_blueprint)
    app.register_blueprint(seeding_commands_blueprint)

    @app.cli.command("version")
    def version():
        """Show application version."""
        print(f"{app.config['NAME']} version: {app.config['VERSION']}")

    @app.route("/csw/<string:catalogue>", methods=["HEAD", "GET", "POST"])
    @auth(optional=True)
    def csw_catalogue(catalogue: str):
        try:
            return app.repositories[escape(catalogue)].process_request(request=request, token=current_token)
        except KeyError:
            return Response(response="Catalogue not found.", status=404)
        except CSWDatabaseNotInitialisedException:
            return Response(response="Catalogue not yet available.", status=500)
        except CSWAuthMissingException:
            return Response(response="Missing authorisation token.", status=401)
        except CSWAuthInsufficientException:
            return Response(response="Insufficient authorisation token.", status=403)

    return app
