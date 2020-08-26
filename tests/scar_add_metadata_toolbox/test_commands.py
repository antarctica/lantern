import json

from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest import mock
from unittest.mock import patch

import pytest

from tests.conftest import TestRecords, TestCollections
from tests.scar_add_metadata_toolbox.classes import MockCollections


class TestCommandRecordsList:
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_list(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "list"])
        assert result.exit_code == 0
        assert "│ 7e3719b4-60a4-4b4e-aa84-cee7a5e7218f │ Test Record 1 (Published)   │ Published   │" in result.output
        assert "│ 39d47e50-f94f-43c5-9060-510d9374b81b │ Test Record 2 (Unpublished) │ Unpublished │" in result.output
        assert "Ok. 2 records." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_not_setup")
    def test_cli_records_list_csw_not_setup(self, app_runner_mocked_csw_not_setup):
        result = app_runner_mocked_csw_not_setup.invoke(args=["records", "list"])
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_auth_token_error")
    def test_cli_records_list_auth_token_error(self, app_runner_mocked_csw_auth_token_error):
        result = app_runner_mocked_csw_auth_token_error.invoke(args=["records", "list"])
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_missing_auth_token")
    def test_cli_records_list_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token):
        result = app_runner_mocked_csw_missing_auth_token.invoke(args=["records", "list"])
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_insufficient_auth_token")
    def test_cli_records_list_auth_token_insufficient(self, app_runner_mocked_csw_insufficient_auth_token):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(args=["records", "list"])
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output


class TestCommandRecordsImport:
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_import(self, app_runner_mocked_csw):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecords.TEST_RECORD_3.value
            json.dump(record_data, record_file)
            record_file.flush()

            result = app_runner_mocked_csw.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 0
            assert f"Ok. Record '{record_data['file_identifier']}' imported." in result.output

            # verify insert
            result = app_runner_mocked_csw.invoke(args=["records", "list"])
            assert result.exit_code == 0
            assert f"{record_data['file_identifier']}" in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_import_allow_update(self, app_runner_mocked_csw):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecords.TEST_RECORD_4.value
            json.dump(record_data, record_file)
            record_file.flush()

            result = app_runner_mocked_csw.invoke(args=["records", "import", record_file.name, "--allow-update"])
            assert result.exit_code == 0
            assert f"Ok. Record '{record_data['file_identifier']}' updated." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_import_publish(self, app_runner_mocked_csw):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecords.TEST_RECORD_5.value
            json.dump(record_data, record_file)
            record_file.flush()

            result = app_runner_mocked_csw.invoke(args=["records", "import", record_file.name, "--publish"])
            assert result.exit_code == 0
            assert f"Ok. Record '{record_data['file_identifier']}' imported." in result.output
            assert f"Ok. Record '{record_data['file_identifier']}' published." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_import_publish_allow_update_allow_republish(self, app_runner_mocked_csw):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecords.TEST_RECORD_6.value
            json.dump(record_data, record_file)
            record_file.flush()

            result = app_runner_mocked_csw.invoke(
                args=["records", "import", record_file.name, "--allow-update", "--publish", "--allow-republish"]
            )
            assert result.exit_code == 0
            assert f"Ok. Record '{record_data['file_identifier']}' updated." in result.output
            assert f"Ok. Record '{record_data['file_identifier']}' republished." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_import_error_no_file_specified(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "import"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORD_PATH'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_import_error_directory_specified(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            result = app_runner_mocked_csw.invoke(args=["records", "import", record_directory])
            assert result.exit_code == 2
            assert f"Error: Invalid value for 'RECORD_PATH': File '{record_directory}' is a directory." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_import_error_nonexistent_file(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "import", "/nonexistent_file"])
        assert result.exit_code == 2
        assert "Error: Invalid value for 'RECORD_PATH': File '/nonexistent_file' does not exist." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_import_error_empty_file(self, app_runner_mocked_csw):
        with NamedTemporaryFile(mode="r+") as record_file:
            result = app_runner_mocked_csw.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert f"No. Record in file '{record_file.name}' is not valid JSON." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_import_error_invalid_json_file(self, app_runner_mocked_csw):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_file.write("Invalid JSON.")
            record_file.flush()

            result = app_runner_mocked_csw.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert f"No. Record in file '{record_file.name}' is not valid JSON." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_not_setup")
    def test_cli_records_import_csw_not_setup(self, app_runner_mocked_csw_not_setup):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecords.TEST_RECORD_3.value
            json.dump(record_data, record_file)
            record_file.flush()

            result = app_runner_mocked_csw_not_setup.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert "No. CSW catalogue not setup." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_auth_token_error")
    def test_cli_records_import_auth_token_error(self, app_runner_mocked_csw_auth_token_error):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecords.TEST_RECORD_3.value
            json.dump(record_data, record_file)
            record_file.flush()

            result = app_runner_mocked_csw_auth_token_error.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_missing_auth_token")
    def test_cli_records_import_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecords.TEST_RECORD_3.value
            json.dump(record_data, record_file)
            record_file.flush()

            result = app_runner_mocked_csw_missing_auth_token.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_insufficient_auth_token")
    def test_cli_records_import_auth_token_insufficient(self, app_runner_mocked_csw_insufficient_auth_token):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecords.TEST_RECORD_3.value
            json.dump(record_data, record_file)
            record_file.flush()

            result = app_runner_mocked_csw_insufficient_auth_token.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_inserts_fail")
    def test_cli_records_import_error_server(self, app_runner_mocked_csw_inserts_fail):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecords.TEST_RECORD_3.value
            json.dump(record_data, record_file)
            record_file.flush()

            result = app_runner_mocked_csw_inserts_fail.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert f"No. Server error importing record '{record_data['file_identifier']}'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_import_error_conflict(self, app_runner_mocked_csw):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecords.TEST_RECORD_7.value
            json.dump(record_data, record_file)
            record_file.flush()

            result = app_runner_mocked_csw.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert (
                f"No. Record '{record_data['file_identifier']}' already exists. Add `--allow-update` flag to allow."
                in result.output
            )

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_import_error_publish_conflict(self, app_runner_mocked_csw):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecords.TEST_RECORD_7.value
            json.dump(record_data, record_file)
            record_file.flush()

            result = app_runner_mocked_csw.invoke(
                args=["records", "import", record_file.name, "--allow-update", "--publish"]
            )
            assert result.exit_code == 64
            assert f"Ok. Record '{record_data['file_identifier']}' updated." in result.output
            assert (
                f"No. Record '{record_data['file_identifier']}' already published. Add `--allow-republish` flag to allow."
                in result.output
            )


