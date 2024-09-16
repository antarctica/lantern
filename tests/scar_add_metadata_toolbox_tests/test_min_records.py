from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from bas_metadata_library.standards.iso_19115_2 import MetadataRecordConfigV4
from flask.testing import FlaskCliRunner
from scar_add_metadata_toolbox_tests.records import TestRecordConfigurations


class TestMinimumRecords:
    """
    An additional set of tests to verify that minium records are handled correctly.

    In time these tests will be integrated into the main test suite.
    """

    @pytest.mark.parametrize(
        "record_data", [TestRecordConfigurations.TEST_RECORD_12, TestRecordConfigurations.TEST_RECORD_13]
    )
    def test_run(self, app_runner_mocked_csw: FlaskCliRunner, record_data: TestRecordConfigurations):
        with NamedTemporaryFile(mode="r+") as record_file:
            record_configuration = MetadataRecordConfigV4(**record_data.value)
            record_configuration.dump(file=Path(record_file.name))

            result = app_runner_mocked_csw.invoke(args=["records", "import", record_file.name])
            assert result.exit_code == 0
            assert f"Ok. Record '{record_configuration.config['file_identifier']}' imported." in result.output

            # verify insert
            result = app_runner_mocked_csw.invoke(args=["records", "list"])
            assert result.exit_code == 0
            assert f"{record_configuration.config['file_identifier']}" in result.output

            # verify build
            result = app_runner_mocked_csw.invoke(args=["site", "build-items"])
            assert result.exit_code == 0
