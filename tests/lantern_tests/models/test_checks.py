from http import HTTPMethod, HTTPStatus
from pathlib import Path
from typing import Final

import cattrs
import pytest

from lantern.lib.metadata_library.models.record.elements.common import (
    Contact,
    ContactIdentity,
    Identifier,
    OnlineResource,
)
from lantern.lib.metadata_library.models.record.elements.distribution import (
    Distribution,
    Distributions,
    Format,
    Size,
    TransferOption,
)
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, OnlineResourceFunctionCode
from lantern.models.checks import Check, CheckState, CheckType, DistributionChecks, RecordChecks
from lantern.models.record.record import Record
from lantern.models.site import SiteContent, SiteRedirect


class TestCheck:
    """Test Check data model."""

    def test_init(self):
        """Can create a Check instance with required values."""
        expected_type = CheckType.NONE
        expected = "x"
        check = Check(type=expected_type, url=expected)
        assert check.type == expected_type
        assert check.url == expected
        assert check.http_method == HTTPMethod.HEAD
        assert check.http_status == HTTPStatus.OK
        assert check.content_length is None
        assert check.redirect_location is None
        assert check.file_identifier is None

    @pytest.mark.cov()
    def test_all(self):
        """Can create a Check instance with all possible values."""
        expected_type = CheckType.NONE
        expected_method = HTTPMethod.GET
        expected_status = HTTPStatus.NOT_FOUND
        expected_int = 1
        expected = "x"
        check = Check(
            type=expected_type,
            url=expected,
            http_method=expected_method,
            http_status=expected_status,
            content_length=expected_int,
            redirect_location=expected,
            file_identifier=expected,
        )
        assert check.type == expected_type
        assert check.url == expected
        assert check.http_method == expected_method
        assert check.http_status == expected_status
        assert check.content_length == expected_int
        assert check.redirect_location == expected
        assert check.file_identifier == expected

    def test_from_site_content(self, fx_site_content: SiteContent):
        """Can create a Check instance from a SiteContent instance."""
        base_url = "https://example.com"
        expected_url = f"{base_url}/x"
        expected_fid = "x"
        fx_site_content.object_meta = {"file_identifier": expected_fid}

        check = Check.from_site_content(content=fx_site_content, check_type=CheckType.ITEM_PAGES, base_url=base_url)
        assert check.url == expected_url
        assert check.file_identifier == expected_fid

    def test_from_site_direct(self):
        """Can create a Check instance from a SiteRedirect instance."""
        expected_http_status = HTTPStatus.MOVED_PERMANENTLY
        redirect = SiteRedirect(path=Path("x"), target="https://y")
        check = Check.from_site_content(content=redirect, check_type=CheckType.ITEM_ALIASES, base_url="x")
        assert check.http_status == expected_http_status
        assert check.file_identifier is None

    @pytest.mark.cov()
    def test_unstructure(self):
        """Can unstructure a Check instance to plain types."""
        expected = {
            "type": CheckType.ITEM_PAGES.value,
            "url": "x",
            "http_method": HTTPMethod.HEAD.value,
            "http_status": HTTPStatus.OK.value,
            "content_length": None,
            "redirect_location": None,
            "file_identifier": None,
            "result_http_status": None,
            "result_output": None,
            "state": "pending",
            "duration": 0.0,
        }
        check = Check(type=CheckType.ITEM_PAGES, url="x")
        converter = cattrs.Converter()
        result = converter.unstructure(check)
        assert result == expected


def _make_dist_opt(href: str, format_href: str | None = None, size: Size | None = None) -> Distribution:
    """Test helper for distribution checks."""
    dist_opt = Distribution(
        distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
        transfer_option=TransferOption(
            online_resource=OnlineResource(href=href, function=OnlineResourceFunctionCode.DOWNLOAD)
        ),
    )
    if format_href:
        dist_opt.format = Format(format="x", href=format_href)
    if size:
        dist_opt.transfer_option.size = size
    return dist_opt