class TestCommandRecordsBulkImport:
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_import(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            with open(str(Path(f"{record_directory}/record.json")), mode="w+") as record_file:
                record_data = TestRecords.TEST_RECORD_3.value
                json.dump(record_data, record_file)
                record_file.flush()

                result = app_runner_mocked_csw.invoke(args=["records", "bulk-import", record_directory])
                assert result.exit_code == 0
                assert "1 records to import/update." in result.output
                assert "# Record 1/1" in result.output
                assert f"Ok. Record '{record_data['file_identifier']}' imported." in result.output
                assert "Ok. 1 records imported/updated." in result.output

                # verify insert
                result = app_runner_mocked_csw.invoke(args=["records", "list"])
                assert result.exit_code == 0
                assert f"{record_data['file_identifier']}" in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_import_allow_update(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            with open(str(Path(f"{record_directory}/record.json")), mode="w+") as record_file:
                record_data = TestRecords.TEST_RECORD_4.value
                json.dump(record_data, record_file)
                record_file.flush()

                result = app_runner_mocked_csw.invoke(
                    args=["records", "bulk-import", record_directory, "--allow-update"]
                )
                assert result.exit_code == 0
                assert "1 records to import/update." in result.output
                assert "# Record 1/1" in result.output
                assert f"Ok. Record '{record_data['file_identifier']}' updated." in result.output
                assert "Ok. 1 records imported/updated." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_import_publish(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            with open(str(Path(f"{record_directory}/record.json")), mode="w+") as record_file:
                record_data = TestRecords.TEST_RECORD_5.value
                json.dump(record_data, record_file)
                record_file.flush()

                result = app_runner_mocked_csw.invoke(args=["records", "bulk-import", record_directory, "--publish"])
                assert result.exit_code == 0
                assert "1 records to import/update." in result.output
                assert "# Record 1/1" in result.output
                assert f"Ok. Record '{record_data['file_identifier']}' imported." in result.output
                assert f"Ok. Record '{record_data['file_identifier']}' published." in result.output
                assert "Ok. 1 records imported/updated." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_import_publish_allow_update_allow_republish(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            with open(str(Path(f"{record_directory}/record.json")), mode="w+") as record_file:
                record_data = TestRecords.TEST_RECORD_6.value
                json.dump(record_data, record_file)
                record_file.flush()

                result = app_runner_mocked_csw.invoke(
                    args=[
                        "records",
                        "bulk-import",
                        record_directory,
                        "--allow-update",
                        "--publish",
                        "--allow-republish",
                    ]
                )
                assert result.exit_code == 0
                assert "1 records to import/update." in result.output
                assert "# Record 1/1" in result.output
                assert f"Ok. Record '{record_data['file_identifier']}' updated." in result.output
                assert f"Ok. Record '{record_data['file_identifier']}' republished." in result.output
                assert "Ok. 1 records imported/updated." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_import_empty_directory(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            result = app_runner_mocked_csw.invoke(args=["records", "bulk-import", record_directory])
            assert result.exit_code == 0
            assert "0 records to import/update." in result.output
            assert "Ok. 0 records imported/updated." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_import_error_no_directory_specified(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-import"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORDS_PATH'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_import_error_file_specified(self, app_runner_mocked_csw):
        with NamedTemporaryFile() as record_file:
            result = app_runner_mocked_csw.invoke(args=["records", "bulk-import", record_file.name])
            assert result.exit_code == 2
            assert (
                f"Error: Invalid value for 'RECORDS_PATH': Directory '{record_file.name}' is a file." in result.output
            )

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_import_error_nonexistent_directory(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-import", "/nonexistent_directory"])
        assert result.exit_code == 2
        assert (
            "Error: Invalid value for 'RECORDS_PATH': Directory '/nonexistent_directory' does not exist."
            in result.output
        )

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_import_error_invoked_command_error(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            valid_record_path = str(Path(f"{record_directory}/01-valid-record.json"))
            invalid_record_path = str(Path(f"{record_directory}/02-invalid-record.json"))
            with open(valid_record_path, mode="w+") as valid_record_file, open(
                invalid_record_path, mode="w+"
            ) as invalid_record_file:
                valid_record_data = TestRecords.TEST_RECORD_3.value
                json.dump(valid_record_data, valid_record_file)
                valid_record_file.flush()
                invalid_record_data = '{"foo":}'
                invalid_record_file.write(invalid_record_data)
                invalid_record_file.flush()

                result = app_runner_mocked_csw.invoke(args=["records", "bulk-import", record_directory])
                assert result.exit_code == 64
                assert "2 records to import/update." in result.output
                assert "# Record 1/2" in result.output
                assert f"Ok. Record '{valid_record_data['file_identifier']}' imported." in result.output
                assert "# Record 2/2" in result.output
                assert f"No. Record in file '{invalid_record_path}' is not valid JSON." in result.output


class TestCommandRecordsPublish:
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_publish(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(
            args=["records", "publish", TestRecords.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 0
        assert f"Ok. Record '{TestRecords.TEST_RECORD_2.value['file_identifier']}' published." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_publish_allow_republish(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(
            args=["records", "publish", TestRecords.TEST_RECORD_1.value["file_identifier"], "--allow-republish"]
        )
        assert result.exit_code == 0
        assert f"Ok. Record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' republished." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_publish_error_no_record_identifier(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "publish"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORD_IDENTIFIER'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_not_setup")
    def test_cli_records_publish_csw_not_setup(self, app_runner_mocked_csw_not_setup):
        result = app_runner_mocked_csw_not_setup.invoke(
            args=["records", "publish", TestRecords.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_auth_token_error")
    def test_cli_records_publish_auth_token_error(self, app_runner_mocked_csw_auth_token_error):
        result = app_runner_mocked_csw_auth_token_error.invoke(
            args=["records", "publish", TestRecords.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_missing_auth_token")
    def test_cli_records_publish_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token):
        result = app_runner_mocked_csw_missing_auth_token.invoke(
            args=["records", "publish", TestRecords.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_insufficient_auth_token")
    def test_cli_records_publish_auth_token_insufficient(self, app_runner_mocked_csw_insufficient_auth_token):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(
            args=["records", "publish", TestRecords.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_publish_error_unknown_record_identifier(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "publish", "unknown-identifier"])
        assert result.exit_code == 64
        assert "No. Record 'unknown-identifier' does not exist." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_publish_error_conflict(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(
            args=["records", "publish", TestRecords.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert (
            f"No. Record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' already published. Add `--allow-republish` flag to allow."
            in result.output
        )

    @pytest.mark.usefixtures("app_runner_mocked_csw_inserts_fail")
    def test_cli_records_import_error_server(self, app_runner_mocked_csw_inserts_fail):
        result = app_runner_mocked_csw_inserts_fail.invoke(
            args=["records", "publish", TestRecords.TEST_RECORD_2.value["file_identifier"]]
        )

        assert result.exit_code == 64
        assert (
            f"No. Server error publishing record '{TestRecords.TEST_RECORD_2.value['file_identifier']}'."
            in result.output
        )


class TestCommandRecordsBulkPublish:
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_publish(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-publish"])
        assert result.exit_code == 0
        assert "1 records to (re)publish." in result.output
        assert "# Record 1/1" in result.output
        assert f"Ok. Record '{TestRecords.TEST_RECORD_2.value['file_identifier']}' published." in result.output
        assert "Ok. 1 records (re)published." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_publish_force_republish(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-publish", "--force-republish"])
        assert result.exit_code == 0
        assert "2 records to (re)publish." in result.output
        assert "# Record 1/2" in result.output
        assert f"Ok. Record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' republished." in result.output
        assert "# Record 2/2" in result.output
        assert f"Ok. Record '{TestRecords.TEST_RECORD_2.value['file_identifier']}' published." in result.output
        assert "Ok. 2 records (re)published." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_inserts_fail")
    def test_cli_records_bulk_publish_error_invoked_command_error(self, app_runner_mocked_csw_inserts_fail):
        result = app_runner_mocked_csw_inserts_fail.invoke(args=["records", "bulk-publish"])
        assert result.exit_code == 64
        assert "1 records to (re)publish." in result.output
        assert "# Record 1/1" in result.output
        assert (
            f"No. Server error publishing record '{TestRecords.TEST_RECORD_2.value['file_identifier']}'."
            in result.output
        )


class TestCommandRecordsExport:
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_export(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")
            result = app_runner_mocked_csw.invoke(
                args=["records", "export", TestRecords.TEST_RECORD_1.value["file_identifier"], str(record_path)]
            )
            assert result.exit_code == 0
            assert f"Ok. Record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' exported." in result.output
            with open(str(record_path), mode="r") as record_file:
                record_data = json.load(record_file)
                assert record_data == TestRecords.TEST_RECORD_1.value

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_export_allow_overwrite(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")

            # Write file out initially
            result = app_runner_mocked_csw.invoke(
                args=["records", "export", TestRecords.TEST_RECORD_1.value["file_identifier"], str(record_path)]
            )
            assert result.exit_code == 0

            result = app_runner_mocked_csw.invoke(
                args=[
                    "records",
                    "export",
                    TestRecords.TEST_RECORD_1.value["file_identifier"],
                    str(record_path),
                    "--allow-overwrite",
                ]
            )
            assert result.exit_code == 0
            assert f"Ok. Record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' re-exported." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_export_error_no_record_identifier_specified(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "export"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORD_IDENTIFIER'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_export_error_no_record_path_specified(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(
            args=["records", "export", TestRecords.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORD_PATH'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_export_error_record_path_directory_specified(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            result = app_runner_mocked_csw.invoke(
                args=["records", "export", TestRecords.TEST_RECORD_1.value["file_identifier"], record_directory]
            )
            assert result.exit_code == 2
            assert f"Error: Invalid value for 'RECORD_PATH': File '{record_directory}' is a directory." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_not_setup")
    def test_cli_records_export_csw_not_setup(self, app_runner_mocked_csw_not_setup):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")
            result = app_runner_mocked_csw_not_setup.invoke(
                args=["records", "export", TestRecords.TEST_RECORD_1.value["file_identifier"], str(record_path)]
            )
            assert result.exit_code == 64
            assert "No. CSW catalogue not setup." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_auth_token_error")
    def test_cli_records_export_auth_token_error(self, app_runner_mocked_csw_auth_token_error):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")
            result = app_runner_mocked_csw_auth_token_error.invoke(
                args=["records", "export", TestRecords.TEST_RECORD_1.value["file_identifier"], str(record_path)]
            )
            assert result.exit_code == 64
            assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_missing_auth_token")
    def test_cli_records_export_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")
            result = app_runner_mocked_csw_missing_auth_token.invoke(
                args=["records", "export", TestRecords.TEST_RECORD_1.value["file_identifier"], str(record_path)]
            )
            assert result.exit_code == 64
            assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_insufficient_auth_token")
    def test_cli_records_list_auth_token_insufficient(self, app_runner_mocked_csw_insufficient_auth_token):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")
            result = app_runner_mocked_csw_insufficient_auth_token.invoke(
                args=["records", "export", TestRecords.TEST_RECORD_1.value["file_identifier"], str(record_path)]
            )
            assert result.exit_code == 64
            assert (
                "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output
            )

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_export_error_unknown_record_identifier(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")

            result = app_runner_mocked_csw.invoke(args=["records", "export", "unknown-identifier", str(record_path)])
            assert result.exit_code == 64
            assert "No. Record 'unknown-identifier' does not exist." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_export_error_conflict(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")

            # Write file out initially
            result = app_runner_mocked_csw.invoke(
                args=["records", "export", TestRecords.TEST_RECORD_1.value["file_identifier"], str(record_path)]
            )
            assert result.exit_code == 0

            result = app_runner_mocked_csw.invoke(
                args=["records", "export", TestRecords.TEST_RECORD_1.value["file_identifier"], str(record_path)]
            )
            assert result.exit_code == 64
            assert (
                f"No. Export of record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' would be overwritten. Add `--allow-overwrite` flag to allow."
                in result.output
            )


class TestCommandRecordsBulkExport:
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_export(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            records_path = Path(record_directory)

            result = app_runner_mocked_csw.invoke(args=["records", "bulk-export", str(records_path)])
            assert result.exit_code == 0
            assert "2 records to (re)export." in result.output
            assert "# Record 1/2" in result.output
            assert f"Ok. Record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' exported." in result.output
            assert "# Record 2/2" in result.output
            assert f"Ok. Record '{TestRecords.TEST_RECORD_2.value['file_identifier']}' exported." in result.output
            assert "Ok. 2 records (re)exported." in result.output

            # Verify export
            record_paths = list(records_path.glob("*.json"))
            assert len(record_paths) == 2
            assert records_path.joinpath(f"{TestRecords.TEST_RECORD_1.value['file_identifier']}.json") in record_paths
            assert records_path.joinpath(f"{TestRecords.TEST_RECORD_2.value['file_identifier']}.json") in record_paths
            with open(
                str(records_path.joinpath(f"{TestRecords.TEST_RECORD_1.value['file_identifier']}.json")), mode="r"
            ) as record_file:
                record_data = json.load(record_file)
                assert record_data == TestRecords.TEST_RECORD_1.value

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_export_allow_overwrite(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            records_path = Path(record_directory)

            # Write file out initially
            record_path = records_path.joinpath(f"{TestRecords.TEST_RECORD_2.value['file_identifier']}.json")
            result = app_runner_mocked_csw.invoke(
                args=["records", "export", TestRecords.TEST_RECORD_2.value["file_identifier"], str(record_path)]
            )
            assert result.exit_code == 0

            result = app_runner_mocked_csw.invoke(
                args=["records", "bulk-export", record_directory, "--allow-overwrite",]
            )
            assert result.exit_code == 0
            assert "2 records to (re)export." in result.output
            assert "# Record 1/2" in result.output
            assert f"Ok. Record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' exported." in result.output
            assert "# Record 2/2" in result.output
            assert f"Ok. Record '{TestRecords.TEST_RECORD_2.value['file_identifier']}' re-exported." in result.output
            assert "Ok. 2 records (re)exported." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_export_error_no_directory_specified(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-export"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORDS_PATH'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_export_error_file_specified(self, app_runner_mocked_csw):
        with NamedTemporaryFile() as record_file:
            result = app_runner_mocked_csw.invoke(args=["records", "bulk-export", record_file.name])
            assert result.exit_code == 2
            assert (
                f"Error: Invalid value for 'RECORDS_PATH': Directory '{record_file.name}' is a file." in result.output
            )

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_export_error_nonexistent_directory(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-export", "/nonexistent_directory"])
        assert result.exit_code == 2
        assert (
            "Error: Invalid value for 'RECORDS_PATH': Directory '/nonexistent_directory' does not exist."
            in result.output
        )

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_export_error_invoked_command_error(self, app_runner_mocked_csw):
        with TemporaryDirectory() as record_directory:
            records_path = Path(record_directory)

            # Write file out initially
            record_path = records_path.joinpath(f"{TestRecords.TEST_RECORD_2.value['file_identifier']}.json")
            result = app_runner_mocked_csw.invoke(
                args=["records", "export", TestRecords.TEST_RECORD_2.value["file_identifier"], str(record_path)]
            )
            assert result.exit_code == 0

            result = app_runner_mocked_csw.invoke(args=["records", "bulk-export", record_directory])
            assert result.exit_code == 64
            assert "2 records to (re)export." in result.output
            assert "# Record 1/2" in result.output
            assert f"Ok. Record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' exported." in result.output
            assert "# Record 2/2" in result.output
            assert (
                f"No. Export of record '{TestRecords.TEST_RECORD_2.value['file_identifier']}' would be overwritten. Add `--allow-overwrite` flag to allow."
                in result.output
            )


class TestCommandRecordsRemove:
    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_remove(self, mock_confirm, app_runner_mocked_csw):
        mock_confirm.return_value = "y"

        result = app_runner_mocked_csw.invoke(
            args=["records", "remove", TestRecords.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 0
        assert f"Ok. Record '{TestRecords.TEST_RECORD_2.value['file_identifier']}' removed." in result.output

        # verify deletion
        result = app_runner_mocked_csw.invoke(
            args=["records", "remove", TestRecords.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert f"No. Record '{TestRecords.TEST_RECORD_2.value['file_identifier']}' does not exist." in result.output

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_remove_aborted(self, mock_confirm, app_runner_mocked_csw):
        mock_confirm.return_value = False

        result = app_runner_mocked_csw.invoke(
            args=["records", "remove", TestRecords.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 1
        assert f"Aborted!" in result.output

        # verify non-deletion
        result = app_runner_mocked_csw.invoke(args=["records", "list"])
        assert result.exit_code == 0
        assert TestRecords.TEST_RECORD_2.value["file_identifier"] in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_remove_force_confirm(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(
            args=["records", "remove", TestRecords.TEST_RECORD_2.value["file_identifier"], "--force-remove"]
        )
        assert result.exit_code == 0
        assert f"Ok. Record '{TestRecords.TEST_RECORD_2.value['file_identifier']}' removed." in result.output

        # verify deletion
        result = app_runner_mocked_csw.invoke(
            args=["records", "remove", TestRecords.TEST_RECORD_2.value["file_identifier"], "--force-remove"]
        )
        assert result.exit_code == 64
        assert f"No. Record '{TestRecords.TEST_RECORD_2.value['file_identifier']}' does not exist." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_remove_error_no_record_identifier_specified(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "remove"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORD_IDENTIFIER'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_not_setup")
    def test_cli_records_remove_csw_not_setup(self, app_runner_mocked_csw_not_setup):
        result = app_runner_mocked_csw_not_setup.invoke(
            args=["records", "remove", TestRecords.TEST_RECORD_2.value["file_identifier"], "--force-remove"]
        )
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_auth_token_error")
    def test_cli_records_remove_auth_token_error(self, app_runner_mocked_csw_auth_token_error):
        result = app_runner_mocked_csw_auth_token_error.invoke(
            args=["records", "remove", TestRecords.TEST_RECORD_2.value["file_identifier"], "--force-remove"]
        )
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_missing_auth_token")
    def test_cli_records_remove_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token):
        result = app_runner_mocked_csw_missing_auth_token.invoke(
            args=["records", "remove", TestRecords.TEST_RECORD_2.value["file_identifier"], "--force-remove"]
        )
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_insufficient_auth_token")
    def test_cli_records_remove_auth_token_insufficient(self, app_runner_mocked_csw_insufficient_auth_token):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(
            args=["records", "remove", TestRecords.TEST_RECORD_2.value["file_identifier"], "--force-remove"]
        )
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_remove_error_unknown_record_identifier(self, mock_confirm, app_runner_mocked_csw):
        mock_confirm.return_value = "y"

        result = app_runner_mocked_csw.invoke(args=["records", "remove", "unknown-identifier"])
        assert result.exit_code == 64
        assert "No. Record 'unknown-identifier' does not exist." in result.output

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_remove_error_published(self, mock_confirm, app_runner_mocked_csw):
        mock_confirm.return_value = "y"

        result = app_runner_mocked_csw.invoke(
            args=["records", "remove", TestRecords.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert (
            f"No. Record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' is published, retract it first."
            in result.output
        )


class TestCommandRecordsBulkRemove:
    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_remove(self, mock_confirm, app_runner_mocked_csw):
        mock_confirm.return_value = "y"

        result = app_runner_mocked_csw.invoke(args=["records", "bulk-remove"])
        assert result.exit_code == 0
        assert f"1 records to remove." in result.output
        assert f"Ok. Record '{TestRecords.TEST_RECORD_2.value['file_identifier']}' removed." in result.output
        assert f"Ok. 1 records removed." in result.output

        # verify deletion
        result = app_runner_mocked_csw.invoke(
            args=["records", "remove", TestRecords.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert f"No. Record '{TestRecords.TEST_RECORD_2.value['file_identifier']}' does not exist." in result.output

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_remove_aborted(self, mock_confirm, app_runner_mocked_csw):
        mock_confirm.return_value = False

        result = app_runner_mocked_csw.invoke(args=["records", "bulk-remove"])
        assert result.exit_code == 1
        assert f"Aborted!" in result.output

        # verify non-deletion
        result = app_runner_mocked_csw.invoke(args=["records", "list"])
        assert result.exit_code == 0
        assert TestRecords.TEST_RECORD_2.value["file_identifier"] in result.output


class TestCommandRecordsRetract:
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_retract(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(
            args=["records", "retract", TestRecords.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 0
        assert f"Ok. Record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' retracted." in result.output

        # verify retraction
        result = app_runner_mocked_csw.invoke(
            args=["records", "retract", TestRecords.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert f"No. Record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' is not published." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_retract_error_no_record_identifier_specified(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "retract"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORD_IDENTIFIER'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_not_setup")
    def test_cli_records_retract_csw_not_setup(self, app_runner_mocked_csw_not_setup):
        result = app_runner_mocked_csw_not_setup.invoke(
            args=["records", "retract", TestRecords.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_auth_token_error")
    def test_cli_records_retract_auth_token_error(self, app_runner_mocked_csw_auth_token_error):
        result = app_runner_mocked_csw_auth_token_error.invoke(
            args=["records", "retract", TestRecords.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_missing_auth_token")
    def test_cli_records_retract_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token):
        result = app_runner_mocked_csw_missing_auth_token.invoke(
            args=["records", "retract", TestRecords.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_insufficient_auth_token")
    def test_cli_records_retract_auth_token_insufficient(self, app_runner_mocked_csw_insufficient_auth_token):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(
            args=["records", "retract", TestRecords.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_retract_error_unknown_record_identifier(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "retract", "unknown-identifier"])
        assert result.exit_code == 64
        assert f"No. Record 'unknown-identifier' is not published." in result.output


class TestCommandRecordsBulkRetract:
    @pytest.mark.usefixtures("app_runner_mocked_csw")
    def test_cli_records_bulk_retract(self, app_runner_mocked_csw):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-retract"])
        assert result.exit_code == 0
        assert f"1 records to retract." in result.output
        assert f"Ok. Record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' retracted." in result.output
        assert f"Ok. 1 records retracted." in result.output

        # verify deletion
        result = app_runner_mocked_csw.invoke(
            args=["records", "retract", TestRecords.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert f"No. Record '{TestRecords.TEST_RECORD_1.value['file_identifier']}' is not published." in result.output


class TestCommandCollectionsList:
    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_list(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(args=["collections", "list"])
        assert result.exit_code == 0
        assert "│ b759077f-bd3f-4a18-bbd7-e6b3f84bc551 │ Test Collection 1  │               1 │" in result.output


class TestCommandCollectionsInspect:
    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_inspect(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(
            args=["collections", "inspect", TestCollections.TEST_COLLECTION_1.value["identifier"]]
        )
        assert result.exit_code == 0
        assert f"Ok. Collection details for '{TestCollections.TEST_COLLECTION_1.value['identifier']}':" in result.output
        assert f"Identifier: {TestCollections.TEST_COLLECTION_1.value['identifier']}" in result.output
        assert f"Title: {TestCollections.TEST_COLLECTION_1.value['title']}" in result.output
        assert TestCollections.TEST_COLLECTION_1.value["summary"] in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_error_no_collection_identifier_specified(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(args=["collections", "inspect"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'COLLECTION_IDENTIFIER'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_inspect_error_unknown_collection(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(args=["collections", "inspect", "unknown-identifier"])
        assert result.exit_code == 64
        assert "No. Collection 'unknown-identifier' does not exist." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_not_setup")
    def test_cli_collections_inspect_csw_not_setup_mocked_collection(
        self, app_runner_mocked_csw_not_setup_mocked_collection
    ):
        result = app_runner_mocked_csw_not_setup_mocked_collection.invoke(
            args=["collections", "inspect", TestCollections.TEST_COLLECTION_1.value["identifier"]]
        )
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_auth_token_error_mocked_collection")
    def test_cli_collections_inspect_auth_token_error(self, app_runner_mocked_csw_auth_token_error_mocked_collection):
        result = app_runner_mocked_csw_auth_token_error_mocked_collection.invoke(
            args=["collections", "inspect", TestCollections.TEST_COLLECTION_1.value["identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_missing_auth_token_mocked_collection")
    def test_cli_collections_inspect_auth_token_missing(
        self, app_runner_mocked_csw_missing_auth_token_mocked_collection
    ):
        result = app_runner_mocked_csw_missing_auth_token_mocked_collection.invoke(
            args=["collections", "inspect", TestCollections.TEST_COLLECTION_1.value["identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_insufficient_auth_token_mocked_collection")
    def test_cli_collections_inspect_auth_token_insufficient(
        self, app_runner_mocked_csw_insufficient_auth_token_mocked_collection
    ):
        result = app_runner_mocked_csw_insufficient_auth_token_mocked_collection.invoke(
            args=["collections", "inspect", TestCollections.TEST_COLLECTION_1.value["identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections_unknown_record")
    def test_cli_collections_inspect_error_unknown_record_in_collection(
        self, app_runner_mocked_collections_unknown_record
    ):
        result = app_runner_mocked_collections_unknown_record.invoke(
            args=["collections", "inspect", TestCollections.TEST_COLLECTION_4.value["identifier"]]
        )
        assert result.exit_code == 64
        assert (
            f"No. Record 'unknown' in collection '{TestCollections.TEST_COLLECTION_4.value['identifier']}' does not exist."
            in result.output
        )


class TestCommandCollectionsImport:
    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_import(self, app_runner_mocked_collections):
        with NamedTemporaryFile(mode="r+") as collection_file:
            collection_data = TestCollections.TEST_COLLECTION_2.value
            json.dump(collection_data, collection_file)
            collection_file.flush()

            result = app_runner_mocked_collections.invoke(args=["collections", "import", collection_file.name])
            assert result.exit_code == 0
            assert f"Ok. Collection '{collection_data['identifier']}' imported." in result.output

            # verify insert
            result = app_runner_mocked_collections.invoke(
                args=["collections", "inspect", collection_data["identifier"]]
            )
            assert result.exit_code == 0
            assert f"Ok. Collection details for '{collection_data['identifier']}':" in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_import_allow_update(self, app_runner_mocked_collections):
        with NamedTemporaryFile(mode="r+") as collection_file:
            collection_data = TestCollections.TEST_COLLECTION_3.value
            json.dump(collection_data, collection_file)
            collection_file.flush()

            result = app_runner_mocked_collections.invoke(
                args=["collections", "import", collection_file.name, "--allow-update"]
            )
            assert result.exit_code == 0
            assert f"Ok. Collection '{collection_data['identifier']}' updated." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_import_error_no_file_specified(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(args=["collections", "import"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'COLLECTION_PATH'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_import_error_directory_specified(self, app_runner_mocked_collections):
        with TemporaryDirectory() as collection_directory:
            result = app_runner_mocked_collections.invoke(args=["collections", "import", collection_directory])
            assert result.exit_code == 2
            assert (
                f"Error: Invalid value for 'COLLECTION_PATH': File '{collection_directory}' is a directory."
                in result.output
            )

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_import_error_nonexistent_file(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(args=["collections", "import", "/nonexistent_file"])
        assert result.exit_code == 2
        assert "Error: Invalid value for 'COLLECTION_PATH': File '/nonexistent_file' does not exist." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_import_error_empty_file(self, app_runner_mocked_collections):
        with NamedTemporaryFile(mode="r+") as collection_file:
            result = app_runner_mocked_collections.invoke(args=["collections", "import", collection_file.name])
            assert result.exit_code == 64
            assert f"No. Collection in file '{collection_file.name}' is not valid JSON." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_import_error_invalid_json_file(self, app_runner_mocked_collections):
        with NamedTemporaryFile(mode="r+") as collection_file:
            collection_file.write("Invalid JSON.")
            collection_file.flush()

            result = app_runner_mocked_collections.invoke(args=["collections", "import", collection_file.name])
            assert result.exit_code == 64
            assert f"No. Collection in file '{collection_file.name}' is not valid JSON." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_import_error_conflict(self, app_runner_mocked_collections):
        with NamedTemporaryFile(mode="r+") as collection_file:
            collection_data = TestCollections.TEST_COLLECTION_3.value
            json.dump(collection_data, collection_file)
            collection_file.flush()

            result = app_runner_mocked_collections.invoke(args=["collections", "import", collection_file.name])
            assert result.exit_code == 64
            assert (
                f"No. Collection '{collection_data['identifier']}' already exists. Add `--allow-update` flag to allow."
                in result.output
            )


class TestCommandCollectionsBulkImport:
    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_import(self, app_runner_mocked_collections):
        with TemporaryDirectory() as collection_directory:
            with open(str(Path(f"{collection_directory}/collection.json")), mode="w+") as collection_file:
                collection_data = TestCollections.TEST_COLLECTION_2.value
                json.dump(collection_data, collection_file)
                collection_file.flush()

                result = app_runner_mocked_collections.invoke(args=["collections", "bulk-import", collection_directory])
                assert result.exit_code == 0
                assert "1 collections to import/update." in result.output
                assert "# Collection 1/1" in result.output
                assert f"Ok. Collection '{collection_data['identifier']}' imported." in result.output
                assert "Ok. 1 collections imported/updated." in result.output

                # verify insert
                result = app_runner_mocked_collections.invoke(
                    args=["collections", "inspect", collection_data["identifier"]]
                )
                assert result.exit_code == 0
                assert f"Ok. Collection details for '{collection_data['identifier']}':" in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_import_allow_update(self, app_runner_mocked_collections):
        with TemporaryDirectory() as collection_directory:
            with open(str(Path(f"{collection_directory}/collection.json")), mode="w+") as collection_file:
                collection_data = TestCollections.TEST_COLLECTION_3.value
                json.dump(collection_data, collection_file)
                collection_file.flush()

                result = app_runner_mocked_collections.invoke(
                    args=["collections", "bulk-import", collection_directory, "--allow-update"]
                )
                assert result.exit_code == 0
                assert "1 collections to import/update" in result.output
                assert "# Collection 1/1" in result.output
                assert f"Ok. Collection '{collection_data['identifier']}' updated." in result.output
                assert "Ok. 1 collections imported/updated." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_import_empty_directory(self, app_runner_mocked_collections):
        with TemporaryDirectory() as record_directory:
            result = app_runner_mocked_collections.invoke(args=["collections", "bulk-import", record_directory])
            assert result.exit_code == 0
            assert "0 collections to import/update." in result.output
            assert "Ok. 0 collections imported/updated." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_import_error_no_directory_specified(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(args=["collections", "bulk-import"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'COLLECTIONS_PATH'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_import_error_file_specified(self, app_runner_mocked_collections):
        with NamedTemporaryFile() as record_file:
            result = app_runner_mocked_collections.invoke(args=["collections", "bulk-import", record_file.name])
            assert result.exit_code == 2
            assert (
                f"Error: Invalid value for 'COLLECTIONS_PATH': Directory '{record_file.name}' is a file."
                in result.output
            )

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_import_error_nonexistent_directory(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(args=["collections", "bulk-import", "/nonexistent_directory"])
        assert result.exit_code == 2
        assert (
            "Error: Invalid value for 'COLLECTIONS_PATH': Directory '/nonexistent_directory' does not exist."
            in result.output
        )

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_import_error_invoked_command_error(self, app_runner_mocked_collections):
        with TemporaryDirectory() as collection_directory:
            valid_collection_path = str(Path(f"{collection_directory}/01-valid-collection.json"))
            invalid_collection_path = str(Path(f"{collection_directory}/02-invalid-collection.json"))
            with open(valid_collection_path, mode="w+") as valid_collection_file, open(
                invalid_collection_path, mode="w+"
            ) as invalid_collection_file:
                valid_collection_data = TestCollections.TEST_COLLECTION_2.value
                json.dump(valid_collection_data, valid_collection_file)
                valid_collection_file.flush()
                invalid_collection_data = '{"foo":}'
                invalid_collection_file.write(invalid_collection_data)
                invalid_collection_file.flush()

                result = app_runner_mocked_collections.invoke(args=["collections", "bulk-import", collection_directory])
                assert result.exit_code == 64
                assert "2 collections to import/update." in result.output
                assert "# Collection 1/2" in result.output
                assert f"Ok. Collection '{valid_collection_data['identifier']}' imported." in result.output
                assert "# Collection 2/2" in result.output
                assert f"No. Collection in file '{invalid_collection_path}' is not valid JSON." in result.output


class TestCommandCollectionsExport:
    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_export(self, app_runner_mocked_collections):
        with TemporaryDirectory() as collection_directory:
            collection_path = Path(collection_directory).joinpath("collection.json")
            result = app_runner_mocked_collections.invoke(
                args=[
                    "collections",
                    "export",
                    TestCollections.TEST_COLLECTION_1.value["identifier"],
                    str(collection_path),
                ]
            )
            assert result.exit_code == 0
            assert (
                f"Ok. Collection '{TestCollections.TEST_COLLECTION_1.value['identifier']}' exported." in result.output
            )

            # verify export
            with open(str(collection_path), mode="r") as collection_file:
                collection_data = json.load(collection_file)
                assert collection_data == TestCollections.TEST_COLLECTION_1.value

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_export_allow_overwrite(self, app_runner_mocked_collections):
        with TemporaryDirectory() as collection_directory:
            collection_path = Path(collection_directory).joinpath("collection.json")

            # Write file out initially
            result = app_runner_mocked_collections.invoke(
                args=[
                    "collections",
                    "export",
                    TestCollections.TEST_COLLECTION_1.value["identifier"],
                    str(collection_path),
                ]
            )
            assert result.exit_code == 0

            result = app_runner_mocked_collections.invoke(
                args=[
                    "collections",
                    "export",
                    TestCollections.TEST_COLLECTION_1.value["identifier"],
                    str(collection_path),
                    "--allow-overwrite",
                ]
            )
            assert result.exit_code == 0
            assert (
                f"Ok. Collection '{TestCollections.TEST_COLLECTION_1.value['identifier']}' re-exported."
                in result.output
            )

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_export_error_no_record_identifier_specified(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(args=["collections", "export"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'COLLECTION_IDENTIFIER'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_export_error_no_record_path_specified(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(
            args=["collections", "export", TestCollections.TEST_COLLECTION_1.value["identifier"]]
        )
        assert result.exit_code == 2
        assert "Error: Missing argument 'COLLECTION_PATH'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_export_error_record_path_directory_specified(self, app_runner_mocked_collections):
        with TemporaryDirectory() as collection_directory:
            result = app_runner_mocked_collections.invoke(
                args=[
                    "collections",
                    "export",
                    TestCollections.TEST_COLLECTION_1.value["identifier"],
                    collection_directory,
                ]
            )
            assert result.exit_code == 2
            assert (
                f"Error: Invalid value for 'COLLECTION_PATH': File '{collection_directory}' is a directory."
                in result.output
            )

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_export_error_unknown_collection_identifier(self, app_runner_mocked_collections):
        with TemporaryDirectory() as collection_directory:
            collection_path = Path(collection_directory).joinpath("collection.json")

            result = app_runner_mocked_collections.invoke(
                args=["collections", "export", "unknown-identifier", str(collection_path)]
            )
            assert result.exit_code == 64
            assert "No. Collection 'unknown-identifier' does not exist." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_export_error_conflict(self, app_runner_mocked_collections):
        with TemporaryDirectory() as collection_directory:
            collection_path = Path(collection_directory).joinpath("collection.json")

            # Write file out initially
            result = app_runner_mocked_collections.invoke(
                args=[
                    "collections",
                    "export",
                    TestCollections.TEST_COLLECTION_1.value["identifier"],
                    str(collection_path),
                ]
            )
            assert result.exit_code == 0

            result = app_runner_mocked_collections.invoke(
                args=[
                    "collections",
                    "export",
                    TestCollections.TEST_COLLECTION_1.value["identifier"],
                    str(collection_path),
                ]
            )
            assert result.exit_code == 64
            assert (
                f"No. Export of collection '{TestCollections.TEST_COLLECTION_1.value['identifier']}' would be overwritten. Add `--allow-overwrite` flag to allow."
                in result.output
            )


class TestCommandCollectionsBulkExport:
    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_export(self, app_runner_mocked_collections):
        with TemporaryDirectory() as collection_directory:
            collections_path = Path(collection_directory)

            result = app_runner_mocked_collections.invoke(args=["collections", "bulk-export", str(collections_path)])
            assert result.exit_code == 0
            assert "1 collections to (re)export." in result.output
            assert "# Collection 1/1" in result.output
            assert (
                f"Ok. Collection '{TestCollections.TEST_COLLECTION_1.value['identifier']}' exported." in result.output
            )
            assert "Ok. 1 collections (re)exported." in result.output

            # verify export
            collection_paths = list(collections_path.glob("*.json"))
            assert len(collection_paths) == 1
            assert (
                collections_path.joinpath(f"{TestCollections.TEST_COLLECTION_1.value['identifier']}.json")
                in collection_paths
            )
            with open(
                str(collections_path.joinpath(f"{TestCollections.TEST_COLLECTION_1.value['identifier']}.json")),
                mode="r",
            ) as collection_file:
                collection_data = json.load(collection_file)
                assert collection_data == TestCollections.TEST_COLLECTION_1.value

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_export_allow_overwrite(self, app_runner_mocked_collections):
        with TemporaryDirectory() as collection_directory:
            collections_path = Path(collection_directory)

            # Write file out initially
            collection_path = collections_path.joinpath(f"{TestCollections.TEST_COLLECTION_1.value['identifier']}.json")
            result = app_runner_mocked_collections.invoke(
                args=[
                    "collections",
                    "export",
                    TestCollections.TEST_COLLECTION_1.value["identifier"],
                    str(collection_path),
                ]
            )
            assert result.exit_code == 0

            result = app_runner_mocked_collections.invoke(
                args=["collections", "bulk-export", collection_directory, "--allow-overwrite",]
            )
            assert result.exit_code == 0
            assert "1 collections to (re)export." in result.output
            assert "# Collection 1/1" in result.output
            assert (
                f"Ok. Collection '{TestCollections.TEST_COLLECTION_1.value['identifier']}' re-exported."
                in result.output
            )
            assert "Ok. 1 collections (re)exported." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_export_error_no_directory_specified(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(args=["collections", "bulk-export"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'COLLECTIONS_PATH'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_export_error_file_specified(self, app_runner_mocked_collections):
        with NamedTemporaryFile() as collection_file:
            result = app_runner_mocked_collections.invoke(args=["collections", "bulk-export", collection_file.name])
            assert result.exit_code == 2
            assert (
                f"Error: Invalid value for 'COLLECTIONS_PATH': Directory '{collection_file.name}' is a file."
                in result.output
            )

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_export_error_nonexistent_directory(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(args=["collections", "bulk-export", "/nonexistent_directory"])
        assert result.exit_code == 2
        assert (
            "Error: Invalid value for 'COLLECTIONS_PATH': Directory '/nonexistent_directory' does not exist."
            in result.output
        )

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_export_error_invoked_command_error(self, app_runner_mocked_collections):
        with TemporaryDirectory() as collection_directory:
            collections_path = Path(collection_directory)

            # Write file out initially
            collection_path = collections_path.joinpath(f"{TestCollections.TEST_COLLECTION_1.value['identifier']}.json")
            result = app_runner_mocked_collections.invoke(
                args=[
                    "collections",
                    "export",
                    TestCollections.TEST_COLLECTION_1.value["identifier"],
                    str(collection_path),
                ]
            )
            assert result.exit_code == 0

            result = app_runner_mocked_collections.invoke(args=["collections", "bulk-export", collection_directory])
            assert result.exit_code == 64
            assert "1 collections to (re)export." in result.output
            assert "# Collection 1/1" in result.output
            assert (
                f"No. Export of collection '{TestCollections.TEST_COLLECTION_1.value['identifier']}' would be overwritten. Add `--allow-overwrite` flag to allow."
                in result.output
            )


class TestCommandCollectionsRemove:
    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_remove(self, mock_confirm, app_runner_mocked_collections):
        mock_confirm.return_value = "y"

        result = app_runner_mocked_collections.invoke(
            args=["collections", "remove", TestCollections.TEST_COLLECTION_1.value["identifier"]]
        )
        assert result.exit_code == 0
        assert f"Ok. Collection '{TestCollections.TEST_COLLECTION_1.value['identifier']}' removed." in result.output

        # verify deletion
        result = app_runner_mocked_collections.invoke(
            args=["collections", "remove", TestCollections.TEST_COLLECTION_1.value["identifier"]]
        )
        assert result.exit_code == 64
        assert (
            f"No. Collection '{TestCollections.TEST_COLLECTION_1.value['identifier']}' does not exist." in result.output
        )

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_remove_aborted(self, mock_confirm, app_runner_mocked_collections):
        mock_confirm.return_value = False

        result = app_runner_mocked_collections.invoke(
            args=["collections", "remove", TestCollections.TEST_COLLECTION_1.value["identifier"]]
        )
        assert result.exit_code == 1
        assert f"Aborted!" in result.output

        # verify non-deletion
        result = app_runner_mocked_collections.invoke(
            args=["collections", "inspect", TestCollections.TEST_COLLECTION_1.value["identifier"]]
        )
        assert result.exit_code == 0
        assert f"Ok. Collection details for '{TestCollections.TEST_COLLECTION_1.value['identifier']}':" in result.output

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_remove_force_confirm(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(
            args=["collections", "remove", TestCollections.TEST_COLLECTION_1.value["identifier"], "--force-remove"]
        )
        assert result.exit_code == 0
        assert f"Ok. Collection '{TestCollections.TEST_COLLECTION_1.value['identifier']}' removed." in result.output

        # verify deletion
        result = app_runner_mocked_collections.invoke(
            args=["collections", "remove", TestCollections.TEST_COLLECTION_1.value["identifier"], "--force-remove"]
        )
        assert result.exit_code == 64
        assert (
            f"No. Collection '{TestCollections.TEST_COLLECTION_1.value['identifier']}' does not exist." in result.output
        )

    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_remove_error_no_record_identifier_specified(self, app_runner_mocked_collections):
        result = app_runner_mocked_collections.invoke(args=["collections", "remove"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'COLLECTION_IDENTIFIER'." in result.output

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_remove_error_unknown_collection_identifier(
        self, mock_confirm, app_runner_mocked_collections
    ):
        mock_confirm.return_value = "y"

        result = app_runner_mocked_collections.invoke(args=["collections", "remove", "unknown-identifier"])
        assert result.exit_code == 64
        assert "No. Collection 'unknown-identifier' does not exist." in result.output


class TestCommandCollectionsBulkRemove:
    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_remove(self, mock_confirm, app_runner_mocked_collections):
        mock_confirm.return_value = "y"

        result = app_runner_mocked_collections.invoke(args=["collections", "bulk-remove"])
        assert result.exit_code == 0
        assert f"1 collections to remove." in result.output
        assert f"Ok. Collection '{TestCollections.TEST_COLLECTION_1.value['identifier']}' removed." in result.output
        assert f"Ok. 1 collections removed." in result.output

        # verify deletion
        result = app_runner_mocked_collections.invoke(
            args=["collections", "remove", TestCollections.TEST_COLLECTION_1.value["identifier"]]
        )
        assert result.exit_code == 64
        assert (
            f"No. Collection '{TestCollections.TEST_COLLECTION_1.value['identifier']}' does not exist." in result.output
        )

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @pytest.mark.usefixtures("app_runner_mocked_collections")
    def test_cli_collections_bulk_remove_aborted(self, mock_confirm, app_runner_mocked_collections):
        mock_confirm.return_value = False

        result = app_runner_mocked_collections.invoke(args=["collections", "bulk-remove"])
        assert result.exit_code == 1
        assert f"Aborted!" in result.output

        # verify non-deletion
        result = app_runner_mocked_collections.invoke(
            args=["collections", "inspect", TestCollections.TEST_COLLECTION_1.value["identifier"]]
        )
        assert result.exit_code == 0
        assert f"Ok. Collection details for '{TestCollections.TEST_COLLECTION_1.value['identifier']}':" in result.output


class TestCommandSiteBuildItemPages:
    @pytest.mark.usefixtures("app_static_site")
    def test_cli_site_item_pages(self, app_static_site):
        result = app_static_site.test_cli_runner().invoke(args=["site", "build-items"])
        assert result.exit_code == 0
        assert "2 item pages to generate." in result.output
        assert "# Item page 1/2" in result.output
        assert f"Ok. Generated item page for '{TestRecords.TEST_RECORD_1.value['file_identifier']}'." in result.output
        assert "# Item page 2/2" in result.output
        assert f"Ok. Generated item page for '{TestRecords.TEST_RECORD_2.value['file_identifier']}'." in result.output
        assert "Ok. 2 item pages generated." in result.output

        # Verify file structure
        item_pages_paths = list(Path(app_static_site.config["SITE_PATH"]).glob("**/*.*"))
        assert len(item_pages_paths) == 2
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"items/{TestRecords.TEST_RECORD_1.value['file_identifier']}/index.html"
            )
            in item_pages_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"items/{TestRecords.TEST_RECORD_2.value['file_identifier']}/index.html"
            )
            in item_pages_paths
        )

    @pytest.mark.usefixtures("app_runner_mocked_csw_not_setup")
    def test_cli_site_item_pages_csw_not_setup(self, app_runner_mocked_csw_not_setup):
        result = app_runner_mocked_csw_not_setup.invoke(args=["site", "build-items"])
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_auth_token_error")
    def test_cli_site_item_pages_auth_token_error(self, app_runner_mocked_csw_auth_token_error):
        result = app_runner_mocked_csw_auth_token_error.invoke(args=["site", "build-items"])
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_missing_auth_token")
    def test_cli_site_item_pages_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token):
        result = app_runner_mocked_csw_missing_auth_token.invoke(args=["site", "build-items"])
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_insufficient_auth_token")
    def test_cli_site_item_pages_auth_token_insufficient(self, app_runner_mocked_csw_insufficient_auth_token):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(args=["site", "build-items"])
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output


class TestCommandSiteBuildCollectionPages:
    @pytest.mark.usefixtures("app_static_site")
    def test_cli_site_collection_pages(self, app_static_site):
        result = app_static_site.test_cli_runner().invoke(args=["site", "build-collections"])
        assert result.exit_code == 0
        assert "1 collection pages to generate." in result.output
        assert "# Collection page 1/1" in result.output
        assert (
            f"Ok. Generated collection page for '{TestCollections.TEST_COLLECTION_1.value['identifier']}'."
            in result.output
        )
        assert "Ok. 1 collection pages generated." in result.output

        # Verify file structure
        collection_pages_paths = list(Path(app_static_site.config["SITE_PATH"]).glob("**/*.*"))
        assert len(collection_pages_paths) == 1
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"collections/{TestCollections.TEST_COLLECTION_1.value['identifier']}/index.html"
            )
            in collection_pages_paths
        )

    @pytest.mark.usefixtures("app_runner_mocked_csw_not_setup_mocked_collection")
    def test_cli_site_collection_pages_csw_not_setup(self, app_runner_mocked_csw_not_setup_mocked_collection):
        result = app_runner_mocked_csw_not_setup_mocked_collection.invoke(args=["site", "build-collections"])
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_auth_token_error_mocked_collection")
    def test_cli_site_collection_pages_auth_token_error(self, app_runner_mocked_csw_auth_token_error_mocked_collection):
        result = app_runner_mocked_csw_auth_token_error_mocked_collection.invoke(args=["site", "build-collections"])
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_missing_auth_token_mocked_collection")
    def test_cli_site_collection_pages_auth_token_missing(
        self, app_runner_mocked_csw_missing_auth_token_mocked_collection
    ):
        result = app_runner_mocked_csw_missing_auth_token_mocked_collection.invoke(args=["site", "build-collections"])
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_insufficient_auth_token_mocked_collection")
    def test_cli_site_collection_pages_auth_token_insufficient(
        self, app_runner_mocked_csw_insufficient_auth_token_mocked_collection
    ):
        result = app_runner_mocked_csw_insufficient_auth_token_mocked_collection.invoke(
            args=["site", "build-collections"]
        )
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output


class TestCommandSiteBuildRecords:
    @pytest.mark.usefixtures("app_static_site")
    def test_cli_site_record_pages(self, app_static_site):
        result = app_static_site.test_cli_runner().invoke(args=["site", "build-records"])
        assert result.exit_code == 0

        assert "6 record pages to generate." in result.output
        assert "# Record page 1/2 (stylesheet 1/3)" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecords.TEST_RECORD_1.value['file_identifier']}' (stylesheet 'iso-html')."
            in result.output
        )
        assert "# Record page 1/2 (stylesheet 2/3)" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecords.TEST_RECORD_1.value['file_identifier']}' (stylesheet 'iso-rubric')."
            in result.output
        )
        assert "# Record page 1/2 (stylesheet 3/3)" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecords.TEST_RECORD_1.value['file_identifier']}' (stylesheet 'iso-xml')."
            in result.output
        )
        assert "# Record page 2/2 (stylesheet 1/3)" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecords.TEST_RECORD_2.value['file_identifier']}' (stylesheet 'iso-html')."
            in result.output
        )
        assert "# Record page 2/2 (stylesheet 2/3)" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecords.TEST_RECORD_2.value['file_identifier']}' (stylesheet 'iso-rubric')."
            in result.output
        )
        assert "# Record page 2/2 (stylesheet 3/3)" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecords.TEST_RECORD_2.value['file_identifier']}' (stylesheet 'iso-xml')."
            in result.output
        )
        assert "Ok. 6 record pages generated." in result.output

        # Verify file structure
        record_pages_paths = list(Path(app_static_site.config["SITE_PATH"]).glob("**/*.*"))
        assert len(record_pages_paths) == 6
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecords.TEST_RECORD_1.value['file_identifier']}/iso-html/{TestRecords.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecords.TEST_RECORD_1.value['file_identifier']}/iso-rubric/{TestRecords.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecords.TEST_RECORD_1.value['file_identifier']}/iso-xml/{TestRecords.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecords.TEST_RECORD_2.value['file_identifier']}/iso-html/{TestRecords.TEST_RECORD_2.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecords.TEST_RECORD_2.value['file_identifier']}/iso-rubric/{TestRecords.TEST_RECORD_2.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecords.TEST_RECORD_2.value['file_identifier']}/iso-xml/{TestRecords.TEST_RECORD_2.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )

    @pytest.mark.usefixtures("app_runner_mocked_csw_not_setup")
    def test_cli_site_record_pages_csw_not_setup(self, app_runner_mocked_csw_not_setup):
        result = app_runner_mocked_csw_not_setup.invoke(args=["site", "build-records"])
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_auth_token_error")
    def test_cli_site_record_pages_auth_token_error(self, app_runner_mocked_csw_auth_token_error):
        result = app_runner_mocked_csw_auth_token_error.invoke(args=["site", "build-records"])
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_missing_auth_token")
    def test_cli_site_record_pages_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token):
        result = app_runner_mocked_csw_missing_auth_token.invoke(args=["site", "build-records"])
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_insufficient_auth_token")
    def test_cli_site_record_pages_auth_token_insufficient(self, app_runner_mocked_csw_insufficient_auth_token):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(args=["site", "build-records"])
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output


class TestCommandSiteBuildPages:
    @pytest.mark.usefixtures("app_static_site")
    def test_cli_site_other_pages(self, app_static_site):
        result = app_static_site.test_cli_runner().invoke(args=["site", "build-pages"])
        assert result.exit_code == 0
        assert "3 legal pages to generate." in result.output
        assert "# Legal page 1/3" in result.output
        assert "Ok. Generated legal page for 'cookies'." in result.output
        assert "# Legal page 2/3" in result.output
        assert "Ok. Generated legal page for 'copyright'." in result.output
        assert "# Legal page 3/3" in result.output
        assert "Ok. Generated legal page for 'privacy'." in result.output
        assert "Ok. 3 legal pages generated." in result.output
        assert "Ok. feedback page generated." in result.output

        # Verify file structure
        other_pages_paths = list(Path(app_static_site.config["SITE_PATH"]).glob("**/*.*"))
        assert len(other_pages_paths) == 4
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("legal/cookies/index.html") in other_pages_paths
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("legal/copyright/index.html") in other_pages_paths
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("legal/privacy/index.html") in other_pages_paths
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("feedback/index.html") in other_pages_paths


class TestCommandSiteCopyAssets:
    @pytest.mark.usefixtures("app_static_site")
    def test_cli_site_copy_assets(self, app_static_site):
        result = app_static_site.test_cli_runner().invoke(args=["site", "copy-assets"])
        assert result.exit_code == 0
        assert "Ok. static assets copied." in result.output

        # Verify file structure
        asset_paths = list(Path(app_static_site.config["SITE_PATH"]).glob("**/*.*"))
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("static/txt/heartbeat.txt") in asset_paths


class TestCommandSiteBuildAll:
    @pytest.mark.usefixtures("app_static_site")
    def test_cli_site_build_all(self, app_static_site):
        result = app_static_site.test_cli_runner().invoke(args=["site", "build"])
        assert result.exit_code == 0
        assert "Ok. 2 item pages generated." in result.output
        assert "Ok. 1 collection pages generated." in result.output
        assert "Ok. 6 record pages generated." in result.output
        assert "Ok. 3 legal pages generated." in result.output
        assert "Ok. feedback page generated." in result.output
        assert "Ok. static assets copied." in result.output
        assert "Ok. Site built." in result.output

        # Verify file structure
        site_paths = list(Path(app_static_site.config["SITE_PATH"]).glob("**/*.*"))
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"items/{TestRecords.TEST_RECORD_1.value['file_identifier']}/index.html"
            )
            in site_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"collections/{TestCollections.TEST_COLLECTION_1.value['identifier']}/index.html"
            )
            in site_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecords.TEST_RECORD_1.value['file_identifier']}/iso-html/{TestRecords.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in site_paths
        )
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("legal/cookies/index.html") in site_paths
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("feedback/index.html") in site_paths
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("static/txt/heartbeat.txt") in site_paths


class TestCommandSitePublish:
    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @mock.patch("scar_add_metadata_toolbox.commands.aws_cli")
    @pytest.mark.usefixtures("app_static_site")
    def test_cli_publish(self, mock_aws_cli, mock_confirm, app_static_site):
        mock_confirm.return_value = "y"
        mock_aws_cli.return_value = None

        result = app_static_site.test_cli_runner().invoke(args=["site", "publish"])
        assert result.exit_code == 0
        assert f"Ok. Site published to '{app_static_site.config['S3_BUCKET']}'" in result.output

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @mock.patch("scar_add_metadata_toolbox.commands.aws_cli")
    @pytest.mark.usefixtures("app_static_site")
    def test_cli_publish_build(self, mock_aws_cli, mock_confirm, app_static_site):
        mock_confirm.return_value = "y"
        mock_aws_cli.return_value = None

        result = app_static_site.test_cli_runner().invoke(args=["site", "publish", "--build"])
        assert result.exit_code == 0
        assert "Ok. Site built." in result.output
        assert f"Ok. Site published to '{app_static_site.config['S3_BUCKET']}'" in result.output

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @pytest.mark.usefixtures("app_static_site")
    def test_cli_publish_aborted(self, mock_confirm, app_static_site):
        mock_confirm.return_value = False

        result = app_static_site.test_cli_runner().invoke(args=["site", "publish"])
        assert result.exit_code == 1
        assert f"Aborted!" in result.output

    @mock.patch("scar_add_metadata_toolbox.commands.aws_cli")
    @pytest.mark.usefixtures("app_static_site")
    def test_cli_publish_force_confirm(self, mock_aws_cli, app_static_site):
        mock_aws_cli.return_value = None

        result = app_static_site.test_cli_runner().invoke(args=["site", "publish", "--force-publish"])
        assert result.exit_code == 0
        assert f"Ok. Site published to '{app_static_site.config['S3_BUCKET']}'" in result.output


class TestCommandCSWSetup:
    @pytest.mark.usefixtures("app_runner_mocked_csw_server")
    def test_cli_setup(self, app_runner_mocked_csw_server):
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "published"])
        assert result.exit_code == 0
        assert f"Ok. Catalogue 'published' setup." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_server")
    def test_cli_setup_catalogue_already_setup(self, app_runner_mocked_csw_server):
        # setup catalogue initially
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "published"])
        assert result.exit_code == 0

        # then repeat
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "published"])
        assert result.exit_code == 0
        assert "Ok. Note CSW catalogue 'published' is already setup." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_server")
    def test_cli_setup_no_catalogue_specified(self, app_runner_mocked_csw_server):
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'CATALOGUE'." in result.output

    @pytest.mark.usefixtures("app_runner_mocked_csw_server")
    def test_cli_setup_invalid_catalogue_specified(self, app_runner_mocked_csw_server):
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "invalid"])
        assert result.exit_code == 64
        assert (
            "No. CSW catalogue 'invalid' does not exist. Valid options are [unpublished, published]." in result.output
        )


class TestCommandAuthSignIn:
    @pytest.mark.usefixtures("app_runner")
    def test_cli_sign_in(self, app_runner):
        result = app_runner.invoke(args=["auth", "sign-in"])
        assert result.exit_code == 0
        assert "Ok. Access token for '*unknown*' set in" in result.output


class TestCommandAuthSignOut:
    @pytest.mark.usefixtures("app_runner")
    def test_cli_sign_out(self, app_runner):
        # sign-in first
        result = app_runner.invoke(args=["auth", "sign-in"])
        assert result.exit_code == 0

        result = app_runner.invoke(args=["auth", "sign-out"])
        assert result.exit_code == 0
        assert "Ok. Access token removed." in result.output

    @pytest.mark.usefixtures("app_runner")
    def test_cli_sign_out_missing_file(self, app_runner):
        result = app_runner.invoke(args=["auth", "sign-out"])
        assert result.exit_code == 0
        assert "Ok. Access token removed." in result.output
