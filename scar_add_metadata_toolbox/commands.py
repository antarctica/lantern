from datetime import date
from json import JSONDecodeError
from sys import exit as sys_exit
from os import EX_USAGE
from pathlib import Path
from uuid import uuid4
from random import choice as random_choice, choices as random_choices
from shutil import copytree

import click

# Exempting Bandit security issue (Using Element to parse untrusted XML data is known to be vulnerable to XML attacks)
#
# We don't currently allow untrusted/user-provided XML so this is not a risk
from lxml.etree import ElementTree, ProcessingInstruction, fromstring, tostring  # nosec
from click import Abort
from click_spinner import spinner
from faker import Faker
from flask import Blueprint, current_app, render_template
from tabulate import tabulate

from scar_add_metadata_toolbox.classes import (
    Record,
    RecordRetractBeforeDeleteException,
    Item,
    Collection,
    CollectionInsertConflictException,
    CollectionNotFoundException,
)
from scar_add_metadata_toolbox.csw import (
    CSWDatabaseAlreadyInitialisedException,
    RecordServerException,
    RecordInsertConflictException,
    RecordNotFoundException,
    CSWDatabaseNotInitialisedException,
    CSWAuthMissingException,
    CSWAuthInsufficientException,
    CSWAuthException,
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
                    "title": record.title,
                    "status": "Published" if record.published else "Unpublished",
                }
            )
        print("")
        print(
            tabulate(
                _records,
                headers={"identifier": "Record Identifier", "title": "Record Title", "status": "Status"},
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


@record_commands_blueprint.cli.command("import")
@click.argument("record_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--allow-update", is_flag=True, help="Update any existing record.")
@click.option("--publish", is_flag=True, help="Publish record after importing.")
@click.option(
    "--allow-republish", is_flag=True, help="Republish any existing, published, record.",
)
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
@click.option(
    "--allow-republish", is_flag=True, help="Republish any existing, published, records.",
)
@click.pass_context
def import_records(
    ctx, records_path: str, allow_update: bool = False, publish: bool = False, allow_republish: bool = False
):
    """Import records from files in a directory."""
    records_path = Path(records_path)
    record_paths = list(records_path.glob("*.json"))

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
@click.option(
    "--allow-republish", is_flag=True, help="Republish any existing, published, record.",
)
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
@click.option(
    "--force-republish", is_flag=True, help="Republish all existing records too.",
)
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
        ctx.invoke(
            publish_record, record_identifier=record_identifier, allow_republish=force_republish,
        )
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
    """Export all records to files in a directory."""
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


collections_commands_blueprint = Blueprint("collections", __name__)
collections_commands_blueprint.cli.short_help = "Manage site collections."


@collections_commands_blueprint.cli.command("list")
def list_collections():
    """List all collections."""
    collections = current_app.collections.get_all()
    _collections = []
    for collection in collections:
        _collections.append(
            {"identifier": collection.identifier, "title": collection.title, "items": len(collection.item_identifiers)}
        )

    print("")
    print(
        tabulate(
            _collections,
            headers={"identifier": "Collection Identifier", "title": "Collection Title", "items": "Items (count)"},
            tablefmt="fancy_grid",
        )
    )
    print("")
    print(f"Ok. {len(collections)} collections.")


@collections_commands_blueprint.cli.command("inspect")
@click.argument("collection-identifier")
def inspect_collection(collection_identifier: str):
    """View details for a collection."""
    try:
        collection = current_app.collections.get(collection_identifier=collection_identifier)

        print(f"Ok. Collection details for '{collection.identifier}':")
        print("")
        print(f"Identifier: {collection.identifier}")
        print(f"Title: {collection.title}")
        print("")
        print(f"Summary:")
        print(collection.summary)
        print("")
        print(f"Items in collection: {len(collection.item_identifiers)}")
        for item_identifier in collection.item_identifiers:
            item = Item(record=current_app.records.retrieve_record(record_identifier=item_identifier))
            print(f"* {item.identifier} - {item.title}")
    except CollectionNotFoundException:
        print(f"No. Collection '{collection_identifier}' does not exist.")
        sys_exit(EX_USAGE)
    except RecordNotFoundException:
        # noinspection PyUnboundLocalVariable
        print(f"No. Record '{item_identifier}' in collection '{collection_identifier}' does not exist.")
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


@collections_commands_blueprint.cli.command("import")
@click.argument("collection_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--allow-update", is_flag=True, help="Update any existing collection.")
def import_collection(collection_path: str, allow_update: bool = False):
    """Import a collection from a file."""
    collection_path = Path(collection_path)

    try:
        collection = Collection()
        collection.load(collection_path=collection_path)
        current_app.collections.add(collection=collection)
        print(f"Ok. Collection '{collection.identifier}' imported.")
    except JSONDecodeError:
        print(f"No. Collection in file '{collection_path}' is not valid JSON.")
        sys_exit(EX_USAGE)
    except CollectionInsertConflictException:
        if not allow_update:
            # noinspection PyUnboundLocalVariable
            print(f"No. Collection '{collection.identifier}' already exists. Add `--allow-update` flag to allow.")
            sys_exit(EX_USAGE)

        current_app.collections.update(collection=collection)
        print(f"Ok. Collection '{collection.identifier}' updated.")


@collections_commands_blueprint.cli.command("bulk-import")
@click.argument("collections_path", type=click.Path(exists=True, file_okay=False))
@click.option("--allow-update", is_flag=True, help="Update any existing collections.")
@click.pass_context
def import_collections(ctx, collections_path: str, allow_update: bool = False):
    """Import records from files in a directory."""
    collections_path = Path(collections_path)
    collection_paths = list(collections_path.glob("*.json"))

    print(f"{len(collection_paths)} collections to import/update.")
    _collection_count = 1
    for collection_path in collection_paths:
        print(f"# Collection {_collection_count}/{len(collection_paths)}")
        ctx.invoke(import_collection, collection_path=str(collection_path), allow_update=allow_update)
        _collection_count += 1
    print(f"Ok. {len(collection_paths)} collections imported/updated.")


@collections_commands_blueprint.cli.command("export")
@click.argument("collection-identifier")
@click.argument("collection_path", type=click.Path(dir_okay=False))
@click.option("--allow-overwrite", is_flag=True, help="Allow existing exports to be overwritten.")
def export_collection(collection_identifier: str, collection_path: str, allow_overwrite: bool = False):
    """Export a collection to a file."""
    collection_path = Path(collection_path)

    try:
        collection = current_app.collections.get(collection_identifier=collection_identifier)
        collection.dump(collection_path=collection_path, overwrite=False)
        print(f"Ok. Collection '{collection.identifier}' exported.")
    except CollectionNotFoundException:
        print(f"No. Collection '{collection_identifier}' does not exist.")
        sys_exit(EX_USAGE)
    except FileExistsError:
        if not allow_overwrite:
            # noinspection PyUnboundLocalVariable
            print(
                f"No. Export of collection '{collection.identifier}' would be overwritten. Add `--allow-overwrite` flag to allow."
            )
            sys_exit(EX_USAGE)
        collection.dump(collection_path=collection_path, overwrite=True)
        print(f"Ok. Collection '{collection.identifier}' re-exported.")


@collections_commands_blueprint.cli.command("bulk-export")
@click.argument("collections_path", type=click.Path(exists=True, file_okay=False))
@click.option("--allow-overwrite", is_flag=True, help="Allow existing exports to be overwritten.")
@click.pass_context
def export_collections(ctx, collections_path: str, allow_overwrite: bool = False):
    """Export all collections to files in a directory."""
    collections_path = Path(collections_path)

    collections = current_app.collections.get_all()

    print(f"{len(collections)} collections to (re)export.")
    _collections_count = 1
    for collection in collections:
        print(f"# Collection {_collections_count}/{len(collections)}")
        collection_path = collections_path.joinpath(f"{collection.identifier}.json")
        ctx.invoke(
            export_collection,
            collection_identifier=collection.identifier,
            collection_path=collection_path,
            allow_overwrite=allow_overwrite,
        )
        _collections_count += 1
    print(f"Ok. {len(collections)} collections (re)exported.")


@collections_commands_blueprint.cli.command("remove")
@click.argument("collection-identifier")
@click.option("--force-remove", is_flag=True, help="Suppress interactive conformation.")
def remove_collection(collection_identifier, force_remove: bool):
    """Remove a collection."""
    if not force_remove:
        if not click.confirm(f"CONFIRM: Permanently remove collection '{collection_identifier}'?", abort=True):
            raise Abort()

    try:
        current_app.collections.delete(collection_identifier=collection_identifier)
        print(f"Ok. Collection '{collection_identifier}' removed.")
    except CollectionNotFoundException:
        print(f"No. Collection '{collection_identifier}' does not exist.")
        sys_exit(EX_USAGE)


@collections_commands_blueprint.cli.command("bulk-remove")
@click.option("--force-remove", is_flag=True, help="Suppress interactive conformation.")
@click.pass_context
def remove_collections(ctx, force_remove: bool):
    """Remove all collections."""
    collections = current_app.collections.get_all()

    if not force_remove:
        if not click.confirm(f"CONFIRM: Permanently remove all {len(collections)} collections?", abort=True):
            raise Abort()

    print(f"{len(collections)} collections to remove.")
    _collection_count = 1
    for collection in collections:
        print(f"# Collection {_collection_count}/{len(collections)}")
        ctx.invoke(remove_collection, collection_identifier=collection.identifier, force_remove=True)
        _collection_count += 1
    print(f"Ok. {len(collections)} collections removed.")


site_commands_blueprint = Blueprint("site", __name__)
site_commands_blueprint.cli.short_help = "Manage static site."

# noinspection PyUnresolvedReferences
@site_commands_blueprint.cli.command("build-items")
def build_items():
    """Build pages for all items."""
    items_output_path = Path(current_app.config["SITE_PATH"]).joinpath("items")

    try:
        with spinner():
            _records = list(current_app.records.retrieve_records())

        print(f"{len(_records)} item pages to generate.")
        _items_count = 1
        for _record in _records:
            print(f"# Item page {_items_count}/{len(_records)}")
            item = Item(record=_record)
            item_output_path = items_output_path.joinpath(f"{item.identifier}/index.html")
            item_output_path.parent.mkdir(exist_ok=True, parents=True)

            with open(str(item_output_path), mode="w") as item_file:
                item_file.write(render_template("app/_views/item-details.j2", item=item))
            print(f"Ok. Generated item page for '{item.identifier}'.")
            _items_count += 1
        print(f"Ok. {len(_records)} item pages generated.")
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
        with spinner():
            collections = current_app.collections.get_all()

        print(f"{len(collections)} collection pages to generate.")
        _collection_count = 1
        for collection in collections:
            print(f"# Collection page {_collection_count}/{len(collections)}")
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
        print(f"Ok. {len(collections)} collection pages generated.")
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
    """Build pages for all records (XML)."""
    stylesheets = ["iso-html", "iso-rubric", "iso-xml"]
    records_output_path = Path(current_app.config["SITE_PATH"]).joinpath("records")

    try:
        with spinner():
            records = list(current_app.records.retrieve_records())

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
                    record_xml_element = ElementTree(fromstring(record_xml))
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
        feedback_page_file.write(render_template(f"app/_views/feedback.j2"))
    print(f"Ok. feedback page generated.")


@site_commands_blueprint.cli.command("copy-assets")
def copy_assets():
    """Copy all static assets (CSS, JS, etc.)."""
    # workaround for lack of `dirs_exist_ok` option in Python 3.6
    try:
        Path(current_app.config["SITE_PATH"]).joinpath("static").unlink()
    except FileNotFoundError:
        pass
    copytree(
        str(Path("./scar_add_metadata_toolbox/static")), str(Path(current_app.config["SITE_PATH"]).joinpath("static"))
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


auth_commands_blueprint = Blueprint("auth", __name__)
auth_commands_blueprint.cli.short_help = "Manage user access to information and functions."


@auth_commands_blueprint.cli.command("sign-in")
def auth_sign_in():
    """Set user access token to use application."""
    auth_flow = current_app.config["CLIENT_AUTH"].initiate_device_flow(scopes=current_app.config["AUTH_CLIENT_SCOPES"])
    click.pause(
        f"To sign-in, visit 'https://microsoft.com/devicelogin', enter this code '{auth_flow['user_code']}' and then press any key..."
    )
    auth_payload = current_app.config["CLIENT_AUTH"].acquire_token_by_device_flow(auth_flow)
    current_app.auth_token.payload = auth_payload
    print(
        f"Ok. Access token for '{current_app.auth_token.access_token_bearer_insecure}' set in '{str(current_app.auth_token.session_file_path.absolute())}'."
    )


@auth_commands_blueprint.cli.command("sign-out")
def auth_sign_out():
    """Remove existing access token if present."""
    try:
        del current_app.auth_token.payload
    except FileNotFoundError:
        pass
    print(f"Ok. Access token removed.")


seeding_commands_blueprint = Blueprint("seed", __name__)
seeding_commands_blueprint.cli.short_help = "Manage sample resources for testing."


@seeding_commands_blueprint.cli.command("records")
@click.argument("count", type=click.INT)
def seed_records(count: int):  # pragma: no cover
    """Create sample records for testing."""
    faker = Faker()

    print(f"{count} records to insert.")
    for i in range(0, count):
        record = Record(
            config={
                "file_identifier": str(uuid4()),
                "language": "eng",
                "character_set": "uft-8",
                "hierarchy_level": "dataset",
                "contacts": [
                    {
                        "organisation": {
                            "name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                            "href": "https://ror.org/01rhff309",
                            "title": "ror",
                        },
                        "phone": "+44 (0)1223 221400",
                        "address": {
                            "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                            "city": "Cambridge",
                            "administrative_area": "Cambridgeshire",
                            "postal_code": "CB3 0ET",
                            "country": "United Kingdom",
                        },
                        "email": "magic@bas.ac.uk",
                        "online_resource": {
                            "href": "https://www.bas.ac.uk/team/magic",
                            "title": "Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                            "description": "General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                            "function": "information",
                        },
                        "role": ["pointOfContact"],
                    }
                ],
                "date_stamp": faker.date_this_year(),
                "metadata_standard": {
                    "name": "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data",
                    "version": "ISO 19115-2:2009(E)",
                },
                "reference_system_info": {
                    "authority": {
                        "title": {"value": "European Petroleum Survey Group (EPSG) Geodetic Parameter Registry"},
                        "dates": [{"date": date(2008, 11, 12), "date_type": "publication"}],
                        "contact": {
                            "organisation": {"name": "European Petroleum Survey Group"},
                            "email": "EPSGadministrator@iogp.org",
                            "online_resource": {
                                "href": "https://www.epsg-registry.org/",
                                "title": "EPSG Geodetic Parameter Dataset",
                                "description": "The EPSG Geodetic Parameter Dataset is a structured dataset of Coordinate Reference Systems and Coordinate Transformations, accessible through this online registry.",
                                "function": "information",
                            },
                            "role": ["publisher"],
                        },
                    },
                    "code": {
                        "value": "urn:ogc:def:crs:EPSG::3031",
                        "href": "http://www.opengis.net/def/crs/EPSG/0/3031",
                    },
                    "version": "6.18.3",
                },
                "maintenance": {"maintenance_frequency": "asNeeded", "progress": "completed"},
                "resource": {
                    "title": {"value": faker.sentence(nb_words=8)},
                    "dates": [
                        {"date_precision": "year", "date": faker.date_this_year(), "date_type": "creation"},
                        {"date": faker.date_this_year(), "date_type": "revision"},
                        {"date": faker.date_time_this_year(), "date_type": "publication"},
                        {"date": faker.date_time_this_year(), "date_type": "released"},
                    ],
                    "edition": f"{faker.random_int(min=1, max=15)}.{faker.random_int(min=1, max=9)}",
                    "abstract": faker.paragraph(nb_sentences=5),
                    "contacts": [
                        {
                            "individual": {
                                "name": f"{faker.last_name()}, {faker.first_name()}",
                                "href": f"https://orcid.org/{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}",
                                "title": "orcid",
                            },
                            "organisation": {
                                "name": "British Antarctic Survey",
                                "href": "https://ror.org/01rhff309",
                                "title": "ror",
                            },
                            "email": f"{str(faker.company_email()).split('@')[0]}@bas.ac.uk",
                            "online_resource": {
                                "href": f"https://orcid.org/{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}",
                                "title": "ORCID record",
                                "description": "ORCID is an open, non-profit, community-driven effort to create and maintain a registry of unique researcher identifiers and a transparent method of linking research activities and outputs to these identifiers.",
                                "function": "information",
                            },
                            "role": ["author"],
                        },
                        {
                            "individual": {
                                "name": f"{faker.last_name()}, {faker.first_name}",
                                "href": f"https://orcid.org/{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}",
                                "title": "orcid",
                            },
                            "organisation": {
                                "name": "British Antarctic Survey",
                                "href": "https://ror.org/01rhff309",
                                "title": "ror",
                            },
                            "email": f"{str(faker.company_email()).split('@')[0]}@bas.ac.uk",
                            "online_resource": {
                                "href": f"https://orcid.org/{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}",
                                "title": "ORCID record",
                                "description": "ORCID is an open, non-profit, community-driven effort to create and maintain a registry of unique researcher identifiers and a transparent method of linking research activities and outputs to these identifiers.",
                                "function": "information",
                            },
                            "role": ["author"],
                        },
                        {
                            "individual": {
                                "name": f"{faker.last_name()}, {faker.first_name}",
                                "href": f"https://orcid.org/{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}",
                                "title": "orcid",
                            },
                            "organisation": {
                                "name": "British Antarctic Survey",
                                "href": "https://ror.org/01rhff309",
                                "title": "ror",
                            },
                            "email": f"{str(faker.company_email()).split('@')[0]}@bas.ac.uk",
                            "online_resource": {
                                "href": f"https://orcid.org/{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}-{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}{faker.random_digit()}",
                                "title": "ORCID record",
                                "description": "ORCID is an open, non-profit, community-driven effort to create and maintain a registry of unique researcher identifiers and a transparent method of linking research activities and outputs to these identifiers.",
                                "function": "information",
                            },
                            "role": ["author"],
                        },
                        {
                            "organisation": {
                                "name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                                "href": "https://ror.org/01rhff309",
                                "title": "ror",
                            },
                            "phone": "+44 (0)1223 221400",
                            "address": {
                                "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                                "city": "Cambridge",
                                "administrative_area": "Cambridgeshire",
                                "postal_code": "CB3 0ET",
                                "country": "United Kingdom",
                            },
                            "email": "magic@bas.ac.uk",
                            "online_resource": {
                                "href": "https://www.bas.ac.uk/team/magic",
                                "title": "Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                                "description": "General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                                "function": "information",
                            },
                            "role": ["publisher", "pointOfContact", "distributor"],
                        },
                    ],
                    "maintenance": {"maintenance_frequency": "biannually", "progress": "completed"},
                    "keywords": [
                        {
                            "terms": [
                                {
                                    "term": str(faker.word()).capitalize(),
                                    "href": f"https://www.eionet.europa.eu/gemet/en/inspire-theme/{faker.random_lowercase_letter()}{faker.random_lowercase_letter()}",
                                }
                            ],
                            "type": "theme",
                            "thesaurus": {
                                "title": {
                                    "value": "General Multilingual Environmental Thesaurus - INSPIRE themes",
                                    "href": "http://www.eionet.europa.eu/gemet/inspire_themes",
                                },
                                "dates": [{"date": date(2008, 8, 16), "date_type": "publication"}],
                                "edition": "4.1.2",
                                "contact": {
                                    "organisation": {
                                        "name": "European Environment Information and Observation Network (EIONET), European Environment Agency (EEA)",
                                        "href": "https://ror.org/02k4b9v70",
                                        "title": "ror",
                                    },
                                    "email": "helpdesk@eionet.europa.eu",
                                    "online_resource": {
                                        "href": "https://www.eionet.europa.eu/gemet/en/themes/",
                                        "title": "GEMET INSPIRE Spatial Data Themes  General Multilingual Environmental Thesaurus",
                                        "description": "GEMET, the GEneral Multilingual Environmental Thesaurus, has been developed as a multilingual thesauri for indexing, retrieval and control of terms in order to save time, energy and funds.",
                                        "function": "information",
                                    },
                                    "role": ["publisher"],
                                },
                            },
                        },
                        {
                            "terms": [
                                {
                                    "term": "TOPOGRAPHY",
                                    "href": "https://gcmdservices.gsfc.nasa.gov/kms/concept/3e822484-c94a-457b-a32f-376fcbd6fd35",
                                },
                                {
                                    "term": f"{str(faker.word()).upper()} {str(faker.word()).upper()}",
                                    "href": f"https://gcmdservices.gsfc.nasa.gov/kms/concept/{str(uuid4())}",
                                },
                            ],
                            "type": "theme",
                            "thesaurus": {
                                "title": {
                                    "value": "Global Change Master Directory (GCMD) Science Keywords",
                                    "href": "https://earthdata.nasa.gov/about/gcmd/global-change-master-directory-gcmd-keywords",
                                },
                                "dates": [{"date": date(2020, 1, 9), "date_type": "publication"}],
                                "edition": "9.1",
                                "contact": {
                                    "organisation": {
                                        "name": "Global Change Data Center, Science and Exploration Directorate, Goddard Space Flight Center (GSFC) National Aeronautics and Space Administration (NASA)",
                                        "href": "https://ror.org/027ka1x80",
                                        "title": "ror",
                                    },
                                    "address": {
                                        "city": "Greenbelt",
                                        "administrative_area": "MD",
                                        "country": "United States of America",
                                    },
                                    "online_resource": {
                                        "href": "https://earthdata.nasa.gov/about/gcmd/global-change-master-directory-gcmd-keywords",
                                        "title": "Global Change Master Directory (GCMD) Keywords",
                                        "description": "The information provided on this page seeks to define how the GCMD Keywords are structured, used and accessed. It also provides information on how users can participate in the further development of the keywords.",
                                        "function": "information",
                                    },
                                    "role": ["publisher"],
                                },
                            },
                        },
                        {
                            "terms": [
                                {
                                    "term": "Topographic mapping",
                                    "href": "http://vocab.nerc.ac.uk/collection/T01/1/9cd3118f-55e2-4c07-b9f4-e260e40e8eb2/1/",
                                }
                            ],
                            "type": "theme",
                            "thesaurus": {
                                "title": {
                                    "value": "British Antarctic Survey research topics",
                                    "href": "http://vocab.nerc.ac.uk/collection/T01/1/",
                                },
                                "dates": [{"date": date(2020, 5, 6), "date_type": "publication"}],
                                "edition": "1",
                                "contact": {
                                    "organisation": {
                                        "name": "UK Polar Data Centre, British Antarctic Survey",
                                        "href": "https://ror.org/01rhff309",
                                        "title": "ror",
                                    },
                                    "phone": "+44 (0)1223 221400",
                                    "address": {
                                        "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                                        "city": "Cambridge",
                                        "administrative_area": "Cambridgeshire",
                                        "postal_code": "CB3 0ET",
                                        "country": "United Kingdom",
                                    },
                                    "email": "polardatacentre@bas.ac.uk",
                                    "online_resource": {
                                        "href": "https://www.bas.ac.uk/team/business-teams/information-services/uk-polar-data-centre/",
                                        "title": "UK Polar Data Centre (UK PDC) - BAS public website",
                                        "description": "General information about the NERC Polar Data Centre (UK PDC) from the British Antarctic Survey (BAS) public website.",
                                        "function": "information",
                                    },
                                    "role": ["publisher"],
                                },
                            },
                        },
                        {
                            "terms": [
                                {
                                    "term": "Antarctic Digital Database",
                                    "href": "http://vocab.nerc.ac.uk/collection/T02/1/8e91de62-b6e3-402e-b11f-73d2c1f37cff/",
                                }
                            ],
                            "type": "theme",
                            "thesaurus": {
                                "title": {
                                    "value": "British Antarctic Survey data catalogue collections",
                                    "href": "http://vocab.nerc.ac.uk/collection/T02/1/",
                                },
                                "dates": [{"date": date(2020, 5, 5), "date_type": "publication"}],
                                "edition": "1",
                                "contact": {
                                    "organisation": {
                                        "name": "UK Polar Data Centre, British Antarctic Survey",
                                        "href": "https://ror.org/01rhff309",
                                        "title": "ror",
                                    },
                                    "phone": "+44 (0)1223 221400",
                                    "address": {
                                        "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                                        "city": "Cambridge",
                                        "administrative_area": "Cambridgeshire",
                                        "postal_code": "CB3 0ET",
                                        "country": "United Kingdom",
                                    },
                                    "email": "polardatacentre@bas.ac.uk",
                                    "online_resource": {
                                        "href": "https://www.bas.ac.uk/team/business-teams/information-services/uk-polar-data-centre/",
                                        "title": "UK Polar Data Centre (UK PDC) - BAS public website",
                                        "description": "General information about the NERC Polar Data Centre (UK PDC) from the British Antarctic Survey (BAS) public website.",
                                        "function": "information",
                                    },
                                    "role": ["publisher"],
                                },
                            },
                        },
                        {
                            "terms": [
                                {
                                    "term": "ANTARCTICA",
                                    "href": "https://gcmdservices.gsfc.nasa.gov/kms/concept/70fb5a3b-35b1-4048-a8be-56a0d865281c",
                                }
                            ],
                            "type": "place",
                            "thesaurus": {
                                "title": {
                                    "value": "Global Change Master Directory (GCMD) Location Keywords",
                                    "href": "https://earthdata.nasa.gov/about/gcmd/global-change-master-directory-gcmd-keywords",
                                },
                                "dates": [{"date": date(2020, 1, 9), "date_type": "publication"}],
                                "edition": "9.1",
                                "contact": {
                                    "organisation": {
                                        "name": "Global Change Data Center, Science and Exploration Directorate, Goddard Space Flight Center (GSFC) National Aeronautics and Space Administration (NASA)",
                                        "href": "https://ror.org/027ka1x80",
                                        "title": "ror",
                                    },
                                    "address": {
                                        "city": "Greenbelt",
                                        "administrative_area": "MD",
                                        "country": "United States of America",
                                    },
                                    "online_resource": {
                                        "href": "https://earthdata.nasa.gov/about/gcmd/global-change-master-directory-gcmd-keywords",
                                        "title": "Global Change Master Directory (GCMD) Keywords",
                                        "description": "The information provided on this page seeks to define how the GCMD Keywords are structured, used and accessed. It also provides information on how users can participate in the further development of the keywords.",
                                        "function": "information",
                                    },
                                    "role": ["publisher"],
                                },
                            },
                        },
                    ],
                    "constraints": {
                        "access": [
                            {
                                "restriction_code": "otherRestrictions",
                                "inspire_limitations_on_public_access": "noLimitations",
                            }
                        ],
                        "usage": [
                            {
                                "copyright_licence": {
                                    "statement": "This information is licensed under the Create Commons Attribution 4.0 International Licence (CC BY 4.0). To view this licence, visit https://creativecommons.org/licenses/by/4.0/",
                                    "href": "https://creativecommons.org/licenses/by/4.0/",
                                }
                            },
                            {
                                "required_citation": {
                                    "statement": "Please cite this item as: 'Produced using data from the SCAR Antarctic Digital Database'."
                                }
                            },
                        ],
                    },
                    "spatial_representation_type": "vector",
                    "language": "eng",
                    "character_set": "uft-8",
                    "topics": ["environment", "geoscientificInformation"],
                    "extent": {
                        "geographic": {
                            "bounding_box": {
                                "west_longitude": -180.0,
                                "east_longitude": 180.0,
                                "south_latitude": -90.0,
                                "north_latitude": -60.0,
                            }
                        },
                        "temporal": {"period": {"start": faker.date_this_decade(), "end": faker.date_this_decade()}},
                    },
                    "formats": [
                        {"format": "Web Map Service"},
                        {
                            "format": "GeoPackage",
                            "href": "https://www.iana.org/assignments/media-types/application/geopackage+sqlite3",
                            "version": "1.2",
                        },
                        {"format": "Shapefile", "href": "https://support.esri.com/en/white-paper/279", "version": "1"},
                    ],
                    "transfer_options": [
                        {
                            "online_resource": {
                                "href": f"https://maps.bas.ac.uk/antarctic/wms?layer=add:{'-'.join(faker.words(nb=4))}",
                                "title": "Web Map Service (WMS)",
                                "description": "Access information as a OGC Web Map Service layer.",
                                "function": "download",
                            }
                        },
                        {
                            "size": {"unit": "kB", "magnitude": faker.random_int()},
                            "online_resource": {
                                "href": f"https://data.bas.ac.uk/download/{str(uuid4())}",
                                "title": "GeoPackage",
                                "description": "Download information as a OGC GeoPackage.",
                                "function": "download",
                            },
                        },
                        {
                            "size": {"unit": "kB", "magnitude": faker.random_int()},
                            "online_resource": {
                                "href": f"https://data.bas.ac.uk/download/{str(uuid4())}",
                                "title": "Shapefile",
                                "description": "Download information as an ESRI Shapefile.",
                                "function": "download",
                            },
                        },
                    ],
                    "lineage": faker.paragraph(nb_sentences=3),
                },
            }
        )
        print(f"# Record {i + 1}/{count}")
        current_app.records.insert_record(record=record)
        print(f"Ok. Inserted record '{record.identifier}.")
    print(f"Ok. Inserted {count} records.")


@seeding_commands_blueprint.cli.command("collections")
@click.argument("count", type=click.INT)
def seed_collections(count: int):  # pragma: no cover
    """Create sample collections for testing."""
    faker = Faker()

    item_identifiers = current_app.records.list_record_identifiers()

    print(f"{count} collections to insert.")
    for i in range(0, count):
        print(f"# Collection {i + 1}/{count}")
        collection = Collection(
            config={
                "identifier": str(uuid4()),
                # Exempting Bandit security issues (pseudo-random generators), not used for security/cryptography
                "title": faker.sentence(nb_words=5),  # nosec
                "summary": "\n\n".join(faker.paragraphs(nb=random_choice(range(1, 4)))),  # nosec
                "topics": ["Topographic Mapping"],
                "publishers": ["Mapping and Geographic Information Centre (MAGIC)"],
                "item_identifiers": random_choices(
                    item_identifiers, k=random_choice(range(1, len(item_identifiers)))  # nosec
                ),
            }
        )
        current_app.collections.add(collection)
        print(f"Ok. Inserted collection '{collection.identifier}.")
    print(f"Ok. Inserted {count} collections.")
