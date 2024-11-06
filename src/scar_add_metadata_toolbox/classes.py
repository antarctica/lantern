from __future__ import annotations

import contextlib
import json
import locale
from collections.abc import Generator
from copy import copy, deepcopy
from datetime import date, datetime
from hashlib import sha1
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from bas_metadata_library.standards.iso_19115_2 import MetadataRecord, MetadataRecordConfigV4
from flask import current_app
from markdown import markdown

from scar_add_metadata_toolbox.csw import (
    CSWClient,
    CSWGetRecordMode,
    RecordInsertConflictError,
    RecordNotFoundError,
)


class RecordRetractBeforeDeleteError(Exception):
    """
    Represents where a record is deleted before it has been first been retracted.

    This is illogical as published records must have an unpublished counterpart. If this unpublished counterpart is
    removed (deleted) this rule would be violated. Instead, the published record must be removed (retracted) first.
    """

    pass


class ItemInvalidSourceRecordError(Exception):
    """Represents a situation where an Item class is instantiated with a Record that doesn't represent an item."""

    pass


class CollectionInvalidSourceRecordError(Exception):
    """Represents where a Collection class is instantiated with a Record that doesn't represent a collection."""

    pass


class RecordSummary:
    """
    Records represent and describe a given resource, often in great detail using a conceptual model.

    These full representations (represented by the Record class) are inherently large and complex and so unwieldy in
    large numbers.

    Record Summaries represent and describe a resource in far less detail. As RecordSummaries are simpler, they
    can be processed more easily than Records, especially in large numbers, such as listings and indexes etc.

    Record Summaries are effectively subsets of Records, however to leverage inheritance, Records inherit from, and
    extend, RecordSummaries.

    Record Summaries are created from a configuration dictionary. Properties are defined to access specific parts of
    this configuration. Record Summaries are intended to be read-only objects.

    Sets of Record Summaries are typically interacted with via a Repository (represented by the Repository class).

    To ensure RecordSummaries remain lightweight, properties should be strictly limited, with anything non-essential
    added to the Record class instead.
    """

    def __init__(self, config: dict | None = None) -> None:
        """
        Initialise class.

        :type config dict
        :param config: Record configuration
        """
        self.config = {}
        if config is not None:
            self.config = config

    def __repr__(self) -> str:
        return f"<RecordSummary / {self.identifier} / {self.title}>"

    @property
    def identifier(self) -> str:
        return self.config["file_identifier"]

    @property
    def hierarchy_level(self) -> str:
        return self.config["hierarchy_level"]

    @property
    def title(self) -> str:
        return self.config["identification"]["title"]["value"]