class TestDistributionChecks:
    """Test generator for checks from record distribution options."""

    def test_init(self):
        """Can create a distribution checks instance."""
        generator = DistributionChecks(distributions=Distributions(), file_identifier="x")
        assert isinstance(generator, DistributionChecks)
        assert len(generator.checks) == 0

    _arc_layer_formats: Final[list[str]] = [
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+raster",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector",
    ]
    _arc_service_formats: Final[list[str]] = [
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+raster",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector",
    ]

    @pytest.mark.parametrize(
        ("distributions", "expected"),
        [
            (Distributions(), []),
            (
                Distributions([_make_dist_opt(href="x")]),
                [Check(type=CheckType.DOWNLOADS_OPEN, url="x", file_identifier="x", content_length=None)],
            ),
            (
                Distributions([_make_dist_opt(href="x", size=Size(magnitude=0, unit="x"))]),
                [Check(type=CheckType.DOWNLOADS_OPEN, url="x", file_identifier="x", content_length=None)],
            ),
            (
                Distributions([_make_dist_opt(href="x", size=Size(magnitude=1, unit="bytes"))]),
                [Check(type=CheckType.DOWNLOADS_OPEN, url="x", file_identifier="x", content_length=1)],
            ),
            (
                Distributions([_make_dist_opt(href="https://data.bas.ac.uk/guides/map-purchasing/")]),
                [
                    Check(
                        type=CheckType.BAS_PUBLISHED_MAP,
                        url="https://data.bas.ac.uk/guides/map-purchasing/",
                        file_identifier="x",
                    )
                ],
            ),
            (
                Distributions([_make_dist_opt(href="x", format_href=f) for f in _arc_layer_formats]),
                [
                    Check(type=CheckType.DOWNLOADS_ARCGIS_LAYER, url="x", file_identifier="x")
                    for _ in _arc_layer_formats
                ],
            ),
            (
                Distributions([_make_dist_opt(href="x", format_href=f) for f in _arc_service_formats]),
                [
                    Check(type=CheckType.DOWNLOADS_ARCGIS_SERVICE, url="x", file_identifier="x")
                    for _ in _arc_layer_formats
                ],
            ),
            (
                Distributions([_make_dist_opt(href="https://nora.nerc.ac.uk/...")]),
                [
                    Check(
                        type=CheckType.DOWNLOADS_NORA,
                        url="https://nora.nerc.ac.uk/...",
                        http_method=HTTPMethod.GET,
                        http_status=HTTPStatus.PARTIAL_CONTENT,
                        file_identifier="x",
                    )
                ],
            ),
            (
                Distributions([_make_dist_opt(href="sftp://san.nerc-bas.ac.uk/...")]),
                [
                    Check(
                        type=CheckType.DOWNLOADS_BAS_SAN,
                        url="sftp://san.nerc-bas.ac.uk/...",
                        file_identifier="x",
                        state=CheckState.SKIPPED,
                    )
                ],
            ),
            (
                Distributions([_make_dist_opt(href="https:/x.sharepoint.com/...")]),
                [
                    Check(
                        type=CheckType.DOWNLOADS_SHAREPOINT,
                        url="https:/x.sharepoint.com/...",
                        file_identifier="x",
                        state=CheckState.SKIPPED,
                    )
                ],
            ),
        ],
    )
    def test_checks(self, fx_record_model_min: Record, distributions: Distributions, expected: list[Check]):
        """Can create expected checks for distribution options."""
        generator = DistributionChecks(distributions=distributions, file_identifier="x")
        assert generator.checks == expected


class TestRecordChecks:
    """Test generator for checks from within a record."""

    def test_init(self, fx_record_model_min: Record):
        """Can create a record checks instance."""
        generator = RecordChecks(fx_record_model_min)
        assert isinstance(generator, RecordChecks)
        assert len(generator.checks) == 0

    def test_doi_checks(self, fx_record_model_min: Record):
        """Can create checks for DOIs in a record."""
        fx_record_model_min.identification.identifiers.append(Identifier(identifier="x", href="x", namespace="doi"))
        generator = RecordChecks(fx_record_model_min)
        checks = generator._doi_checks
        assert len(checks) == 1

    def test_distribution_checks(self, fx_record_model_min: Record):
        """Can create checks for distribution options in a record."""
        dist_opt = _make_dist_opt(href="x")
        fx_record_model_min.distribution.append(dist_opt)
        generator = RecordChecks(fx_record_model_min)
        checks = generator._distribution_checks
        assert len(checks) == 1
