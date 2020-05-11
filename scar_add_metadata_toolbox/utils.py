import os

from typing import Dict, Any

# noinspection PyPackageRequirements
from werkzeug.utils import import_string


def _create_app_config() -> Dict[str, Any]:
    """
    Creates an object to use as a Flask app's configuration

    Creates an instance of a class defined in config.py specific to the application environment (e.g. production).

    This is a standalone class to aid in mocking during testing.

    :return: object for a Flask app's configuration
    """
    return import_string(f"scar_add_metadata_toolbox.config.{str(os.environ['FLASK_ENV']).capitalize()}Config")()
