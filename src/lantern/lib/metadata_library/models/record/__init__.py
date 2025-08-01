import contextlib
import json
import logging
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from hashlib import sha1
from typing import TypeVar

import cattrs
from bas_metadata_library.standards.iso_19115_2 import MetadataRecord, MetadataRecordConfigV4
from bas_metadata_library.standards.iso_19115_common.utils import _decode_date_properties
from deepdiff import DeepDiff
from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from lantern.lib.metadata_library.models.record.elements.common import clean_dict
from lantern.lib.metadata_library.models.record.elements.data_quality import DataQuality
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution
from lantern.lib.metadata_library.models.record.elements.identification import Identification
from lantern.lib.metadata_library.models.record.elements.metadata import Metadata
from lantern.lib.metadata_library.models.record.elements.projection import ReferenceSystemInfo
from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode

TRecord = TypeVar("TRecord", bound="Record")


class RecordInvalidError(Exception):
    """Raised when a record has invalid content."""

    def __init__(self, validation_error: Exception) -> None:
        self.validation_error = validation_error


class RecordSchema(Enum):
    """Record validation schemas."""

    ISO_2_V4 = "iso_2_v4"
    MAGIC_V1 = "magic_discovery_v1"

    @staticmethod
    def map_href(href: str) -> "RecordSchema":
        """
        Map a schema href to a RecordSchema enum.

        Raises a KeyError if unsupported or unknown.
        """
        mapping = {
            "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json": RecordSchema.ISO_2_V4,
            "https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1/": RecordSchema.MAGIC_V1,
        }
        return mapping[href]

    @staticmethod
    def get_schema_contents(schema: "RecordSchema") -> dict:
        """
        Get contents of schema.

        Raises a KeyError if unsupported or unknown.
        """
        mapping = {
            RecordSchema.ISO_2_V4: (
                "bas_metadata_library.schemas.dist",
                "iso_19115_2_v4.json",
            ),
            RecordSchema.MAGIC_V1: (
                "bas_metadata_library.schemas.dist",
                "magic_discovery_v1.json",
            ),
        }
        schema_ref, schema_file = mapping[schema]
        with (
            resources_as_file(resources_files(schema_ref)) as resources_path,
            resources_path.joinpath(schema_file).open() as f,
        ):
            return json.load(f)


