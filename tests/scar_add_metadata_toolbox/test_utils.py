from unittest import mock

import pytest

from scar_add_metadata_toolbox.utils import aws_cli


class MockAwsCli:
    def __init__(self, exit_code: int = 0):
        self.exit_code = exit_code

    # noinspection PyUnusedLocal
    def main(self, *args):
        return self.exit_code


@mock.patch("scar_add_metadata_toolbox.utils.create_clidriver")
def test_aws_cli_success(mock_aws_cli):
    mock_aws_cli.return_value = MockAwsCli()
    aws_cli(["foo", "bar"])


@mock.patch("scar_add_metadata_toolbox.utils.create_clidriver")
def test_aws_cli_error(mock_aws_cli):
    mock_aws_cli.return_value = MockAwsCli(exit_code=1)
    with pytest.raises(RuntimeError) as e:
        aws_cli(["foo", "bar"])
    assert f"AWS CLI exited with code 1" in str(e.value)
