from lantern.lib.metadata_library.models.record.enums import ProgressCode
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys
from lantern.models.item.base.enums import AccessLevel, ResourceTypeLabel
from lantern.models.item.base.item import ItemBase
from lantern.models.record.revision import RecordRevision


class ItemWebsiteSearch(ItemBase):
    """
    Representation of a resource within the BAS Public Website.

    Website Search items structure a base item into the form used to represent catalogue items within the search system
    of the BAS Public Website (www.bas.ac.uk). See https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/450

    This representation consists of two parts:

    - information about each item (such as its title and abstract) for import into the Public Website
        - provided by the `_content()` property
    - a wrapper around this info for the API the Public Website harvests from to populate catalogue items
        - provided by the `dumps()` method

    In addition to a catalogue RecordRevision instance, this Item variant requires:
    - a static identifier to identify the system each item originates from
    - a base URL to generate fully qualified URLs to each item (dynamic to support testing and production environments)

    Note: This class supports a limited subset of Record properties, as determined by the needs of the Public Website.
    """

    def __init__(
        self, record: RecordRevision, admin_meta_keys: AdministrationKeys | None, source: str, base_url: str
    ) -> None:
        super().__init__(record=record, admin_keys=admin_meta_keys)
        self._source = source
        self._base_url = base_url

        if not isinstance(self._record, RecordRevision):
            msg = "record must be a RecordRevision instance"
            raise TypeError(msg) from None
        self._record: RecordRevision

    @property
    def _type_label(self) -> str:
        """Label for item hierarchy level."""
        return ResourceTypeLabel[self.resource_type.name].value

    @property
    def _description(self) -> str:
        """
        Descriptive text for the item.

        Intended to be short and concise for use in search results.

        Returned in order of preference to prefer explicitly summarised content. The first available value is returned.
        """
        return self.summary_html if self.summary_html is not None else self.description_html

    @property
    def _date(self) -> str:
        """
        A representative date for the item.

        Formatted as an ISO 8601 date(time) to the greatest precision known.

        Returned in order of preference to prefer more up-to-date values. The first available value is returned.
        """
        dates = self.record.identification.dates
        if dates.revision:
            return dates.revision.unstructure()
        if dates.publication:
            return dates.publication.unstructure()
        return dates.creation.unstructure()  # ty: ignore[possibly-missing-attribute]

    @property
    def _thumbnail_href(self) -> str | None:
        """Fully qualified URL to an optional item thumbnail."""
        if self.overview_graphic is None:
            return None
        return self.overview_graphic.href

    @property
    def _href(self) -> str:
        """
        Fully qualified URL to the item.

        Used as the outbound link to the item from the Public Website.
        """
        return f"{self._base_url}/items/{self.resource_id}/"

    @property
    def _deleted(self) -> bool:
        """
        Flag to indicate whether item should be withdrawn from the website.

        Required by the BAS Data Catalogue / Public Website sync API as supporting information. If True the item will
        be flagged for removal/deletion from the Public Website.

        Value is based on the item's maintenance information and defaults to False (not deleted).
        """
        progress = self.record.identification.maintenance.progress
        return progress == ProgressCode.OBSOLETE or progress == ProgressCode.HISTORICAL_ARCHIVE

    @property
    def _content(self) -> dict:
        """
        Compiled website search item.

        Required by the BAS Data Catalogue / Public Website sync API as core information describing the item.

        Structure is defined by the JSON Schema describing search items:
        https://metadata-resources.data.bas.ac.uk/public-website-catalogue-search/search-item-schema-v1.json
        """
        return {
            "id": self.resource_id,
            "revision": self.resource_revision,
            "type": self._type_label,
            "title": self.title_plain,
            "description": self._description,
            "date": self._date,
            "version": self.edition,
            "thumbnail_href": self._thumbnail_href,
            "keywords": [],
            "href": self._href,
        }

    @property
    def open_access(self) -> bool:
        """
        Whether item is open access.

        As determined by administrative metadata.
        """
        return self.admin_resource_access == AccessLevel.PUBLIC

    def dumps(self) -> dict:
        """
        BAS Data Catalogue / Public Website sync API entity for item.

        Values structured as needed to insert/update a record in the BAS Data Catalogue / Public Website sync API
        """
        return {
            "file_identifier": self.resource_id,
            "file_revision": self.resource_revision,
            "source": self._source,
            "content": self._content,
            "deleted": self._deleted,
        }
