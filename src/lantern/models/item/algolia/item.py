import json
from datetime import UTC, date, datetime
from typing import NotRequired, TypedDict

from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys as AdminMetadataKeys

from lantern.lib.metadata_library.models.record.elements.common import (
    Constraint,
    Constraints,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
    Identifiers,
)
from lantern.lib.metadata_library.models.record.elements.identification import (
    Identification,
)
from lantern.lib.metadata_library.models.record.elements.metadata import Metadata
from lantern.lib.metadata_library.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    DatePrecisionCode,
    HierarchyLevelCode,
)
from lantern.models.item.base.item import ItemBase, ItemSummaryBase
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision


class ObjectRecord(TypedDict):
    """
    RecordRevision represented as an Algolia search index object.

    `object*` properties are intended for internal use.

    `objectRecData` is a JSON encoded list/tuple of values needed to recreate a minimally valid record (not all values).
    See `ItemAlgolia._record_data` and `ItemAlgolia._loads_from_algolia_object` for encoding/decoding.
    """

    objectID: str
    objectType: str
    objectTypeIcon: str
    objectRevID: str
    objectRevDate: int
    objectDate: NotRequired[int]
    objectRecData: str

    type: str
    name: str
    nameHtml: str
    summaryHtml: NotRequired[str]
    restricted: bool
    date: NotRequired[str]
    edition: NotRequired[str]
    imageUrl: NotRequired[str]
    childrenCountFmt: NotRequired[str]


