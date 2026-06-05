import json
from datetime import UTC, date, datetime
from typing import TypedDict

from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys as AdminMetadataKeys

from lantern.lib.metadata_library.models.record.elements.common import (
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
    Identifiers,
)
from lantern.lib.metadata_library.models.record.elements.identification import Identification
from lantern.lib.metadata_library.models.record.elements.metadata import Metadata
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, HierarchyLevelCode
from lantern.models.item.base.item import ItemBase
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision


class ObjectRecord(TypedDict):
    """RecordRevision represented as an Algolia search index object."""

    objectID: str
    objectType: str
    objectRevID: str
    objectRevDate: int
    title: str
    summary: str | None
    _recordData: str


class ItemAlgolia(ItemBase):
    """
    Representation of a resource within the Algolia cloud search platform.

    Algolia representation of a resource within the BAS Data Catalogue / Metadata ecosystem.

    Maps a catalogue / ISO 19115 resource to the schemaless information model used by Algolia indexes. For consistency
    and typing support, Algolia objects used within this class are defined by the ObjectRecord typed dict, and consists
    of a reduced set of properties relevant to search applications.

    Items can be created from either a Record or an Algolia object, from which either representation is then available.

    Note: Where an Item is created from an Algolia object, the reconstructured Record instance, and Item properties
    based on this Record, will be limited to the limited subset of properties Objects contain.

    Note: Due to the above, and to ensure consistency, where an Item is created from a Record, it will be converted to
    an Algolia object and then reconstructed.

    Note: Due to the limited nature of Records returned by this class, they have limited utility and are not intended
    or supported for general use.
    """

    def __init__(
        self,
        record: RecordRevision | None = None,
        algolia_object: ObjectRecord | None = None,
        admin_keys: AdminMetadataKeys | None = None,
    ) -> None:
        """Initialise from record or algolia_object."""
        if record and not isinstance(record, RecordRevision):
            msg = "Record must be a RecordRevision."
            raise TypeError(msg) from None
        if algolia_object:
            record = self._loads_from_algolia_object(algolia_object)
        if not record:
            msg = "Catalogue record revision or an Algolia object must be provided."
            raise TypeError(msg) from None

        super().__init__(record, admin_keys)
        # limit record to properties Algolia object contains
        self._record: RecordRevision = self._loads_from_algolia_object(self.object)

    @staticmethod
    def _loads_from_algolia_object(obj_record: ObjectRecord) -> RecordRevision:
        """
        Create minimal record revision from an Algolia object dict.

        These reconstructed records are not suitable for general use, as Algolia objects only include the subset of
        properties relevant to search. They are only intended for comparing against a full record when troubleshooting.

        The ISO required abstract (about) property is not included in Algolia objects due to its length. A placeholder
        '-' value used instead.

        The ISO required metadata point of contact is copied from the catalogue required resource point of contact,
        which also requires an email address. The metadata PoC will therefore include this adddress as well.

        Inverse to `ItemAlgolia.object`.
        """
        _record_data: list = json.loads(obj_record["_recordData"])
        _poc_type, _poc_val, _poc_email, _created = tuple(_record_data)
        poc = Contact(
            organisation=ContactIdentity(name=_poc_val) if _poc_type == "o" else None,
            individual=ContactIdentity(name=_poc_val) if _poc_type == "i" else None,
            email=_poc_email,
            role={ContactRoleCode.POINT_OF_CONTACT},
        )
        creation = Date.structure(_created)

        return RecordRevision(
            file_identifier=obj_record["objectID"],
            file_revision=obj_record["objectRevID"],
            hierarchy_level=HierarchyLevelCode[obj_record["objectType"]],
            metadata=Metadata(
                contacts=Contacts([poc]),
                date_stamp=datetime.fromtimestamp(obj_record["objectRevDate"], tz=UTC).date(),
            ),
            identification=Identification(
                title=obj_record["title"],
                purpose=obj_record["summary"],
                abstract="-",  # cannot be empty
                dates=Dates(creation=creation),
                identifiers=Identifiers(
                    [
                        Identifier(
                            identifier=obj_record["objectID"],
                            href=f"https://{CATALOGUE_NAMESPACE}/items/{obj_record['objectID']}",
                            namespace=CATALOGUE_NAMESPACE,
                        )
                    ]
                ),
                contacts=Contacts([poc]),
                language="eng",
            ),
        )

    @staticmethod
    def _to_timestamp(d: date | datetime) -> int:
        """
        Encode date(time) as a Unix timestamp.

        Algolia does not support dates.
        """
        if isinstance(d, datetime):
            return int(d.timestamp())
        return int(datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp())

    @property
    def _record_data(self) -> str:
        """
        Additional data needed to reconstruct Algolia object as a valid record.

        0: poc_name_type ('o' | 'i')
        1: poc_name_val (str)
        2: poc_email (str)
        3: created (str)
        """
        _poc = self.contacts.filter(roles=ContactRoleCode.POINT_OF_CONTACT)[0]
        _poc_org_name = _poc.organisation.name if _poc.organisation else None
        _poc_ind_name = _poc.individual.name if _poc.individual else None
        poc_type = "o" if _poc_org_name else "i"
        poc_val = _poc_org_name if _poc_org_name else _poc_ind_name
        poc_email = _poc.email
        created = self.record.identification.dates.creation.unstructure()  # ty:ignore[unresolved-attribute]

        return json.dumps(obj=(poc_type, poc_val, poc_email, created), ensure_ascii=False)

    @property
    def object(self) -> ObjectRecord:
        """
        Create Algolia object dict from a record.

        Inverse to `ItemAlgolia._loads_from_algolia_object()`.
        Lossy counterpart to `ItemBase.record` due to partial properties.
        """
        obj: ObjectRecord = {
            "objectID": self.resource_id,
            "objectType": self.resource_type.name,
            "objectRevID": self.resource_revision or "",
            "objectRevDate": self._to_timestamp(self.record.metadata.date_stamp),
            "title": self.title_plain,
            "summary": self.summary_plain,
            "_recordData": self._record_data,
        }
        return obj

    @property
    def record(self) -> RecordRevision:
        """Get underlying RecordRevision."""
        return self._record
