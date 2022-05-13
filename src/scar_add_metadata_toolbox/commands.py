from json import JSONDecodeError
from os import EX_USAGE
from pathlib import Path
from shutil import copytree, rmtree
from sys import exit as sys_exit

import click
from click import Abort
from click_spinner import spinner
from flask import Blueprint, current_app, render_template
from importlib_resources import files as resource_path
from lxml.etree import (
    ElementTree,
    fromstring,
    ProcessingInstruction,
    tostring,
)  # nosec - see 'lxml` package (bandit)' section in README
from tabulate import tabulate

from scar_add_metadata_toolbox.classes import (
    Collection,
    Item,
    Record,
    RecordRetractBeforeDeleteException,
)
from scar_add_metadata_toolbox.csw import (
    CSWAuthException,
    CSWAuthInsufficientException,
    CSWAuthMissingException,
    CSWDatabaseAlreadyInitialisedException,
    CSWDatabaseNotInitialisedException,
    CSWDatabasePostGISExtensionUnavailable,
    RecordInsertConflictException,
    RecordNotFoundException,
    RecordServerException,
)
from scar_add_metadata_toolbox.utils import aws_cli

record_commands_blueprint = Blueprint("records", __name__)
record_commands_blueprint.cli.short_help = "Manage metadata records."


@record_commands_blueprint.cli.command("list")
def list_records():
    """List all records."""
    try:
        records = current_app.records.list_records()
        _records = []
        for record in records.values():
            _records.append(
                {
                    "identifier": record.identifier,
                    "type": record.hierarchy_level,
                    "title": record.title,
                    "status": "Published" if record.published else "Unpublished",
                }
            )
        print("")
        print(
            tabulate(
                _records,
                headers={
                    "identifier": "Record Identifier",
                    "type": "Record Type",
                    "title": "Record Title",
                    "status": "Status",
                },
                tablefmt="fancy_grid",
            )
        )
        print("")
        print(f"Ok. {len(records)} records.")
    except CSWDatabaseNotInitialisedException:
        print("No. CSW catalogue not setup.")
        sys_exit(EX_USAGE)
    except CSWAuthException:
        print("No. Error with auth token. Try signing out and in again or seek support.")
        sys_exit(EX_USAGE)
    except CSWAuthMissingException:
        print("No. Missing auth token. Run `auth sign-in` first.")
        sys_exit(EX_USAGE)
    except CSWAuthInsufficientException:
        print("No. Missing permissions in auth token. Seek support to assign required permissions.")
        sys_exit(EX_USAGE)


@record_commands_blueprint.cli.command("import")  # noqa: C901
@click.argument("record_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--allow-update", is_flag=True, help="Update any existing record.")
@click.option("--publish", is_flag=True, help="Publish record after importing.")
@click.option("--allow-republish", is_flag=True, help="Republish any existing, published, record.")
@click.pass_context
def import_record(
    ctx, record_path: str, allow_update: bool = False, publish: bool = False, allow_republish: bool = False
):
    """Import a record from a file."""
    try:
        record_path = Path(record_path)
        record = Record()
        record.load(record_path=record_path)
        current_app.records.insert_record(record=record, update=False)
        print(f"Ok. Record '{record.identifier}' imported.")
    except JSONDecodeError:
        print(f"No. Record in file '{record_path}' is not valid JSON.")
        sys_exit(EX_USAGE)
    except CSWDatabaseNotInitialisedException:
        print("No. CSW catalogue not setup.")
        sys_exit(EX_USAGE)
    except CSWAuthException:
        print("No. Error with auth token. Try signing out and in again or seek support.")
        sys_exit(EX_USAGE)
    except CSWAuthMissingException:
        print("No. Missing auth token. Run `auth sign-in` first.")
        sys_exit(EX_USAGE)
    except CSWAuthInsufficientException:
        print("No. Missing permissions in auth token. Seek support to assign required permissions.")
        sys_exit(EX_USAGE)
    except RecordServerException:
        # noinspection PyUnboundLocalVariable
        print(f"No. Server error importing record '{record.identifier}'.")
        sys_exit(EX_USAGE)
    except RecordInsertConflictException:
        if not allow_update:
            # noinspection PyUnboundLocalVariable
            print(f"No. Record '{record.identifier}' already exists. Add `--allow-update` flag to allow.")
            sys_exit(EX_USAGE)

        current_app.records.insert_record(record=record, update=True)
        print(f"Ok. Record '{record.identifier}' updated.")

    if publish:
        ctx.invoke(publish_record, record_identifier=record.identifier, allow_republish=allow_republish)


