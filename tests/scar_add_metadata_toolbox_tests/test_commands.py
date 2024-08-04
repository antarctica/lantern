from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest import mock
from unittest.mock import Mock

import pytest
from bas_metadata_library.standards.iso_19115_2 import MetadataRecordConfigV3
from flask import Flask
from flask.testing import FlaskCliRunner

from tests.scar_add_metadata_toolbox_tests.records import TestRecordConfigurations


class TestCommandRecordsList:
    def test_cli_records_list(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "list"])
        assert result.exit_code == 0
        assert (
            "│ 7e3719b4-60a4-4b4e-aa84-cee7a5e7218f │ dataset       "
            "│ Test Item Record 7 (Imported, Duplicate of Test Record 1)             │ Published   │" in result.output
        )
        assert (
            "│ 39d47e50-f94f-43c5-9060-510d9374b81b │ dataset       "
            "│ Test Item Record 2 (Unpublished)                                      │ Unpublished │" in result.output
        )
        assert (
            "│ b759077f-bd3f-4a18-bbd7-e6b3f84bc551 │ collection    "
            "│ Test Collection 3 (Imported, Updated, Duplicate of Test Collection 1) │ Published   │" in result.output
        )
        assert "Ok. 3 records." in result.output

    def test_cli_records_list_csw_not_setup(self, app_runner_mocked_csw_not_setup: FlaskCliRunner):
        result = app_runner_mocked_csw_not_setup.invoke(args=["records", "list"])
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    def test_cli_records_list_auth_token_error(self, app_runner_mocked_csw_auth_token_error: FlaskCliRunner):
        result = app_runner_mocked_csw_auth_token_error.invoke(args=["records", "list"])
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    def test_cli_records_list_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token: FlaskCliRunner):
        result = app_runner_mocked_csw_missing_auth_token.invoke(args=["records", "list"])
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    def test_cli_records_list_auth_token_insufficient(
        self, app_runner_mocked_csw_insufficient_auth_token: FlaskCliRunner
    ):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(args=["records", "list"])
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output


class TestCommandRecordsImport:
    def test_cli_records_import(self, app_runner_mocked_csw: FlaskCliRunner):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecordConfigurations.TEST_RECORD_3.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 0
            assert f"Ok. Record '{record_data['file_identifier']}' imported." in result.output

            # verify insert
            result = app_runner_mocked_csw.invoke(args=["records", "list"])
            assert result.exit_code == 0
            assert f"{record_data['file_identifier']}" in result.output

    def test_cli_records_import_allow_update(self, app_runner_mocked_csw: FlaskCliRunner):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecordConfigurations.TEST_RECORD_4.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw.invoke(args=["records", "import", record_file.name, "--allow-update"])
            assert result.exit_code == 0
            assert f"Ok. Record '{record_data['file_identifier']}' updated." in result.output

    def test_cli_records_import_publish(self, app_runner_mocked_csw: FlaskCliRunner):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecordConfigurations.TEST_RECORD_5.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw.invoke(args=["records", "import", record_file.name, "--publish"])
            assert result.exit_code == 0
            assert f"Ok. Record '{record_data['file_identifier']}' imported." in result.output
            assert f"Ok. Record '{record_data['file_identifier']}' published." in result.output

    def test_cli_records_import_publish_allow_update_allow_republish(self, app_runner_mocked_csw: FlaskCliRunner):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecordConfigurations.TEST_RECORD_6.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw.invoke(
                args=["records", "import", record_file.name, "--allow-update", "--publish", "--allow-republish"]
            )
            assert result.exit_code == 0
            assert f"Ok. Record '{record_data['file_identifier']}' updated." in result.output
            assert f"Ok. Record '{record_data['file_identifier']}' republished." in result.output

    def test_cli_records_import_error_no_file_specified(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "import"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORD_PATH'." in result.output

    def test_cli_records_import_error_directory_specified(self, app_runner_mocked_csw: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            result = app_runner_mocked_csw.invoke(args=["records", "import", record_directory])
            assert result.exit_code == 2
            assert f"Error: Invalid value for 'RECORD_PATH': File '{record_directory}' is a directory." in result.output

    def test_cli_records_import_error_nonexistent_file(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "import", "/nonexistent_file"])
        assert result.exit_code == 2
        assert "Error: Invalid value for 'RECORD_PATH': File '/nonexistent_file' does not exist." in result.output

    def test_cli_records_import_error_empty_file(self, app_runner_mocked_csw: FlaskCliRunner):
        with NamedTemporaryFile(mode="r+") as record_file:
            result = app_runner_mocked_csw.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert f"No. Record in file '{record_file.name}' is not valid JSON." in result.output

    def test_cli_records_import_error_invalid_json_file(self, app_runner_mocked_csw: FlaskCliRunner):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_file.write("Invalid JSON.")
            record_file.flush()

            result = app_runner_mocked_csw.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert f"No. Record in file '{record_file.name}' is not valid JSON." in result.output

    def test_cli_records_import_csw_not_setup(self, app_runner_mocked_csw_not_setup: FlaskCliRunner):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecordConfigurations.TEST_RECORD_3.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw_not_setup.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert "No. CSW catalogue not setup." in result.output

    def test_cli_records_import_auth_token_error(self, app_runner_mocked_csw_auth_token_error: FlaskCliRunner):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecordConfigurations.TEST_RECORD_3.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw_auth_token_error.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    def test_cli_records_import_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token: FlaskCliRunner):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecordConfigurations.TEST_RECORD_3.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw_missing_auth_token.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    def test_cli_records_import_auth_token_insufficient(
        self, app_runner_mocked_csw_insufficient_auth_token: FlaskCliRunner
    ):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecordConfigurations.TEST_RECORD_3.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw_insufficient_auth_token.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output

    def test_cli_records_import_error_server(self, app_runner_mocked_csw_inserts_fail: FlaskCliRunner):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecordConfigurations.TEST_RECORD_3.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw_inserts_fail.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert f"No. Server error importing record '{record_data['file_identifier']}'." in result.output

    def test_cli_records_import_error_conflict(self, app_runner_mocked_csw: FlaskCliRunner):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecordConfigurations.TEST_RECORD_7.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 64
            assert (
                f"No. Record '{record_data['file_identifier']}' already exists. Add `--allow-update` flag to allow."
                in result.output
            )

    def test_cli_records_import_error_publish_conflict(self, app_runner_mocked_csw: FlaskCliRunner):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_data = TestRecordConfigurations.TEST_RECORD_7.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw.invoke(
                args=["records", "import", record_file.name, "--allow-update", "--publish"]
            )
            assert result.exit_code == 64
            assert f"Ok. Record '{record_data['file_identifier']}' updated." in result.output
            assert (
                f"No. Record '{record_data['file_identifier']}' already published. "
                f"Add `--allow-republish` flag to allow." in result.output
            )


