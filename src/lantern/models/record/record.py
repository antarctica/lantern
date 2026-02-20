import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import TypeVar
from uuid import UUID

import cattrs

from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, HierarchyLevelCode
from lantern.lib.metadata_library.models.record.record import Record as RecordBase
from lantern.lib.metadata_library.models.record.record import RecordInvalidError, RecordSchema
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE

TRecord = TypeVar("TRecord", bound="Record")


@dataclass(kw_only=True)
class Record(RecordBase):
    """
    Representation of a resource within the BAS Data Catalogue specifically.

    Catalogue records extend the base ISO 19115 Record class, requiring the `file_identifier` property.
    """

    file_identifier: str

    def __post_init__(self) -> None:
        """
        Validate properties.

        File identifier is checked for here (that it exists) and in validation (that it's a UUID).
        """
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

    def _validate_file_identifier(self) -> None:
        """Verify resource file identifier."""
        try:
            UUID(self.file_identifier)
        except ValueError:
            if self.file_identifier == "x":
                # workaround for app tests
                return

            msg = f"Invalid file identifier '{self.file_identifier}' must be a UUID."
            exp = ValueError(msg)
            raise RecordInvalidError(validation_error=exp) from None

    def _validate_identifiers(self) -> None:
        """Verify non file identifier resource identifier."""
        try:
            identifier = self.identification.identifiers.filter(CATALOGUE_NAMESPACE)[0]
        except IndexError as e:
            msg = "No resource identifier with catalogue namespace."
            raise RecordInvalidError(validation_error=ValueError(msg)) from e
        if identifier.identifier != self.file_identifier:
            msg = "Invalid identifier value in Catalogue resource identifier."
            raise RecordInvalidError(validation_error=ValueError(msg)) from None
        if identifier.href != f"https://data.bas.ac.uk/items/{self.file_identifier}":
            msg = "Invalid href in Catalogue resource identifier."
            raise RecordInvalidError(validation_error=ValueError(msg)) from None

    def _validate_poc(self) -> None:
        """Verify record resource point of contact."""
        pocs = self.identification.contacts.filter(roles=ContactRoleCode.POINT_OF_CONTACT)
        if not pocs:
            msg = "No resource contact with Point of Contact role."
            exp = ValueError(msg)
            raise RecordInvalidError(validation_error=exp)

    def _validate_extents(self) -> None:
        """Verify record extents."""
        extent_ids = []
        for extent in self.identification.extents:
            if extent.identifier in extent_ids:
                msg = f"Duplicate extent identifier '{extent.identifier}', must be unique."
                exp = ValueError(msg)
                raise RecordInvalidError(validation_error=exp)
            extent_ids.append(extent.identifier)

    def _validate_aliases(self) -> None:
        """Verify record alias values."""
        product_prefixes = ["products", "maps"]
        prefixes = {
            HierarchyLevelCode.COLLECTION: ["collections"],
            HierarchyLevelCode.DATASET: ["datasets"],
            HierarchyLevelCode.INITIATIVE: ["projects"],
            HierarchyLevelCode.PRODUCT: product_prefixes,
            HierarchyLevelCode.PAPER_MAP_PRODUCT: product_prefixes,
        }

        for alias in self.identification.identifiers.filter(ALIAS_NAMESPACE):
            expected = f"https://data.bas.ac.uk/{alias.identifier}"
            if alias.href != expected:
                msg = f"Invalid alias href '{alias.href}' must be '{expected}'."
                exp = ValueError(msg)
                raise RecordInvalidError(validation_error=exp)

            if len(alias.identifier.split("/")) > 2:
                msg = f"Invalid alias identifier '{alias.identifier}' must not contain additional '/' values."
                exp = ValueError(msg)
                raise RecordInvalidError(validation_error=exp)

            if alias.identifier.split("/")[0] not in prefixes.get(self.hierarchy_level, []):
                msg = f"Invalid prefix in alias identifier '{alias.identifier}' for hierarchy level."
                exp = ValueError(msg)
                raise RecordInvalidError(validation_error=exp)

            try:
                UUID(alias.identifier.split("/")[-1])
                msg = f"Invalid alias identifier '{alias.identifier}' must not contain a UUID."
                exp = ValueError(msg)
                raise RecordInvalidError(validation_error=exp)
            except ValueError:
                pass

    def validate(self, use_profiles: bool = True, force_schemas: list[RecordSchema] | None = None) -> None:
        """
        Verify records against Catalogue specific requirements.

        Raises `RecordInvalidError` exception if invalid.

        Checks that records:
        - file identifier is a UUID
        - include an identifier with the catalogue namespace and file_identifier value
        - include a contact with the 'Point of Contact' role
        - use unique extent identifiers if included
        - don't use UUIDs as aliases, and/or include additional `/` values

        See docs/data_model.md#record-validation for more information.
        """
        super().validate(use_profiles, force_schemas)
        self._validate_file_identifier()
        self._validate_identifiers()
        self._validate_poc()
        self._validate_extents()
        self._validate_aliases()
