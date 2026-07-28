import json
import logging
import os
import subprocess
import sys
from http import HTTPStatus
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer, RequestMatcher
from pytest_mock import MockerFixture
from werkzeug import Response

from lantern.catalogues.bas import BasCatalogue
from lantern.config import Config
from lantern.contrib.non_interactive_publishing_workflow import (
    Args,
    _clean_input_records,
    _commit_records,
    _ensure_changeset,
    _filter_records,
    _parse_records,
    _reduce_records,
    _run,
    _webhook,
    entrypoint,
)
from lantern.models.record.record import Record
from lantern.models.repository import GitUpsertResults
from tests.lantern_tests.models.record.test_record import TestRecord


class TestPublishingWorkflow:
    """Test non-interactive publishing workflow contrib module."""

    @pytest.mark.parametrize(
        "record",
        [
            TestRecord._make_valid_record(),  # pass
            TestRecord._make_record("1"),  # fail, invalid file ID for catalogue record
            TestRecord._make_valid_record(
                "25dba66e-a12b-477a-be13-b8ee5f023a69"
            ),  # warn, valid but unsupported extra config
        ],
    )
    def test_parse_records(
        self, caplog: pytest.LogCaptureFixture, fx_logger: logging.Logger, tmp_path: Path, record: Record
    ):
        """Can parse valid records from a directory."""
        search_path = tmp_path.joinpath("records")
        search_path.mkdir()
        record_path = search_path.joinpath(f"{record.file_identifier}.json")
        record_str = record.dumps_json(strip_admin=False)
        if record.file_identifier == "25dba66e-a12b-477a-be13-b8ee5f023a69":
            # Add unsupported (but valid) config
            record_config = json.loads(record_str)
            record_config["identification"]["credit"] = "x"
            record_str = json.dumps(record_config, ensure_ascii=False)
        record_path.write_text(record_str)

        results = _parse_records(logger=fx_logger, search_path=search_path)
        if record.file_identifier == "1":
            assert len(results) == 0
            assert "Record '1' does not validate, skipping." in caplog.text
        else:
            assert results == {record_path: record}
        if record.file_identifier == "25dba66e-a12b-477a-be13-b8ee5f023a69":
            assert (
                "Record '25dba66e-a12b-477a-be13-b8ee5f023a69' contains unsupported content the catalogue will ignore."
                in caplog.text
            )

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("state", ["created", "exists", "updated"])
    def test_filter_records(
        self,
        caplog: pytest.LogCaptureFixture,
        fx_logger: logging.Logger,
        fx_bas_catalogue: BasCatalogue,
        fx_config: Config,
        tmp_path: Path,
        state: str,
    ):
        """Can filter records based on whether they are different to a remote store."""
        import_path = tmp_path.joinpath("records")
        import_path.mkdir()
        record = TestRecord._make_valid_record()
        record_path = import_path / f"{record.file_identifier}.json"
        record_path.write_text(record.dumps_json(strip_admin=False))
        record_paths = {record_path: record}
        expected = record_paths if state != "exists" else {}

        results = _filter_records(
            logger=fx_logger,
            cat=fx_bas_catalogue,
            branch=fx_config.STORE_GITLAB_DEFAULT_BRANCH,
            record_paths=record_paths,
        )
        assert results == expected
        if state == "exists":
            assert f"Record '{record.file_identifier}' is the same as stored version, skipping." in caplog.text

    def test_clean_input_records(self, fx_logger: logging.Logger, tmp_path: Path):
        """Can remove record files included in commit results."""
        import_path = tmp_path.joinpath("records")
        import_path.mkdir()
        record = TestRecord._make_valid_record()
        record_path = import_path / "x.json"  # intentionally don't name after the file identifier
        record_path.write_text(record.dumps_json(strip_admin=False))
        assert record_path.exists()

        commit = GitUpsertResults(
            branch="x",
            commit="x",
            new_identifiers=[record.file_identifier],
            updated_identifiers=[],
        )
        _clean_input_records(logger=fx_logger, record_paths={record_path: record}, results=commit)
        assert not record_path.exists()

    def test_reduce_records(
        self, mocker: MockerFixture, fx_logger: logging.Logger, fx_bas_catalogue: BasCatalogue, tmp_path: Path
    ):
        """
        Can reduce a set of records by combining record parse and filter methods.

        Filter method mocked to avoid GitLab store requests.
        """
        import_path = tmp_path.joinpath("records")
        import_path.mkdir()
        record = TestRecord._make_valid_record()
        record_path = import_path / f"{record.file_identifier}.json"
        record_path.write_text(record.dumps_json(strip_admin=False))
        expected = {record_path: record}

        mocker.patch("lantern.contrib.non_interactive_publishing_workflow._filter_records", return_value=expected)

        args = Args(
            env="testing",
            path=import_path,
            changeset_base="test",
            changeset_title="Workflow test",
            changeset_message="...",
            commit_title="Test commit from workflow",
            commit_message="...",
            author_name="Connie Watson",
            author_email="conwat@bas.ac.uk",
        )
        results = _reduce_records(logger=fx_logger, cat=fx_bas_catalogue, args=args)
        assert results == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("state", ["created", "exists"])
    def test_ensure_changeset(
        self, fx_logger: logging.Logger, fx_bas_catalogue: BasCatalogue, tmp_path: Path, state: str
    ):
        """Can create or reuse a merge request for a changeset."""
        args = Args(
            env="testing",
            path=tmp_path,
            changeset_base="test",
            changeset_title="Workflow test",
            changeset_message="...",
            commit_title="Test commit from workflow",
            commit_message="...",
            author_name="Connie Watson",
            author_email="conwat@bas.ac.uk",
        )
        result = _ensure_changeset(logger=fx_logger, cat=fx_bas_catalogue, args=args)
        assert result == "https://gitlab.example.com/group/project/-/merge_requests/1"

    def test_commit_records(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_config: Config,
        fx_bas_catalogue: BasCatalogue,
        tmp_path: Path,
    ):
        """
        Can commit a set of records and remove corresponding config files.

        Catalogue commit method is mock as catalogue methods are tested elsewhere.
        """
        import_path = tmp_path.joinpath("records")
        import_path.mkdir()
        record = TestRecord._make_valid_record()
        record_path = import_path / f"{record.file_identifier}.json"
        record_path.write_text(record.dumps_json(strip_admin=False))
        expected = GitUpsertResults(
            branch="x",
            commit="x",
            new_identifiers=[record.file_identifier],
            updated_identifiers=[],
        )

        mocker.patch("lantern.contrib.non_interactive_publishing_workflow.BasCatalogue.commit", return_value=expected)

        args = Args(
            env="testing",
            path=import_path,
            changeset_base="test",
            changeset_title="Workflow test",
            changeset_message="...",
            commit_title="Test commit from workflow",
            commit_message="...",
            author_name="Connie Watson",
            author_email="conwat@bas.ac.uk",
        )
        results = _commit_records(
            logger=fx_logger, config=fx_config, cat=fx_bas_catalogue, records={record_path: record}, args=args
        )
        assert results == expected
        assert not record_path.exists()

    def test_webhook(self, fx_logger: logging.Logger, fx_config: Config, httpserver: HTTPServer):
        """Can post workflow results to webhook."""
        _route = "/webhook"
        httpserver.expect_request(_route).respond_with_response(Response(status=HTTPStatus.ACCEPTED))
        expected = {
            "commit": {
                "branch": "x",
                "commit": "x",
                "new_identifiers": ["x"],
                "updated_identifiers": [],
                "url": f"{fx_config.TEMPLATES_ITEM_VERSIONS_ENDPOINT}/-/commit/x",
            },
            "merge_request": {"url": "x"},
        }

        commit = GitUpsertResults(
            branch=expected["commit"]["branch"],
            commit=expected["commit"]["commit"],
            new_identifiers=expected["commit"]["new_identifiers"],
            updated_identifiers=expected["commit"]["updated_identifiers"],
        )
        _webhook(
            logger=fx_logger,
            config=fx_config,
            commit=commit,
            mr_url=expected["merge_request"]["url"],
            wh_url=httpserver.url_for(_route),
        )

        httpserver.assert_request_made(RequestMatcher(_route))
        for _request, response in httpserver.iter_matching_requests(RequestMatcher(_route)):
            assert _request.json == expected
            assert response.status_code == HTTPStatus.ACCEPTED

    def test_parse_args(self, tmp_path: Path):
        """Can use argparse to get workflow arguements."""
        import_path = tmp_path / "records"
        import_path.mkdir()
        script_path = tmp_path / "script.py"

        with script_path.open(mode="w") as f:
            f.write("""
#!/usr/bin/env python3
import json
from dataclasses import asdict
from lantern.contrib.non_interactive_publishing_workflow import parse_args
args = parse_args()
d = asdict(args)
d['path'] = str(d['path'])
print(json.dumps(d))
""")

        expected = Args(
            env="testing",
            path=import_path,
            changeset_base="test",
            changeset_title="Workflow test",
            changeset_message="...",
            commit_title="Test commit from workflow",
            commit_message="...",
            author_name="Connie Watson",
            author_email="conwat@bas.ac.uk",
            webhook="https://example.com/webhook",
        )

        args = {
            "--site": expected.env,
            "--path": str(expected.path),
            "--changeset-base": expected.changeset_base,
            "--changeset-title": expected.changeset_title,
            "--changeset-message": expected.changeset_message,
            "--commit-title": expected.commit_title,
            "--commit-message": expected.commit_message,
            "--author-name": expected.author_name,
            "--author-email": expected.author_email,
            "--webhook": expected.webhook,
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
        assert result.returncode == 0

        args = Args(**json.loads(result.stdout))
        args.path = Path(args.path)
        assert args == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.cov()
    @pytest.mark.parametrize("cov", ["no-records", "no-webhook"])
    def test_run(
        self,
        mocker: MockerFixture,
        caplog: pytest.LogCaptureFixture,
        fx_logger: logging.Logger,
        fx_config: Config,
        tmp_path: Path,
        cov: str,
    ):
        """
        Can exercise conditionals for no records and no webhook, for coverage tests.

        Note: For 'no-webhook', the VCR recording is the same as for 'test_entrypoint' but without the last request.
        """
        # Rsync call for trusted content doesn't use requests etc. so not captured by VCR
        mock = mocker.MagicMock()
        mock.returncode = 0
        mocker.patch("sysrsync.runner.subprocess.run", return_value=mock)

        # Ensure cache is ephemeral per test
        os.environ["LANTERN_STORE_GITLAB_CACHE_PATH"] = str(tmp_path.joinpath("cache"))

        record = TestRecord._make_valid_record()  # fid: 5d5b4e21-fd32-409c-be83-ca1c339903e5
        import_path = tmp_path.joinpath("records")
        import_path.mkdir()
        if cov != "no-records":
            import_path.joinpath(f"{record.file_identifier}.json").write_text(record.dumps_json(strip_admin=False))

        args = Args(
            env="testing",
            path=import_path,
            changeset_base="test",
            changeset_title="Workflow test",
            changeset_message="...",
            commit_title="Test commit from workflow",
            commit_message="...",
            author_name="Connie Watson",
            author_email="conwat@bas.ac.uk",
            webhook="https://example.com/webhook",
        )
        if cov == "no-webhook":
            args.webhook = None

        _run(logger=fx_logger, config=fx_config, args=args)
        if cov == "no-records":
            assert "No new or updated records to commit, exiting." in caplog.text

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_entrypoint(self, mocker: MockerFixture, tmp_path: Path):
        """Can run non-interactive publishing workflow."""
        # Rsync call for trusted content doesn't use requests etc. so not captured by VCR
        mock = mocker.MagicMock()
        mock.returncode = 0
        mocker.patch("sysrsync.runner.subprocess.run", return_value=mock)

        # Ensure cache is ephemeral per test
        os.environ["LANTERN_STORE_GITLAB_CACHE_PATH"] = str(tmp_path.joinpath("cache"))

        record = TestRecord._make_valid_record()  # fid: 5d5b4e21-fd32-409c-be83-ca1c339903e5
        import_path = tmp_path.joinpath("records")
        import_path.mkdir()
        import_path.joinpath(f"{record.file_identifier}.json").write_text(record.dumps_json(strip_admin=False))

        args = Args(
            env="testing",
            path=import_path,
            changeset_base="test",
            changeset_title="Workflow test",
            changeset_message="...",
            commit_title="Test commit from workflow",
            commit_message="...",
            author_name="Connie Watson",
            author_email="conwat@bas.ac.uk",
            webhook="https://example.com/webhook",
        )
        entrypoint(args)
