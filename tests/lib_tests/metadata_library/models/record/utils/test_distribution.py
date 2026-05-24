import csv
from pathlib import Path

import pytest

from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Format, Size
from lantern.lib.metadata_library.models.record.presets.contacts import MAGIC_DISTRIBUTOR
from lantern.lib.metadata_library.models.record.utils.distribution import DistributionMaker, ZapFormat


class TestZapFormat:
    """Test DistributionFormat data class."""

    @pytest.mark.parametrize("description", [True, False])
    @pytest.mark.parametrize("extensions", [True, False])
    @pytest.mark.parametrize("types", [True, False])
    def test_init(self, description: bool, extensions: bool, types: bool) -> None:
        """Can initialise class with default values if needed."""
        exp_description = "x" if description else None
        exp_extensions = [".x", ".xx"] if extensions else []
        exp_types = ["x/x", "x/xx"] if types else []
        params = {"slug": "x", "name": "x", "url": "x"}
        if description:
            params["description"] = "x"
        if extensions:
            params["extensions"] = exp_extensions
        if types:
            params["media_types"] = exp_types

        zap = ZapFormat(**params)

        assert zap.slug == "x"
        assert zap.name == "x"
        assert zap.url == "x"
        assert zap.description == exp_description
        assert zap.extensions == exp_extensions
        assert zap.media_types == exp_types


class TestDistributionMaker:
    """Test `make_file_format`, `make_distribution` and `make_file_distribution` presets."""

    def test_init(self):
        """Can initialise class with zap formats."""
        maker = DistributionMaker()
        assert len(maker._formats) > 0

    @pytest.mark.parametrize("file_path", [Path("x.csv"), Path("x.CSV")])
    def test_format_by_ext(self, file_path: Path):
        """Can make a distribution format from a known file path extension."""
        maker = DistributionMaker()
        result = maker.format_by_ext(file_path)
        assert isinstance(result, ZapFormat)
        assert result.url == "https://www.iana.org/assignments/media-types/text/csv"

    def test_format_by_ext_invalid(self):
        """Cannot make a distribution format from an unknown file path extension."""
        maker = DistributionMaker()
        with pytest.raises(ValueError, match=r"unknown media type for extension '.x'."):
            maker.format_by_ext(Path("x.x"))

    @pytest.mark.parametrize("format_description", [None, "x"])
    @pytest.mark.parametrize("size_bytes", [None, 123])
    def test_make_dist_option(self, format_description: str | None, size_bytes: int | None):
        """Can make a distribution option with Zap format and optional format description and resource size."""
        format_ = ZapFormat(
            slug="csv",
            name="Comma Separated Values",
            url="https://www.iana.org/assignments/media-types/text/csv",
            extensions=[".csv"],
            media_types="text/csv",
        )
        if format_description:
            format_.description = format_description

        maker = DistributionMaker()
        result = maker.make_dist_option(format_=format_, href="x", distributor=MAGIC_DISTRIBUTOR, size_bytes=size_bytes)

        assert isinstance(result, Distribution)
        assert isinstance(result.format, Format)
        assert result.format.format == format_.name
        assert result.transfer_option.online_resource.href == "x"
        assert result.distributor == MAGIC_DISTRIBUTOR
        resource_description = result.transfer_option.online_resource.description
        if format_description:
            assert resource_description == format_description
        else:
            assert resource_description is None
        if size_bytes:
            assert isinstance(result.transfer_option.size, Size)
            assert result.transfer_option.size.unit == "bytes"
            assert result.transfer_option.size.magnitude == size_bytes
        else:
            assert result.transfer_option.size is None

    def test_from_file(self, tmp_path: Path):
        """Can make a distribution option for a local file available at an access URL via a distributor."""
        csv_path = tmp_path / "x.csv"
        with csv_path.open("w", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["x", "y"])

        maker = DistributionMaker()
        result = maker.from_file(file_path=csv_path, href="x", distributor=MAGIC_DISTRIBUTOR)

        assert isinstance(result, Distribution)
        assert isinstance(result.format, Format)
        assert result.format.href == "https://www.iana.org/assignments/media-types/text/csv"
        assert result.transfer_option.online_resource.href == "x"
        assert isinstance(result.transfer_option.size, Size)
        assert result.transfer_option.size.unit == "bytes"
        assert result.transfer_option.size.magnitude == 5
        assert result.distributor == MAGIC_DISTRIBUTOR