@record_commands_blueprint.cli.command("bulk-import")
@click.argument("records_path", type=click.Path(exists=True, file_okay=False))
@click.option("--allow-update", is_flag=True, help="Update any existing records.")
@click.option("--publish", is_flag=True, help="Publish records after importing.")
@click.option("--allow-republish", is_flag=True, help="Republish any existing, published, records.")
@click.pass_context
def import_records(
    ctx, records_path: str, allow_update: bool = False, publish: bool = False, allow_republish: bool = False
):
    """Import records from files in a directory."""
    records_path = Path(records_path)
    record_paths = list(sorted(records_path.glob("*.json")))

    print(f"{len(record_paths)} records to import/update.")
    _record_count = 1
    for record_path in record_paths:
        print(f"# Record {_record_count}/{len(record_paths)}")
        ctx.invoke(
            import_record,
            record_path=str(record_path),
            allow_update=allow_update,
            publish=publish,
            allow_republish=allow_republish,
        )
        _record_count += 1
    print(f"Ok. {len(record_paths)} records imported/updated.")


@record_commands_blueprint.cli.command("publish")
@click.argument("record-identifier")
@click.option("--allow-republish", is_flag=True, help="Republish any existing, published, record.")
def publish_record(record_identifier: str, allow_republish: bool = False):
    """Publish a record."""
    try:
        current_app.records.publish_record(record_identifier=record_identifier, republish=False)
        print(f"Ok. Record '{record_identifier}' published.")
    except CSWDatabaseNotInitialisedException:
        print("No. CSW catalogue not setup.")
        sys_exit(EX_USAGE)
    except CSWAuthException:
        print("No. Error with auth token. Try signing out and in again or seek support.")
        sys_exit(EX_USAGE)
    except CSWAuthMissingException:
        print("No. Missing auth token. Run `auth sign-in` first.")
        sys_exit(EX_USAGE)
    except CSWAuthInsufficientException:
        print("No. Missing permissions in auth token. Seek support to assign required permissions.")
        sys_exit(EX_USAGE)
    except RecordNotFoundException:
        print(f"No. Record '{record_identifier}' does not exist.")
        sys_exit(EX_USAGE)
    except RecordServerException:
        # noinspection PyUnboundLocalVariable
        print(f"No. Server error publishing record '{record_identifier}'.")
        sys_exit(EX_USAGE)
    except RecordInsertConflictException:
        if not allow_republish:
            print(f"No. Record '{record_identifier}' already published. Add `--allow-republish` flag to allow.")
            sys_exit(EX_USAGE)

        current_app.records.publish_record(record_identifier=record_identifier, republish=True)
        print(f"Ok. Record '{record_identifier}' republished.")


@record_commands_blueprint.cli.command("bulk-publish")
@click.option("--force-republish", is_flag=True, help="Republish all existing records too.")
@click.pass_context
def publish_records(ctx, force_republish: bool = False):
    """Publish all (un)published records."""
    record_identifiers = current_app.records.list_distinct_unpublished_record_identifiers()
    if force_republish:
        record_identifiers = current_app.records.list_record_identifiers()

    print(f"{len(record_identifiers)} records to (re)publish.")
    _record_count = 1
    for record_identifier in record_identifiers:
        print(f"# Record {_record_count}/{len(record_identifiers)}")
        ctx.invoke(publish_record, record_identifier=record_identifier, allow_republish=force_republish)
        _record_count += 1
    print(f"Ok. {len(record_identifiers)} records (re)published.")