class Record(RecordSummary):
    """
    Records represent and describe a given resource, often in great detail using a conceptual model.

    Currently assumed to be ISO 19115 (Geographic Information).

    As full representations are inherently large and complex, they are unwieldy in large numbers, such as indexes. In
    these circumstances, record summaries (represented by the RecordSummaries class), with an intentionally restricted
    set of properties can be processed and used more easily when in greater numbers compared to Records.

    Records are effectively supersets of RecordSummaries and so inherit from and extend them. Collections of records
    are typically held in a repository (represented by the Repository class).

    Records are created from a configuration dictionary. Properties are defined to access specific parts of this
    configuration, with additional processing performed as needed. Records are intended to be read-only.

    Properties currently track the ISO 19115 abstract model quite closely. As this catalogue evolves to cover other
    resources this may change.
    """

    def __repr__(self) -> str:
        return f"<Record / {self.identifier}>"

    @staticmethod
    def _process_contacts(contacts: list[dict]) -> dict[str, list[dict]]:
        """
        Process contacts into a dict, keyed by role.

        ISO allows multiple contacts to have the same role (e.g. multiple authors). The BAS Metadata Library config
        also allows contacts to have multiple roles (e.g. publisher and distributor). This method will restructure, and
        where needed duplicate, contacts to group them by their roles.

        E.g. This (simplified) input:

        ```
        [
            {
                "name": "MAGIC",
                "roles": [
                    "point of contact",
                    "distributor"
                ]
            },
            {
                "name": "Constance Watson",
                "roles": [
                    "author"
                ]
            },
            {
                "name": "John Cinnamon",
                "roles": [
                    "author"
                ]
            }
        ]
        ```

        Will become:

        ```
        {
            "author": [
                {
                    "name": "Constance Watson"
                },
                {
                    "name": "John Cinnamon"
                }
            ],
            "point of contact": [
                {
                    "name": "MAGIC"
                }
            ],
            "distributor": [
                {
                    "name": "MAGIC"
                }
            ]
        }
        ```
        """
        _contacts_by_role = {}
        for contact in contacts:
            for role in contact["role"]:
                if role not in _contacts_by_role:
                    _contacts_by_role[role] = []
                _contacts_by_role[role].append(contact)
        return _contacts_by_role

    @staticmethod
    def _filter_keywords(keywords: list[dict], keyword_type: str) -> list[dict]:
        """
        Filter descriptive keywords by keyword type.

        ISO supports multiple types of descriptive keywords (e.g. theme, place). As each type is typically used
        differently, this method filters keywords for a specified type (e.g. only theme keywords).

        Keyword types are defined by the relevant BAS Metadata Library record configuration schema and ISO code list.
        """
        _keywords = []
        for keyword_set in keywords:
            if keyword_set["type"] == keyword_type:
                _keywords.append(keyword_set)

        return _keywords

    @staticmethod
    def _process_temporal_extent(temporal_extent: dict | None) -> dict[str, datetime | None]:
        """
        Assemble a temporal extent.

        Temporal extents consist of an optional start and end date instant. This method checks whether either the start
        or end period has been specified, and if not, use a default 'undefined' value.

        :return: temporal extent with default start/end values if not specified
        :rtype dict
        """
        _temporal_extent = {"start": None, "end": None}

        if temporal_extent is None:
            return _temporal_extent

        with contextlib.suppress(KeyError):
            _temporal_extent["start"] = temporal_extent["period"]["start"]["date"]
        with contextlib.suppress(KeyError):
            _temporal_extent["end"] = temporal_extent["period"]["end"]["date"]

        return _temporal_extent

    @property
    def abstract(self) -> str:
        return self.config["identification"]["abstract"]

    @property
    def aggregations(self) -> list[dict]:
        try:
            return self.config["identification"]["aggregations"]
        except KeyError:
            return []

    @property
    def character_set(self) -> str:
        return self.config["identification"]["character_set"]

    @property
    def constraints(self) -> list[dict[str, str]]:
        return self.config["identification"].get("constraints", [])

    @property
    def contacts(self) -> dict[str, list[dict]]:
        return self._process_contacts(contacts=self.config["identification"]["contacts"])

    @property
    def dates(self) -> dict[str, dict[str, str | date | datetime]]:
        _dates = {}
        for date_type, date_value in self.config["identification"]["dates"].items():
            if "date_precision" not in date_value:
                date_value["date_precision"] = None
            _dates[date_type] = date_value
        return _dates

    @property
    def distributions(self) -> list[dict]:
        return self.config.get("distribution", [])

    @property
    def edition(self) -> str | None:
        return self.config["identification"].get("edition", None)

    @property
    def extents(self) -> list[dict]:
        extents = []

        try:
            for _extent in self.config["identification"]["extents"]:
                extent = deepcopy(_extent)
                if "temporal" not in extent:
                    extent["temporal"] = None
                extent["temporal"] = self._process_temporal_extent(temporal_extent=extent["temporal"])
                extents.append(extent)
        except KeyError:
            return extents

        return extents

    @property
    def graphic_overviews(self) -> list[dict]:
        return self.config["identification"].get("graphic_overviews", [])

    @property
    def identifiers(self) -> list[dict]:
        return self.config["identification"].get("identifiers", [])

    @property
    def language(self) -> str:
        return self.config["identification"]["language"]

    @property
    def lineage(self) -> str | None:
        try:
            return self.config["identification"]["lineage"]["statement"]
        except KeyError:
            return None

    @property
    def location_keywords(self) -> list[dict]:
        keywords = self.config["identification"].get("keywords", [])
        return self._filter_keywords(keywords=keywords, keyword_type="place")

    @property
    def maintenance_frequency(self) -> str | None:
        try:
            return self.config["identification"]["maintenance"]["maintenance_frequency"]
        except KeyError:
            return None

    @property
    def metadata_character_set(self) -> str:
        return self.config["metadata"]["character_set"]

    @property
    def metadata_language(self) -> str:
        return self.config["metadata"]["language"]

    @property
    def metadata_maintenance_frequency(self) -> str | None:
        try:
            return self.config["metadata"]["maintenance"]["maintenance_frequency"]
        except KeyError:
            return None

    @property
    def metadata_maintenance_progress(self) -> str | None:
        try:
            return self.config["metadata"]["maintenance"]["progress"]
        except KeyError:
            return None

    @property
    def metadata_standard_name(self) -> str | None:
        try:
            return self.config["metadata"]["metadata_standard"]["name"]
        except KeyError:
            return None

    @property
    def metadata_standard_version(self) -> str | None:
        try:
            return self.config["metadata"]["metadata_standard"]["version"]
        except KeyError:
            return None

    @property
    def metadata_updated(self) -> date:
        return self.config["metadata"]["date_stamp"]

    @property
    def other_citation_details(self) -> str | None:
        try:
            return self.config["identification"]["other_citation_details"]
        except KeyError:
            return None

    @property
    def series_name(self) -> str | None:
        try:
            return self.config["identification"]["series"].get("name", None)
        except KeyError:
            return None

    @property
    def series_edition(self) -> str | None:
        try:
            return self.config["identification"]["series"].get("edition", None)
        except KeyError:
            return None

    @property
    def spatial_reference_system(self) -> dict | None:
        try:
            return self.config["reference_system_info"]
        except KeyError:  # pragma: no cover (will be addressed in #116)
            return None

    @property
    def spatial_representation_type(self) -> str | None:
        try:
            return self.config["identification"]["spatial_representation_type"]
        except KeyError:  # pragma: no cover (will be addressed in #116)
            return None

    @property
    def spatial_resolution(self) -> int | None:
        return self.config["identification"].get("spatial_resolution", None)

    @property
    def supplemental_information(self) -> str | None:
        return self.config["identification"].get("supplemental_information", None)

    @property
    def theme_keywords(self) -> list[dict]:
        keywords = self.config["identification"].get("keywords", None)

        if keywords is None:
            return []

        return self._filter_keywords(keywords=keywords, keyword_type="theme")

    @property
    def topics(self) -> list[str]:
        return self.config["identification"].get("topics", [])

    def load(self, record_path: Path) -> None:
        """
        Load a Record from a file encoded using JSON.

        Specifically load a BAS Metadata Library record configuration for ISO 19115-2 that has been JSON encoded.
        """
        configuration = MetadataRecordConfigV4()
        configuration.load(file=record_path)
        self.config: dict[str, Any] = configuration.config

    def dump(self, record_path: Path, overwrite: bool = False) -> None:
        """
        Save a Record to a file encoded using JSON.

        Specifically saves a BAS Metadata Library record configuration for ISO 19115-2 using JSON encoding.
        """
        configuration = MetadataRecordConfigV4(**self.config)
        configuration.validate()

        try:
            if record_path.exists():
                raise FileExistsError from None  # noqa: TRY301
            configuration.dump(file=record_path)
        except FileExistsError:
            if not overwrite:
                raise FileExistsError() from None
            configuration.dump(file=record_path)

    def dumps(self, dump_format: str) -> str:
        """
        Encode a Record in a given format.

        Specifically encodes a BAS Metadata Library record configuration for ISO 19115-2 using a specified encoding.

        Currently, only the 'xml' format is supported for rendering a record configuration as ISO XML. Others may be
        added in the future as needs arise.
        """
        if dump_format != "xml":
            msg = f"Unsupported dump format: {dump_format}"
            raise ValueError(msg)

        configuration = MetadataRecordConfigV4(**self.config)
        record = MetadataRecord(configuration=configuration)
        return record.generate_xml_document().decode()


class MirrorRecordSummary(Record):
    """
    Mirrored record summaries extend record summaries with a 'published' status.

    Representing whether a record is *published* or *unpublished* based on the repositories a record appears within in
    a mirrored repository.
    """

    def __init__(self, config: dict, published: bool) -> None:
        super().__init__(config=config)
        self.published = published

    def __repr__(self) -> str:
        return f"<MirrorRecordSummary / {self.identifier} / {'Published' if self.published else 'Unpublished'}>"


class MirrorRecord(MirrorRecordSummary, Record):
    """Mirrored records extend mirrored record summaries and records."""

    def __init__(self, config: dict, published: bool) -> None:
        super().__init__(config=config, published=published)

    def __repr__(self) -> str:
        return f"<MirrorRecord / {self.identifier} / {'Published' if self.published else 'Unpublished'}>"


