import os

from time import sleep
from pycsw.core import admin
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, ProgrammingError

from scar_add_metadata_toolbox import create_app

app = create_app()

# setup internal CSW servers
# TODO: Move and improve this (check for db tables, wait for 10 seconds for DB to avoid loop?
app.logger.info("Waiting for unpublished CSW database to become available...")
db = create_engine(app.config["CSW_CONFIG_UNPUBLISHED"]["repository"]["database"])
current_try = 0
max_tries = 10
sleep_seconds = 3
while current_try < max_tries:
    try:
        db.execute("SELECT version();")
        app.logger.info("CSW unpublished database available")
        break
    except OperationalError:
        app.logger.debug(f"CSW unpublished database not yet available [{current_try}/{max_tries}]")
        sleep(sleep_seconds)
    current_try += 1
else:
    app.logger.error(
        f"CSW unpublished database [{app.config['CSW_CONFIG_UNPUBLISHED']['repository']['database']}] not available "
        f"after {max_tries}"
    )
    raise RuntimeError(f"CSW unpublished database not available after {max_tries} tries.")
try:
    admin.setup_db(
        database=app.config["CSW_CONFIG_UNPUBLISHED"]["repository"]["database"],
        table=app.config["CSW_CONFIG_UNPUBLISHED"]["repository"]["table"],
        home="/tmp/unpublished",
    )
except ProgrammingError:
    app.logger.info("CSW unpublished database already configured")

app.logger.info("Waiting for published CSW database to become available...")
db = create_engine(app.config["CSW_CONFIG_PUBLISHED"]["repository"]["database"])
current_try = 0
max_tries = 10
sleep_seconds = 3
while current_try < max_tries:
    try:
        db.execute("SELECT version();")
        app.logger.info("CSW published database available")
        break
    except OperationalError:
        app.logger.debug(f"CSW published database not yet available [{current_try}/{max_tries}]")
        sleep(sleep_seconds)
    current_try += 1
else:
    app.logger.error(
        f"CSW published database [{app.config['CSW_CONFIG_PUBLISHED']['repository']['database']}] not available after "
        f"{max_tries}"
    )
    raise RuntimeError(f"CSW published database not available after {max_tries} tries.")
try:
    admin.setup_db(
        database=app.config["CSW_CONFIG_PUBLISHED"]["repository"]["database"],
        table=app.config["CSW_CONFIG_PUBLISHED"]["repository"]["table"],
        home="/tmp/published",
    )
except ProgrammingError:
    app.logger.info("CSW published database already configured")

if "PYCHARM_HOSTED" in os.environ:
    # Exempting Bandit security issue (binding to all network interfaces)
    #
    # All interfaces option used because the network available within the container can vary across providers
    # This is only used when debugging with PyCharm. A standalone web server is used in production.
    app.run(host="0.0.0.0", port=9000, debug=True, use_debugger=False, use_reloader=False)  # nosec