@record_commands_blueprint.cli.command("export")
@click.argument("record-identifier")
@click.argument("record_path", type=click.Path(dir_okay=False))
@click.option("--allow-overwrite", is_flag=True, help="Allow existing export to be overwritten.")
def export_record(record_identifier: str, record_path: str, allow_overwrite: bool = False):
    """Export a record to a file."""
    record_path = Path(record_path)

    try:
        record = current_app.records.retrieve_record(record_identifier=record_identifier)
        record.dump(record_path=record_path, overwrite=False)
        print(f"Ok. Record '{record_identifier}' exported.")
    except CSWDatabaseNotInitialisedException:
        print("No. CSW catalogue not setup.")
        sys_exit(EX_USAGE)
    except CSWAuthException:
        print("No. Error with auth token. Try signing out and in again or seek support.")
        sys_exit(EX_USAGE)
    except CSWAuthMissingException:
        print("No. Missing auth token. Run `auth sign-in` first.")
        sys_exit(EX_USAGE)
    except CSWAuthInsufficientException:
        print("No. Missing permissions in auth token. Seek support to assign required permissions.")
        sys_exit(EX_USAGE)
    except RecordNotFoundException:
        print(f"No. Record '{record_identifier}' does not exist.")
        sys_exit(EX_USAGE)
    except FileExistsError:
        if not allow_overwrite:
            print(
                f"No. Export of record '{record_identifier}' would be overwritten. Add `--allow-overwrite` flag to allow."
            )
            sys_exit(EX_USAGE)

        # noinspection PyUnboundLocalVariable
        record.dump(record_path=record_path, overwrite=True)
        print(f"Ok. Record '{record_identifier}' re-exported.")


@record_commands_blueprint.cli.command("bulk-export")
@click.argument("records_path", type=click.Path(exists=True, file_okay=False))
@click.option("--allow-overwrite", is_flag=True, help="Allow existing exports to be overwritten.")
@click.pass_context
def export_records(ctx, records_path: str, allow_overwrite: bool = False):
    """Export all records as files in a directory."""
    records_path = Path(records_path)
    record_identifiers = current_app.records.list_record_identifiers()

    print(f"{len(record_identifiers)} records to (re)export.")
    _record_count = 1
    for record_identifier in record_identifiers:
        print(f"# Record {_record_count}/{len(record_identifiers)}")
        record_path = records_path.joinpath(f"{record_identifier}.json")
        ctx.invoke(
            export_record,
            record_identifier=record_identifier,
            record_path=record_path,
            allow_overwrite=allow_overwrite,
        )
        _record_count += 1
    print(f"Ok. {len(record_identifiers)} records (re)exported.")


@record_commands_blueprint.cli.command("remove")
@click.argument("record-identifier")
@click.option("--force-remove", is_flag=True, help="Suppress interactive conformation.")
def remove_record(record_identifier: str, force_remove: bool):
    """Remove an unpublished record."""
    if not force_remove:
        if not click.confirm(f"CONFIRM: Permanently remove record '{record_identifier}'?", abort=True):
            raise Abort()

    try:
        current_app.records.delete_record(record_identifier=record_identifier)
        print(f"Ok. Record '{record_identifier}' removed.")
    except CSWDatabaseNotInitialisedException:
        print("No. CSW catalogue not setup.")
        sys_exit(EX_USAGE)
    except CSWAuthException:
        print("No. Error with auth token. Try signing out and in again or seek support.")
        sys_exit(EX_USAGE)
    except CSWAuthMissingException:
        print("No. Missing auth token. Run `auth sign-in` first.")
        sys_exit(EX_USAGE)
    except CSWAuthInsufficientException:
        print("No. Missing permissions in auth token. Seek support to assign required permissions.")
        sys_exit(EX_USAGE)
    except RecordNotFoundException:
        print(f"No. Record '{record_identifier}' does not exist.")
        sys_exit(EX_USAGE)
    except RecordRetractBeforeDeleteException:
        print(f"No. Record '{record_identifier}' is published, retract it first.")
        sys_exit(EX_USAGE)


@record_commands_blueprint.cli.command("bulk-remove")
@click.pass_context
def remove_records(ctx):
    """Remove all unpublished records."""
    record_identifiers = current_app.records.list_distinct_unpublished_record_identifiers()

    if not click.confirm(f"CONFIRM: Permanently remove all {len(record_identifiers)} unpublished records?", abort=True):
        raise Abort()

    print(f"{len(record_identifiers)} records to remove.")
    _record_count = 1
    for record_identifier in record_identifiers:
        print(f"# Record {_record_count}/{len(record_identifiers)}")
        ctx.invoke(remove_record, record_identifier=record_identifier, force_remove=True)
        _record_count += 1
    print(f"Ok. {len(record_identifiers)} records removed.")


