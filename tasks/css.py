import logging
import subprocess
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from boto3 import client as S3Client  # noqa: N812
from jinja2 import Environment, FileSystemLoader, select_autoescape
from moto import mock_aws
from tests.conftest import _init_fake_store
from tests.resources.records.admin_keys.testing_keys import load_keys
from tests.resources.stores.fake_records_store import FakeRecordsStore

from lantern.config import Config as BaseConfig
from lantern.exporters.site import SiteExporter
from lantern.exporters.verification import VerificationReport
from lantern.models.site import ExportMeta
from lantern.models.verification.enums import VerificationResult, VerificationType
from lantern.models.verification.jobs import VerificationJob
from lantern.models.verification.types import VerificationContext


# noinspection PyPep8Naming
class Config(BaseConfig):
    """Local config class."""

    def __init__(self) -> None:
        super().__init__()

    @property
    def AWS_ACCESS_ID(self) -> str:  # noqa: N802
        """AWS access key ID."""
        return "x"

    @property
    def AWS_ACCESS_SECRET(self) -> str:  # noqa: N802
        """AWS access key secret."""
        return "x"


def export_test_site(export_path: Path) -> None:
    """Export test records as a static site."""
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    store = FakeRecordsStore(logger=logger)

    with mock_aws():
        s3_client = S3Client(
            "s3",
            aws_access_key_id="x",
            aws_secret_access_key="x",  # noqa: S106
            region_name="eu-west-1",
        )

    meta = ExportMeta(
        base_url="x",
        build_key="x",
        html_title="",
        sentry_src="x",
        plausible_domain="x",
        embedded_maps_endpoint="x",
        items_enquires_endpoint="x",
        items_enquires_turnstile_key="x",
        generator="x",
        version="x",
        export_path=export_path,
        s3_bucket="x",
        parallel_jobs=1,
        admin_meta_keys=load_keys(),
        trusted=True,
    )

    exporter = SiteExporter(
        config=Config(),
        meta=meta,
        s3=s3_client,
        logger=logger,
        init_store=_init_fake_store,
        selected_identifiers={record.file_identifier for record in store.select()},
    )
    exporter.export()

    # Include verification report
    report_path = export_path / "-" / "verification" / "index.html"
    context: VerificationContext = {
        "BASE_URL": "https://example.com",
        "SHAREPOINT_PROXY_ENDPOINT": "x",
        "SAN_PROXY_ENDPOINT": "x",
    }
    jobs = [
        VerificationJob(
            result=VerificationResult.PASS,
            type=VerificationType.SITE_PAGES,
            url="https://example.com/-/index",
            context=context,
            data={"duration": timedelta(microseconds=1)},
        ),
        VerificationJob(
            result=VerificationResult.FAIL,
            type=VerificationType.ITEM_PAGES,
            url="https://example.com/items/123",
            context=context,
            data={"file_identifier": "x", "duration": timedelta(microseconds=1)},
        ),
        VerificationJob(
            result=VerificationResult.SKIP,
            type=VerificationType.ITEM_PAGES,
            url="https://example.com/items/123",
            context=context,
            data={"file_identifier": "x"},
        ),
    ]
    report = VerificationReport(meta.site_metadata, jobs=jobs, context=context)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w") as report_file:
        report_file.write(report.dumps())

    print(f"Exported test site inc. verification report to '{export_path.resolve()}'")


def regenerate_styles(tw_bin: Path, site_path: Path, base_path: Path) -> None:
    """
    Regenerate app Tailwind CSS styles.

    Steps:
    - render a Jinja2 template to produce source CSS (to dynamically set the Tailwind content path) as a temp file
    - process this with the Tailwind CLI into an output CSS file
    - append a trailing new line to the output file (to satisfy linters)
    """
    templates_path = base_path / "templates"
    output_path = base_path / "css" / "main.css"
    _jinja = Environment(loader=FileSystemLoader(str(templates_path)), autoescape=select_autoescape())

    src_css = _jinja.get_template("_assets/css/main.css.j2").render(site_path=site_path.resolve())

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
    """Entrypoint."""
    site_dir = TemporaryDirectory()
    site_path = Path(site_dir.name)
    tw_bin = Path(".venv/bin/tailwindcss")
    base_path = Path("src/lantern/resources")

    export_test_site(export_path=site_path)
    regenerate_styles(tw_bin=tw_bin, site_path=site_path, base_path=base_path)
    site_dir.cleanup()
    print("Updated site styles. Re-run build to apply.")


if __name__ == "__main__":
    main()