class Repository:
    """
    Represents a data store with an interface for creating, retrieving, updating and deleting Records.

    Externally, repositories present an abstracted interface for interacting with records using the Record and
    RecordSummary classes. Internally, repositories are backed by an OGC Catalogue Services for the Web (CSW) catalogue.

    For example:

    * when creating a record - a Record class instance is converted into an ISO 19115-2 record encoded using XML and
      inserted into a CSW server using the CSW transactional profile
    * when retrieving a record - a CSW GetRecord request is made and the XML encoded ISO 19115-2 record is converted
      back into a Record class
    """

    def __init__(self, client_config: dict) -> None:
        self.csw_client = CSWClient(config=client_config)

    def retrieve_record(self, record_identifier: str) -> Record:
        """
        Retrieve a record from the repository.

        Record identifiers are the same as ISO 19115-2 file identifiers.

        :type record_identifier str
        :param record_identifier: identifier of the record to retrieve
        :rtype Record
        :return: requested record
        """
        record_xml = self.csw_client.get_record(identifier=record_identifier, mode=CSWGetRecordMode.FULL)
        record_config = MetadataRecord(record=record_xml).make_config()
        record_config.validate()
        return Record(config=record_config.config)

    def retrieve_records(self) -> Generator[Record, None, None]:
        """
        Retrieve all records in the repository.

        Note: Records are returned using a generator for use in iterators such as for loops. If an actual List of
        records is needed, for calculating a length for example, the return value can be wrapped, e.g.

        ```
        records_count = len(list(repository.retrieve_records()))
        ```
        """
        for record_xml in self.csw_client.get_records(mode=CSWGetRecordMode.FULL):
            record_config = MetadataRecord(record=record_xml).make_config()
            record_config.validate()
            yield Record(config=record_config.config)

    def list_record_identifiers(self) -> list[str]:
        """
        Retrieve identifiers for all records in the repository.

        Record identifiers are the same as ISO 19115-2 file identifiers.

        :rtype list
        :return: all record identifiers
        """
        return list(self.list_records().keys())

    def list_records(self) -> dict[str, RecordSummary]:
        """
        Retrieve summaries for all records in the repository.

        Records are returned as a dictionary rather than a list to allow specific records to be easily selected.

        :rtype dict
        :return: all summarised records, keyed by record identifier
        """
        _record_summaries = {}

        for record_xml in self.csw_client.get_records(mode=CSWGetRecordMode.FULL):
            record_config = MetadataRecord(record=record_xml).make_config()
            record = RecordSummary(config=record_config.config)
            _record_summaries[record.identifier] = record
        return _record_summaries

    def insert_record(self, record: Record, update: bool = False) -> None:
        # noinspection GrazieInspection
        """
        Create a new record, or updates an existing record, in the repository.

        Records are assumed to be new records by default and will raise an exception if this causes a conflict. Records
        can be updated instead by setting the updated parameter to True.

        :type record Record
        :param record: record to be created or updated
        :type update bool
        :param update: whether an existing record can be overridden
        """
        try:
            record_xml = record.dumps(dump_format="xml")
            self.csw_client.insert_record(record=record_xml)
        except RecordInsertConflictError:
            if not update:
                raise RecordInsertConflictError() from None

            # noinspection PyUnboundLocalVariable
            self.csw_client.update_record(record=record_xml)

    def delete_record(self, record_identifier: str) -> None:
        """
        Delete a record from the repository.

        Record identifiers are the same as ISO 19115-2 file identifiers.

        :type record_identifier str
        :param record_identifier: identifier of the record to delete
        """
        self.csw_client.delete_record(identifier=record_identifier)


class MirrorRepository:
    """
    Represents a composite data store with an interface for managing Records.

    Externally, repositories present an abstracted interface for interacting with records using the MirrorRecord and
    MirrorRecordSummary classes. Internally, mirror repositories are backed by two Repository classes to represent
    'published' and 'unpublished' records.

    If a record exists in both repositories, it is considered published (all records must appear in the unpublished
    repository). If a published record is retracted, it is deleted from the published catalogue, and can then optionally
    also be deleted from the unpublished catalogue (fully deleting the record), or created in the published repository
    again to (re)publish it.
    """

    def __init__(self, unpublished_repository_config: dict, published_repository_config: dict) -> None:
        self.published_repository = Repository(**published_repository_config)
        self.unpublished_repository = Repository(**unpublished_repository_config)

    def retrieve_record(self, record_identifier: str) -> MirrorRecord:
        """
        Retrieve a record from the repository.

        Record identifiers are the same as ISO 19115-2 file identifiers.

        If the record appears in both repositories it will be considered published.

        :type record_identifier str
        :param record_identifier: identifier of the record to retrieve
        :rtype MirrorRecord
        :return: requested record
        """
        try:
            record = self.published_repository.retrieve_record(record_identifier=record_identifier)
            return MirrorRecord(config=record.config, published=True)
        except RecordNotFoundError:
            record = self.unpublished_repository.retrieve_record(record_identifier=record_identifier)
            return MirrorRecord(config=record.config, published=False)

    # retrieve_records() method removed as part of #133/#134

    def retrieve_published_records(self) -> list[MirrorRecord]:
        """
        Retrieve all published records in the repository.

        Note: Records are returned using a generator for use in iterators such as for loops. If an actual List of
        records is needed, for calculating a length for example, the return value can be wrapped, e.g.

        ```
        records_count = len(list(repository.retrieve_published_records()))
        ```

        :rtype list
        :return: all published records
        """
        for published_record in self.published_repository.retrieve_records():
            yield MirrorRecord(config=published_record.config, published=True)

    def list_record_identifiers(self) -> list[str]:
        """
        Retrieve identifiers for all records in the repository.

        Record identifiers are the same as ISO 19115-2 file identifiers.

        Note: As all records have to appear in the unpublished repository we can just return its identifiers using the
        relevant method. The published catalogue's identifiers would only ever be a subset of those.

        :rtype list
        :return: all record identifiers
        """
        return self.unpublished_repository.list_record_identifiers()

    def list_unpublished_record_identifiers(self) -> list[str]:
        """
        Retrieve identifiers for all records in the repository.

        Record identifiers are the same as ISO 19115-2 file identifiers.

        Note: Use the `list_distinct_unpublished_record_identifiers()` method to only return unpublished, rather than
        all, records.

        :rtype list
        :return: all record identifiers
        """
        return self.unpublished_repository.list_record_identifiers()

    def list_published_record_identifiers(self) -> list[str]:
        """
        Retrieve identifiers for all published records in the repository.

        Record identifiers are the same as ISO 19115-2 file identifiers.

        :rtype list
        :return: published record identifiers
        """
        return self.published_repository.list_record_identifiers()

    def list_distinct_unpublished_record_identifiers(self) -> list[str]:
        """
        Retrieve identifiers for all unpublished records in the repository.

        This method *only* returns identifiers for records that have not been published.

        I.e. this method returns identifiers for the subset of records that do not appear in the published repository.

        Record identifiers are the same as ISO 19115-2 file identifiers.

        :rtype list
        :return: unpublished record identifiers
        """
        unpublished_record_identifiers = self.list_unpublished_record_identifiers()
        published_record_identifiers = self.list_published_record_identifiers()
        return list(set(unpublished_record_identifiers) - set(published_record_identifiers))

    def list_records(self) -> dict[str, MirrorRecordSummary]:
        """
        Retrieve summaries for all records in the repository.

        Records are returned as a dictionary rather than a list to allow specific records to be easily selected.
        """
        _records = {}

        unpublished_records = self.unpublished_repository.list_records()
        published_record_identifiers = self.published_repository.list_record_identifiers()

        for record_identifier, unpublished_record in unpublished_records.items():
            _record_published = False
            if record_identifier in published_record_identifiers:
                _record_published = True
            _records[record_identifier] = MirrorRecordSummary(
                config=unpublished_record.config, published=_record_published
            )
        return _records

    def insert_record(self, record: Record, update: bool = False) -> None:
        """
        Create a new, unpublished, record, or updates an existing record in the unpublished repository.

        Records are assumed to be new by default and will raise an exception if this causes a conflict. Records can be
        updated instead by setting the updated parameter to True.

        To create or update a record in the published repository (publishing or republishing it) use the
        `publish_record()` method.

        :type record Record
        :param record: record to be created or updated
        :type update bool
        :param update: whether an existing record can be overridden
        """
        self.unpublished_repository.insert_record(record=record, update=update)

    def delete_record(self, record_identifier: str) -> None:
        """
        Delete a record from the unpublished repository.

        Record identifiers are the same as ISO 19115-2 file identifiers.

        Note: As all records must appear in the unpublished repository, if the record exists in the published repository
        an error will be raised and record won't be deleted from the unpublished repository. Use the `retract()` method
        to delete the record from the published repository first.

        :type record_identifier str
        :param record_identifier: identifier of the record to delete
        """
        if record_identifier in self.published_repository.list_record_identifiers():
            raise RecordRetractBeforeDeleteError()

        self.unpublished_repository.delete_record(record_identifier=record_identifier)

    def publish_record(self, record_identifier: str, republish: bool = False) -> None:
        """
        Create a new, published, record, or updates an existing record in the published repository.

        Records are assumed to be new by default and will raise an exception if this causes a conflict. Records can be
        updated (republished) instead by setting the updated parameter to True.

        :type record_identifier str
        :param record_identifier: identifier of the record to publish or republish
        :type republish bool
        :param republish: whether an existing record can be overridden
        """
        try:
            record = self.unpublished_repository.retrieve_record(record_identifier=record_identifier)
        except RecordNotFoundError:
            raise RecordNotFoundError() from None

        try:
            self.published_repository.insert_record(record=record, update=False)
        except RecordInsertConflictError:
            if not republish:
                raise RecordInsertConflictError() from None
            self.published_repository.insert_record(record=record, update=True)

    def retract_record(self, record_identifier: str) -> None:
        """
        Delete (retracts) a record from the published repository.

        Record identifiers are the same as ISO 19115-2 file identifiers.

        :type record_identifier str
        :param record_identifier: identifier of the record to delete/retract
        """
        self.published_repository.delete_record(record_identifier=record_identifier)

    def related_record_summaries(self, record: Record) -> dict[str, MirrorRecordSummary]:
        """
        Get summaries of related resources for a record.

        Related resources are taken from aggregations, filtered to the catalogue namespace.
        """
        summaries = self.list_records()
        related_summaries: dict[str, MirrorRecordSummary] = {}

        for aggregation in record.aggregations:
            if (
                aggregation["identifier"]["identifier"] in summaries
                and aggregation["identifier"]["namespace"] == "data.bas.ac.uk"
            ):
                summary = summaries[aggregation["identifier"]["identifier"]]
                related_summaries[summary.identifier] = summary

        return related_summaries