@record_commands_blueprint.cli.command("retract")
@click.argument("record-identifier")
def retract_record(record_identifier: str):
    """Retract a published record."""
    try:
        current_app.records.retract_record(record_identifier=record_identifier)
        print(f"Ok. Record '{record_identifier}' retracted.")
    except CSWDatabaseNotInitialisedException:
        print("No. CSW catalogue not setup.")
        sys_exit(EX_USAGE)
    except CSWAuthException:
        print("No. Error with auth token. Try signing out and in again or seek support.")
        sys_exit(EX_USAGE)
    except CSWAuthMissingException:
        print("No. Missing auth token. Run `auth sign-in` first.")
        sys_exit(EX_USAGE)
    except CSWAuthInsufficientException:
        print("No. Missing permissions in auth token. Seek support to assign required permissions.")
        sys_exit(EX_USAGE)
    except RecordNotFoundException:
        print(f"No. Record '{record_identifier}' is not published.")
        sys_exit(EX_USAGE)


@record_commands_blueprint.cli.command("bulk-retract")
@click.pass_context
def retract_records(ctx):
    """Retract all published records."""
    record_identifiers = current_app.records.list_published_record_identifiers()

    print(f"{len(record_identifiers)} records to retract.")
    _record_count = 1
    for record_identifier in record_identifiers:
        print(f"# Record {_record_count}/{len(record_identifiers)}")
        ctx.invoke(retract_record, record_identifier=record_identifier)
        _record_count += 1
    print(f"Ok. {len(record_identifiers)} records retracted.")


site_commands_blueprint = Blueprint("site", __name__)
site_commands_blueprint.cli.short_help = "Manage static site."


# noinspection PyUnresolvedReferences
@site_commands_blueprint.cli.command("build-items")
def build_items():
    """Build pages for all published items."""
    items_output_path = Path(current_app.config["SITE_PATH"]).joinpath("items")

    try:
        # noinspection PyArgumentList
        with spinner():
            all_records = list(current_app.records.retrieve_published_records())
            selected_records = []
            for record in all_records:
                if record.hierarchy_level != "collection":
                    selected_records.append(record)

        print(f"{len(selected_records)} item pages to generate.")
        _items_count = 1
        for record in selected_records:
            print(f"# Item page {_items_count}/{len(selected_records)}")
            item = Item(record=record)
            item_output_path = items_output_path.joinpath(f"{item.identifier}/index.html")
            item_output_path.parent.mkdir(exist_ok=True, parents=True)

            with open(str(item_output_path), mode="w") as item_file:
                item_file.write(render_template("app/_views/item-details.j2", item=item))
            print(f"Ok. Generated item page for '{item.identifier}'.")
            _items_count += 1
        print(f"Ok. {len(selected_records)} item pages generated.")
    except CSWDatabaseNotInitialisedException:
        print("No. CSW catalogue not setup.")
        sys_exit(EX_USAGE)
    except CSWAuthException:
        print("No. Error with auth token. Try signing out and in again or seek support.")
        sys_exit(EX_USAGE)
    except CSWAuthMissingException:
        print("No. Missing auth token. Run `auth sign-in` first.")
        sys_exit(EX_USAGE)
    except CSWAuthInsufficientException:
        print("No. Missing permissions in auth token. Seek support to assign required permissions.")
        sys_exit(EX_USAGE)


# noinspection PyUnresolvedReferences
@site_commands_blueprint.cli.command("build-collections")
def build_collections():
    """Build pages for all collections."""
    collections_output_path = Path(current_app.config["SITE_PATH"]).joinpath("collections")

    try:
        # noinspection PyArgumentList
        with spinner():
            all_records = list(current_app.records.retrieve_published_records())
            selected_records = []
            for record in all_records:
                if record.hierarchy_level == "collection":
                    selected_records.append(record)

        print(f"{len(selected_records)} collection pages to generate.")
        _collection_count = 1
        for record in selected_records:
            print(f"# Collection page {_collection_count}/{len(selected_records)}")
            collection = Collection(record=record)
            collection_output_path = collections_output_path.joinpath(f"{collection.identifier}/index.html")
            collection_output_path.parent.mkdir(exist_ok=True, parents=True)

            _collection_items = []
            with click.progressbar(collection.item_identifiers) as item_identifiers:
                for item_identifier in item_identifiers:
                    _collection_items.append(
                        Item(record=current_app.records.retrieve_record(record_identifier=item_identifier))
                    )
            collection.items = _collection_items

            with open(str(collection_output_path), mode="w") as collection_file:
                collection_file.write(render_template("app/_views/collection-details.j2", collection=collection))
            print(f"Ok. Generated collection page for '{collection.identifier}'.")
            _collection_count += 1
        print(f"Ok. {len(selected_records)} collection pages generated.")
    except CSWDatabaseNotInitialisedException:
        print("No. CSW catalogue not setup.")
        sys_exit(EX_USAGE)
    except CSWAuthException:
        print("No. Error with auth token. Try signing out and in again or seek support.")
        sys_exit(EX_USAGE)
    except CSWAuthMissingException:
        print("No. Missing auth token. Run `auth sign-in` first.")
        sys_exit(EX_USAGE)
    except CSWAuthInsufficientException:
        print("No. Missing permissions in auth token. Seek support to assign required permissions.")
        sys_exit(EX_USAGE)


