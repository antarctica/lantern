import json

from datetime import date, datetime
from hashlib import sha1
from pathlib import Path
from typing import Dict, List, Union
from urllib.parse import urlparse as url_parse, parse_qs as query_string_parse

from backports.datetime_fromisoformat import MonkeyPatch
from dateutil.relativedelta import relativedelta
from markdown import markdown

from scar_add_metadata_toolbox.csw import (
    CSWGetRecordMode,
    CSWClient,
    RecordNotFoundException,
    RecordInsertConflictException,
)

from scar_add_metadata_toolbox.hazmat.metadata import (
    generate_record_config_from_record_xml,
    generate_xml_record_from_record_config_without_xml_declaration,
    dump_record_to_json,
    load_record_from_json,
    process_usage_constraints,
)

# Workaround for lack of `date(time).fromisoformat()` method in Python 3.6
MonkeyPatch.patch_fromisoformat()


class RecordRetractBeforeDeleteException(Exception):
    """
    Represents a situation whereby a record is deleted before it has been first been retracted

    This is illogical as published records must have an unpublished counterpart. If this unpublished counterpart is
    removed (deleted) this rule would be violated. Instead the published record must be removed (retracted) first.
    """

    pass


class CollectionInsertConflictException(Exception):
    """
    Represents a situation where a collection to be inserted already exists in a set of collections

    Collections must be unique. If a collection is inserted into a set with the same identifier as an existing
    collection, neither collection would be unique and this rule would be violated. Collections may be updated instead.
    """

    pass


class CollectionNotFoundException(Exception):
    """
    Represents a situation where a given collection does not exist
    """

    pass


class RecordSummary:
    """
    Records represent and describe a given resource, often in great detail using a conceptual model. These full
    representations (represented by the Record class) are inherently large and complex and so unwieldy in large numbers,
    such as indexes.

    Record summaries also represent and describe a resource but in far less detail. As RecordSummaries are simpler, they
    can be processed more easily when in greater numbers than Records.

    Record summaries are effectively subsets of Records, however to leverage inheritance, Records inherit from and
    extend RecordSummaries. Collections of record summaries are typically held in a repository (represented by the
    Repository class).

    Record summaries are created from a configuration dictionary. Properties are defined to access specific parts of
    this configuration. Record summaries are intended to be read-only objects.

    To ensure RecordSummaries remain lightweight, properties should be strictly limited, with anything non-essential
    added to the Record class instead.
    """

    def __init__(self, config: dict = None):
        """
        :type config dict
        :param config: Record configuration
        """
        self.config = {}
        if config is not None:
            self.config = config

    def __repr__(self):
        return f"<RecordSummary / {self.identifier} / {self.title}>"

    @property
    def identifier(self) -> str:
        return self.config["file_identifier"]

    @property
    def title(self) -> str:
        return self.config["resource"]["title"]["value"]


