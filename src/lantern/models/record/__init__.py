import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import TypeVar

import cattrs

from lantern.lib.metadata_library.models.record import Record as RecordBase

TRecord = TypeVar("TRecord", bound="Record")


@dataclass(kw_only=True)
class Record(RecordBase):
    """
    Representation of a resource within the BAS Data Catalogue specifically.

    Catalogue records extend the base ISO 19115 Record class, requiring the `file_identifier` property.
    """

    file_identifier: str

    def __post_init__(self) -> None:
        """Validate properties."""
        super().__post_init__()
        if self.file_identifier is None:
            msg = "Records require a file_identifier."
            raise ValueError(msg)

    @classmethod
    def structure(cls: type[TRecord], value: dict) -> "Record":
        """
        Create a Record instance from plain types.

        Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(Record, lambda d, t: Record.structure(d))`
        """
        value_ = deepcopy(value)
        cls._pre_structure(value_)  # from parent class
        converter = cls._converter_up()  # from parent class
        instance = converter.structure(value_, cls)

        # workaround where file_identifier is None which cattrs casts to a string as 'None'
        if instance.file_identifier == "None" and value.get("file_identifier") is None:
            # noinspection PyTypeChecker
            instance.file_identifier = None

        instance.__post_init__()
        return instance

    @classmethod
    def loads(cls, value: dict, check_supported: bool = False, logger: logging.Logger | None = None) -> "Record":
        """
        Create a Record from a JSON schema instance and additional context.

        Where `value` is a dict representing a Record config, with an additional `file_revision` key for the revision.

        See the parent class for details on other parameters.
        """
        if check_supported:
            cls._config_supported(value, logger=logger)

        converter = cattrs.Converter()
        converter.register_structure_hook(Record, lambda d, t: cls.structure(d))
        return converter.structure(value, cls)