@site_commands_blueprint.cli.command("build-records")
def build_records():
    """Build pages for all published records (XML)."""
    stylesheets = ["iso-html", "iso-rubric", "iso-xml"]
    records_output_path = Path(current_app.config["SITE_PATH"]).joinpath("records")

    try:
        # noinspection PyArgumentList
        with spinner():
            records = list(current_app.records.retrieve_published_records())

        print(f"{len(records) * len(stylesheets)} record pages to generate.")
        _records_count = 1
        for record in records:
            _stylesheet_count = 1
            for stylesheet in stylesheets:
                print(
                    f"# Record page {_records_count}/{len(records)} (stylesheet {_stylesheet_count}/{len(stylesheets)})"
                )
                record_output_path = records_output_path.joinpath(
                    f"{record.identifier}/{stylesheet}/{record.identifier}.xml"
                )
                record_output_path.parent.mkdir(exist_ok=True, parents=True)

                with open(str(record_output_path), mode="w") as record_file:
                    record_xml = record.dumps(dump_format="xml")
                    record_xml_element = ElementTree(fromstring(record_xml.encode()))
                    record_xml_element_root = record_xml_element.getroot()

                    if stylesheet == "iso-html":
                        record_xml_element_root.addprevious(
                            ProcessingInstruction(
                                "xml-stylesheet", 'type="text/xsl" href="/static/xsl/iso-html/xml-to-html-ISO.xsl"'
                            )
                        )
                    elif stylesheet == "iso-rubric":
                        record_xml_element_root.addprevious(
                            ProcessingInstruction(
                                "xml-stylesheet", 'type="text/xsl" href="/static/xsl/iso-rubric/isoRubricHTML.xsl"'
                            )
                        )

                    record_file.write(
                        tostring(record_xml_element, pretty_print=True, xml_declaration=True, encoding="utf-8").decode()
                    )
                print(f"Ok. Generated item page for '{record.identifier}' (stylesheet '{stylesheet}').")
                _stylesheet_count += 1
            _records_count += 1
        print(f"Ok. {len(records) * len(stylesheets)} record pages generated.")
    except CSWDatabaseNotInitialisedException:
        print("No. CSW catalogue not setup.")
        sys_exit(EX_USAGE)
    except CSWAuthException:
        print("No. Error with auth token. Try signing out and in again or seek support.")
        sys_exit(EX_USAGE)
    except CSWAuthMissingException:
        print("No. Missing auth token. Run `auth sign-in` first.")
        sys_exit(EX_USAGE)
    except CSWAuthInsufficientException:
        print("No. Missing permissions in auth token. Seek support to assign required permissions.")
        sys_exit(EX_USAGE)


# noinspection PyUnresolvedReferences
@site_commands_blueprint.cli.command("build-pages")
def build_pages():
    """Build pages for legal policies and feedback form."""
    legal_pages = ["cookies", "copyright", "privacy"]
    legal_pages_output_path = Path(current_app.config["SITE_PATH"]).joinpath("legal")

    print(f"{len(legal_pages)} legal pages to generate.")
    _legal_pages_count = 1
    for legal_page in legal_pages:
        print(f"# Legal page {_legal_pages_count}/{len(legal_pages)}")
        legal_page_output_path = legal_pages_output_path.joinpath(f"{legal_page}/index.html")
        legal_page_output_path.parent.mkdir(exist_ok=True, parents=True)

        with open(str(legal_page_output_path), mode="w") as legal_page_file:
            legal_page_file.write(render_template(f"app/_views/legal/{legal_page}.j2"))
        print(f"Ok. Generated legal page for '{legal_page}'.")
        _legal_pages_count += 1
    print(f"Ok. {len(legal_pages)} legal pages generated.")

    feedback_page_output_path = Path(current_app.config["SITE_PATH"]).joinpath("feedback/index.html")
    feedback_page_output_path.parent.mkdir(exist_ok=True, parents=True)
    with open(str(feedback_page_output_path), mode="w") as feedback_page_file:
        feedback_page_file.write(render_template("app/_views/feedback.j2"))
    print("Ok. feedback page generated.")


