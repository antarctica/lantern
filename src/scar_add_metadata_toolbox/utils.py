from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from awscli.clidriver import create_clidriver
from flask import current_app, render_template
from jinja2 import PackageLoader, PrefixLoader
from lxml.etree import (
    ElementTree,
    ProcessingInstruction,
    fromstring,
    tostring,
)  # nosec - see 'lxml` package (bandit)' section in README

from scar_add_metadata_toolbox.classes import Item, Record
from scar_add_metadata_toolbox.csw import CSWServer


def _create_app_jinja_loader() -> PrefixLoader:
    """
    Create a Jinja environment's template sources.

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


def _create_csw_repositories(repositories_config: dict) -> dict[str, CSWServer]:
    """
    Create application CSW servers.

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


def aws_cli(*cmd) -> None:  # noqa: ANN002
    """
    AWS CLI python bindings.

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
            msg = f"AWS CLI exited with code {exit_code}"
            raise RuntimeError(msg)
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def _build_item(record: Record) -> None:
    """Build page for specified record."""
    items_output_path = Path(current_app.config["SITE_PATH"]).joinpath("items")

    item = Item(record=record)
    item_output_path = items_output_path.joinpath(f"{item.identifier}/index.html")
    item_output_path.parent.mkdir(exist_ok=True, parents=True)

    with item_output_path.open(mode="w") as item_file:
        # noinspection PyUnresolvedReferences
        item_file.write(render_template("app/_views/item-details.j2", item=item))


RECORD_STYLESHEETS = ["iso-html", "iso-rubric", "iso-xml"]


def _build_record(
    record: Record,
    on_stylesheet_begin: Callable[[int, str], None] | None = None,
    on_stylesheet_done: Callable[[int, str], None] | None = None,
) -> None:
    """Build pages for specified record (XML)."""
    records_output_path = Path(current_app.config["SITE_PATH"]).joinpath("records")

    _stylesheet_count = 1
    for stylesheet in RECORD_STYLESHEETS:
        if on_stylesheet_begin is not None:
            on_stylesheet_begin(_stylesheet_count, stylesheet)

        record_output_path = records_output_path.joinpath(f"{record.identifier}/{stylesheet}/{record.identifier}.xml")
        record_output_path.parent.mkdir(exist_ok=True, parents=True)

        with record_output_path.open(mode="w") as record_file:
            record_xml = record.dumps(dump_format="xml")
            record_xml_element = ElementTree(fromstring(record_xml.encode()))  # noqa: S320
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

        if on_stylesheet_done is not None:
            on_stylesheet_done(_stylesheet_count, stylesheet)

        _stylesheet_count += 1