@dataclass(kw_only=True)
class Record:
    """
    Representation of a resource within the BAS Data Catalogue / Metadata ecosystem.

    Records are low-level view of a resource using the ISO 19115 information model. This class is an incomplete mapping
    of the BAS Metadata Library ISO 19115:2003 / 19115-2:2009 v4 configuration schema [1] to Python dataclasses, with
    code lists represented by Python enums. See [4]/[5] for (un)supported config elements.

    Complete record configurations can be loaded from a plain Python dict using `loads_schema()` and dumped back using
    `dumps_schema()`. This class cannot be used to load/dump from/to XML.

    Schema definition: resource [2]
    ISO element: gmd:MD_Metadata [3]

    [1] https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json
    [2] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1430
    [3] https://www.datypic.com/sc/niem21/e-gmd_MD_Metadata.html
    [4] Supported elements (not exhaustive):
        - `*.citation.title`
        - `*.citation.dates`
        - `*.citation.edition`
        - `*.citation.contacts` (except `contact.position`)
        - `*.citation.identifiers`
        - `*.citation.series` (with local workaround for `series.page`)

        - `$schema`
        - `file_identifier`
        - `hierarchy_level`
        - `metadata.character_set` (hard-coded)
        - `metadata.language` (hard-coded)
        - `metadata.contacts` (see `*.citation.contacts`)
        - `metadata.date_stamp`
        - `metadata.metadata_standard`
        - `reference_system_info`
        - `identification.title` (via `*.citation.title`)
        - `identification.dates` (via `*.citation.dates`)
        - `identification.edition` (via `*.citation.edition`)
        - `identification.identifiers` (via `*.citation.identifiers`)
        - `identification.contacts` (except `*.citation.contacts`)
        - `identification.abstract`
        - `identification.purpose`
        - `identification.other_citation_details`
        - `identification.supplemental_information`
        - `identification.constraints` (except permissions)
        - `identification.aggregations`
        - `identification.extents` (temporal and bounding box extents only)
        - `identification.graphic_overviews`
        - `identification.spatial_resolution`
        - `identification.maintenance`
        - `identification.character_set` (hard-coded)
        - `identification.language` (hard-coded)
        - `(identification.)data_quality.domain_consistency`
        - `(identification.)data_quality.lineage.statement`
        - `distribution.distributor`
        - `distribution.format` (`format` and `href` only)
        - `distribution.transfer_option`

    ? online resource ?

    [5] Unsupported elements (not exhaustive):
        - `*.contact.position`
        - `*.online_resource.protocol`
        - `(identification.)data_quality.lineage.process_step`
        - `(identification.)data_quality.lineage.sources`
        - `distribution.format` (except name and URL)
        - `identification.credit`
        - `identification.constraint.permissions`
        - `identification.extent.geographic.identifier`
        - `identification.extent.vertical`
        - `identification.keywords`
        - `identification.resource_formats`
        - `identification.spatial_representation_type`
        - `identification.status`
        - `identification.topics`
        - `metadata.maintenance` (identification only)
    """

    _schema: str = (
        "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json"
    )

    file_identifier: str | None = None
    hierarchy_level: HierarchyLevelCode
    metadata: Metadata
    reference_system_info: ReferenceSystemInfo | None = None
    identification: Identification
    data_quality: DataQuality | None = None
    distribution: list[Distribution] | None = None

    def __post_init__(self) -> None:
        """Process defaults."""
        if self.distribution is None:
            self.distribution = []

    @property
    def sha1(self) -> str:
        """SHA1 hash of Record configuration."""
        return sha1(json.dumps(self.dumps(), indent=0, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()  # noqa: S324

    @staticmethod
    def _normalise_static_config_values(value: dict) -> dict:
        """Adjust properties that will be set by default within a Record to allow for accurate config comparisons."""
        normalised = deepcopy(value)

        normalised["metadata"]["character_set"] = "utf8"
        normalised["metadata"]["language"] = "eng"
        normalised["metadata"]["metadata_standard"] = {
            "name": "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data",
            "version": "ISO 19115-2:2009(E)",
        }
        if "maintenance" in normalised["metadata"]:
            del normalised["metadata"]["maintenance"]

        normalised["identification"]["character_set"] = "utf8"
        normalised["identification"]["language"] = "eng"

        if "$schema" in normalised and normalised["$schema"] == Record._schema:
            del normalised["$schema"]

        return normalised

    @staticmethod
    def _config_supported(config: dict, logger: logging.Logger | None = None) -> bool:
        """
        Check if a record configuration is supported by this class.

        To ensure an accurate comparison, default/hard-coded values are added to a copy of the config before comparison.

        Set `logger` to enable optional logging of any unsupported content as a debug message.
        """
        record = Record.loads(config)
        check = record.dumps()
        normalised = Record._normalise_static_config_values(config)
        supported = normalised == check
        if logger and not supported:
            logger.warning(
                f"Record '{config.get('file_identifier')}' contains unsupported content that will be ignored."
            )
            diff = DeepDiff(check, normalised, verbose_level=2)
            logger.debug(diff.pretty(prefix="Diff: "))
        return supported

    @staticmethod
    def _move_dq_elements(value: dict) -> dict:
        """
        Move any data quality elements out of identification until v5 schema available.

        See https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-library/-/issues/255.
        """
        dq = {}
        if (
            "identification" in value
            and "lineage" in value["identification"]
            and "statement" in value["identification"]["lineage"]
        ):
            dq["lineage"] = value["identification"]["lineage"]
        if "identification" in value and "domain_consistency" in value["identification"]:
            dq["domain_consistency"] = value["identification"]["domain_consistency"]
        if dq:
            value["data_quality"] = dq
        return value

    @classmethod
    def structure(cls: type[TRecord], value: dict) -> "Record":
        """
        Create a Record instance from plain types.

        Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(Record, lambda d, t: Record.structure(d))`
        """
        value_ = deepcopy(value)

        # move any data quality elements out of identification
        # https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-library/-/issues/255
        value_ = cls._move_dq_elements(value_)

        converter = cattrs.Converter()
        converter.register_structure_hook(Metadata, lambda d, t: Metadata.structure(d))
        converter.register_structure_hook(ReferenceSystemInfo, lambda d, t: ReferenceSystemInfo.structure(d))
        converter.register_structure_hook(Identification, lambda d, t: Identification.structure(d))
        converter.register_structure_hook(DataQuality, lambda d, t: DataQuality.structure(d))
        return converter.structure(value_, cls)

    def unstructure(self) -> dict:
        """
        Convert Record to plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(Record, lambda d: d.unstructure())`
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Metadata, lambda d: d.unstructure())
        converter.register_unstructure_hook(ReferenceSystemInfo, lambda d: d.unstructure())
        converter.register_unstructure_hook(Identification, lambda d: d.unstructure())
        converter.register_unstructure_hook(DataQuality, lambda d: d.unstructure())
        value = clean_dict(converter.unstructure(self))

        # move data quality elements into identification until v5 schema available
        # https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-library/-/issues/255
        if "data_quality" in value:
            value["identification"] = {**value["identification"], **value["data_quality"]}
            del value["data_quality"]

        # remove internal keys (ensuring order)
        value.pop("_schema", None)

        return value

    @classmethod
    def loads(cls, value: dict, check_supported: bool = False, logger: logging.Logger | None = None) -> "Record":
        """
        Create a Record from a JSON schema instance.

        Set `check_supported` to True to check the configuration is fully supported by this class.
        Set `logger` to enable optional logging of any unsupported content as a debug message.
        """
        if check_supported:
            cls._config_supported(value, logger=logger)

        converter = cattrs.Converter()
        converter.register_structure_hook(Record, lambda d, t: Record.structure(d))
        return converter.structure(value, cls)

    def dumps(self) -> dict:
        """Export Record as a dict with plain, JSON safe, types."""
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Record, lambda d: d.unstructure())
        return converter.unstructure(self)

    def dumps_json(self) -> str:
        """Export Record as JSON Schema instance string."""
        return json.dumps({"$schema": self._schema, **self.dumps()}, indent=2, ensure_ascii=False)

    def dumps_xml(self) -> str:
        """Export Record as an ISO 19115 XML document using the BAS Metadata Library."""
        config = MetadataRecordConfigV4(**_decode_date_properties(self.dumps()))
        record = MetadataRecord(configuration=config)
        return record.generate_xml_document().decode()

    @property
    def _profile_schemas(self) -> list[RecordSchema]:
        """Load any supported validation schemas based on any domain consistency elements within the Record."""
        if self.data_quality is None:
            return []

        schemas = []
        for dc in self.data_quality.domain_consistency:
            with contextlib.suppress(KeyError):
                schemas.append(RecordSchema.map_href(dc.specification.href))

        return schemas

    def _get_validation_schemas(
        self, use_profiles: bool = True, force_schemas: list[RecordSchema] | None = None
    ) -> list[dict]:
        """Get contents of selected validation schemas."""
        selected_schemas = [RecordSchema.ISO_2_V4]
        if use_profiles:
            selected_schemas.extend(self._profile_schemas)
        if force_schemas is not None:
            selected_schemas = force_schemas

        return [RecordSchema.get_schema_contents(schema) for schema in selected_schemas]

    def validate(self, use_profiles: bool = True, force_schemas: list[RecordSchema] | None = None) -> None:
        """
        Validate Record against JSON Schemas.

        By default, records are validated against the BAS Metadata Library ISO 19115:2003 / 19115-2:2009 v4 schema,
        plus schemas matched from any domain consistency elements. Set `use_profiles = False`to disable.

        Use `force_schemas` to select specific schemas to validate against.

        Any failed validation will raise a `RecordInvalidError` exception.
        """
        config = {"$schema": self._schema, **self.dumps()}
        schemas = self._get_validation_schemas(use_profiles=use_profiles, force_schemas=force_schemas)

        for schema in schemas:
            try:
                validate(instance=config, schema=schema)
            except ValidationError as e:
                raise RecordInvalidError(e) from e