class Record(RecordSummary):
    """
    Records represent and describe a given resource, often in great detail using a conceptual model - currently assumed
    to be ISO 19115 (Geographic Information).

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

    def __repr__(self):
        return f"<Record / {self.identifier}>"

    def _process_resource_dates(self) -> Dict[str, Dict[str, Union[str, date, datetime]]]:
        """
        Processes resource dates into a dict, keyed by date type, with precision

        ISO allows multiple dates of the same type (e.g. multiple publication dates) however this doesn't make much
        sense and is harder to interact with. This method will restructure dates by their date type and stored with a
        default precision of 'day'. This precision will be overridden if less precise.

        E.g. This input:

        ```
        [
            {
                "date_type": "creation",
                "date": <date 2020-01-01>,
                "date_precision": "year"
            },
            {
                "date_type": "publication",
                "date": <datetime 2020-04-20T14:43:30>,
            }
        ]
        ```

        Will become:

        ```
        {
            'creation": {
                "date": <date 2020-01-01>,
                "date_precision": "year"
            },
            "publication": {
                "date": <datetime 2020-04-20T14:43:30>,
                "date_precision": "day"
            }
        ]
        ```

        :rtype dict
        :return: resource dates keyed by date type
        """
        resource_dates = {}
        for resource_date in self.config["resource"]["dates"]:
            _resource_date = {"value": resource_date["date"], "precision": "day"}
            try:
                _resource_date["precision"] = resource_date["date_precision"]
            except KeyError:
                pass
            resource_dates[resource_date["date_type"]] = _resource_date
        return resource_dates

    def _process_resource_contacts(self) -> Dict[str, List[dict]]:
        """
        Processes resource points of contact into a dict, key by role

        ISO allows multiple contacts to have the same role (e.g. multiple authors). The BAS Metadata Library config
        allows contacts to have multiple roles (e.g. publisher and distributor). This method will restructure contacts
        by their roles.

        E.g. This (simplified) input:

        ```
        [
            {
                "organisation_name": "MAGIC",
                "roles": [
                    "point of contact",
                    "distributor"
                ]
            },
            {
                "organisation_name": "Constance Watson",
                "roles": [
                    "author"
                ]
            },
            {
                "organisation_name": "John Cinnamon",
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
                    "organisation_name": "Constance Watson"
                },
                {
                    "organisation_name": "John Cinnamon"
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

        :rtype dict
        :return: resource contacts keyed by role
        """
        resource_contacts = {}
        for resource_contact in self.config["resource"]["contacts"]:
            for resource_contact_role in resource_contact["role"]:
                if resource_contact_role not in resource_contacts.keys():
                    resource_contacts[resource_contact_role] = []
                resource_contacts[resource_contact_role].append(resource_contact)
        return resource_contacts

    def _filter_resource_keywords(self, keyword_type: str) -> List[dict]:
        """
        Filters resource descriptive keywords by keyword type

        ISO supports multiple keyword type for descriptive keywords (e.g. theme, place), as each type is typically used
        differently, this method filters keywords for a specified type (e.g. only theme keywords).

        Keyword types are defined by the relevant BAS Metadata Library record configuration schema.

        :type keyword_type str
        :param keyword_type: descriptive keyword type
        :rtype list
        :return: list of descriptive keywords of the specified keyword type
        """
        _keywords = []
        for keywords in self.config["resource"]["keywords"]:
            if keywords["type"] == keyword_type:
                _keywords.append(keywords)

        return _keywords

    @property
    def abstract(self) -> str:
        return self.config["resource"]["abstract"]

    @property
    def character_set(self) -> str:
        return self.config["resource"]["character_set"]

    @property
    def contacts(self) -> Dict[str, List[dict]]:
        return self._process_resource_contacts()

    @property
    def dates(self) -> Dict[str, Dict[str, Union[str, date, datetime]]]:
        return self._process_resource_dates()

    @property
    def edition(self) -> str:
        return self.config["resource"]["edition"]

    @property
    def geographic_extent(self) -> Dict:
        return self.config["resource"]["extent"]["geographic"]

    def hierarchy_level(self) -> str:
        return self.config["hierarchy_level"]

    @property
    def language(self) -> str:
        return self.config["resource"]["language"]

    @property
    def lineage(self) -> str:
        return self.config["resource"]["lineage"]

    @property
    def location_keywords(self) -> List[dict]:
        return self._filter_resource_keywords(keyword_type="place")

    @property
    def maintenance_frequency(self) -> str:
        return self.config["resource"]["maintenance"]["maintenance_frequency"]

    @property
    def metadata_character_set(self) -> str:
        return self.config["character_set"]

    @property
    def metadata_language(self) -> str:
        return self.config["language"]

    @property
    def metadata_maintenance_frequency(self) -> str:
        return self.config["maintenance"]["maintenance_frequency"]

    @property
    def metadata_maintenance_progress(self) -> str:
        return self.config["maintenance"]["progress"]

    @property
    def metadata_standard_name(self) -> str:
        return self.config["metadata_standard"]["name"]

    @property
    def metadata_standard_version(self) -> str:
        return self.config["metadata_standard"]["version"]

    @property
    def metadata_updated(self) -> date:
        return self.config["date_stamp"]

    @property
    def spatial_reference_system(self) -> dict:
        return self.config["reference_system_info"]

    @property
    def spatial_representation_type(self) -> str:
        return self.config["resource"]["spatial_representation_type"]

    @property
    def theme_keywords(self) -> List[dict]:
        return self._filter_resource_keywords(keyword_type="theme")

    @property
    def temporal_extent(self) -> Dict[str, datetime]:
        return {
            "start": self.config["resource"]["extent"]["temporal"]["period"]["start"],
            "end": self.config["resource"]["extent"]["temporal"]["period"]["end"],
        }

    @property
    def transfer_options(self) -> List[dict]:
        return self.config["resource"]["transfer_options"]

    @property
    def usage_constraints(self) -> Dict[str, dict]:
        return process_usage_constraints(constraints=self.config["resource"]["constraints"]["usage"])

    @property
    def topics(self) -> List[str]:
        return self.config["resource"]["topics"]

    def load(self, record_path: Path) -> None:
        """
        Loads a Record from a file encoded using JSON

        Specifically load a BAS Metadata Library record configuration for ISO 19115-2 that has been JSON encoded.

        :type record_path Path
        :param record_path: path to file containing JSON encoded record configuration
        """
        with open(str(record_path)) as record_file:
            _record_config = json.load(record_file)
            self.config = load_record_from_json(record=_record_config)

    def dump(self, record_path: Path, overwrite: bool = False) -> None:
        """
        Saves a Record to a file encoded using JSON

        Specifically saves a BAS Metadata Library record configuration for ISO 19115-2 using JSON encoding.

        :type record_path Path
        :param record_path: desired path of file that will contain JSON encoded record configuration
        :type overwrite: bool
        :param overwrite: if the desired file already exists, whether to replace its contents
        """
        _record_config = dump_record_to_json(record=self.config)
        try:
            with open(str(record_path), mode="x") as record_file:
                json.dump(_record_config, record_file, indent=4)
        except FileExistsError:
            if not overwrite:
                raise FileExistsError()

            with open(str(record_path), mode="w") as record_file:
                json.dump(_record_config, record_file, indent=4)

    def dumps(self, dump_format: str) -> str:
        """
        Encode a Record in a given format

        Specifically encodes a BAS Metadata Library record configuration for ISO 19115-2 using a specified encoding.

        Currently only the 'xml' format is supported for rendering a record configuration as ISO XML. Others may be
        added in the future as needs arise.

        :type dump_format str
        :param dump_format: format to encode record configuration in
        :rtype str
        :return: encoded record configuration
        """
        if dump_format == "xml":
            return generate_xml_record_from_record_config_without_xml_declaration(record_config=self.config)


class MirrorRecordSummary(Record):
    """
    Mirrored record summaries extend record summaries with a 'published' status, representing whether a record is
    *published* or *unpublished* based on the repositories a record appears within in a mirrored repository.
    """

    def __init__(self, config: dict, published: bool):
        super().__init__(config=config)
        self.published = published

    def __repr__(self):
        return f"<MirrorRecordSummary / {self.identifier} / {'Published' if self.published else 'Unpublished'}>"


class MirrorRecord(MirrorRecordSummary, Record):
    """
    Mirrored records extend mirrored record summaries and records.
    """

    def __init__(self, config: dict, published: bool):
        super().__init__(config=config, published=published)

    def __repr__(self):
        return f"<MirrorRecord / {self.identifier} / {'Published' if self.published else 'Unpublished'}>"


class Repository:
    """
    Represents a data store with an interface for creating, retrieving, updating and deleting Records

    Externally, repositories present an abstracted interface for interacting with records using the Record and
    RecordSummary classes. Internally, repositories are backed by an OGC Catalogue Services for the Web (CSW) catalogue.

    For example:

    * when creating a record - a Record class instance is converted into an ISO 19115-2 record encoded using XML and
      inserted into a CSW server using the CSW transactional profile
    * when retrieving a record - a CSW GetRecord request is made and the XML encoded ISO 19115-2 record is converted
      back into a Record class
    """

    def __init__(self, client_config: dict):
        """
        :type client_config dict
        :param client_config: configuration for the CSWClient class instance that backs this repository
        """
        self.csw_client = CSWClient(config=client_config)

    def retrieve_record(self, record_identifier: str) -> Record:
        """
        Retrieves a record from the repository

        Record identifiers are the same as ISO 19115-2 file identifiers.

        :type record_identifier str
        :param record_identifier: identifier of the record to retrieve
        :rtype Record
        :return: requested record
        """
        record_xml = self.csw_client.get_record(identifier=record_identifier, mode=CSWGetRecordMode.FULL)
        record_config = generate_record_config_from_record_xml(record_xml=record_xml)
        return Record(config=record_config)

    def retrieve_records(self) -> List[Record]:
        """
        Retrieves all records in the repository

        Note: Records are returned using a generator for use in iterators such as for loops. If an actual List of
        records is needed, for calculating a length for example, the return value can be wrapped, e.g.

        ```
        records_count = len(list(repository.retrieve_records()))
        ```

        :rtype list
        :return: all records
        """
        for record_xml in self.csw_client.get_records(mode=CSWGetRecordMode.FULL):
            record_config = generate_record_config_from_record_xml(record_xml=record_xml)
            yield Record(config=record_config)

    def list_record_identifiers(self) -> List[str]:
        """
        Retrieves identifiers for all records in the repository

        Record identifiers are the same as ISO 19115-2 file identifiers.

        :rtype list
        :return: all record identifiers
        """
        return list(self.list_records().keys())

    def list_records(self) -> Dict[str, RecordSummary]:
        """
        Retrieves summaries for all records in the repository

        Records are returned as a dictionary rather than a list to allow specific records to be easily selected.

        :rtype dict
        :return: all summarised records, keyed by record identifier
        """
        _record_summaries = {}
        for record_xml in self.csw_client.get_records(mode=CSWGetRecordMode.BRIEF):
            record_config = generate_record_config_from_record_xml(record_xml=record_xml, validate_record_config=False)
            record = RecordSummary(config=record_config)
            _record_summaries[record.identifier] = record
        return _record_summaries

    def insert_record(self, record: Record, update: bool = False) -> None:
        """
        Creates a new record, or updates an existing record, in the repository

        Records are assumed to be new records by default and will raise an exception if this causes a conflict. Records
        can be updated instead by setting the updated parameter to True.

        :type record Record
        :param record: record to be created or updated
        :type update bool
        :param update: whether an existing record can be overridden
        """
        try:
            record_xml = generate_xml_record_from_record_config_without_xml_declaration(record_config=record.config)
            self.csw_client.insert_record(record=record_xml)
        except RecordInsertConflictException:
            if not update:
                raise RecordInsertConflictException()

            # noinspection PyUnboundLocalVariable
            self.csw_client.update_record(record=record_xml)

    def delete_record(self, record_identifier: str) -> None:
        """
        Deletes a record from the repository

        Record identifiers are the same as ISO 19115-2 file identifiers.

        :type record_identifier str
        :param record_identifier: identifier of the record to delete
        """
        self.csw_client.delete_record(identifier=record_identifier)


class MirrorRepository:
    """
    Represents a composite data store with an interface for creating, retrieving, updating, deleting, publishing and
    retracting Records

    Externally, repositories present an abstracted interface for interacting with records using the MirrorRecord and
    MirrorRecordSummary classes. Internally, mirror repositories are backed by two Repository classes to represent
    'published' and 'unpublished' records.

    If a record exists in both repositories, it is considered published (all records must appear in the unpublished
    repository). If a published record is retracted, it is deleted from the published catalogue, and can then optionally
    also be deleted from the unpublished catalogue (fully deleting the record), or created in the published repository
    again to (re)publish it.
    """

    def __init__(self, unpublished_repository_config: dict, published_repository_config: dict):
        """
        :type unpublished_repository_config dict
        :param unpublished_repository_config: configuration for the unpublished Repository class instance
        :type published_repository_config dict
        :param published_repository_config: configuration for the published Repository class instance
        """
        self.published_repository = Repository(**published_repository_config)
        self.unpublished_repository = Repository(**unpublished_repository_config)

    def retrieve_record(self, record_identifier: str) -> MirrorRecord:
        """
        Retrieves a record from the repository

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
        except RecordNotFoundException:
            record = self.unpublished_repository.retrieve_record(record_identifier=record_identifier)
            return MirrorRecord(config=record.config, published=False)

    def retrieve_records(self) -> List[MirrorRecord]:
        """
        Retrieves all records in the repository

        Note: Records are returned using a generator for use in iterators such as for loops. If an actual List of
        records is needed, for calculating a length for example, the return value can be wrapped, e.g.

        ```
        records_count = len(list(repository.retrieve_records()))
        ```

        :rtype list
        :return: all records
        """
        unpublished_records = self.unpublished_repository.retrieve_records()
        published_record_identifiers = self.published_repository.list_record_identifiers()

        for unpublished_record in unpublished_records:
            _record_published = False
            if unpublished_record.identifier in published_record_identifiers:
                _record_published = True
            yield MirrorRecord(config=unpublished_record.config, published=_record_published)

    def list_record_identifiers(self) -> List[str]:
        """
        Retrieves identifiers for all records in the repository

        Record identifiers are the same as ISO 19115-2 file identifiers.

        Note: As all records have to appear in the unpublished repository we can just return it's identifiers using the
        relevant method. The published catalogue's identifiers would only ever be a subset of those.

        :rtype list
        :return: all record identifiers
        """
        return self.unpublished_repository.list_record_identifiers()

    def list_unpublished_record_identifiers(self) -> List[str]:
        """
        Retrieves identifiers for all records in the repository

        Record identifiers are the same as ISO 19115-2 file identifiers.

        Note: Use the `list_distinct_unpublished_record_identifiers()` method to only return unpublished, rather than
        all, records.

        :rtype list
        :return: all record identifiers
        """
        return self.unpublished_repository.list_record_identifiers()

    def list_published_record_identifiers(self) -> List[str]:
        """
        Retrieves identifiers for all published records in the repository

        Record identifiers are the same as ISO 19115-2 file identifiers.

        :rtype list
        :return: published record identifiers
        """
        return self.published_repository.list_record_identifiers()

    def list_distinct_unpublished_record_identifiers(self) -> List[str]:
        """
        Retrieves identifiers for all unpublished records in the repository

        This method *only* returns identifiers for records that have not been published.

        I.e. this method returns identifiers for the subset of records that do not appear in the published repository.

        Record identifiers are the same as ISO 19115-2 file identifiers.

        :rtype list
        :return: unpublished record identifiers
        """
        unpublished_record_identifiers = self.list_unpublished_record_identifiers()
        published_record_identifiers = self.list_published_record_identifiers()
        return list(set(unpublished_record_identifiers) - set(published_record_identifiers))

    def list_records(self) -> Dict[str, MirrorRecordSummary]:
        """
        Retrieves summaries for all records in the repository

        Records are returned as a dictionary rather than a list to allow specific records to be easily selected.

        :rtype dict
        :return: all summarised records, keyed by record identifier
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
        Creates a new, unpublished, record, or updates an existing record in the unpublished repository

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

    def delete_record(self, record_identifier) -> None:
        """
        Deletes a record from the unpublished repository

        Record identifiers are the same as ISO 19115-2 file identifiers.

        Note: As all records must appear in the unpublished repository, if the record exists in the published repository
        an error will be raised and record won't be deleted from the unpublished repository. Use the `retract()` method
        to delete the record from the published repository first.

        :type record_identifier str
        :param record_identifier: identifier of the record to delete
        """
        if record_identifier in self.published_repository.list_record_identifiers():
            raise RecordRetractBeforeDeleteException()

        self.unpublished_repository.delete_record(record_identifier=record_identifier)

    def publish_record(self, record_identifier: str, republish: bool = False) -> None:
        """
        Creates a new, published, record, or updates an existing record in the published repository

        Records are assumed to be new by default and will raise an exception if this causes a conflict. Records can be
        updated (republished) instead by setting the updated parameter to True.

        :type record_identifier str
        :param record_identifier: identifier of the record to publish or republish
        :type republish bool
        :param republish: whether an existing record can be overridden
        """
        try:
            record = self.unpublished_repository.retrieve_record(record_identifier=record_identifier)
        except RecordNotFoundException:
            raise RecordNotFoundException()

        try:
            self.published_repository.insert_record(record=record, update=False)
        except RecordInsertConflictException:
            if not republish:
                raise RecordInsertConflictException()
            self.published_repository.insert_record(record=record, update=True)

    def retract_record(self, record_identifier: str) -> None:
        """
        Deletes (retracts) a record from the published repository

        Record identifiers are the same as ISO 19115-2 file identifiers.

        :type record_identifier str
        :param record_identifier: identifier of the record to delete/retract
        """
        self.published_repository.delete_record(record_identifier=record_identifier)


class Item:
    """
    Items are abstractions of records specific and tailored to the needs of this project.

    Items are read only and use a record internally for exposing information through properties. They are designed to
    provide final output to humans, rather than for onward use or interpretation by other services - use records for
    that.

    Various formatting, processing and filtering methods are used to transform some information to be more easily
    understood or to make more contextual sense.
    """

    def __init__(self, record: Record):
        """
        :type record Record
        :param record: Record item is based on
        """
        self.record = record

    def __repr__(self):
        return f"<Item / {self.identifier}>"

    @staticmethod
    def _format_date(date_datetime: Union[date, datetime], native_precision: str = "day") -> str:
        """
        Format a date for display

        Currently all dates use the default ISO 8601 representation upto their native precision.

        Note: Native precision currently only applies to dates and not times within datetimes - i.e. a datetime with
        seconds will be displayed with seconds even though the native precision may be day.

        For example:

        * a date `<date 2020-04-20 precision=day>` will be formatted as "2020-04-20"
        * a date `<date 2020-01-01 precision=year>` will be formatted as "2020"
        * a datetime `<datetime 2020-04-20T14:30:45 precision=day>` will be formatted as "2020-04-20T14:30:45"
        * a datetime `<datetime 2020-04-20T14:30 precision=day>` will be formatted as "2020-04-20T14:30"

        :type date_datetime date or datetime
        :param date_datetime: date or datetime to be formatted
        :type native_precision str
        :param native_precision: maximum precision of
        :rtype str
        :return: ISO 8601 date or datetime
        """
        if native_precision == "day":
            return date_datetime.isoformat()
        elif native_precision == "year":
            return str(date_datetime.year)

    @staticmethod
    def _format_language(language: str) -> str:
        """
        Format an ISO 19115 language code list value

        Note: It is currently assumed that where English is used this refers to the United Kingdom localisation.

        Note: Other code values can be added as needed in future.

        :type language str
        :param language: ISO 19115 language code list value
        :rtype str
        :return: formatted language name
        """
        if language == "eng":
            return "English (United Kingdom)"

    @staticmethod
    def _format_maintenance_frequency(maintenance_frequency: str) -> str:
        """
        Format an ISO 19115 maintenance frequency code list value

        Note: Other code values can be added as needed in future.

        :type maintenance_frequency str
        :param maintenance_frequency: ISO 19115 maintenance frequency code list value
        :rtype str
        :return: formatted maintenance frequency value
        """
        if maintenance_frequency == "biannually":
            return "Biannually (every 6 months)"
        elif maintenance_frequency == "asNeeded":
            return "As Needed"

    @staticmethod
    def _format_organisation_name(organisation_name: str) -> str:
        """
        Format an organisation name

        Typically this is used to remove redundant information from names, as items will be shown in a BAS branded page
        template it isn't necessary to include 'British Antarctic Survey' in organisation names for example, whereas
        records may be harvested and shown in non-BAS branded websites so that context is needed.

        Names may also be modified to include helpful, but informal, elements such as abbreviations.

        Note: Other organisation names can be added as needed in future

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
        Format the name of a keyword set

        In ISO 19115 keywords that are published by an authority can include a thesaurus that describes what the keyword
        set is, the authority behind them, etc.

        As keywords are shown in a relatively narrow part of the page and titles are often quite verbose, this method
        shortens them into something more suitable, whilst still being easily identifiable.

        Note: Other thesaurus titles can be added as needed in future.

        :type thesaurus_title str
        :param thesaurus_title: title of the keyword set as defined in the keyword thesaurus
        :rtype str
        :return: formatted thesaurus title
        """
        if thesaurus_title == "General Multilingual Environmental Thesaurus - INSPIRE themes":
            return "INSPIRE themes"
        elif thesaurus_title == "Global Change Master Directory (GCMD) Science Keywords":
            return "GCMD Science Keywords"
        elif thesaurus_title == "Global Change Master Directory (GCMD) Location Keywords":
            return "GCMD Location Keywords"

    @staticmethod
    def _format_spatial_reference_system(spatial_reference_system_code: Dict[str, str]) -> str:
        """
        Format a spatial reference system identifier

        Formal identifiers for spatial reference systems (or coordinate/spatial reference systems) are readily
        accessible to those not very familiar with them. This method expands identifiers to include information people
        will understand, if only at a high level (e.g. that it relates to Antarctic rather than the Arctic).

        Wherever possible URIs are used to match identifiers to avoid ambiguity with how they are referenced as codes.

        Note: Other reference systems can be added as needed in the future.

        :type spatial_reference_system_code dict
        :param spatial_reference_system_code: spatial reference system containing a href property with an identifier URI
        :rtype str
        :return: formatted spatial reference system identifier, including markdown links
        """
        if spatial_reference_system_code["href"] == "http://www.opengis.net/def/crs/EPSG/0/3031":
            return "WGS 84 / Antarctic Polar Stereographic ([EPSG:3031](https://spatialreference.org/ref/epsg/3031/))"

    @staticmethod
    def _process_bounding_box_geojson(bounding_box: Dict[str, str]) -> Dict:
        """
        Constructs a GeoJSON bounding box for an items spatial extent

        By default this method uses a top-left and bottom-right pair of coordinates to define a box indicating the
        extent of an item.

        However, where a dataset covers all of Antarctica, a bounding box and corners no longer make sense (either to
        humans or to mapping libraries). To workaround this, known regions that should be treated differently are
        detected and an alternative feature used instead. For Antarctica for example a polygon is used to effectively
        define a bounding radius from the South pole that covers the Antarctic continent.

        This method can be expanded as needed to accommodate other areas where a bounding box feature is unsuitable.

        :type bounding_box dict
        :param bounding_box: bounding box as a set of maximum/minimum latitude/longitude using WGS 84
        :rtype dict
        :return: GeoJSON feature representing a bounding area (box, circle, polygon, etc.)
        """
        bounding_polygon = {
            "type": "FeatureCollection",
            "name": "bounding_polygon",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::3031"}},
            "features": [
                {
                    "type": "Feature",
                    "properties": {"gid": 1, "label": "Bounding polygon"},
                    "geometry": {
                        "type": "polygon",
                        "coordinates": [
                            [bounding_box["west_longitude"], bounding_box["south_latitude"]],
                            [bounding_box["east_longitude"], bounding_box["south_latitude"]],
                            [bounding_box["east_longitude"], bounding_box["north_latitude"]],
                            [bounding_box["west_longitude"], bounding_box["north_latitude"]],
                            [bounding_box["west_longitude"], bounding_box["south_latitude"]],
                        ],
                    },
                }
            ],
        }

        if (
            bounding_box["east_longitude"] == 180
            and bounding_box["north_latitude"] == -60
            and bounding_box["south_latitude"] == -90
            and bounding_box["west_longitude"] == -180
        ):
            antarctic_polygon_geometry = {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-0.000005819109207, -3333134.027676715515554],
                        [-232507.676298886770383, -3325014.680707213934511],
                        [-463882.598564556566998, -3300696.196441804990172],
                        [-692997.531439224374481, -3260297.052091349847615],
                        [-918736.24995012988802, -3204014.068240646272898],
                        [-1139998.977853273041546, -3132121.449904185254127],
                        [-1355707.745328332995996, -3044969.450702776666731],
                        [-1564811.640943090897053, -2942982.666416062042117],
                        [-1766291.931537110125646, -2826657.966405434999615],
                        [-1959167.025387293193489, -2696562.072916458826512],
                        [-2142497.254424094222486, -2553328.800065048970282],
                        [-2315389.452199890743941, -2397655.965958814136684],
                        [-2477001.305306139867753, -2230301.992997379507869],
                        [-2626545.457007425837219, -2052082.212955917464569],
                        [-2763293.343295965809375, -1863864.894608139060438],
                        [-2886578.742180570960045, -1666567.013848418835551],
                        [-2995801.019590450450778, -1461149.78611955512315],
                        [-3090428.055569021496922, -1248613.98350662435405],
                        [-3169998.836708850227296, -1029995.059075984405354],
                        [-3234125.702162629924715, -806358.102252019802108],
                        [-3282496.232287866529077, -578792.649808516609482],
                        [-3314874.770723965018988, -348407.377755039895419],
                        [-3331103.572484511416405, -116324.700031127562397],
                        [-3331103.572485930752009, 116324.699990476612584],
                        [-3314874.770722748246044, 348407.377766617632005],
                        [-3282496.232285845093429, 578792.649819981306791],
                        [-3234125.702159813605249, 806358.102263315580785],
                        [-3169998.836705251596868, 1029995.059087058994919],
                        [-3090428.055564660578966, 1248613.983517418382689],
                        [-2995801.01958534726873, 1461149.786130018532276],
                        [-2886578.742174750193954, 1666567.013858501100913],
                        [-2763293.343318711034954, 1863864.894574417034164],
                        [-2626545.457032468169928, 2052082.21292386460118],
                        [-2477001.305298350285739, 2230301.993006030563265],
                        [-2315389.452191516757011, 2397655.965966900810599],
                        [-2142497.254415175877512, 2553328.800072531681508],
                        [-1959167.025377874495462, 2696562.072923301719129],
                        [-1766291.931527236010879, 2826657.96641160454601],
                        [-1564811.640932813985273, 2942982.666421526577324],
                        [-1355707.7453176996205, 3044969.4507075115107],
                        [-1139998.977891495916992, 3132121.449890273623168],
                        [-918736.249989229603671, 3204014.068229434546083],
                        [-692997.531427837326191, 3260297.052093770354986],
                        [-463882.598553028190508, 3300696.196443425025791],
                        [-232507.676287271577166, 3325014.680708026047796],
                        [0.000005823307071, 3333134.027676715515554],
                        [232507.676298889826285, 3325014.680707213934511],
                        [463882.598564561398234, 3300696.196441804524511],
                        [692997.531439226237126, 3260297.052091349381953],
                        [918736.249950131517835, 3204014.068240645807236],
                        [1139998.977853274671361, 3132121.449904184788465],
                        [1355707.745328336255625, 3044969.450702775269747],
                        [1564811.640943094389513, 2942982.666416060645133],
                        [1766291.931537112686783, 2826657.96640543313697],
                        [1959167.02538729691878, 2696562.072916456032544],
                        [2142497.254424097947776, 2553328.800065045710653],
                        [2315389.452199894469231, 2397655.965958810877055],
                        [2477001.305306143593043, 2230301.992997375782579],
                        [2626545.457007427234203, 2052082.212955916067585],
                        [2763293.343295966740698, 1863864.894608137197793],
                        [2886578.742180571891367, 1666567.013848417671397],
                        [2995801.019590451382101, 1461149.786119553493336],
                        [3090428.055569022428244, 1248613.983506622724235],
                        [3169998.836708850692958, 1029995.059075982775539],
                        [3234125.702162631321698, 806358.102252014563419],
                        [3282496.2322878674604, 578792.649808511836454],
                        [3314874.77072396595031, 348407.377755034365691],
                        [3331103.572484511416405, 116324.70003112575796],
                        [3331103.572485930286348, -116324.699990478446125],
                        [3314874.770722747780383, -348407.377766619436443],
                        [3282496.232285844627768, -578792.649819983053021],
                        [3234125.702159813605249, -806358.102263317327015],
                        [3169998.836705251131207, -1029995.059087060857564],
                        [3090428.055564659647644, -1248613.983517420012504],
                        [2995801.019585346337408, -1461149.786130020162091],
                        [2886578.742174749262631, -1666567.013858502265066],
                        [2763293.343318709172308, -1863864.894574420759454],
                        [2626545.457032464910299, -2052082.212923869024962],
                        [2477001.30529834702611, -2230301.993006034288555],
                        [2315389.452191513031721, -2397655.96596690453589],
                        [2142497.254415172617882, -2553328.800072534941137],
                        [1959167.025377869838849, -2696562.072923305444419],
                        [1766291.931527237640694, -2826657.966411604080349],
                        [1564811.640932811424136, -2942982.666421527974308],
                        [1355707.745317697525024, -3044969.450707511976361],
                        [1139998.977891490561888, -3132121.449890275485814],
                        [918736.249989224597812, -3204014.068229435943067],
                        [692997.531427832553163, -3260297.052093770820647],
                        [463882.598553023708519, -3300696.196443425957114],
                        [232507.676287265872816, -3325014.680708026513457],
                        [-0.000005829470669, -3333134.027676715515554],
                    ]
                ],
            }
            bounding_polygon["features"][0]["geometry"] = antarctic_polygon_geometry

        return bounding_polygon

    @staticmethod
    def _process_status(maintenance_frequency: str, released_date: Union[date, datetime]):
        """
        Determines whether an item is current or outdated/superseded etc

        Supported maintenance frequencies are:

        * biannual (periodic)
        * as-needed (non-periodic)

        Possible statuses are:

        * current
        * outdated

        Maintenance frequencies are based on ISO 19115 maintenance frequency code list values.

        Where an item has a periodic maintenance frequency (e.g. every month), an overdue date is calculated by adding
        the maintenance frequency to the items release date. If the current date is less or equal to this overdue date
        it's considered current, otherwise it's deemed to be outdated.

        Note: Other status values can be added as needed in future.

        Note: This method includes code paths that are not currently used and so are exempt from code coverage. These
        paths are known to be needed in future and will therefore be tested and included in coverage in the future.

        :type maintenance_frequency str
        :param maintenance_frequency: maintenance frequency code list value
        :type released_date date or datetime
        :param released_date: item release date
        :rtype str
        :return: item status
        """
        if maintenance_frequency == "asNeeded":  # pragma: no cover (added for future use)
            return "current"

        _now = datetime.today()
        _overdue = released_date
        if type(released_date) == date:  # pragma: no cover (added for future use)
            _now = _now.date()
        if maintenance_frequency == "biannually":
            _overdue += relativedelta(months=+6)

        if _now <= _overdue:
            return "current"
        return "outdated"  # pragma: no cover (added for future use)

    @staticmethod
    def _process_download(transfer_option: dict) -> Dict[str, str]:
        """
        Generate an abstracted dataset download option

        Transforms a ISO 19115 transfer option into an abstracted download option intended specifically for the item
        page template. It remaps elements such as size sizes and file names which are currently used to infer the data
        format using conventional names. Special support is included for OGC WMS URIs to extract elements such as base
        endpoint and layer.

        In future, ISO transfer options will be associated to an distribution format removing the need to infer data
        formats from conventional file names.

        :type transfer_option dict
        :param transfer_option: ISO transfer option
        :rtype dict
        :return: item download option
        """
        download = {
            # Exempting Bandit security issue (weak hash method), not used for security/cryptography
            "id": sha1(transfer_option["online_resource"]["href"].encode("utf-8")).hexdigest(),  # nosec
            "format": None,
            "format_title": None,
            "format_description": None,
            "format_version": None,
            "size": None,
            "url": transfer_option["online_resource"]["href"],
        }

        if transfer_option["online_resource"]["title"] == "GeoPackage":
            download["format"] = "gpkg"
            download["format_title"] = "GeoPackage"
            download["format_description"] = "OGC GeoPackage"
            download["format_version"] = "1.2"
        elif transfer_option["online_resource"]["title"] == "Shapefile":
            download["format"] = "shp"
            download["format_title"] = "Shapefile"
            download["format_description"] = "ESRI Shapefile"
            download["format_version"] = "1"
        elif transfer_option["online_resource"]["title"] == "Web Map Service (WMS)":
            download["format"] = "wms"
            download["format_title"] = "Web Map Service (WMS)"
            download["format_description"] = "OGC Web Map Service"

        if "size" in transfer_option.keys():
            download["size"] = f"{transfer_option['size']['magnitude']} {transfer_option['size']['unit']}"

        if download["format"] == "wms":
            url_parsed = url_parse(download["url"])
            url_query_string = query_string_parse(url_parsed.query)
            download["endpoint"] = f"{url_parsed.scheme}://{url_parsed.netloc}{url_parsed.path}"
            download["layer"] = url_query_string["layer"][0]

        return download

    @staticmethod
    def _filter_keyword_terms(keyword_sets: List[dict], keyword_set_url: str) -> List[dict]:
        """
        Filter a specific keyword set from a collection of keyword sets based on the keyword set's URI

        :type keyword_sets dict
        :param keyword_sets: collection of keyword sets to filter
        :type keyword_set_url str
        :param keyword_set_url: URI of keyword set to filter out of the collection of keyword sets
        :rtype dict
        :return: filtered keyword set
        """
        for keyword_set in keyword_sets:
            if keyword_set["thesaurus"]["title"]["href"] == keyword_set_url:
                return keyword_set["terms"]

    @property
    def abstract(self) -> str:
        return self.record.abstract

    @property
    def abstract_markdown(self) -> str:
        return markdown(self.abstract, output_format="html5")

    @property
    def authors(self) -> List[dict]:
        return self.record.contacts["author"]

    @property
    def character_set(self) -> str:
        return str(self.record.character_set).upper()

    @property
    def citation(self) -> str:
        return self.record.usage_constraints["required_citation"]["statement"]

    @property
    def collections(self) -> List[str]:
        """
        Item's Collections

        Collections are implemented as a descriptive keyword set using the NERC Vocabulary Service (T02).

        Currently only collection names to show as free text values are returned. In future, collection IDs will be
        returned to allow linking items to their collections.

        :rtype list
        :return: Collection names
        """
        collection_terms = self._filter_keyword_terms(
            keyword_sets=self.record.theme_keywords, keyword_set_url="http://vocab.nerc.ac.uk/collection/T02/1/"
        )
        # return a list of just term values
        return [term["term"] for term in collection_terms]

    @property
    def created(self) -> str:
        _date = self.record.dates["creation"]
        return self._format_date(date_datetime=_date["value"], native_precision=_date["precision"])

    @property
    def data_type(self) -> str:
        return self.record.spatial_representation_type

    @property
    def downloads(self) -> List[Dict[str, str]]:
        downloads = []
        for transfer_option in self.record.transfer_options:
            downloads.append(self._process_download(transfer_option=transfer_option))
        return downloads

    @property
    def edition(self) -> str:
        return self.record.edition

    @property
    def geographic_extent(self) -> Dict:
        geographic_extent = self.record.geographic_extent
        geographic_extent["bounding_box_geojson"] = self._process_bounding_box_geojson(
            bounding_box=geographic_extent["bounding_box"]
        )
        return geographic_extent

    @property
    def identifier(self) -> str:
        return self.record.identifier

    @property
    def item_type(self) -> str:
        return self.record.hierarchy_level()

    @property
    def language(self) -> str:
        return self._format_language(language=self.record.language)

    @property
    def licence(self) -> dict:
        return self.record.usage_constraints["copyright_licence"]

    @property
    def lineage(self) -> str:
        return self.record.lineage

    @property
    def lineage_markdown(self) -> str:
        return markdown(self.lineage, output_format="html5")

    @property
    def location_keywords(self) -> List[dict]:
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
    def metadata_maintenance_progress(self) -> str:
        return str(self.record.metadata_maintenance_progress).capitalize()

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
    def metadata_standard_name(self) -> str:
        return self.record.metadata_standard_name

    @property
    def metadata_standard_version(self) -> str:
        return self.record.metadata_standard_version

    @property
    def metadata_updated(self) -> str:
        return self._format_date(date_datetime=self.record.metadata_updated, native_precision="day")

    @property
    def released(self) -> str:
        _date = self.record.dates["released"]
        return self._format_date(date_datetime=_date["value"], native_precision=_date["precision"])

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
    def published(self) -> str:
        _date = self.record.dates["publication"]
        return self._format_date(date_datetime=_date["value"], native_precision=_date["precision"])

    @property
    def publishers(self) -> List[str]:
        publishers = self.record.contacts["publisher"]
        _publishers = []
        for publisher in publishers:
            _publishers.append(self._format_organisation_name(organisation_name=publisher["organisation"]["name"]))
        return _publishers

    @property
    def temporal_extent(self) -> Dict[str, str]:
        return {
            "start": self._format_date(date_datetime=self.record.temporal_extent["start"], native_precision="day"),
            "end": self._format_date(date_datetime=self.record.temporal_extent["start"], native_precision="day"),
        }

    @property
    def spatial_reference_system(self) -> str:
        return self._format_spatial_reference_system(
            spatial_reference_system_code=self.record.spatial_reference_system["code"]
        )

    @property
    def spatial_reference_system_markdown(self) -> str:
        return markdown(self.spatial_reference_system, output_format="html5")

    @property
    def status(self) -> str:
        return self._process_status(
            maintenance_frequency=self.record.maintenance_frequency,
            released_date=self.record.dates["released"]["value"],
        )

    @property
    def theme_keywords(self) -> List[dict]:
        """
        Theme keywords (filtered)

        Theme keywords are currently used for two keyword sets that the catalogue treats differently:

        * BAS research topics - http://vocab.nerc.ac.uk/collection/T01/1/
        * Data catalogue collections - http://vocab.nerc.ac.uk/collection/T02/1/

        As these keyword sets are exposed through other Item properties (collections and topics respectively), they are
        filtered out from other theme keyword sets. Additionally, ISO Topics are filtered in as a theme keyword set.

        :rtype list
        :return: theme keyword sets, exc. BAS research topics and data catalogue collections, inc. ISO topics
        """
        theme_keywords = []
        excluded_keyword_sets = [
            "http://vocab.nerc.ac.uk/collection/T01/1/",
            "http://vocab.nerc.ac.uk/collection/T02/1/",
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
        return markdown(self.title, output_format="html5")

    @property
    def topics(self) -> List[str]:
        """
        Item's research topics

        Research topics are implemented as a descriptive keyword set using the NERC Vocabulary Service (T01).

        Currently only topic names to show as free text values are returned. In future, topic IDs will be returned to
        allow linking items to their collections.

        :rtype list
        :return: Topic names
        """
        topic_terms = self._filter_keyword_terms(
            keyword_sets=self.record.theme_keywords, keyword_set_url="http://vocab.nerc.ac.uk/collection/T01/1/"
        )
        # return a list of just term values
        return [term["term"] for term in topic_terms]

    @property
    def updated(self) -> str:
        _date = self.record.dates["revision"]
        return self._format_date(date_datetime=_date["value"], native_precision=_date["precision"])


class Collection:
    """
    Collections represent an unstructured set of Items that are somehow related. Collections are independent of other
    grouping mechanisms, such as descriptive keywords, dataset series and aggregations, publishers and/or any other
    common properties.

    Collections only exist within the data catalogue and can be used to relate any set of items together by including
    the relevant collection identifier as a descriptive keyword in Records (that underpin Items). Currently items in
    collections also need to be defined directly in the collection definitions file (`collections.json`).

    See the project README for Collection configurations properties.
    """

    def __init__(self, config: dict = None):
        self.config = {}
        if self.config is not None:
            self.config = config

    def __repr__(self):
        return f"<Collection / {self.identifier}>"

    @property
    def identifier(self) -> str:
        return self.config["identifier"]

    @property
    def title(self) -> str:
        return self.config["title"]

    @property
    def title_markdown(self) -> str:
        return markdown(self.title, output_format="html5")

    @property
    def topics(self) -> List[str]:
        return self.config["topics"]

    @property
    def publishers(self) -> List[str]:
        return self.config["publishers"]

    @property
    def summary(self) -> str:
        return self.config["summary"]

    @property
    def summary_markdown(self) -> str:
        return markdown(self.summary, output_format="html5")

    @property
    def item_identifiers(self) -> List[str]:
        return self.config["item_identifiers"]

    def load(self, collection_path: Path) -> None:
        """
        Loads a Collection from a file encoded using JSON

        :type collection_path Path
        :param collection_path: path to file containing JSON encoded record configuration
        """
        with open(str(collection_path)) as collection_file:
            self.config = json.load(collection_file)

    def dump(self, collection_path: Path, overwrite: bool = False) -> None:
        """
        Saves a Collection to a file encoded using JSON

        :type collection_path Path
        :param collection_path: desired path of file that will contain JSON encoded record configuration
        :type overwrite: bool
        :param overwrite: if the desired file already exists, whether to replace its contents
        """
        try:
            with open(str(collection_path), mode="x") as collection_file:
                json.dump(self.config, collection_file, indent=4)
        except FileExistsError:
            if not overwrite:
                raise FileExistsError()

            with open(str(collection_path), mode="w") as collection_file:
                json.dump(self.config, collection_file, indent=4)

    def dumps(self) -> Dict:
        """
        Return a collections configuration

        :rtype dict
        :return: collection configuration
        """
        return self.config


class Collections:
    """
    Represents a data store with an interface for creating, retrieving, updating and deleting Collections

    Collections use a file to encode a series of Collection configurations with methods to interact with this file and
    the configurations it contains.
    """

    def __init__(self, config: dict):
        """
        :type config dict
        :param config: Collections configuration, consisting of a single parameter for the path to a collections file
        """
        self.collections = {}
        self.collections_path = None
        if "collections_path" in config.keys():
            self.collections_path = config["collections_path"]

        try:
            with open(str(self.collections_path), mode="r") as collections_file:  # pragma: no cover
                collections_data = json.load(collections_file)
                for collection_config in collections_data.values():
                    self.add(collection=Collection(config=collection_config))
        except FileNotFoundError:  # pragma: no cover
            # Ignore because the collections file hasn't been setup yet
            pass

    def get_all(self) -> List[Collection]:
        """
        Retrieve all Collections

        :rtype list
        :return: all Collections
        """
        _collections = []
        for collection_identifier in self.collections.keys():
            _collections.append(self.get(collection_identifier=collection_identifier))
        return _collections

    def get(self, collection_identifier: str) -> Collection:
        """
        Retrieve specific Collection specified by its identifier

        :rtype Collection
        :return: specified Collection
        """
        try:
            return Collection(config=self.collections[collection_identifier])
        except KeyError:
            raise CollectionNotFoundException()

    def add(self, collection: Collection) -> None:
        """
        Create a new Collections

        :type collection Collection
        :param collection: Collection to create
        """
        if collection.identifier in self.collections.keys():
            raise CollectionInsertConflictException

        self.update(collection=collection)

    def update(self, collection: Collection) -> None:  # pragma: no cover (method mocked in testing)
        """
        Update an existing Collection

        :type collection Collection
        :param collection: Collection to update
        """
        self.collections[collection.identifier] = collection.dumps()

        with open(str(self.collections_path), mode="w") as collections_file:
            json.dump(self.collections, collections_file, indent=4)

    def delete(self, collection_identifier: str) -> None:  # pragma: no cover (method mocked in testing)
        """
        Delete a specific Collection specified by its identifier

        :rtype str
        :return: Collection identifier
        """
        del self.collections[collection_identifier]

        with open(str(self.collections_path), mode="w") as collections_file:
            json.dump(self.collections, collections_file, indent=4)