class TestCommandRecordsBulkImport:
    def test_cli_records_bulk_import(self, app_runner_mocked_csw: FlaskCliRunner):
        with (
            TemporaryDirectory() as record_directory,
            Path(f"{record_directory}/record.json").open(mode="w+") as record_file,
        ):
            record_data = TestRecordConfigurations.TEST_RECORD_3.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

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

    def test_cli_records_bulk_import_allow_update(self, app_runner_mocked_csw: FlaskCliRunner):
        with (
            TemporaryDirectory() as record_directory,
            Path(f"{record_directory}/record.json").open(mode="w+") as record_file,
        ):
            record_data = TestRecordConfigurations.TEST_RECORD_4.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw.invoke(args=["records", "bulk-import", record_directory, "--allow-update"])
            assert result.exit_code == 0
            assert "1 records to import/update." in result.output
            assert "# Record 1/1" in result.output
            assert f"Ok. Record '{record_data['file_identifier']}' updated." in result.output
            assert "Ok. 1 records imported/updated." in result.output

    def test_cli_records_bulk_import_publish(self, app_runner_mocked_csw: FlaskCliRunner):
        with (
            TemporaryDirectory() as record_directory,
            Path(f"{record_directory}/record.json").open(mode="w+") as record_file,
        ):
            record_data = TestRecordConfigurations.TEST_RECORD_5.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw.invoke(args=["records", "bulk-import", record_directory, "--publish"])
            assert result.exit_code == 0
            assert "1 records to import/update." in result.output
            assert "# Record 1/1" in result.output
            assert f"Ok. Record '{record_data['file_identifier']}' imported." in result.output
            assert f"Ok. Record '{record_data['file_identifier']}' published." in result.output
            assert "Ok. 1 records imported/updated." in result.output

    def test_cli_records_bulk_import_publish_allow_update_allow_republish(self, app_runner_mocked_csw: FlaskCliRunner):
        with (
            TemporaryDirectory() as record_directory,
            Path(f"{record_directory}/record.json").open(mode="w+") as record_file,
        ):
            record_data = TestRecordConfigurations.TEST_RECORD_6.value
            # noinspection PyArgumentList
            record_configuration = MetadataRecordConfigV3(**record_data)
            record_configuration.dump(file=Path(record_file.name))

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

    def test_cli_records_bulk_import_empty_directory(self, app_runner_mocked_csw: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            result = app_runner_mocked_csw.invoke(args=["records", "bulk-import", record_directory])
            assert result.exit_code == 0
            assert "0 records to import/update." in result.output
            assert "Ok. 0 records imported/updated." in result.output

    def test_cli_records_bulk_import_error_no_directory_specified(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-import"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORDS_PATH'." in result.output

    def test_cli_records_bulk_import_error_file_specified(self, app_runner_mocked_csw: FlaskCliRunner):
        with NamedTemporaryFile() as record_file:
            result = app_runner_mocked_csw.invoke(args=["records", "bulk-import", record_file.name])
            assert result.exit_code == 2
            assert (
                f"Error: Invalid value for 'RECORDS_PATH': Directory '{record_file.name}' is a file." in result.output
            )

    def test_cli_records_bulk_import_error_nonexistent_directory(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-import", "/nonexistent_directory"])
        assert result.exit_code == 2
        assert (
            "Error: Invalid value for 'RECORDS_PATH': Directory '/nonexistent_directory' does not exist."
            in result.output
        )

    def test_cli_records_bulk_import_error_invoked_command_error(self, app_runner_mocked_csw: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            valid_record_path = Path(f"{record_directory}/01-valid-record.json")
            invalid_record_path = Path(f"{record_directory}/02-invalid-record.json")
            with (
                valid_record_path.open(mode="w+") as valid_record_file,
                invalid_record_path.open(mode="w+") as invalid_record_file,
            ):
                valid_record_data = TestRecordConfigurations.TEST_RECORD_3.value
                # noinspection PyArgumentList
                record_configuration = MetadataRecordConfigV3(**valid_record_data)
                record_configuration.dump(file=Path(valid_record_file.name))
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
    def test_cli_records_publish(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(
            args=["records", "publish", TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 0
        assert (
            f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}' published."
            in result.output
        )

    def test_cli_records_publish_allow_republish(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(
            args=[
                "records",
                "publish",
                TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"],
                "--allow-republish",
            ]
        )
        assert result.exit_code == 0
        assert (
            f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' republished."
            in result.output
        )

    def test_cli_records_publish_error_no_record_identifier(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "publish"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORD_IDENTIFIER'." in result.output

    def test_cli_records_publish_csw_not_setup(self, app_runner_mocked_csw_not_setup: FlaskCliRunner):
        result = app_runner_mocked_csw_not_setup.invoke(
            args=["records", "publish", TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    def test_cli_records_publish_auth_token_error(self, app_runner_mocked_csw_auth_token_error: FlaskCliRunner):
        result = app_runner_mocked_csw_auth_token_error.invoke(
            args=["records", "publish", TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    def test_cli_records_publish_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token: FlaskCliRunner):
        result = app_runner_mocked_csw_missing_auth_token.invoke(
            args=["records", "publish", TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    def test_cli_records_publish_auth_token_insufficient(
        self, app_runner_mocked_csw_insufficient_auth_token: FlaskCliRunner
    ):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(
            args=["records", "publish", TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output

    def test_cli_records_publish_error_unknown_record_identifier(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "publish", "unknown-identifier"])
        assert result.exit_code == 64
        assert "No. Record 'unknown-identifier' does not exist." in result.output

    def test_cli_records_publish_error_conflict(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(
            args=["records", "publish", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert (
            f"No. Record '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' already published. Add "
            f"`--allow-republish` flag to allow." in result.output
        )

    def test_cli_records_import_error_server(self, app_runner_mocked_csw_inserts_fail: FlaskCliRunner):
        result = app_runner_mocked_csw_inserts_fail.invoke(
            args=["records", "publish", TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"]]
        )

        assert result.exit_code == 64
        assert (
            f"No. Server error publishing record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}'."
            in result.output
        )


class TestCommandRecordsBulkPublish:
    def test_cli_records_bulk_publish(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-publish"])
        assert result.exit_code == 0
        assert "1 records to (re)publish." in result.output
        assert "# Record 1/1" in result.output
        assert (
            f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}' published."
            in result.output
        )
        assert "Ok. 1 records (re)published." in result.output

    def test_cli_records_bulk_publish_force_republish(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-publish", "--force-republish"])
        assert result.exit_code == 0
        assert "3 records to (re)publish." in result.output
        assert "# Record 1/3" in result.output
        assert (
            f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' republished."
            in result.output
        )
        assert "# Record 2/3" in result.output
        assert (
            f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}' published."
            in result.output
        )
        assert "# Record 3/3" in result.output
        assert (
            f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}' republished."
            in result.output
        )
        assert "Ok. 3 records (re)published." in result.output

    def test_cli_records_bulk_publish_error_invoked_command_error(
        self, app_runner_mocked_csw_inserts_fail: FlaskCliRunner
    ):
        result = app_runner_mocked_csw_inserts_fail.invoke(args=["records", "bulk-publish"])
        assert result.exit_code == 64
        assert "1 records to (re)publish." in result.output
        assert "# Record 1/1" in result.output
        assert (
            f"No. Server error publishing record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}'."
            in result.output
        )


class TestCommandRecordsExport:
    def test_cli_records_export(self, app_runner_mocked_csw: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")
            result = app_runner_mocked_csw.invoke(
                args=[
                    "records",
                    "export",
                    TestRecordConfigurations.TEST_RECORD_7.value["file_identifier"],
                    str(record_path),
                ]
            )
            assert result.exit_code == 0
            assert (
                f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_7.value['file_identifier']}' exported."
                in result.output
            )

            # verify export
            export_record_configuration = MetadataRecordConfigV3()
            export_record_configuration.load(file=record_path)
            # noinspection PyArgumentList
            verification_record_configuration = MetadataRecordConfigV3(**TestRecordConfigurations.TEST_RECORD_7.value)
            assert export_record_configuration.config == verification_record_configuration.config

    def test_cli_records_export_allow_overwrite(self, app_runner_mocked_csw: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")

            # Write file out initially
            result = app_runner_mocked_csw.invoke(
                args=[
                    "records",
                    "export",
                    TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"],
                    str(record_path),
                ]
            )
            assert result.exit_code == 0

            result = app_runner_mocked_csw.invoke(
                args=[
                    "records",
                    "export",
                    TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"],
                    str(record_path),
                    "--allow-overwrite",
                ]
            )
            assert result.exit_code == 0
            assert (
                f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' re-exported."
                in result.output
            )

    def test_cli_records_export_error_no_record_identifier_specified(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "export"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORD_IDENTIFIER'." in result.output

    def test_cli_records_export_error_no_record_path_specified(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(
            args=["records", "export", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORD_PATH'." in result.output

    def test_cli_records_export_error_record_path_directory_specified(self, app_runner_mocked_csw: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            result = app_runner_mocked_csw.invoke(
                args=[
                    "records",
                    "export",
                    TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"],
                    record_directory,
                ]
            )
            assert result.exit_code == 2
            assert f"Error: Invalid value for 'RECORD_PATH': File '{record_directory}' is a directory." in result.output

    def test_cli_records_export_csw_not_setup(self, app_runner_mocked_csw_not_setup: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")
            result = app_runner_mocked_csw_not_setup.invoke(
                args=[
                    "records",
                    "export",
                    TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"],
                    str(record_path),
                ]
            )
            assert result.exit_code == 64
            assert "No. CSW catalogue not setup." in result.output

    def test_cli_records_export_auth_token_error(self, app_runner_mocked_csw_auth_token_error: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")
            result = app_runner_mocked_csw_auth_token_error.invoke(
                args=[
                    "records",
                    "export",
                    TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"],
                    str(record_path),
                ]
            )
            assert result.exit_code == 64
            assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    def test_cli_records_export_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")
            result = app_runner_mocked_csw_missing_auth_token.invoke(
                args=[
                    "records",
                    "export",
                    TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"],
                    str(record_path),
                ]
            )
            assert result.exit_code == 64
            assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    def test_cli_records_list_auth_token_insufficient(
        self, app_runner_mocked_csw_insufficient_auth_token: FlaskCliRunner
    ):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")
            result = app_runner_mocked_csw_insufficient_auth_token.invoke(
                args=[
                    "records",
                    "export",
                    TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"],
                    str(record_path),
                ]
            )
            assert result.exit_code == 64
            assert (
                "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output
            )

    def test_cli_records_export_error_unknown_record_identifier(self, app_runner_mocked_csw: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")

            result = app_runner_mocked_csw.invoke(args=["records", "export", "unknown-identifier", str(record_path)])
            assert result.exit_code == 64
            assert "No. Record 'unknown-identifier' does not exist." in result.output

    def test_cli_records_export_error_conflict(self, app_runner_mocked_csw: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            record_path = Path(record_directory).joinpath("record.json")

            # Write file out initially
            result = app_runner_mocked_csw.invoke(
                args=[
                    "records",
                    "export",
                    TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"],
                    str(record_path),
                ]
            )
            assert result.exit_code == 0

            result = app_runner_mocked_csw.invoke(
                args=[
                    "records",
                    "export",
                    TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"],
                    str(record_path),
                ]
            )
            assert result.exit_code == 64
            assert (
                f"No. Export of record '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' would be "
                f"overwritten. Add `--allow-overwrite` flag to allow." in result.output
            )


class TestCommandRecordsBulkExport:
    def test_cli_records_bulk_export(self, app_runner_mocked_csw: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            records_path = Path(record_directory)

            result = app_runner_mocked_csw.invoke(args=["records", "bulk-export", str(records_path)])
            assert result.exit_code == 0
            assert "3 records to (re)export." in result.output
            assert "# Record 1/3" in result.output
            assert (
                f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' exported."
                in result.output
            )
            assert "# Record 2/3" in result.output
            assert (
                f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}' exported."
                in result.output
            )
            assert "# Record 3/3" in result.output
            assert (
                f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}' exported."
                in result.output
            )
            assert "Ok. 3 records (re)exported." in result.output

            # Verify export
            record_paths = list(records_path.glob("*.json"))
            assert len(record_paths) == 3
            assert (
                records_path.joinpath(f"{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}.json")
                in record_paths
            )
            assert (
                records_path.joinpath(f"{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}.json")
                in record_paths
            )
            assert (
                records_path.joinpath(f"{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}.json")
                in record_paths
            )

            export_record_configuration = MetadataRecordConfigV3()
            export_record_configuration.load(
                file=records_path.joinpath(f"{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}.json")
            )
            # noinspection PyArgumentList
            verification_record_configuration = MetadataRecordConfigV3(**TestRecordConfigurations.TEST_RECORD_7.value)
            assert export_record_configuration.config == verification_record_configuration.config

    def test_cli_records_bulk_export_allow_overwrite(self, app_runner_mocked_csw: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            records_path = Path(record_directory)

            # Write file out initially
            record_path = records_path.joinpath(
                f"{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}.json"
            )
            result = app_runner_mocked_csw.invoke(
                args=[
                    "records",
                    "export",
                    TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"],
                    str(record_path),
                ]
            )
            assert result.exit_code == 0

            result = app_runner_mocked_csw.invoke(
                args=[
                    "records",
                    "bulk-export",
                    record_directory,
                    "--allow-overwrite",
                ]
            )
            assert result.exit_code == 0
            assert "3 records to (re)export." in result.output
            assert "# Record 1/3" in result.output
            assert (
                f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' exported."
                in result.output
            )
            assert "# Record 2/3" in result.output
            assert (
                f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}' re-exported."
                in result.output
            )
            assert "# Record 3/3" in result.output
            assert (
                f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}' exported."
                in result.output
            )
            assert "Ok. 3 records (re)exported." in result.output

    def test_cli_records_bulk_export_error_no_directory_specified(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-export"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORDS_PATH'." in result.output

    def test_cli_records_bulk_export_error_file_specified(self, app_runner_mocked_csw: FlaskCliRunner):
        with NamedTemporaryFile() as record_file:
            result = app_runner_mocked_csw.invoke(args=["records", "bulk-export", record_file.name])
            assert result.exit_code == 2
            assert (
                f"Error: Invalid value for 'RECORDS_PATH': Directory '{record_file.name}' is a file." in result.output
            )

    def test_cli_records_bulk_export_error_nonexistent_directory(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-export", "/nonexistent_directory"])
        assert result.exit_code == 2
        assert (
            "Error: Invalid value for 'RECORDS_PATH': Directory '/nonexistent_directory' does not exist."
            in result.output
        )

    def test_cli_records_bulk_export_error_invoked_command_error(self, app_runner_mocked_csw: FlaskCliRunner):
        with TemporaryDirectory() as record_directory:
            records_path = Path(record_directory)

            # Write file out initially
            record_path = records_path.joinpath(
                f"{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}.json"
            )
            result = app_runner_mocked_csw.invoke(
                args=[
                    "records",
                    "export",
                    TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"],
                    str(record_path),
                ]
            )
            assert result.exit_code == 0

            result = app_runner_mocked_csw.invoke(args=["records", "bulk-export", record_directory])
            assert result.exit_code == 64
            assert "3 records to (re)export." in result.output
            assert "# Record 1/3" in result.output
            assert (
                f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' exported."
                in result.output
            )
            assert "# Record 2/3" in result.output
            assert (
                f"No. Export of record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}' would be "
                f"overwritten. Add `--allow-overwrite` flag to allow." in result.output
            )


class TestCommandRecordsRemove:
    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    def test_cli_records_remove(self, mock_confirm: Mock, app_runner_mocked_csw: FlaskCliRunner):
        mock_confirm.return_value = "y"

        result = app_runner_mocked_csw.invoke(
            args=["records", "remove", TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 0
        assert (
            f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}' removed." in result.output
        )

        # verify deletion
        result = app_runner_mocked_csw.invoke(
            args=["records", "remove", TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert (
            f"No. Record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}' does not exist."
            in result.output
        )

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    def test_cli_records_remove_aborted(self, mock_confirm: Mock, app_runner_mocked_csw: FlaskCliRunner):
        mock_confirm.return_value = False

        result = app_runner_mocked_csw.invoke(
            args=["records", "remove", TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 1
        assert "Aborted!" in result.output

        # verify non-deletion
        result = app_runner_mocked_csw.invoke(args=["records", "list"])
        assert result.exit_code == 0
        assert TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"] in result.output

    def test_cli_records_remove_force_confirm(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(
            args=[
                "records",
                "remove",
                TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"],
                "--force-remove",
            ]
        )
        assert result.exit_code == 0
        assert (
            f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}' removed." in result.output
        )

        # verify deletion
        result = app_runner_mocked_csw.invoke(
            args=[
                "records",
                "remove",
                TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"],
                "--force-remove",
            ]
        )
        assert result.exit_code == 64
        assert (
            f"No. Record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}' does not exist."
            in result.output
        )

    def test_cli_records_remove_error_no_record_identifier_specified(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "remove"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORD_IDENTIFIER'." in result.output

    def test_cli_records_remove_csw_not_setup(self, app_runner_mocked_csw_not_setup: FlaskCliRunner):
        result = app_runner_mocked_csw_not_setup.invoke(
            args=[
                "records",
                "remove",
                TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"],
                "--force-remove",
            ]
        )
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    def test_cli_records_remove_auth_token_error(self, app_runner_mocked_csw_auth_token_error: FlaskCliRunner):
        result = app_runner_mocked_csw_auth_token_error.invoke(
            args=[
                "records",
                "remove",
                TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"],
                "--force-remove",
            ]
        )
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    def test_cli_records_remove_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token: FlaskCliRunner):
        result = app_runner_mocked_csw_missing_auth_token.invoke(
            args=[
                "records",
                "remove",
                TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"],
                "--force-remove",
            ]
        )
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    def test_cli_records_remove_auth_token_insufficient(
        self, app_runner_mocked_csw_insufficient_auth_token: FlaskCliRunner
    ):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(
            args=[
                "records",
                "remove",
                TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"],
                "--force-remove",
            ]
        )
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    def test_cli_records_remove_error_unknown_record_identifier(
        self, mock_confirm: Mock, app_runner_mocked_csw: FlaskCliRunner
    ):
        mock_confirm.return_value = "y"

        result = app_runner_mocked_csw.invoke(args=["records", "remove", "unknown-identifier"])
        assert result.exit_code == 64
        assert "No. Record 'unknown-identifier' does not exist." in result.output

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    def test_cli_records_remove_error_published(self, mock_confirm: Mock, app_runner_mocked_csw: FlaskCliRunner):
        mock_confirm.return_value = "y"

        result = app_runner_mocked_csw.invoke(
            args=["records", "remove", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert (
            f"No. Record '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' is published, "
            f"retract it first." in result.output
        )


class TestCommandRecordsBulkRemove:
    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    def test_cli_records_bulk_remove(self, mock_confirm: Mock, app_runner_mocked_csw: FlaskCliRunner):
        mock_confirm.return_value = "y"

        result = app_runner_mocked_csw.invoke(args=["records", "bulk-remove"])
        assert result.exit_code == 0
        assert "1 records to remove." in result.output
        assert (
            f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}' removed." in result.output
        )
        assert "Ok. 1 records removed." in result.output

        # verify deletion
        result = app_runner_mocked_csw.invoke(
            args=["records", "remove", TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert (
            f"No. Record '{TestRecordConfigurations.TEST_RECORD_2.value['file_identifier']}' does not exist."
            in result.output
        )

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    def test_cli_records_bulk_remove_aborted(self, mock_confirm: Mock, app_runner_mocked_csw: FlaskCliRunner):
        mock_confirm.return_value = False

        result = app_runner_mocked_csw.invoke(args=["records", "bulk-remove"])
        assert result.exit_code == 1
        assert "Aborted!" in result.output

        # verify non-deletion
        result = app_runner_mocked_csw.invoke(args=["records", "list"])
        assert result.exit_code == 0
        assert TestRecordConfigurations.TEST_RECORD_2.value["file_identifier"] in result.output


class TestCommandRecordsRetract:
    def test_cli_records_retract(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(
            args=["records", "retract", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 0
        assert (
            f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' retracted."
            in result.output
        )

        # verify retraction
        result = app_runner_mocked_csw.invoke(
            args=["records", "retract", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert (
            f"No. Record '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' is not published."
            in result.output
        )

    def test_cli_records_retract_error_no_record_identifier_specified(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "retract"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'RECORD_IDENTIFIER'." in result.output

    def test_cli_records_retract_csw_not_setup(self, app_runner_mocked_csw_not_setup: FlaskCliRunner):
        result = app_runner_mocked_csw_not_setup.invoke(
            args=["records", "retract", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    def test_cli_records_retract_auth_token_error(self, app_runner_mocked_csw_auth_token_error: FlaskCliRunner):
        result = app_runner_mocked_csw_auth_token_error.invoke(
            args=["records", "retract", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    def test_cli_records_retract_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token: FlaskCliRunner):
        result = app_runner_mocked_csw_missing_auth_token.invoke(
            args=["records", "retract", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    def test_cli_records_retract_auth_token_insufficient(
        self, app_runner_mocked_csw_insufficient_auth_token: FlaskCliRunner
    ):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(
            args=["records", "retract", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output

    def test_cli_records_retract_error_unknown_record_identifier(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "retract", "unknown-identifier"])
        assert result.exit_code == 64
        assert "No. Record 'unknown-identifier' is not published." in result.output


class TestCommandRecordsBulkRetract:
    def test_cli_records_bulk_retract(self, app_runner_mocked_csw: FlaskCliRunner):
        result = app_runner_mocked_csw.invoke(args=["records", "bulk-retract"])
        assert result.exit_code == 0
        assert "2 records to retract." in result.output
        assert (
            f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' retracted."
            in result.output
        )
        assert (
            f"Ok. Record '{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}' retracted."
            in result.output
        )
        assert "Ok. 2 records retracted." in result.output

        # verify deletion
        result = app_runner_mocked_csw.invoke(
            args=["records", "retract", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert (
            f"No. Record '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' is not published."
            in result.output
        )


class TestCommandSiteBuildItemPages:
    def test_cli_site_item_pages(self, app_static_site: Flask):
        result = app_static_site.test_cli_runner().invoke(args=["site", "build-items"])
        assert result.exit_code == 0
        assert "1 item pages to generate." in result.output
        assert "# Item page 1/1" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}'."
            in result.output
        )
        assert "Ok. 1 item pages generated." in result.output

        # Verify file structure
        item_pages_paths = list(Path(app_static_site.config["SITE_PATH"]).glob("**/*.*"))
        assert len(item_pages_paths) == 1
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"items/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/index.html"
            )
            in item_pages_paths
        )

    def test_cli_site_item_pages_csw_not_setup(self, app_runner_mocked_csw_not_setup: FlaskCliRunner):
        result = app_runner_mocked_csw_not_setup.invoke(args=["site", "build-items"])
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    def test_cli_site_item_pages_auth_token_error(self, app_runner_mocked_csw_auth_token_error: FlaskCliRunner):
        result = app_runner_mocked_csw_auth_token_error.invoke(args=["site", "build-items"])
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    def test_cli_site_item_pages_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token: FlaskCliRunner):
        result = app_runner_mocked_csw_missing_auth_token.invoke(args=["site", "build-items"])
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    def test_cli_site_item_pages_auth_token_insufficient(
        self, app_runner_mocked_csw_insufficient_auth_token: FlaskCliRunner
    ):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(args=["site", "build-items"])
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output


class TestCommandSiteBuildItemPage:
    def test_cli_site_item_page(self, app_static_site: Flask):
        result = app_static_site.test_cli_runner().invoke(
            args=["site", "build-item", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 0
        assert (
            f"Generating item page for '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}'"
            in result.output
        )
        assert (
            f"Ok. Generated item page for '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}'."
            in result.output
        )

        # Verify file structure
        item_pages_paths = list(Path(app_static_site.config["SITE_PATH"]).glob("**/*.*"))
        assert len(item_pages_paths) == 1
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"items/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/index.html"
            )
            in item_pages_paths
        )

    def test_cli_site_item_page_csw_not_setup(self, app_runner_mocked_csw_not_setup: FlaskCliRunner):
        result = app_runner_mocked_csw_not_setup.invoke(
            args=["site", "build-item", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    def test_cli_site_item_page_auth_token_error(self, app_runner_mocked_csw_auth_token_error: FlaskCliRunner):
        result = app_runner_mocked_csw_auth_token_error.invoke(
            args=["site", "build-item", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    def test_cli_site_item_page_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token: FlaskCliRunner):
        result = app_runner_mocked_csw_missing_auth_token.invoke(
            args=["site", "build-item", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    def test_cli_site_item_page_auth_token_insufficient(
        self, app_runner_mocked_csw_insufficient_auth_token: FlaskCliRunner
    ):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(
            args=["site", "build-item", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output

    def test_cli_site_item_page_record_missing(self, app_static_site: Flask):
        result = app_static_site.test_cli_runner().invoke(args=["site", "build-item", "does-not-exist"])
        assert result.exit_code == 64
        assert "No. Record 'does-not-exist' does not exist."


class TestCommandSiteBuildCollectionPages:
    def test_cli_site_collection_pages(self, app_static_site: Flask):
        result = app_static_site.test_cli_runner().invoke(args=["site", "build-collections"])
        assert result.exit_code == 0
        assert "1 collection pages to generate." in result.output
        assert "# Collection page 1/1" in result.output
        assert (
            f"Ok. Generated collection page for '{TestRecordConfigurations.TEST_RECORD_8.value['file_identifier']}'."
            in result.output
        )
        assert "Ok. 1 collection pages generated." in result.output

        # Verify file structure
        collection_pages_paths = list(Path(app_static_site.config["SITE_PATH"]).glob("**/*.*"))
        assert len(collection_pages_paths) == 1
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"collections/{TestRecordConfigurations.TEST_RECORD_8.value['file_identifier']}/index.html"
            )
            in collection_pages_paths
        )

    def test_cli_site_collection_pages_csw_not_setup(self, app_runner_mocked_csw_not_setup: FlaskCliRunner):
        result = app_runner_mocked_csw_not_setup.invoke(args=["site", "build-collections"])
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    def test_cli_site_collection_pages_auth_token_error(self, app_runner_mocked_csw_auth_token_error: FlaskCliRunner):
        result = app_runner_mocked_csw_auth_token_error.invoke(args=["site", "build-collections"])
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    def test_cli_site_collection_pages_auth_token_missing(
        self, app_runner_mocked_csw_missing_auth_token: FlaskCliRunner
    ):
        result = app_runner_mocked_csw_missing_auth_token.invoke(args=["site", "build-collections"])
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    def test_cli_site_collection_pages_auth_token_insufficient(
        self, app_runner_mocked_csw_insufficient_auth_token: FlaskCliRunner
    ):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(args=["site", "build-collections"])
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output


class TestCommandSiteBuildRecordPages:
    def test_cli_site_record_pages(self, app_static_site: Flask):
        result = app_static_site.test_cli_runner().invoke(args=["site", "build-records"])
        assert result.exit_code == 0

        assert "6 record pages to generate." in result.output
        assert "# Record page 1/2 (stylesheet 1/3)" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' "
            f"(stylesheet 'iso-html')." in result.output
        )
        assert "# Record page 1/2 (stylesheet 2/3)" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' "
            f"(stylesheet 'iso-rubric')." in result.output
        )
        assert "# Record page 1/2 (stylesheet 3/3)" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' "
            f"(stylesheet 'iso-xml')." in result.output
        )
        assert "# Record page 2/2 (stylesheet 1/3)" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}' "
            f"(stylesheet 'iso-html')." in result.output
        )
        assert "# Record page 2/2 (stylesheet 2/3)" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}' "
            f"(stylesheet 'iso-rubric')." in result.output
        )
        assert "# Record page 2/2 (stylesheet 3/3)" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}' "
            f"(stylesheet 'iso-xml')." in result.output
        )
        assert "Ok. 6 record pages generated." in result.output

        # Verify file structure
        record_pages_paths = list(Path(app_static_site.config["SITE_PATH"]).glob("**/*.*"))
        assert len(record_pages_paths) == 6
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/iso-html/"
                f"{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/iso-rubric/"
                f"{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/iso-xml/"
                f"{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}/iso-html/"
                f"{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}/iso-rubric/"
                f"{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}/iso-xml/"
                f"{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )

    def test_cli_site_record_pages_csw_not_setup(self, app_runner_mocked_csw_not_setup: FlaskCliRunner):
        result = app_runner_mocked_csw_not_setup.invoke(args=["site", "build-records"])
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    def test_cli_site_record_pages_auth_token_error(self, app_runner_mocked_csw_auth_token_error: FlaskCliRunner):
        result = app_runner_mocked_csw_auth_token_error.invoke(args=["site", "build-records"])
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    def test_cli_site_record_pages_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token: FlaskCliRunner):
        result = app_runner_mocked_csw_missing_auth_token.invoke(args=["site", "build-records"])
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    def test_cli_site_record_pages_auth_token_insufficient(
        self, app_runner_mocked_csw_insufficient_auth_token: FlaskCliRunner
    ):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(args=["site", "build-records"])
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output


class TestCommandSiteBuildRecordPage:
    def test_cli_site_build_record(self, app_static_site: Flask):
        result = app_static_site.test_cli_runner().invoke(
            args=["site", "build-record", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 0

        assert (
            f"3 record pages to generate for record "
            f"'{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}'." in result.output
        )
        assert "# Stylesheet 1/3" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' "
            f"(stylesheet 'iso-html')." in result.output
        )
        assert "# Stylesheet 2/3" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' "
            f"(stylesheet 'iso-rubric')." in result.output
        )
        assert "# Stylesheet 3/3" in result.output
        assert (
            f"Ok. Generated item page for '{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}' "
            f"(stylesheet 'iso-xml')." in result.output
        )
        assert (
            f"Ok. 3 record pages generated for record "
            f"'{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}'." in result.output
        )

        # Verify file structure
        record_pages_paths = list(Path(app_static_site.config["SITE_PATH"]).glob("**/*.*"))
        assert len(record_pages_paths) == 3
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/iso-html/"
                f"{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/iso-rubric/"
                f"{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/iso-xml/"
                f"{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )

    def test_cli_site_record_pages_csw_not_setup(self, app_runner_mocked_csw_not_setup: FlaskCliRunner):
        result = app_runner_mocked_csw_not_setup.invoke(
            args=["site", "build-record", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. CSW catalogue not setup." in result.output

    def test_cli_site_record_pages_auth_token_error(self, app_runner_mocked_csw_auth_token_error: FlaskCliRunner):
        result = app_runner_mocked_csw_auth_token_error.invoke(
            args=["site", "build-record", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Error with auth token. Try signing out and in again or seek support." in result.output

    def test_cli_site_record_pages_auth_token_missing(self, app_runner_mocked_csw_missing_auth_token: FlaskCliRunner):
        result = app_runner_mocked_csw_missing_auth_token.invoke(
            args=["site", "build-record", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing auth token. Run `auth sign-in` first." in result.output

    def test_cli_site_record_pages_auth_token_insufficient(
        self, app_runner_mocked_csw_insufficient_auth_token: FlaskCliRunner
    ):
        result = app_runner_mocked_csw_insufficient_auth_token.invoke(
            args=["site", "build-record", TestRecordConfigurations.TEST_RECORD_1.value["file_identifier"]]
        )
        assert result.exit_code == 64
        assert "No. Missing permissions in auth token. Seek support to assign required permissions." in result.output

    def test_cli_site_item_page_record_missing(self, app_static_site: Flask):
        result = app_static_site.test_cli_runner().invoke(args=["site", "build-record", "does-not-exist"])
        assert result.exit_code == 64
        assert "No. Record 'does-not-exist' does not exist."


class TestCommandSiteBuildPages:
    def test_cli_site_other_pages(self, app_static_site: Flask):
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
    def test_cli_site_copy_assets(self, app_static_site: Flask):
        result = app_static_site.test_cli_runner().invoke(args=["site", "copy-assets"])
        assert result.exit_code == 0
        assert "Ok. static assets copied." in result.output

        # Verify file structure
        asset_paths = list(Path(app_static_site.config["SITE_PATH"]).glob("**/*.*"))
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("static/txt/heartbeat.txt") in asset_paths
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("static/css/app.css") in asset_paths


class TestCommandSiteBuildAll:
    def test_cli_site_build_all(self, app_static_site: Flask):
        result = app_static_site.test_cli_runner().invoke(args=["site", "build"])
        assert result.exit_code == 0
        assert "Ok. 1 item pages generated." in result.output
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
                f"items/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/index.html"
            )
            in site_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"collections/{TestRecordConfigurations.TEST_RECORD_10.value['file_identifier']}/index.html"
            )
            in site_paths
        )
        assert (
            Path(app_static_site.config["SITE_PATH"]).joinpath(
                f"records/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/iso-html/"
                f"{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in site_paths
        )
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("legal/cookies/index.html") in site_paths
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("feedback/index.html") in site_paths
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("static/txt/heartbeat.txt") in site_paths
        assert Path(app_static_site.config["SITE_PATH"]).joinpath("static/css/app.css") in site_paths


class TestCommandSitePublish:
    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @mock.patch("scar_add_metadata_toolbox.commands.aws_cli")
    def test_cli_publish(self, mock_aws_cli, mock_confirm: Mock, app_static_site: Flask):  # noqa: ANN001
        mock_confirm.return_value = "y"
        mock_aws_cli.return_value = None

        result = app_static_site.test_cli_runner().invoke(args=["site", "publish"])
        assert result.exit_code == 0
        assert f"Ok. Site published to '{app_static_site.config['S3_BUCKET']}'" in result.output

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    @mock.patch("scar_add_metadata_toolbox.commands.aws_cli")
    def test_cli_publish_build(self, mock_aws_cli, mock_confirm: Mock, app_static_site: Flask):  # noqa: ANN001
        mock_confirm.return_value = "y"
        mock_aws_cli.return_value = None

        result = app_static_site.test_cli_runner().invoke(args=["site", "publish", "--build"])
        assert result.exit_code == 0
        assert "Ok. Site built." in result.output
        assert f"Ok. Site published to '{app_static_site.config['S3_BUCKET']}'" in result.output

    @mock.patch("scar_add_metadata_toolbox.commands.click.confirm")
    def test_cli_publish_aborted(self, mock_confirm: Mock, app_static_site: Flask):
        mock_confirm.return_value = False

        result = app_static_site.test_cli_runner().invoke(args=["site", "publish"])
        assert result.exit_code == 1
        assert "Aborted!" in result.output

    @mock.patch("scar_add_metadata_toolbox.commands.aws_cli")
    def test_cli_publish_force_confirm(self, mock_aws_cli, app_static_site: Flask):  # noqa: ANN001
        mock_aws_cli.return_value = None

        result = app_static_site.test_cli_runner().invoke(args=["site", "publish", "--force-publish"])
        assert result.exit_code == 0
        assert f"Ok. Site published to '{app_static_site.config['S3_BUCKET']}'" in result.output


class TestCommandCSWSetupBackingDB:
    def test_cli_setup_backing_db(self, app_runner_mocked_csw_server: FlaskCliRunner):
        catalogue = "published"
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "db", catalogue])
        assert result.exit_code == 0
        assert f"Ok. Backing database for Catalogue '{catalogue}' set up." in result.output

    def test_cli_setup_backing_db_catalogue_already_setup(self, app_runner_mocked_csw_server: FlaskCliRunner):
        catalogue = "published"
        # setup catalogue initially ...
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "db", catalogue])
        assert result.exit_code == 0
        assert f"Ok. Backing database for Catalogue '{catalogue}' set up." in result.output

        # ... then repeat
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "db", catalogue])
        assert result.exit_code == 0
        assert f"Ok. Note: Backing database for Catalogue '{catalogue}' already setup." in result.output

    def test_cli_setup_backing_db_no_catalogue_specified(self, app_runner_mocked_csw_server: FlaskCliRunner):
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "db"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'CATALOGUE'." in result.output

    def test_cli_setup_backing_db_invalid_catalogue_specified(self, app_runner_mocked_csw_server: FlaskCliRunner):
        catalogue = "invalid"
        catalogues = ["unpublished", "published"]
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "db", "invalid"])
        assert result.exit_code == 64
        assert (
            f"No. CSW catalogue '{catalogue}' does not exist. "
            f"Valid options are [{', '.join(catalogues)}]." in result.output
        )


class TestCommandCSWSetupBackingRepo:
    def test_cli_setup_backing_repo(self, app_runner_mocked_csw_server: FlaskCliRunner):
        catalogue = "unpublished"
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "repo", catalogue])
        assert result.exit_code == 0
        assert f"Ok. Tracking repo for Catalogue '{catalogue}' set up." in result.output

    def test_cli_setup_backing_repo_catalogue_already_setup(self, app_runner_mocked_csw_server: FlaskCliRunner):
        catalogue = "unpublished"
        # setup catalogue initially ...
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "repo", catalogue])
        assert result.exit_code == 0
        assert f"Ok. Tracking repo for Catalogue '{catalogue}' set up." in result.output

        # ... then repeat
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "repo", catalogue])
        assert result.exit_code == 0
        assert f"Ok. Note: Tracking repo for CSW catalogue '{catalogue}' already setup." in result.output

    def test_cli_setup_backing_repo_catalogue_not_enabled(
        self, app_runner_mocked_csw_server_tracking_not_enabled: FlaskCliRunner
    ):
        catalogue = "published"
        result = app_runner_mocked_csw_server_tracking_not_enabled.invoke(args=["csw", "setup", "repo", catalogue])
        assert result.exit_code == 64
        assert (
            f"No. Revision tracking not enabled for Catalogue '{catalogue}'. Enable this feature and try again."
            in result.output
        )

    def test_cli_setup_backing_repo_catalogue_invalid_credentials(
        self, app_runner_mocked_csw_server_tracking_invalid_credentials: FlaskCliRunner
    ):
        catalogue = "unpublished"
        result = app_runner_mocked_csw_server_tracking_invalid_credentials.invoke(
            args=["csw", "setup", "repo", catalogue]
        )
        assert result.exit_code == 64
        assert (
            "No. Access credentials for revision tracking git remote are invalid. Check credentials and try again."
            in result.output
        )

    def test_cli_setup_backing_repo_no_catalogue_specified(self, app_runner_mocked_csw_server: FlaskCliRunner):
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "repo"])
        assert result.exit_code == 2
        assert "Error: Missing argument 'CATALOGUE'." in result.output

    def test_cli_setup_backing_db_invalid_catalogue_specified(self, app_runner_mocked_csw_server: FlaskCliRunner):
        catalogue = "invalid"
        catalogues = ["unpublished", "published"]
        result = app_runner_mocked_csw_server.invoke(args=["csw", "setup", "repo", "invalid"])
        assert result.exit_code == 64
        assert (
            f"No. CSW catalogue '{catalogue}' does not exist. "
            f"Valid options are [{', '.join(catalogues)}]." in result.output
        )


class TestCommandAuthSignIn:
    @pytest.mark.xfail(reason="Auth suspended - see MAGIC/add-metadata-toolbox#380")
    def test_cli_sign_in(self, app_runner: FlaskCliRunner):
        result = app_runner.invoke(args=["auth", "sign-in"])
        assert result.exit_code == 0
        assert "Ok. Access token for '*unknown*' set in" in result.output


class TestCommandAuthSignOut:
    @pytest.mark.xfail(reason="Auth suspended - see MAGIC/add-metadata-toolbox#380")
    def test_cli_sign_out(self, app_runner: FlaskCliRunner):
        # sign-in first
        result = app_runner.invoke(args=["auth", "sign-in"])
        assert result.exit_code == 0

        result = app_runner.invoke(args=["auth", "sign-out"])
        assert result.exit_code == 0
        assert "Ok. Access token removed." in result.output

    def test_cli_sign_out_missing_file(self, app: Flask, app_runner: FlaskCliRunner):
        # ensure auth file doesn't exist to trigger exception
        auth_file_path: Path = app.config["AUTH_SESSION_FILE_PATH"]
        if auth_file_path.exists():
            auth_file_path.unlink()

        result = app_runner.invoke(args=["auth", "sign-out"])
        assert result.exit_code == 0
        assert "Ok. Access token removed." in result.output
