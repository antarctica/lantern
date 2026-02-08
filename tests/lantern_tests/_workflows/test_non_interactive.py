import subprocess
import sys
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from tests.lantern_tests.models.record.test_record import TestRecord


class TestPublishingWorkflow:
    """Test non-interactive publishing workflow."""

    @staticmethod
    def _get_script_path() -> Path:
        return (
            Path(__file__)
            .parent.parent.parent.parent.joinpath("resources/scripts/non-interactive-publishing-workflow.py")
            .resolve()
        )

    @staticmethod
    def _make_records_path(tmp_path: Path) -> Path:
        """Create a records dir under the pytest-managed tmp_path and write one record."""
        records_path = tmp_path / "records"
        records_path.mkdir(parents=True, exist_ok=True)
        record = TestRecord._make_valid_record()
        (records_path / f"{record.file_identifier}.json").write_text(record.dumps_json(strip_admin=False))
        return records_path

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_run(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Can run workflow in isolated subprocess."""
        mock = mocker.MagicMock()
        mock.returncode = 0
        mocker.patch("sysrsync.runner.subprocess.run", return_value=mock)

        records_path = self._make_records_path(tmp_path)
        script_path = self._get_script_path()

        args = {
            "--path": str(records_path),
            "--changeset-base": "test",
            "--changeset-title": "Workflow test",
            "--changeset-message": "...",
            "--commit-title": "Test commit from workflow",
            "--commit-message": "...",
            "--author-name": "Connie Watson",
            "--author-email": "conwat@bas.ac.uk",
            "--webhook": "https://example.com/webhook",
        }

        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                str(script_path),
                *[f"{opt}={val}" for opt, val in args.items()],
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Script failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
