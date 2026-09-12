# Compile Tailwind classes used in static site output

import logging
import subprocess
from http import HTTPStatus
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, select_autoescape
from tests.resources.admin_keys import test_keys
from tests.resources.catalogues.fake_catalogue import FakeCatalogue

from lantern.config import Config as ConfigBase
from lantern.models.checks import Check, CheckState, CheckType
from lantern.models.site import ExportMeta
from lantern.outputs.checks import ChecksOutput

if TYPE_CHECKING:
    from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys


class Config(ConfigBase):
    """Config with test keys."""

    @property
    def ADMIN_METADATA_KEYS(self) -> AdministrationKeys:  # noqa: N802
        """Administration metadata keys."""
        return test_keys()


def export_test_site(export_path: Path) -> None:
    """Export test records as a static site."""
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    config = Config()
    catalogue = FakeCatalogue(logger=logger, config=config, base_path=export_path)
    catalogue.export(trusted=False)
    catalogue.export(trusted=True)  # To ensure admin tab classes are generated

    # Include fake checks report - mixed/different site env used to ensure both styles are included
    report_path = export_path / "-" / "checks" / "index.html"
    checks = [
        Check(
            type=CheckType.SITE_HEALTH,
            url="x",
            state=CheckState.PASS,
            duration=0.1,
            result_http_status=HTTPStatus.OK,
            result_output="OK",
        ),
        Check(
            type=CheckType.RECORD_PAGES_XML,
            url="x",
            file_identifier="x",
            state=CheckState.FAILED,
            duration=0.1,
            result_http_status=HTTPStatus.NOT_FOUND,
            result_output="Bad",
        ),
        Check(
            type=CheckType.DOWNLOADS_SHAREPOINT_OTHER,
            url="x",
            file_identifier="x",
            state=CheckState.SKIPPED,
            duration=0.0,
        ),
        Check(
            type=CheckType.ITEM_ALIASES,
            url="x",
            file_identifier="x",
            state=CheckState.PENDING,
            duration=0.0,
        ),
    ]
    meta = ExportMeta.from_config(config=config, env="testing", build_repo_ref="83fake48", trusted=False)
    output = ChecksOutput(logger=logger, meta=meta, checks=checks)
    report_data = output.content[1]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w") as report_file:
        report_file.write(report_data.content)  # ty:ignore[invalid-argument-type]

    print(f"Exported test site inc. checks report to '{export_path.resolve()}'")


def regenerate_styles(tw_bin: Path, site_paths: list[Path], base_path: Path) -> None:
    """
    Regenerate app Tailwind CSS styles.

    Steps:
    - render a Jinja2 template to produce source CSS (to dynamically set Tailwind content paths) as a temp file
    - process this with the Tailwind CLI into an output CSS file
    - append a trailing new line to the output file (to satisfy linters)

    Note: The templated CSS input file references one or more sources of rendered/reference content which the Tailwind
    CLI uses for tree-shaking needed classes. In this task, these content paths are temporary (un)trusted site builds.
    Where classes are conditional based on templates, and are not triggered by the contents of these builds they won't
    be included in the output CSS.
    """
    templates_path = base_path / "templates"
    content_paths = [p.resolve() for p in site_paths]
    output_path = base_path / "css" / "main.css"
    _jinja = Environment(loader=FileSystemLoader(str(templates_path)), autoescape=select_autoescape())

    src_css = _jinja.get_template("_assets/css/main.css.j2").render(content_paths=content_paths)

    with TemporaryDirectory() as tmp_dir:
        src_path = Path(tmp_dir) / "main.src.css"
        # write templated source CSS to a temp file
        with src_path.open("w") as src_file:
            src_file.write(src_css)
        # process with Tailwind CLI
        subprocess.run(  # noqa: S603
            [tw_bin, "-i", str(src_path.resolve()), "-o", str(output_path.resolve()), "--minify"], check=True
        )
    # append trailing new line to output file
    with output_path.open("a") as out_file:
        out_file.write("\n")

    print(f"Saved regenerated styles to '{output_path.resolve()}'")


def main() -> None:
    """
    Entrypoint.

    `tmp_dir` isn't used as the `site_path` as a parallel '-trusted' path will be created by `export_test_site()`.
    I.e. `tmp_dir/site` and `tmp_dir/site-trusted` will be created.
    """
    tmp_dir = TemporaryDirectory()
    site_path = Path(tmp_dir.name) / "site"
    tw_bin = Path(".venv/bin/tailwindcss")
    base_path = Path("src/lantern/resources")

    export_test_site(export_path=site_path)
    regenerate_styles(
        tw_bin=tw_bin, site_paths=[site_path, site_path.with_name(f"{site_path.name}-trusted")], base_path=base_path
    )
    tmp_dir.cleanup()
    print("Updated site styles. Re-run build to apply.")


if __name__ == "__main__":
    main()