class Item:
    """
    Items are abstractions of Records.

    They are specific and tailored to the needs of this project, using any hierarchy level except 'collection', which
    is represented by the Collection class for historical reasons.

    Items are read only and use a Record internally for exposing information through properties. They are designed to
    provide final output to humans, rather than for onward use or interpretation by other services - use Records for
    that.

    Various formatting, processing and filtering methods are used to transform some information to be more easily
    understood or to make more contextual sense.
    """

    def __init__(self, record: Record, related_summaries: list[MirrorRecordSummary]) -> None:
        self.record = record
        self._related_records = related_summaries

        if self.record.hierarchy_level == "collection":
            raise ItemInvalidSourceRecordError()

    def __repr__(self) -> str:
        return f"<Item / {self.identifier}>"

    @staticmethod
    def _format_date(date_datetime: date | datetime, date_precision: str | None = None) -> str:
        """
        Format a date for display.

        Date(time)s are formatted using ISO 8601, upto an optional data precision.

        For example:
        * `{'date': date(2020,4,20)}` will be formatted as "2020-04-20"
        * `{'date': date(2020,1,1), 'date_precision':'year'}` will be formatted as "2020"
        * `{'date': datetime(2020,4,20,14)}` will be formatted as "2020-04-20T14:00:00"
        * `{'date': datetime(2020,4,20,14,26,45)}` will be formatted as "2020-04-20T14:26:45"

        :type date_datetime date or datetime
        :param date_datetime: date or datetime to be formatted
        :type date_precision str
        :param date_precision: maximum precision of
        :rtype str
        :return: ISO 8601 date or datetime
        """
        if date_precision is None:
            return date_datetime.isoformat()
        if date_precision == "year":  # noqa: RET503 (will be refactored away)
            return str(date_datetime.year)

    @staticmethod
    def _format_language(language: str) -> str:
        """
        Format an ISO 19115 language code list value.

        Note: It is currently assumed that where English is used this refers to a United Kingdom (GB) localisation.

        :type language str
        :param language: ISO 19115 language code list value
        :rtype str
        :return: formatted language name
        """
        if language == "eng":  # noqa: RET503 (will be refactored away)
            return "English (United Kingdom)"

    @staticmethod
    def _format_maintenance_frequency(maintenance_frequency: str) -> str:
        """
        Format an ISO 19115 maintenance frequency code list value.

        :type maintenance_frequency str
        :param maintenance_frequency: ISO 19115 maintenance frequency code list value
        :rtype str
        :return: formatted maintenance frequency value
        """
        if maintenance_frequency == "biannually":
            return "Biannually (every 6 months)"
        if maintenance_frequency == "asNeeded":  # noqa: RET503 (will be refactored away)
            return "As Needed"

    @staticmethod
    def _format_organisation_name(organisation_name: str) -> str:
        """
        Format an organisation name.

        Typically, this is used to remove redundant information from names. For example, as items will be shown in a
        BAS branded webpage, it isn't necessary to include 'British Antarctic Survey' in organisation names.

        This may also be used to include helpful, but informal, elements in names, such as abbreviations.

        :type organisation_name str
        :param organisation_name: organisation name
        :rtype str
        :return: formatted organisation name
        """
        if organisation_name == "Mapping and Geographic Information Centre, British Antarctic Survey":
            return "Mapping and Geographic Information Centre (MAGIC)"
        return organisation_name

    @staticmethod
    def _format_keyword_thesaurus_title(thesaurus_title: str) -> str:
        """
        Format the name of a keyword set.

        In ISO 19115 keywords that are published by an authority can include a thesaurus that describes what the keyword
        set is, the authority behind them, etc.

        As keywords are shown in a relatively narrow part of the page and titles are often quite verbose, this method
        shortens them into something more suitable, whilst still being easily identifiable.

        :type thesaurus_title str
        :param thesaurus_title: title of the keyword set as defined in the keyword thesaurus
        :rtype str
        :return: formatted thesaurus title
        """
        if thesaurus_title == "General Multilingual Environmental Thesaurus - INSPIRE themes":
            return "INSPIRE themes"
        if thesaurus_title == "Global Change Master Directory (GCMD) Science Keywords":
            return "GCMD Science Keywords"
        if thesaurus_title == "Global Change Master Directory (GCMD) Location Keywords":  # noqa: RET503
            return "GCMD Location Keywords"

    @staticmethod
    def _format_spatial_reference_system(spatial_reference_system_code: dict[str, str]) -> str:
        """
        Format a spatial reference system identifier.

        Formal identifiers for spatial reference systems (or coordinate/spatial reference systems) are not readily
        accessible to those not very familiar with them. This method expands identifiers to include information people
        will understand, if only at a high level (e.g. that it relates to Antarctic rather than the Arctic). It may
        also use a less formal, but more useful, URL for more information about the reference system.

        Wherever possible URIs are used to match identifiers, to avoid ambiguity with how they are referenced as codes
        or names.

        :type spatial_reference_system_code dict
        :param spatial_reference_system_code: spatial reference system containing a href property with an identifier URI
        :rtype str
        :return: formatted spatial reference system identifier, including Markdown links
        """
        if spatial_reference_system_code["href"] == "http://www.opengis.net/def/crs/EPSG/0/3031":
            return "WGS 84 / Antarctic Polar Stereographic ([EPSG:3031](https://spatialreference.org/ref/epsg/3031/))"
        if spatial_reference_system_code["href"] == "http://www.opengis.net/def/crs/EPSG/0/4326":  # noqa: RET503
            return "WGS 84 ([EPSG:4326](https://spatialreference.org/ref/epsg/wgs-84/))"

    @staticmethod
    def _process_extents(extents: list[dict]) -> dict[str, dict]:
        """
        Index geographic, vertical or temporal extents with IDs.

        Extents without an ID are omitted.
        """
        _ = {}
        for extent in extents:
            if "id" in extent:
                _[extent["id"]] = extent
        return _

    @staticmethod
    def _process_bounding_box_geometry(bounding_box: dict[str, str]) -> dict[str, str | list]:
        """
        Construct a GeoJSON geometry for a bounding box within a spatial extent.

        Uses the top-left and bottom-right pair of coordinates in a bounding box to make as GeoJSON polygon.
        """
        return {
            "type": "Polygon",
            "coordinates": [
                [
                    [bounding_box["west_longitude"], bounding_box["south_latitude"]],
                    [bounding_box["east_longitude"], bounding_box["south_latitude"]],
                    [bounding_box["east_longitude"], bounding_box["north_latitude"]],
                    [bounding_box["west_longitude"], bounding_box["north_latitude"]],
                    [bounding_box["west_longitude"], bounding_box["south_latitude"]],
                ],
            ],
        }

    @staticmethod
    def _process_download(distribution: dict, distributions: list[dict]) -> dict[str, str] | None:  # noqa: C901
        """
        Generate an item download.

        Transforms a ISO 19115 transfer option and optionally an associated format, into an item download option. These
        download options are bespoke to this data catalogue, using inference and hard-coded formatting options to enrich
        or simplify information to be more useful.

        Unknown formats will be passed through and may not be handled as expected. Some formats are skipped as
        unsupported.

        Some distribution types vary depending on whether another distribution is present, or not. For example, an
        ArcGIS Feature Service will be combined with a Feature Layer if present.
        """
        format_dict = distribution.get("format")
        if format_dict is not None:
            distribution_format = format_dict.get("format")
            distribution_format_href = format_dict.get("href")
        else:  # pragma: no cover (will be addressed in #116)
            distribution_format = None
            distribution_format_href = None

        download = {
            "id": sha1(json.dumps(distribution).encode()).hexdigest(),  # noqa: S324 - nosec
            "format": None,
            "format_title": None,
            "format_description": None,
            "hasSize": True,
            "size": None,
            "url": distribution["transfer_option"]["online_resource"]["href"],
        }

        if "size" in distribution["transfer_option"]:
            size = distribution["transfer_option"]["size"]
            download["size"] = f"{size['magnitude']}{size['unit']}"

        if distribution_format_href == "https://www.iana.org/assignments/media-types/application/geopackage+sqlite3":
            download["format"] = "gpkg"
            download["format_title"] = "GeoPackage"
            download["format_description"] = "OGC GeoPackage"
        elif distribution_format_href == "https://www.iana.org/assignments/media-types/application/vnd.shp":
            download["format"] = "shp"
            download["format_title"] = "Shapefile"
            download["format_description"] = "ESRI Shapefile"
        elif (
            distribution_format_href == "https://www.iana.org/assignments/media-types/application/pdf"
        ):  # pragma: no cover (added for future use)
            download["format"] = "pdf"
            download["format_title"] = "PDF"
            download["format_description"] = "Adobe PDF"
        elif (
            distribution_format_href == "https://www.iana.org/assignments/media-types/application/png"
        ):  # pragma: no cover (added for future use)
            download["format"] = "png"
            download["format_title"] = "PNG"
            download["format_description"] = "PNG image"
        elif distribution_format == "ArcGIS Feature Layer":
            download["format"] = "arcgis_feature_layer"
            download["format_title"] = "ArcGIS Feature Layer"
            download["format_description"] = "Esri ArcGIS Feature Layer"
            download["hasSize"] = False
        elif distribution_format == "ArcGIS Tile Layer":
            download["format"] = "arcgis_tile_layer"
            download["format_title"] = "ArcGIS Tile Layer"
            download["format_description"] = "Esri ArcGIS Tile Layer"
            download["hasSize"] = False
        elif distribution_format == "ArcGIS Feature Service":
            download["format"] = "arcgis_feature_service"
            download["format_title"] = "ArcGIS Feature Service"
            download["format_description"] = "Esri ArcGIS Feature Service"
            download["hasSize"] = False
        elif distribution_format == "ArcGIS Vector Tile Service":
            download["format"] = "arcgis_vector_tile_service"
            download["format_title"] = "ArcGIS Vector Tile Service"
            download["format_description"] = "Esri ArcGIS Vector Tile Service"
            download["hasSize"] = False

        # skip option if it is an unsupported type
        if distribution_format == "Web Map Service":
            return None

        # include service URL from ArcGIS feature service within ArcGIS feature layer options
        if distribution_format == "ArcGIS Feature Layer":
            for _distribution in distributions:
                if _distribution.get("format") and _distribution["format"]["format"] == "ArcGIS Feature Service":
                    download["service_url"] = _distribution["transfer_option"]["online_resource"]["href"]
                    break

        # include service URL from ArcGIS vector tile service within ArcGIS tile layer options
        if distribution_format == "ArcGIS Tile Layer":
            for _distribution in distributions:
                if _distribution.get("format") and _distribution["format"]["format"] == "ArcGIS Vector Tile Service":
                    download["service_url"] = _distribution["transfer_option"]["online_resource"]["href"]
                    break

        # skip option if it has already been aggregated into another option
        if distribution_format == "ArcGIS Feature Service":
            for _distribution in distributions:
                if _distribution.get("format") and _distribution["format"]["format"] == "ArcGIS Feature Layer":
                    return None

        # skip option if it has already been aggregated into another option
        if distribution_format == "ArcGIS Vector Tile Service":
            for _distribution in distributions:
                if _distribution.get("format") and _distribution["format"]["format"] == "ArcGIS Tile Layer":
                    return None

        return download

    @staticmethod
    def _process_supplemental_info(supplemental_information_str: str) -> dict:
        try:
            return json.loads(supplemental_information_str)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _process_physical_size(width_mm: float, height_mm: float) -> str:
        if width_mm == 210 and height_mm == 297:
            return "A4 Portrait (width: 21.0cm, height: 29.7cm)"
        if width_mm == 297 and height_mm == 210:
            return "A4 Landscape (width: 29.7cm, height: 21.0cm)"

        return f"Width: {width_mm}mm, Height: {height_mm}mm"

    def _filter_aggregations(
        self, aggregations: list[dict], association_type: str, initiative_type: str | None = None
    ) -> list[dict]:
        """
        Filter aggregations by an association type, and optionally an initiative type.

        Aggregations in ISO can be used for expressing multiple types of relationship between one resource and others.
        Two, code list options are used to indicate the type of relationship (the association type, required), and the
        context of this relationship (the initiative type, optional).

        Association and initiative types are defined by the relevant BAS Metadata Library record configuration schema
        and ISO code lists.

        For example:

        | Association Type   | Initiative Type | Example/Description                                                |
        | ------------------ | --------------- | ------------------------------------------------------------------ |
        | revisionOf         | -               | a record replaces/updates another                                  |
        | isComposedOf       | Collection      | a record is made up of a set of other records to form a collection |

        As different combinations of association and initiative types are typically used differently, this method
        filters keywords for a specified type (e.g. only 'isComposedOf' aggregations).

        Where a related/aggregated resource is within this catalogue, it is enhanced with the title of the related
        resource to provide a human readable identifier.
        """
        _aggregations = []

        for aggregation in aggregations:
            if aggregation["association_type"] == association_type:
                if initiative_type is not None and aggregation["initiative_type"] != initiative_type:
                    continue

                _aggregation = copy(aggregation)
                try:
                    _aggregation["identifier"]["title"] = self._related_records[
                        _aggregation["identifier"]["identifier"]
                    ].title
                except KeyError:
                    _aggregation["identifier"]["title"] = _aggregation["identifier"]["identifier"]
                    if _aggregation["identifier"]["namespace"] == "data.bas.ac.uk":
                        _aggregation["identifier"]["title"] = (
                            f"Unknown Item ({_aggregation['identifier']['identifier']})"
                        )
                _aggregations.append(_aggregation)

        return _aggregations

    @staticmethod
    def _filter_keyword_terms(keyword_sets: list[dict], keyword_set_url: str) -> list[dict]:
        """
        Filter a specific keyword set from a collection of keyword sets based on the keyword set's URI.

        :type keyword_sets dict
        :param keyword_sets: collection of keyword sets to filter
        :type keyword_set_url str
        :param keyword_set_url: URI of keyword set to filter out of the collection of keyword sets
        :rtype dict
        :return: filtered keyword set
        """
        for keyword_set in keyword_sets:  # noqa: RET503 (will be refactored away)
            if keyword_set["thesaurus"]["title"]["href"] == keyword_set_url:
                return keyword_set["terms"]

    @staticmethod
    def _filter_identifiers(identifiers: list[dict], namespace: str) -> list[dict]:
        """Return identifiers by namespace."""
        _ = []
        for identifier_ in identifiers:
            if identifier_["namespace"] == namespace:
                _.append(identifier_)
        return _

    @staticmethod
    def _filter_graphic_overviews(overviews: list[dict], identifier: str) -> dict | None:
        for overview in overviews:
            if overview["identifier"] == identifier:
                return overview
        return None

    @property
    def abstract(self) -> str:
        return self.record.abstract

    @property
    def abstract_markdown(self) -> str:
        return markdown(self.abstract, output_format="html")

    @property
    def authors(self) -> list[dict]:
        return self.record.contacts.get("author", [])

    @property
    def bounding_geographic_extent(self) -> dict | None:
        indexed_extents = self._process_extents(extents=self.geographic_extents)
        return indexed_extents.get("bounding", None)

    @property
    def bounding_geographic_extent_embedded_map_href(self) -> str:
        if self.bounding_geographic_extent is None:
            return "#"

        with current_app.app_context():
            geom = urlencode(
                {"geom": json.dumps(self.bounding_geographic_extent["bounding_box_geometry"]["coordinates"])}
            )
            return f"{current_app.config['EXTENT_MAP_ENDPOINT']}/?{geom}"

    @property
    def bounding_temporal_extent(self) -> dict | None:
        indexed_extents = self._process_extents(extents=self.temporal_extents)
        return indexed_extents.get("bounding", None)

    @property
    def character_set(self) -> str:
        return str(self.record.character_set).upper()

    @property
    def citation(self) -> str | None:
        return self.record.other_citation_details

    @property
    def citation_markdown(self) -> str:
        return markdown(self.citation, output_format="html")

    @property
    def created(self) -> str:
        _date = self.record.dates["creation"]
        return self._format_date(date_datetime=_date["date"], date_precision=_date["date_precision"])

    @property
    def data_type(self) -> str:
        return self.record.spatial_representation_type

    @property
    def downloads(self) -> list[dict[str, str]]:
        downloads = []

        for distribution in self.record.distributions:
            download = self._process_download(distribution=distribution, distributions=self.record.distributions)
            if download is not None:
                downloads.append(download)

        return downloads

    @property
    def edition(self) -> str:
        return self.record.edition

    @property
    def geographic_extents(self) -> list[dict]:
        geographic_extents = []

        for extent in self.record.extents:
            geographic_extent = deepcopy(extent["geographic"])
            geographic_extent["bounding_box_geometry"] = self._process_bounding_box_geometry(
                bounding_box=geographic_extent["bounding_box"]
            )
            if "identifier" in extent:
                geographic_extent["id"] = extent["identifier"]
            geographic_extents.append(geographic_extent)

        return geographic_extents

    @property
    def identifier(self) -> str:
        return self.record.identifier

    @property
    def image_overview(self) -> dict | None:
        overview = self._filter_graphic_overviews(overviews=self.record.graphic_overviews, identifier="overview")
        if overview is None:
            return None
        return {
            "href": overview["href"],
            "alt_text": overview["description"],
        }

    @property
    def isbns(self) -> list[str]:
        isbns = []

        for isbn in self._filter_identifiers(identifiers=self.record.identifiers, namespace="isbn"):
            isbns.append(isbn["identifier"])

        return isbns

    @property
    def item_type(self) -> str:
        return self.record.hierarchy_level

    @property
    def language(self) -> str:
        return self._format_language(language=self.record.language)

    @property
    def licence_url(self) -> str | None:
        for constraint in self.record.constraints:
            if constraint["type"] == "usage" and constraint["restriction_code"] == "license":
                return constraint["href"]

        return None

    @property
    def lineage(self) -> str:
        return self.record.lineage

    @property
    def lineage_markdown(self) -> str:
        return markdown(self.lineage, output_format="html")

    @property
    def location_keywords(self) -> list[dict]:
        location_keywords = self.record.location_keywords
        for location_keyword in location_keywords:
            location_keyword["thesaurus"]["title"]["value"] = self._format_keyword_thesaurus_title(
                thesaurus_title=location_keyword["thesaurus"]["title"]["value"]
            )
        return location_keywords

    @property
    def maintenance_frequency(self) -> str:
        return self._format_maintenance_frequency(maintenance_frequency=self.record.maintenance_frequency)

    @property
    def metadata_maintenance_progress(self) -> str | None:
        progress = self.record.metadata_maintenance_progress

        if progress is None:
            return None

        return str(progress).capitalize()

    @property
    def metadata_character_set(self) -> str:
        return str(self.record.metadata_character_set).upper()

    @property
    def metadata_language(self) -> str:
        return self._format_language(language=self.record.metadata_language)

    @property
    def metadata_maintenance_frequency(self) -> str:
        return self._format_maintenance_frequency(maintenance_frequency=self.record.metadata_maintenance_frequency)

    @property
    def metadata_standard_name(self) -> str | None:
        return self.record.metadata_standard_name

    @property
    def metadata_standard_version(self) -> str | None:
        return self.record.metadata_standard_version

    @property
    def metadata_updated(self) -> str:
        return self._format_date(date_datetime=self.record.metadata_updated)

    @property
    def related_datasets(self) -> list[dict]:
        return self._filter_aggregations(
            aggregations=self.record.aggregations, association_type="crossReference", initiative_type="investigation"
        )

    @property
    def related_references(self) -> list[dict]:
        return self._filter_aggregations(
            aggregations=self.record.aggregations, association_type="crossReference", initiative_type="sciencePaper"
        )

    @property
    def related_collections(self) -> list[dict]:
        """Item's Collections."""
        return self._filter_aggregations(
            aggregations=self.record.aggregations, association_type="largerWorkCitation", initiative_type="collection"
        )

    @property
    def related_physical_reverse(self) -> dict | None:
        reverse_of = self._filter_aggregations(
            aggregations=self.record.aggregations, association_type="physicalReverseOf"
        )
        if len(reverse_of) == 0:
            return None
        return reverse_of[0]

    @property
    def related_projects(self) -> list[dict]:
        return self._filter_aggregations(
            aggregations=self.record.aggregations, association_type="crossReference", initiative_type="project"
        )

    @property
    def released(self) -> str | None:
        _date = self.record.dates.get("released", None)

        if _date is None:
            return None

        return self._format_date(date_datetime=_date["date"], date_precision=_date["date_precision"])

    @property
    def physical_size(self) -> str:
        kv = self.supplemental_information_json

        if "physical_size_width_mm" in kv and "physical_size_height_mm" in kv:
            return self._process_physical_size(
                width_mm=kv["physical_size_width_mm"], height_mm=kv["physical_size_height_mm"]
            )

        return ""

    @property
    def point_of_contact(self) -> str:
        points_of_contact = self.record.contacts["pointOfContact"]
        point_of_contact = points_of_contact[0]
        return self._format_organisation_name(organisation_name=point_of_contact["organisation"]["name"])

    @property
    def point_of_contact_details(self) -> dict:
        points_of_contact = self.record.contacts["pointOfContact"]
        point_of_contact = points_of_contact[0]
        point_of_contact["organisation"]["name"] = self._format_organisation_name(
            organisation_name=point_of_contact["organisation"]["name"]
        )
        return point_of_contact

    @property
    def published(self) -> str | None:
        _date = self.record.dates.get("publication", None)

        if _date is None:
            return None

        return self._format_date(date_datetime=_date["date"], date_precision=_date["date_precision"])

    @property
    def scale(self) -> str | None:
        scale = self.record.spatial_resolution
        if scale is None:
            return None

        locale.setlocale(locale.LC_ALL, "")
        return f"1:{locale.format_string('%d', scale, grouping=True)}"

    @property
    def series(self) -> str | None:
        if self.record.series_name is None:
            return None
        if self.record.series_edition is None:
            return self.record.series_name
        return f"{self.record.series_name} ({self.record.series_edition})"

    @property
    def series_markdown(self) -> str | None:
        if self.series is None:
            return None
        return markdown(self.series, output_format="html")

    @property
    def spatial_reference_system(self) -> str | None:
        if self.record.spatial_reference_system is None:
            return None  # pragma: no cover (will be addressed in #116)

        return self._format_spatial_reference_system(
            spatial_reference_system_code=self.record.spatial_reference_system["code"]
        )

    @property
    def spatial_reference_system_markdown(self) -> str | None:
        if self.spatial_reference_system is None:
            return None  # pragma: no cover (will be addressed in #116)

        return markdown(self.spatial_reference_system, output_format="html")

    @property
    def supplemental_information_json(self) -> dict:
        if self.record.supplemental_information is None:
            return {}

        return self._process_supplemental_info(self.record.supplemental_information)

    @property
    def templates_tabs(self) -> dict:
        config = {
            "active_tab": "data",
            "is_visible": {
                "data": False,
                "authors": False,
                "licence": False,
                "extent": False,
                "lineage": False,
                "related": False,
                "additional": True,
                "contact": True,
            },
        }

        if len(self.downloads) > 0:
            config["is_visible"]["data"] = True

        if len(self.authors) > 0:
            config["is_visible"]["authors"] = True

        if self.licence_url is not None:
            config["is_visible"]["licence"] = True

        if self.bounding_geographic_extent is not None or self.bounding_temporal_extent is not None:
            config["is_visible"]["extent"] = True

        if self.lineage is not None:
            config["is_visible"]["lineage"] = True

        if (
            len(self.related_collections) > 0
            or len(self.related_datasets) > 0
            or len(self.related_projects) > 0
            or len(self.related_references) > 0
        ):
            config["is_visible"]["related"] = True

        for tab, is_visible in config["is_visible"].items():
            if is_visible:
                config["active_tab"] = tab
                break

        return config

    @property
    def temporal_extents(self) -> list[dict[str, str]]:
        temporal_extents = []

        for extent in self.record.extents:
            temporal_extent = {
                "start": self._format_date(date_datetime=extent["temporal"]["start"]),
                "end": self._format_date(date_datetime=extent["temporal"]["end"]),
            }
            if "identifier" in extent:
                temporal_extent["id"] = extent["identifier"]
            temporal_extents.append(temporal_extent)

        return temporal_extents

    @property
    def theme_keywords(self) -> list[dict]:
        """
        Theme keywords (filtered).

        Theme keywords are currently used for two keyword sets that the catalogue treats as special cases:

        1. BAS research topics - http://vocab.nerc.ac.uk/collection/T01/current1/
        2. Data catalogue collections - http://vocab.nerc.ac.uk/collection/T02/current/ (deprecated)

        As these keyword sets are exposed through other Item properties (collections and topics respectively), they are
        filtered _out_ from other theme keyword sets. Additionally, ISO Topics are filtered _in_ as a theme keyword set.

        :rtype list
        :return: theme keyword sets, exc. BAS research topics and data catalogue collections, inc. ISO topics
        """
        theme_keywords = []
        excluded_keyword_sets = [
            "http://vocab.nerc.ac.uk/collection/T01/current/",
            "http://vocab.nerc.ac.uk/collection/T02/current/",
        ]

        _iso_topics_keyword_terms = []
        for iso_topic in self.record.topics:
            _iso_topics_keyword_terms.append({"term": iso_topic})
        _iso_topics_keyword_set = {"terms": _iso_topics_keyword_terms, "thesaurus": {"title": {"value": "ISO Topics"}}}
        theme_keywords.append(_iso_topics_keyword_set)

        _theme_keywords = self.record.theme_keywords
        for theme_keyword in _theme_keywords:
            if theme_keyword["thesaurus"]["title"]["href"] in excluded_keyword_sets:
                continue

            theme_keyword["thesaurus"]["title"]["value"] = self._format_keyword_thesaurus_title(
                thesaurus_title=theme_keyword["thesaurus"]["title"]["value"]
            )
            theme_keywords.append(theme_keyword)

        return theme_keywords

    @property
    def title(self) -> str:
        return self.record.title

    @property
    def title_markdown(self) -> str:
        return markdown(self.title, output_format="html")

    @property
    def topics(self) -> list[str]:
        """
        Item's research topics.

        Research topics are implemented as a descriptive keyword set using the NERC Vocabulary Service (T01).

        Note: These are separate to ISO Topics, which are treated as a description keyword set (see the
        `Item.theme_keywords` property).

        :rtype list
        :return: Topic names
        """
        topic_terms = self._filter_keyword_terms(
            keyword_sets=self.record.theme_keywords, keyword_set_url="http://vocab.nerc.ac.uk/collection/T01/current/"
        )

        if topic_terms is None:
            return []

        # return a list of just term values
        return [term["term"] for term in topic_terms]

    @property
    def updated(self) -> str | None:
        try:
            _date = self.record.dates["revision"]
            return self._format_date(date_datetime=_date["date"], date_precision=_date["date_precision"])
        except KeyError:  # pragma: no cover (will be addressed in #116)
            return None


