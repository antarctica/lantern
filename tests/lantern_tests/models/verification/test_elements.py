import pytest

from lantern.lib.metadata_library.models.record.elements.common import (
    Contact,
    ContactIdentity,
    Identifier,
    OnlineResource,
)
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Format, Size, TransferOption
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, OnlineResourceFunctionCode
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.models.verification.elements import VerificationDistribution, VerificationRecord
from lantern.models.verification.enums import VerificationDistributionType, VerificationType
from lantern.models.verification.types import VerificationContext


class TestVerificationDistribution:
    """Test verification distribution."""

    def test_init(self, fx_record_model_min: Record):
        """Can create a VerificationDistribution from an underlying Distribution and Record."""
        expected = "x"
        record_distribution = Distribution(
            distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
            transfer_option=TransferOption(
                online_resource=OnlineResource(href=expected, function=OnlineResourceFunctionCode.DOWNLOAD)
            ),
        )

        distribution = VerificationDistribution(
            distribution=record_distribution, file_identifier=fx_record_model_min.file_identifier
        )

        assert isinstance(distribution, VerificationDistribution)
        assert distribution._href_raw == expected
        assert distribution._file_identifier == fx_record_model_min.file_identifier

    def test_repr(self):
        """Can get string representation of VerificationDistribution instance."""
        href = "https://nora.nerc.ac.uk/x"
        file_identifier = "691ce233-9480-4655-92d2-5ef9dee1ae4d"
        expected = f"Distribution(resource=691c...ae4d, type={VerificationDistributionType.NORA.name}, href={href})"
        record_distribution = Distribution(
            distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
            transfer_option=TransferOption(
                online_resource=OnlineResource(href=href, function=OnlineResourceFunctionCode.DOWNLOAD)
            ),
        )

        distribution = VerificationDistribution(distribution=record_distribution, file_identifier=file_identifier)
        assert repr(distribution) == expected

    @pytest.mark.parametrize(
        ("href", "format_href", "expected"),
        [
            *[
                ("x", href, VerificationDistributionType.ARCGIS_LAYER)
                for href in VerificationDistribution.arcgis_layer_media_types
            ],
            *[
                ("x", href, VerificationDistributionType.ARCGIS_SERVICE)
                for href in VerificationDistribution.arcgis_service_media_types
            ],
            *[("x", href, VerificationDistributionType.FILE) for href in VerificationDistribution.file_media_types],
            ("https://nora.nerc.ac.uk/x", None, VerificationDistributionType.NORA),
            (
                "https://nora.nerc.ac.uk/x",
                VerificationDistribution.file_media_types[0],
                VerificationDistributionType.NORA,
            ),
            (
                "https://www.bas.ac.uk/data/our-data/maps/how-to-order-a-map/",
                None,
                VerificationDistributionType.PUBLISHED_MAP,
            ),
            ("https://example.sharepoint.com/x", None, VerificationDistributionType.SHAREPOINT),
            (
                "https://example.sharepoint.com/x",
                VerificationDistribution.file_media_types[0],
                VerificationDistributionType.SHAREPOINT,
            ),
        ],
    )
    def test_type(self, href: str, format_href: str | None, expected: VerificationDistributionType):
        """Can get distribution verification type from distribution format and or href."""
        record_distribution = Distribution(
            distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
            transfer_option=TransferOption(
                online_resource=OnlineResource(href=href, function=OnlineResourceFunctionCode.DOWNLOAD)
            ),
        )
        if format_href is not None:
            record_distribution.format = Format(format="x", href=format_href)

        distribution = VerificationDistribution(distribution=record_distribution, file_identifier="x")
        assert distribution._type == expected

    def test_type_unknown(self):
        """Can't get verification type for unknown combination of distribution format and href."""
        record_distribution = Distribution(
            distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
            format=Format(format="x", href="x"),
            transfer_option=TransferOption(
                online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
            ),
        )
        distribution = VerificationDistribution(distribution=record_distribution, file_identifier="x")
        with pytest.raises(ValueError, match=r"Unsupported verification distribution type"):
            _ = distribution._type

    @pytest.mark.parametrize(
        ("href", "format_href", "expected"),
        [
            ("x", VerificationDistribution.file_media_types[0], "x"),
            (
                "https://www.arcgis.com/home/item.html?id=123",
                VerificationDistribution.arcgis_layer_media_types[0],
                "https://www.arcgis.com/sharing/rest/content/items/123?f=json",
            ),
            (
                "https://www.arcgis.com/123",
                VerificationDistribution.arcgis_service_media_types[0],
                "https://www.arcgis.com/123?f=json",
            ),
            (
                "https://example.sharepoint.com/:i:/r/personal/conwat_example_com/Documents/foo%20bar.jpg?x=y",
                None,
                "/foo bar.jpg",
            ),
        ],
    )
    def test_href(self, href: str, format_href: str | None, expected: str):
        """Can get processed href."""
        record_distribution = Distribution(
            distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
            transfer_option=TransferOption(
                online_resource=OnlineResource(href=href, function=OnlineResourceFunctionCode.DOWNLOAD)
            ),
        )
        if format_href is not None:
            record_distribution.format = Format(format="x", href=format_href)

        distribution = VerificationDistribution(distribution=record_distribution, file_identifier="x")
        assert distribution._href == expected

    @pytest.mark.parametrize("size", [None, 1.0, -1])
    def test_bytes(self, fx_record_model_min: Record, size: float | None):
        """Can get distribution size in bytes."""
        record_distribution = Distribution(
            distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
            transfer_option=TransferOption(
                online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
            ),
        )
        if size is not None:
            record_distribution.transfer_option.size = Size(unit="bytes", magnitude=size)
        if size == -1:
            record_distribution.transfer_option.size = Size(unit="x", magnitude=1.0)

        distribution = VerificationDistribution(
            distribution=record_distribution, file_identifier=fx_record_model_min.file_identifier
        )

        if size is None or size == -1:
            assert distribution._bytes is None
        else:
            assert distribution._bytes == size

    @pytest.mark.parametrize(
        ("href", "format_href", "expected"),
        [
            (
                "x",
                VerificationDistribution.file_media_types[0],
                [VerificationType.ITEM_DOWNLOADS, VerificationType.DOWNLOADS_OPEN],
            ),
            (
                "https://nora.nerc.ac.uk/x.jpg",
                VerificationDistribution.file_media_types[3],
                [VerificationType.ITEM_DOWNLOADS, VerificationType.DOWNLOADS_NORA],
            ),
            (
                "https://example.sharepoint.com/:i:/r/personal/conwat_example_com/Documents/foo%20bar.jpg?x=y",
                VerificationDistribution.file_media_types[3],
                [VerificationType.ITEM_DOWNLOADS, VerificationType.DOWNLOADS_SHAREPOINT],
            ),
            (
                "sftp://san.nerc-bas.ac.uk/data/x",
                None,
                [VerificationType.ITEM_DOWNLOADS, VerificationType.SAN_REFERENCE],
            ),
            (
                "x",
                VerificationDistribution.arcgis_layer_media_types[0],
                [VerificationType.ITEM_DOWNLOADS, VerificationType.DOWNLOADS_ARCGIS_LAYERS],
            ),
            (
                "x",
                VerificationDistribution.arcgis_service_media_types[0],
                [VerificationType.ITEM_DOWNLOADS, VerificationType.DOWNLOADS_ARCGIS_SERVICES],
            ),
        ],
    )
    def test_jobs(self, href: str, format_href: str | None, expected: list[VerificationType]):
        """Can generate verification jobs relevant to distribution."""
        record_distribution = Distribution(
            distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
            transfer_option=TransferOption(
                online_resource=OnlineResource(href=href, function=OnlineResourceFunctionCode.DOWNLOAD)
            ),
        )
        if format_href:
            record_distribution.format = Format(format="x", href=format_href)
        distribution = VerificationDistribution(distribution=record_distribution, file_identifier="x")

        results = distribution.jobs(
            context={
                "BASE_URL": "https://example.com",
                "SHAREPOINT_PROXY_ENDPOINT": "https://proxy.com",
                "SAN_PROXY_ENDPOINT": "https://proxy.com",
            }
        )

        job_types = sorted([result.type.name for result in results])
        expected_types = sorted([expected.name for expected in expected])
        assert job_types == expected_types

    def test_job_sharepoint(self):
        """Specifically check that SharePoint jobs are generated correctly."""
        proxy = "https://proxy.com"
        record_distribution = Distribution(
            format=Format(format="x", href=VerificationDistribution.file_media_types[3]),
            distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href="https://example.sharepoint.com/:i:/r/personal/conwat_example_com/Documents/foo%20bar.jpg?x=y",
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                )
            ),
        )
        distribution = VerificationDistribution(distribution=record_distribution, file_identifier="x")

        results = distribution.jobs(
            context={"BASE_URL": "https://example.com", "SHAREPOINT_PROXY_ENDPOINT": proxy, "SAN_PROXY_ENDPOINT": "x"}
        )
        job = next((result for result in results if result.type == VerificationType.DOWNLOADS_SHAREPOINT), None)

        assert job is not None
        assert job.type == VerificationType.DOWNLOADS_SHAREPOINT
        assert job.context["URL"] == proxy
        assert job.context["JSON"] == {"path": "/foo bar.jpg"}

    def test_job_san(self):
        """Specifically check that SAN reference jobs are generated correctly."""
        proxy = "https://proxy.com"
        record_distribution = Distribution(
            distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href="sftp://san.nerc-bas.ac.uk/data/x",
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                )
            ),
        )
        distribution = VerificationDistribution(distribution=record_distribution, file_identifier="x")

        results = distribution.jobs(
            context={"BASE_URL": "https://example.com", "SHAREPOINT_PROXY_ENDPOINT": "x", "SAN_PROXY_ENDPOINT": proxy}
        )
        job = next((result for result in results if result.type == VerificationType.SAN_REFERENCE), None)

        assert job is not None
        assert job.type == VerificationType.SAN_REFERENCE
        assert job.context["URL"] == proxy
        assert job.context["JSON"] == {"path": "/data/x"}


