import logging
import subprocess
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from boto3 import client as S3Client  # noqa: N812
from jinja2 import Environment, FileSystemLoader, select_autoescape
from moto import mock_aws
from tests.resources.stores.fake_records_store import FakeRecordsStore

from lantern.config import Config as BaseConfig
from lantern.exporters.site import SiteExporter
from lantern.exporters.verification import VerificationReport
from lantern.models.verification.enums import VerificationResult, VerificationType
from lantern.models.verification.jobs import VerificationJob
from lantern.models.verification.types import VerificationContext


# noinspection PyPep8Naming
class Config(BaseConfig):
    """Local config class."""

    def __init__(self, export_path: Path) -> None:
        super().__init__()
        self._path = export_path

    @property
    def EXPORT_PATH(self) -> Path:
        """Export path."""
        return self._path

    @property
    def AWS_S3_BUCKET(self) -> str:
        """S3 bucket name."""
        return "x"

    @property
    def AWS_ACCESS_ID(self) -> str:
        """AWS access key ID."""
        return "x"

    @property
    def AWS_ACCESS_SECRET(self) -> str:
        """AWS access key secret."""
        return "x"

    @property
    def VERIFY_SHAREPOINT_PROXY_ENDPOINT(self) -> str:
        """SharePoint proxy endpoint."""
        return "x"


def export_test_site(export_path: Path) -> None:
    """Export test records as a static site."""
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    config = Config(export_path=export_path)
    store = FakeRecordsStore(logger=logger)
    store.populate()

    with mock_aws():
        s3_client = S3Client(
            "s3",
            aws_access_key_id="x",
            aws_secret_access_key="x",  # noqa: S106
            region_name="eu-west-1",
        )

    exporter = SiteExporter(config=config, s3=s3_client, logger=logger, get_record=store.get)
    exporter.select(file_identifiers={record.file_identifier for record in store.records})
    exporter.export()

    # Include verification report
    report_path = export_path / "-" / "verification" / "index.html"
    context: VerificationContext = {
        "BASE_URL": "https://example.com",
        "SHAREPOINT_PROXY_ENDPOINT": config.VERIFY_SHAREPOINT_PROXY_ENDPOINT,
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
    report = VerificationReport(config=config, jobs=jobs, context=context)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w") as report_file:
        report_file.write(report.dumps())

    print(f"Exported test site inc. verification report to '{export_path.resolve()}'")


def regenerate_styles(tw_bin: Path, site_path: Path, output_path: Path) -> None:
    """Regenerate app Tailwind CSS styles."""
    _jinja = Environment(loader=FileSystemLoader("src/lantern/resources/css"), autoescape=select_autoescape())
    src_css = _jinja.get_template("main.css.j2").render(site_path=site_path.resolve())

    with TemporaryDirectory() as tmp_dir:
        src_path = Path(tmp_dir) / "main.src.css"
        with src_path.open("w") as src_file:
            src_file.write(src_css)

        subprocess.run(  # noqa: S603
            [tw_bin, "-i", str(src_path.resolve()), "-o", str(output_path.resolve()), "--minify"], check=True
        )

    # append trailing new line
    with output_path.open("a") as out_file:
        out_file.write("\n")

    print(f"Saved regenerated styles to '{output_path.resolve()}'")


def main() -> None:
    """Entrypoint."""
    site_dir = TemporaryDirectory()
    site_path = Path(site_dir.name)
    tw_bin = Path(".venv/bin/tailwindcss")
    styles_path = Path("src/lantern/resources/css/main.css")

    export_test_site(export_path=site_path)
    regenerate_styles(tw_bin=tw_bin, site_path=site_path, output_path=styles_path)
    site_dir.cleanup()
    print("Updated site styles. Re-run build to apply.")


if __name__ == "__main__":
    main()