class ItemAlgolia(ItemBase):
    """
    Representation of a resource within the Algolia cloud search platform.

    Maps a catalogue / ISO 19115 resource to the schemaless information model used by Algolia indexes. For consistency
    and typing support, Algolia objects used within this class and wider catalogue are defined by the `ObjectRecord`
    typed dict, which consists of a reduced set of properties relevant to search applications.

    Algolia items support one or more representations, depending on the input type:

    1. an Algolia search index object (via `object`)
    2. a minimal RecordRevision (via `record`)

    Items can be created from either of these representations, however where an object is used, only the minimal record
    representation is available (as creating objects requires record properties that are not included in objects).

    Note: To ensure consistency between input types, Item properties are limited to a minimal record, and as such have
    limited utility. The primary, and only supported, purpose of this class is to generate objects from records.

    To implement this, whilst allowing objects to be created from records:
    - the standard `self._record` value holds a minimal record
    - an additional `self.__record` value holds the original record if available

    `self._record` is populated by:
    - converting an Algolia object into a minimal record
    - converting an input record first into an object, then into a minimal record from this object

    See also: https://www.algolia.com/doc/guides/sending-and-managing-data/prepare-your-data#algolia-records
    """

    def __init__(
        self,
        record: RecordRevision | None = None,
        algolia_object: ObjectRecord | None = None,
        admin_keys: AdminMetadataKeys | None = None,
    ) -> None:
        """Initialise from record or algolia_object."""
        self.__record = record  # back up original record if available
        if record and not isinstance(record, RecordRevision):
            msg = "Record must be a RecordRevision."
            raise TypeError(msg) from None
        if algolia_object:
            record = self._loads_from_algolia_object(algolia_object)
        if not record:
            msg = "Catalogue record revision or an Algolia object must be provided."
            raise TypeError(msg) from None

        super().__init__(record, admin_keys)

        # limit record to properties Algolia object contains (see __record for original record if provided)
        self._record: RecordRevision = self._loads_from_algolia_object(algolia_object or self.object)

    @staticmethod
    def _loads_from_algolia_object(obj_record: ObjectRecord) -> RecordRevision:
        """
        Create a minimal record revision from an Algolia object dict.

        These reconstructed records are not suitable for general use, as Algolia objects only include the subset of
        properties relevant to search. They are only intended for complying with Store base class requirements.

        Notes on differences (not exhaustive):

        - metadata point of contact: this property is not included in Algolia objects, instead a copy of the catalogue
          required resource point of contact is used instead, including the catalogue requird email

        - title: this property is only included in Algolia objects in derived pre-formatted forms (HTML and plaintext),
          the plaintext form is used

        - abstract (about): this property is not included in Algolia objects due to its length, a placeholder '-' value
          is used instead

        - constraints and administration metadata: these properties are not included in Algolia objects except as a
          lossy, derived, binary value, which, as a special case, is encoded as a simplified access constraint

        Limited inverse to `ItemAlgolia.object`.
        """
        _record_data: list = json.loads(obj_record["objectRecData"])
        _poc_type, _poc_val, _poc_email, _created = tuple(_record_data)
        poc = Contact(
            organisation=ContactIdentity(name=_poc_val) if _poc_type == "o" else None,
            individual=ContactIdentity(name=_poc_val) if _poc_type == "i" else None,
            email=_poc_email,
            role={ContactRoleCode.POINT_OF_CONTACT},
        )
        restriction = (
            ConstraintRestrictionCode.RESTRICTED if obj_record["restricted"] else ConstraintRestrictionCode.UNRESTRICTED
        )

        return RecordRevision(
            file_identifier=obj_record["objectID"],
            file_revision=obj_record["objectRevID"],
            hierarchy_level=HierarchyLevelCode[obj_record["objectType"]],
            metadata=Metadata(
                contacts=Contacts([poc]),
                date_stamp=datetime.fromtimestamp(obj_record["objectRevDate"], tz=UTC).date(),
            ),
            identification=Identification(
                title=obj_record["name"],
                abstract="-",  # cannot be empty
                dates=Dates(creation=Date.structure(_created)),
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
                constraints=Constraints([Constraint(type=ConstraintTypeCode.ACCESS, restriction_code=restriction)]),
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
        Additional data needed to reconstruct an Algolia object as a minimal record.

        Required to reconstruct a minimally valid record:
        0: poc_name_type ('o' | 'i')
        1: poc_name_val (str)
        2: poc_email (str)
        3: created (str)
        """
        _poc = self.contacts.filter(roles=ContactRoleCode.POINT_OF_CONTACT)[0]
        _poc_org_name = _poc.organisation.name if _poc.organisation else None
        _poc_ind_name = _poc.individual.name if _poc.individual else None
        _dates = self.record.identification.dates

        poc_type = "o" if _poc_org_name else "i"
        poc_val = _poc_org_name if _poc_org_name else _poc_ind_name
        poc_email = _poc.email
        created = _dates.creation.unstructure() if _dates.creation else "?"

        return json.dumps(obj=(poc_type, poc_val, poc_email, created), ensure_ascii=False)

    @property
    def object(self) -> ObjectRecord:
        """
        Create Algolia object dict from a record.

        Inverse to `ItemAlgolia._loads_from_algolia_object()`.
        Lossy counterpart to `ItemBase.record` due to partial properties.
        """
        if not self.__record:
            msg = "Creating Algolia objects requires a record."
            raise ValueError(msg) from None

        _summary = ItemSummaryBase(record=self.__record, admin_keys=self._admin_keys)
        _summary_date = _summary.date
        _summary_children = _summary.children

        obj: ObjectRecord = {
            "objectID": self.resource_id,
            "objectType": self.resource_type.name,
            "objectTypeIcon": _summary.resource_type_icon,
            "objectRevID": self.resource_revision or "",
            "objectRevDate": self._to_timestamp(self.record.metadata.date_stamp),
            "objectRecData": self._record_data,
            "type": _summary.resource_type_label,
            "name": self.title_plain,
            "nameHtml": _summary.title_fmt,
            "restricted": _summary.restricted,
        }
        if _summary.summary_fmt:
            obj["summaryHtml"] = _summary.summary_fmt
        if _summary_date:
            obj["objectDate"] = self._to_timestamp(_summary_date.date)
            pattern = (
                "%Y"
                if _summary_date.precision == DatePrecisionCode.YEAR
                else ("%B %Y" if _summary_date.precision == DatePrecisionCode.MONTH else "%d %B %Y")
            )
            obj["date"] = _summary_date.date.strftime(pattern)
        if _summary.edition_fmt:
            obj["edition"] = _summary.edition_fmt
        if _summary.graphic_href:
            obj["imageUrl"] = _summary.graphic_href
        if _summary_children:
            obj["childrenCountFmt"] = _summary_children
        return obj

    @property
    def record(self) -> RecordRevision:
        """Get underlying RecordRevision."""
        return self._record