class Collection:
    """
    Collections are abstractions of Records.

     They are specific and tailored to the needs of this project, and map to the 'collection' hierarchy level in ISO
     19115. All other hierarchy levels are represented by the Item class.

    They are used to represent an unstructured set of Items that are somehow related. Collections are independent of
    other grouping mechanisms, such as: descriptive keywords, aggregations, publishers and/or other common properties.

    As with Items, Collections are read only and use a Record internally for exposing information through properties.
    They are designed to provide final output to humans, rather than for onward use or interpretation by other services
    - use Records for that.

    Various formatting, processing and filtering methods are used to transform some information to be more easily
    understood or to make more contextual sense.
    """

    def __init__(self, record: Record) -> None:
        self.record = record

        if self.record.hierarchy_level != "collection":
            raise CollectionInvalidSourceRecordError()

    def __repr__(self) -> str:
        return f"<Collection / {self.identifier}>"

    @staticmethod
    def _filter_aggregations(
        aggregations: list[dict], association_type: str, initiative_type: str | None = None
    ) -> list[dict]:
        """
        Filter aggregations by an association type, and optionally an initiative type.

        Aggregations in ISO can be used for expressing multiple types of relationship between one resource and others.
        Two, code list options are used to indicate the type of relationship (the association type, required), and the
        context of this relationship (the initiative type, optional).

        Association and initiative types are defined by the relevant BAS Metadata Library record configuration schema
        and ISO code lists.

        For example:

        | Association Type   | Initiative Type | Example/Description                                                |
        | ------------------ | --------------- | ------------------------------------------------------------------ |
        | revisionOf         | -               | a record replaces/updates another                                  |
        | isComposedOf       | Collection      | a record is made up of a set of other records to form a collection |

        As different combinations of association and initiative types are typically used differently, this method
        filters keywords for a specified type (e.g. only 'isComposedOf' aggregations).

        :type aggregations: list
        :param aggregations: list of (all) aggregations
        :type association_type: str
        :param association_type: association type to filter by
        :type initiative_type: str
        :param initiative_type: optionally, initiative type to filter by
        :rtype list
        :return: subset of descriptive keywords that are for the specified association, and optionally initiative, type
        """
        _aggregations = []
        for aggregation in aggregations:
            if (
                aggregation["association_type"] == association_type
                and aggregation["initiative_type"] == initiative_type
            ):
                _aggregations.append(aggregation)

        return _aggregations

    @staticmethod
    def _filter_keyword_terms(keyword_sets: list[dict], keyword_set_url: str) -> list[dict]:
        """
        Filter a specific keyword set from a collection of keyword sets based on the keyword set's URI.

        :type keyword_sets dict
        :param keyword_sets: collection of keyword sets to filter
        :type keyword_set_url str
        :param keyword_set_url: URI of keyword set to filter out of the collection of keyword sets
        :rtype dict
        :return: filtered keyword set
        """
        for keyword_set in keyword_sets:  # noqa: RET503 (will be refactored away)
            if keyword_set["thesaurus"]["title"]["href"] == keyword_set_url:
                return keyword_set["terms"]

    @property
    def identifier(self) -> str:
        return self.record.identifier

    @property
    def title(self) -> str:
        return self.record.title

    @property
    def title_markdown(self) -> str:
        return markdown(self.title, output_format="html")

    @property
    def topics(self) -> list[str]:
        """
        Collection's research topics.

        Research topics are implemented as a descriptive keyword set using the NERC Vocabulary Service (T01).

        Note: These are separate to ISO Topics, which are treated as a description keyword set.

        :rtype list
        :return: Topic names
        """
        topic_terms = self._filter_keyword_terms(
            keyword_sets=self.record.theme_keywords, keyword_set_url="http://vocab.nerc.ac.uk/collection/T01/current/"
        )

        if topic_terms is None:
            return []

        # return a list of just term values
        return [term["term"] for term in topic_terms]

    @property
    def summary(self) -> str:
        return self.record.abstract

    @property
    def summary_markdown(self) -> str:
        # noinspection PyTypeChecker
        return markdown(self.summary, output_format="html5")

    @property
    def item_identifiers(self) -> list[str] | None:
        """
        Item identifiers in Collection.

        Items within the Collection, as specified by a record's aggregations. Returned as a list of Item identifiers.

        Note: Only items that exist within the BAS Data Catalogue are currently supported, as determined by the
        namespace of each aggregation identifier (specifically 'data.bas.ac.uk').

        :return: List of Item identifiers in a Collection
        """
        collection_aggregations = self._filter_aggregations(
            aggregations=self.record.aggregations, association_type="isComposedOf", initiative_type="collection"
        )
        if len(collection_aggregations) < 1:
            return None

        item_identifiers = []
        for collection_aggregate in collection_aggregations:
            if collection_aggregate["identifier"]["namespace"] == "data.bas.ac.uk":
                item_identifiers.append(collection_aggregate["identifier"]["identifier"])
        return item_identifiers
