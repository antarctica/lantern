import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import TypeVar

import cattrs

from lantern.lib.metadata_library.models.record import Record, clean_dict
from lantern.lib.metadata_library.models.record.summary import RecordSummary

TRecordRevision = TypeVar("TRecordRevision", bound="RecordRevision")
TRecordRevisionSummary = TypeVar("TRecordRevisionSummary", bound="RecordRevisionSummary")


@dataclass()
class RecordRevision(Record):
    """
    Representation of information about a resource at a given time within the BAS Data Catalogue / Metadata ecosystem.

    Records are low-level views of a resource using the ISO 19115 information model. Record Revisions represent a record
    at a specific point in time, when they had a particular configuration.

    Record Revisions are intended to be used as a drop-in replacement for `Record` in most cases, with the addition of
    a non-standard `file_revision` property holding an identifier for the revision.

    The structure and format of this identifier is intentionally not specified, beyond being a string. It is assumed
    and strongly recommended that these values are unique and relate to a version control system such as Git.
    """

    file_revision: str

    def __post_init__(self) -> None:
        """Post-initialisation checks."""
        if not self.file_revision:
            msg = "RecordRevision cannot be empty."
            raise ValueError(msg)

        super().__post_init__()

    @staticmethod
    def _config_supported(config: dict, logger: logging.Logger | None = None) -> bool:
        """
        Check if a record configuration is supported by this class.

        To ensure an accurate comparison, default/hard-coded values are added to a copy of the config before comparison.

        Set `logger` to enable optional logging of any unsupported content as a debug message.
        """
        record = RecordRevision.loads(config)
        return Record._check_supported(candidate=config, comparison=record.dumps(with_revision=True), logger=logger)

    @classmethod
    def structure(cls: type[TRecordRevision], value: dict) -> "RecordRevision":
        """
        Create a Record Revision instance from plain types.

        Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(RecordRevision, lambda d, t: RecordRevision.structure(d))`
        """
        value_ = deepcopy(value)
        cls._pre_structure(value_)  # from parent class
        converter = cls._converter_up()  # from parent class
        instance = converter.structure(value_, cls)
        instance.__post_init__()
        return instance

    def unstructure(self) -> dict:
        """
        Convert Record Revision to plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(RecordRevision, lambda d: d.unstructure())`
        """
        converter = self._converter_down()  # from parent class
        value = clean_dict(converter.unstructure(self))
        self._post_unstructure(value)  # from parent class
        return value

    @classmethod
    def loads(
        cls, value: dict, check_supported: bool = False, logger: logging.Logger | None = None
    ) -> "RecordRevision":
        """
        Create a Record Revision from a JSON schema instance and additional context.

        Where `value` is a dict representing a Record config, with an additional `file_revision` key for the revision.

        See the parent class for details on other parameters.
        """
        if "file_revision" not in value or not value["file_revision"]:
            msg = "RecordRevision cannot be empty."
            raise ValueError(msg)

        if check_supported:
            cls._config_supported(value, logger=logger)

        converter = cattrs.Converter()
        converter.register_structure_hook(RecordRevision, lambda d, t: cls.structure(d))
        return converter.structure(value, cls)

    def dumps(self, with_revision: bool = False) -> dict:
        """
        Export Record Revision as a dict with plain, JSON safe, types.

        `with_revision` False by default for compatibility `dumps_xml()`, `validate()`, etc. from parent class.
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(RecordRevision, lambda d: d.unstructure())
        data = converter.unstructure(self)

        if not with_revision:
            data.pop("file_revision", None)
        return data


@dataclass()
class RecordRevisionSummary(RecordSummary):
    """
    Summary of a resource at a given time within the BAS Data Catalogue / Metadata ecosystem.

    RecordSummaries are low-level views of key aspects of a resource, using the ISO 19115 information model. Record
    Revision Summaries represent a summary of a record at a specific point in time, when they had a particular
    configuration.

    As RecordSummaries are intended to be derived from Records, RecordRevisionSummaries are intended to be derived from
    RecordRevisions using `loads()`.
    """

    file_revision: str

    @classmethod
    def structure(cls: type[TRecordRevisionSummary], value: dict) -> "RecordRevisionSummary":
        """
        Create a RecordSummary instance from plain types.

        Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(RecordRevisionSummary, lambda d, t: RecordRevisionSummary.structure(d))`
        """
        value_ = deepcopy(value)
        converter = cls._converter_up()
        return converter.structure(value_, cls)

    def unstructure(self) -> dict:
        """
        Convert to plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(RecordRevisionSummary, lambda d: d.unstructure())`
        """
        converter = self._converter_down()
        return clean_dict(converter.unstructure(self))

    def dumps(self) -> dict:
        """Create a JSON safe dict."""
        converter = cattrs.Converter()
        converter.register_unstructure_hook(RecordRevisionSummary, lambda d: d.unstructure())
        return converter.unstructure(self)

    @classmethod
    def _loads_json_dict(cls: type[TRecordRevisionSummary], value: dict) -> "RecordRevisionSummary":
        """Create a RecordSummary from a config dict loaded from JSON."""
        converter = cattrs.Converter()
        converter.register_structure_hook(RecordRevisionSummary, lambda d, t: RecordRevisionSummary.structure(d))
        return converter.structure(value, cls)

    # noinspection DuplicatedCode
    @classmethod
    def _loads_record(cls: type[TRecordRevisionSummary], record: RecordRevision) -> "RecordRevisionSummary":
        """Create a RecordRevisionSummary from a Record."""
        return cls(
            file_revision=record.file_revision,
            file_identifier=record.file_identifier,
            hierarchy_level=record.hierarchy_level,
            date_stamp=record.metadata.date_stamp,
            title=record.identification.title,
            purpose=record.identification.purpose,
            edition=record.identification.edition,
            creation=record.identification.dates.creation,
            revision=record.identification.dates.revision,
            publication=record.identification.dates.publication,
            graphic_overviews=record.identification.graphic_overviews,
            constraints=record.identification.constraints,
            aggregations=record.identification.aggregations,
        )

    @classmethod
    def loads(cls: type[TRecordRevisionSummary], value: RecordRevision | dict) -> "RecordRevisionSummary":
        """Create a RecordRevisionSummary from a Record."""
        if isinstance(value, Record):
            return cls._loads_record(value)
        return cls._loads_json_dict(value)