class TestVerificationRecord:
    """Test verification record."""

    def test_init(self, fx_revision_model_min: RecordRevision):
        """Can create a VerificationRecord from an underlying Record."""
        record = VerificationRecord(record=fx_revision_model_min)

        assert isinstance(record, VerificationRecord)

    @pytest.mark.parametrize(("identifiers", "distributions"), [(False, False), (True, False), (False, True)])
    def test_jobs(self, fx_revision_model_min: RecordRevision, identifiers: bool, distributions: bool):
        """Can generate verification jobs relevant to record."""
        context: VerificationContext = {
            "BASE_URL": "https://example.com",
            "SHAREPOINT_PROXY_ENDPOINT": "https://proxy.com",
            "SAN_PROXY_ENDPOINT": "https://proxy.com",
        }
        distribution = Distribution(
            distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
            format=Format(format="x", href=VerificationDistribution.file_media_types[0]),
            transfer_option=TransferOption(
                online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
            ),
        )
        alias = Identifier(identifier="x/x", href=f"https://{CATALOGUE_NAMESPACE}/x/x", namespace=ALIAS_NAMESPACE)
        doi = Identifier(identifier="x/x", href="https://doi.org/x/x", namespace="doi")
        record = VerificationRecord(record=fx_revision_model_min)
        if identifiers:
            fx_revision_model_min.identification.identifiers.extend([alias, doi])
        if distributions:
            fx_revision_model_min.distribution.append(distribution)

        results = record.jobs(context)
        record_json_job = next(
            (result for result in results if result.type == VerificationType.RECORD_PAGES_JSON), None
        )
        record_xml_job = next((result for result in results if result.type == VerificationType.RECORD_PAGES_XML), None)
        record_html_job = next(
            (result for result in results if result.type == VerificationType.RECORD_PAGES_HTML), None
        )
        item_html_job = next((result for result in results if result.type == VerificationType.ITEM_PAGES), None)
        alias_job = next((result for result in results if result.type == VerificationType.ALIAS_REDIRECTS), None)
        doi_job = next((result for result in results if result.type == VerificationType.DOI_REDIRECTS), None)
        distribution_file_job = next(
            (result for result in results if result.type == VerificationType.DOWNLOADS_OPEN), None
        )

        assert record_json_job is not None
        assert record_xml_job is not None
        assert record_html_job is not None
        assert item_html_job is not None
        if distributions:
            assert distribution_file_job is not None
        if identifiers:
            assert alias_job is not None
            assert doi_job is not None
