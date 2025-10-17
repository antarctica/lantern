import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import TypeVar

import cattrs

from lantern.lib.metadata_library.models.record.utils.clean import clean_dict
from lantern.models.record.record import Record

TRecordRevision = TypeVar("TRecordRevision", bound="RecordRevision")


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
        super().__post_init__()

        if not self.file_revision:
            msg = "Record Revisions require a file_revision."
            raise ValueError(msg)

    @staticmethod
    def _config_supported(config: dict, logger: logging.Logger | None = None) -> bool:
        """
        Check if a record configuration is supported by this class.

        To ensure an accurate comparison, default/hard-coded values are added to a copy of the config before comparison.

        Set `logger` to enable optional logging of any unsupported content as a debug message.
        """
        record = RecordRevision.loads(config)
        return Record._eq(
            candidate=config, comparison=record.dumps(strip_admin=False, with_revision=True), logger=logger
        )

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
        if check_supported:
            cls._config_supported(value, logger=logger)

        converter = cattrs.Converter()
        converter.register_structure_hook(RecordRevision, lambda d, t: cls.structure(d))
        return converter.structure(value, cls)

    def dumps(self, strip_admin: bool = True, with_revision: bool = False) -> dict:
        """
        Export Record Revision as a dict with plain, JSON safe, types.

        If `strip_admin` is true, any administrative metadata instance included in the record is removed.
        `with_revision` is false by default for compatibility `dumps_xml()`, `validate()`, etc. from parent class.
        """
        if strip_admin:
            self.strip_admin_metadata()

        converter = cattrs.Converter()
        converter.register_unstructure_hook(RecordRevision, lambda d: d.unstructure())
        data = converter.unstructure(self)

        if not with_revision:
            data.pop("file_revision", None)
        return data
