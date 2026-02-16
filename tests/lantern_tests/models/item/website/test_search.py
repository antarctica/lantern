from datetime import date

import pytest
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata

from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.elements.identification import GraphicOverview
from lantern.lib.metadata_library.models.record.enums import ProgressCode
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, set_admin
from lantern.models.item.base.enums import ResourceTypeLabel
from lantern.models.item.website.search import ItemWebsiteSearch
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.models.site import SiteMeta


class TestItemWebsiteSearch:
    """Test BAS Public Website search item."""

    base_url = "https://example.com"

    def test_init(self, fx_site_meta: SiteMeta, fx_revision_model_min: RecordRevision):
        """Can create an ItemWebsiteSearch."""
        item = ItemWebsiteSearch(
            record=fx_revision_model_min, admin_meta_keys=None, source=fx_site_meta.generator, base_url=self.base_url
        )
        assert isinstance(item, ItemWebsiteSearch)
        assert item._record == fx_revision_model_min

    def test_init_invalid_type(self, fx_site_meta: SiteMeta, fx_record_model_min: Record):
        """Cannot create an ItemCatalogue if not a RecordRevision."""
        with pytest.raises(TypeError, match=r"record must be a RecordRevision instance"):
            # noinspection PyTypeChecker
            _ = ItemWebsiteSearch(
                record=fx_record_model_min, admin_meta_keys=None, source=fx_site_meta.generator, base_url=self.base_url
            )

    def test_dumps_min(self, fx_site_meta: SiteMeta, fx_revision_model_min: RecordRevision):
        """Can dump a valid Catalogue / Public Website sync API entity for an item with minimal properties."""
        expected = {
            "file_identifier": fx_revision_model_min.file_identifier,
            "file_revision": fx_revision_model_min.file_revision,
            "source": "lantern",
            "content": {
                "id": fx_revision_model_min.file_identifier,
                "revision": fx_revision_model_min.file_revision,
                "type": ResourceTypeLabel.DATASET.value,
                "title": "x",
                "description": "<p>x</p>",
                "date": "2014-06-30",
                "version": None,
                "thumbnail_href": None,
                "keywords": [],
                "href": f"{self.base_url}/items/{fx_revision_model_min.file_identifier}/",
            },
            "deleted": False,
        }
        item = ItemWebsiteSearch(
            record=fx_revision_model_min, admin_meta_keys=None, source=fx_site_meta.generator, base_url=self.base_url
        )

        assert item.dumps() == expected

    def test_dumps_max(self, fx_site_meta: SiteMeta, fx_revision_model_min: RecordRevision):
        """Can dump a valid Catalogue / Public Website sync API entity for an item with all supported properties."""
        edition = "x"
        thumbnail_href = "x.jpg"

        expected = {
            "file_identifier": fx_revision_model_min.file_identifier,
            "file_revision": fx_revision_model_min.file_revision,
            "source": "lantern",
            "content": {
                "id": fx_revision_model_min.file_identifier,
                "revision": fx_revision_model_min.file_revision,
                "type": ResourceTypeLabel.DATASET.value,
                "title": "x",
                "description": "<p>x</p>",
                "date": "2014-06-30",
                "version": edition,
                "thumbnail_href": thumbnail_href,
                "keywords": [],
                "href": f"{self.base_url}/items/{fx_revision_model_min.file_identifier}/",
            },
            "deleted": False,
        }
        fx_revision_model_min.identification.edition = edition
        fx_revision_model_min.identification.graphic_overviews.append(
            GraphicOverview(identifier="overview", href=thumbnail_href, mime_type="image/jpeg")
        )

        item = ItemWebsiteSearch(
            record=fx_revision_model_min, admin_meta_keys=None, source=fx_site_meta.generator, base_url=self.base_url
        )

        assert item.dumps() == expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("has_purpose", "expected"),
        [(False, "<p>x</p>"), (True, "<p>y</p>")],
    )
    def test_description(
        self, fx_site_meta: SiteMeta, fx_revision_model_min: RecordRevision, has_purpose: bool, expected: str
    ):
        """Can select preferred date from available options."""
        if has_purpose:
            fx_revision_model_min.identification.purpose = "y"

        item = ItemWebsiteSearch(
            record=fx_revision_model_min, admin_meta_keys=None, source=fx_site_meta.generator, base_url=self.base_url
        )

        assert item._description == expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("has_publication", "has_revision", "expected"),
        [
            (False, False, "2014-06-30"),
            (True, False, "2015-01-01"),
            (False, True, "2016-01-01"),
            (True, True, "2016-01-01"),
        ],
    )
    def test_dates(
        self,
        fx_site_meta: SiteMeta,
        fx_revision_model_min: RecordRevision,
        has_publication: bool,
        has_revision: bool,
        expected: str,
    ):
        """Can select preferred date from available options."""
        publication = Date(date=date(2015, 1, 1))
        revision = Date(date=date(2016, 1, 1))
        if has_publication:
            fx_revision_model_min.identification.dates.publication = publication
        if has_revision:
            fx_revision_model_min.identification.dates.revision = revision

        item = ItemWebsiteSearch(
            record=fx_revision_model_min, admin_meta_keys=None, source=fx_site_meta.generator, base_url=self.base_url
        )

        assert item._date == expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("progress", "expected"),
        [(None, False), (ProgressCode.OBSOLETE, True), (ProgressCode.HISTORICAL_ARCHIVE, True)],
    )
    def test_deleted(
        self, fx_site_meta: SiteMeta, fx_revision_model_min: RecordRevision, progress: ProgressCode, expected: bool
    ):
        """Can determine if item should be marked as removed from maintenance info."""
        fx_revision_model_min.identification.maintenance.progress = progress
        item = ItemWebsiteSearch(
            record=fx_revision_model_min, admin_meta_keys=None, source=fx_site_meta.generator, base_url=self.base_url
        )
        assert item._deleted == expected

    @pytest.mark.parametrize("open_access", [False, True])
    def test_open_access(
        self,
        fx_site_meta: SiteMeta,
        fx_revision_model_min: RecordRevision,
        fx_admin_meta_keys: AdministrationKeys,
        open_access: bool,
    ):
        """Can determine if resource is open access."""
        if open_access:
            admin_meta = AdministrationMetadata(
                id=fx_revision_model_min.file_identifier,
                metadata_permissions=[OPEN_ACCESS],
                resource_permissions=[OPEN_ACCESS],
            )
            set_admin(keys=fx_admin_meta_keys, record=fx_revision_model_min, admin_meta=admin_meta)

        item = ItemWebsiteSearch(
            record=fx_revision_model_min,
            admin_meta_keys=fx_admin_meta_keys,
            source=fx_site_meta.generator,
            base_url=self.base_url,
        )
        assert item.open_access == open_access