@site_commands_blueprint.cli.command("copy-assets")
def copy_assets():
    """Copy all static assets (CSS, JS, etc.).

    Note: The path returned by importlib_resources is not a normal Path object and needs to converted before it can be
    used. The empty `.joinpath()` method is part of this conversion.
    """
    # workaround for lack of `dirs_exist_ok` option in copytree in Python 3.6
    try:
        rmtree(Path(current_app.config["SITE_PATH"]).joinpath("static"))
    except FileNotFoundError:
        pass

    copytree(
        str(Path(resource_path("scar_add_metadata_toolbox.static").joinpath(""))),
        str(Path(current_app.config["SITE_PATH"]).joinpath("static")),
    )
    print("Ok. static assets copied.")


@site_commands_blueprint.cli.command("build")
@click.pass_context
def build_all(ctx):
    """Build all static site components."""
    ctx.invoke(build_records)
    ctx.invoke(build_items)
    ctx.invoke(build_collections)
    ctx.invoke(build_pages)
    ctx.invoke(copy_assets)
    print("Ok. Site built.")


@site_commands_blueprint.cli.command("publish")
@click.option("--build", is_flag=True, help="Build static site components prior to publishing.")
@click.option("--force-publish", is_flag=True, help="Suppress interactive conformation.")
@click.pass_context
def build_publish(ctx, build: bool = False, force_publish: bool = False):
    """Publish static site build to remote location."""
    if build:
        ctx.invoke(build_all)
    if not force_publish:
        if not click.confirm(f"CONFIRM: Publish static site to '{current_app.config['S3_BUCKET']}'?", abort=True):
            raise Abort()

    aws_cli(
        [
            "s3",
            "sync",
            str(Path(current_app.config["SITE_PATH"])),
            f"s3://{current_app.config['S3_BUCKET']}",
            "--delete",
        ]
    )
    print(f"Ok. Site published to '{current_app.config['S3_BUCKET']}'")


csw_commands_blueprint = Blueprint("csw", __name__)
csw_commands_blueprint.cli.short_help = "Manage CSW catalogues."


@csw_commands_blueprint.cli.command("setup")
@click.argument("catalogue")
def setup_catalogue(catalogue: str):
    """Setup catalogue database structure."""
    try:
        # noinspection PyArgumentList
        with spinner():
            current_app.repositories[catalogue].setup()
        print(f"Ok. Catalogue '{catalogue}' setup.")
    except KeyError:
        print(
            f"No. CSW catalogue '{catalogue}' does not exist. Valid options are [{', '.join(current_app.repositories.keys())}]."
        )
        sys_exit(EX_USAGE)
    except CSWDatabaseAlreadyInitialisedException:
        print(f"Ok. Note CSW catalogue '{catalogue}' is already setup.")
    except CSWDatabasePostGISExtensionUnavailable:  # pragma: no cover (will be addressed in #116)
        print(
            "No. CSW backing database does not have the PostGIS extension enabled. Enable this extension and try again."
        )


auth_commands_blueprint = Blueprint("auth", __name__)
auth_commands_blueprint.cli.short_help = "Manage user access to information and functions."


@auth_commands_blueprint.cli.command("sign-in")
def auth_sign_in():
    """Set user access token to use application."""
    auth_flow = current_app.config["CLIENT_AUTH"].initiate_device_flow(scopes=current_app.config["AUTH_CLIENT_SCOPES"])
    click.pause(
        f"To sign-in, visit 'https://microsoft.com/devicelogin', "
        f"enter this code '{auth_flow['user_code']}' and then press any key..."
    )
    auth_payload = current_app.config["CLIENT_AUTH"].acquire_token_by_device_flow(auth_flow)
    current_app.auth_token.payload = auth_payload
    print(
        f"Ok. Access token for '{current_app.auth_token.access_token_bearer_insecure}' "
        f"set in '{str(current_app.auth_token.session_file_path.absolute())}'."
    )


@auth_commands_blueprint.cli.command("sign-out")
def auth_sign_out():
    """Remove existing access token if present."""
    try:
        del current_app.auth_token.payload
    except FileNotFoundError:  # pragma: no cover (will be addressed in #231)
        pass
    print("Ok. Access token removed.")
