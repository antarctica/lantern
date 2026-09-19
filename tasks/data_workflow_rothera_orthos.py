# Automatically process Rothera progress monitoring orthomosaics

import csv
import json
import subprocess
from argparse import ArgumentParser
from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from enum import Enum
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import inquirer
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from inquirer import Path as InquirerPath
from rich.console import Console
from rich.progress_bar import ProgressBar
from rich.table import Table
from tasks._shared import dump_records, init, init_s3
from tasks.artefacts_deposit import get_permissions
from tasks.record_supersede import process_predecessor, process_successor
from tasks.records_zap import revise_collection

from lantern.exporters.s3 import S3Exporter
from lantern.lib.magic_distribution.client import MagicResourceDistributionClient
from lantern.lib.magic_distribution.formats import ArtefactFormatLabel, ArtefactFormats
from lantern.lib.magic_distribution.models.artefact import (
    ArtefactLocalFile,
    ArtefactSharePointFile,
)
from lantern.lib.metadata_library.models.record.elements.common import (
    Constraints,
    Date,
    Dates,
    OnlineResource,
)
from lantern.lib.metadata_library.models.record.elements.data_quality import Lineage
from lantern.lib.metadata_library.models.record.elements.distribution import (
    Distribution,
    Size,
    TransferOption,
)
from lantern.lib.metadata_library.models.record.elements.identification import (
    Extent,
    Extents,
    GraphicOverview,
    GraphicOverviews,
    Identification,
)
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    ContactRoleCode,
    HierarchyLevelCode,
    OnlineResourceFunctionCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import (
    BAS_STAFF as BAS_STAFF_PERMISSION,
)
from lantern.lib.metadata_library.models.record.presets.admin import (
    OPEN_ACCESS as OPEN_ACCESS_PERMISSION,
)
from lantern.lib.metadata_library.models.record.presets.aggregations import (
    make_bas_cat_collection_member,
    make_in_bas_cat_collection,
)
from lantern.lib.metadata_library.models.record.presets.base import RecordMagic
from lantern.lib.metadata_library.models.record.presets.constraints import BAS_STAFF, MAGIC_PRODUCTS_V1
from lantern.lib.metadata_library.models.record.presets.contacts import MICROSOFT_DISTRIBUTOR, make_bas_role
from lantern.lib.metadata_library.models.record.presets.extents import make_bbox_extent, make_temporal_extent
from lantern.lib.metadata_library.models.record.record import RecordInvalidError

if TYPE_CHECKING:
    import logging
    from collections.abc import Iterator

    from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys

    from lantern.catalogues.bas import BasCatalogue
    from lantern.models.record.record import Record


@dataclass
class EventManifest:
    """
    Properties of an image product specific to this workflow (termed an event), as initially loaded from a CSV manifest.

    Defines properties that can't be derived from input files.
    """

    file_identifier: str
    acquisition_date: date
    cde_ref_geotiff: str | None
    cde_ref_jpeg: str | None


@dataclass
class EventProcessed(EventManifest):
    """Extended event properties to include generated/existing image file paths."""

    geotiff_path: Path
    geotiff_bbox: tuple[float, float, float, float]  # min_x,, max_x,, min_y, max_y
    jpeg_path: Path
    thumbnail_path: Path


@dataclass
class EventRecord(EventProcessed):
    """Extended event properties to include generated record."""

    record: RecordEvent


@dataclass
class EventDeposited(EventRecord):
    """Extended event properties to include deposited file artefacts."""

    geotiff_file_artefact: ArtefactSharePointFile
    jpeg_file_artefact: ArtefactSharePointFile
    thumbnail_file_url: str


@dataclass
class EventProvisioned(EventDeposited):
    """Extended event properties to include provisioned service artefacts."""

    source_service_url: str


@dataclass
class EventFinished(EventProvisioned):
    """
    EventProvisioned subclass to indicate a finished metadata record.

    This progress indication use is implicit with other Event subclasses but for thi stage there aren't any additional
    properties that need adding.
    """


class EventStage(Enum):
    """Event processing stages."""

    NOT_INITIALISED = "not initialised"
    MANIFEST = "in manifest"
    PROCESSED = "images processed"
    RECORD = "record generated"
    DEPOSITED = "files deposited"
    PROVISIONED = "services provisioned"
    FINISHED = "record finished"


class RecordEvent(RecordMagic):
    """
    Records representing drone image events.

    Extends a base MAGIC record with hard-coded and templated properties specific to this workflow.

    Extends RecordMagic to:
    - set resource access constraints and permissions to BAS Staff
    - set resource usage constraints to MAGIC Products local licence
    - set the title, purpose and abstract to templated values using the event acquisition date
    - set the lineage statement to a static template
    - set the edition to a simple static value
    - set the creation date to the event acquisition date (which is not strictly correct)
    - set the publication and released dates to now (which is not ideal as they will move forwards when regenerated)
    - add an author for the Engineering team
    - add the record to the relevant parent collection
    - add a bounding extent based on the event source image georeferencing and event acquisition date
    """

    def __init__(
        self,
        admin_keys: AdministrationKeys,
        now: datetime,
        event: EventProcessed,
        collection_id: str,
        edition_count: int,
    ) -> None:
        _title = f"Rothera Station Orthomosaic {event.acquisition_date.isoformat()}"
        _purpose = f"Orthomosaic of Rothera Station, derived from UAV imagery captured {self._date_fmt(event.acquisition_date)}."
        _abstract = dedent("""\
            Orthomosaic of Rothera Station derived from UAV imagery acquired by the BAS Engineering Team for site progress recording and general visual reference.

            > [!WARNING]
            > This item is not a survey-grade output and has known positional accuracy limitations.

            Further details on acquisition, processing, data quality and restrictions on use are provided in the [Lineage](#tab-lineage).
         """)
        _lineage = "The orthomosaic was generated from UAV imagery captured by the BAS Engineering Team at Rothera Research Station.\n\n### Instrumentation\n\nUAV model:\n\n* DJI Mavic 3 Enterprise\n\nCamera specification:\n\n* Sensor: 4/3 CMOS, 20 MP effective pixels\n* Lens field of view: 84°\n* Equivalent focal length: 24mm\n* Aperture: f/2.8-f/11\n* Focus range: 1m to infinity\n* ISO range: 100-6400\n* Electronic shutter speed: 8-1/8000s\n* Mechanical shutter speed: 8-1/2000s\n* Maximum image size: 5280x3956 pixels\n\n### Data processing and accuracy\n\nThe orthomosaic was produced through photogrammetric processing of the UAV imagery and exported in the UTM Zone 19S coordinate system.\n\nNo surveyed Ground Control Points were used during the processing. The dataset was therefore georeferenced using the UAV's internal positional information only.\n\nNo independent accuracy assessment was undertaken; therefore, the positional accuracy of the dataset has not been independently verified. As the imagery was not acquired or processed for accurate mapping or survey purposes, no Ground Sampling Distance (GSD) has been specified, and no photogrammetric processing or accuracy report is available for this item.\n\n> [!WARNING]\n> This orthomosaic is intended for visual reference, site awareness, and general progress-record purposes only.\n>\n> It should not be used for precise measurement, setting out, design verification, engineering assessment, asset positioning, boundary definition, or any other survey-grade application."
        _edition = self._calver_edition(event.acquisition_date, count=edition_count)

        # ISO minimum properties need to be set on init (plus edition for the automatic citation)
        # creation date is not set as it's not known (it isn't necessarily the acquisition date)
        super().__init__(
            file_identifier=event.file_identifier,
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            identification=Identification(
                title=_title,
                purpose=_purpose,
                abstract=_abstract,
                dates=Dates(publication=Date(date=now), released=Date(date=now)),
                edition=_edition,
            ),
            admin_keys=admin_keys,
            admin_meta=AdministrationMetadata(
                id=event.file_identifier,
                metadata_permissions=[OPEN_ACCESS_PERMISSION],
                resource_permissions=[BAS_STAFF_PERMISSION],
            ),
        )

        self.identification.contacts.ensure(make_bas_role(roles={ContactRoleCode.AUTHOR}, team_name="Engineering Team"))
        self.identification.constraints = Constraints([BAS_STAFF, MAGIC_PRODUCTS_V1])
        self.identification.aggregations.ensure(make_in_bas_cat_collection(collection_id=collection_id))
        self.identification.extents = Extents(
            [
                Extent(
                    identifier="bounding",
                    geographic=make_bbox_extent(*event.geotiff_bbox),
                    temporal=make_temporal_extent(start=event.acquisition_date, end=event.acquisition_date),
                )
            ]
        )
        self.data_quality.lineage = Lineage(statement=_lineage)

    @staticmethod
    def _date_fmt(d: date) -> str:
        """
        Formatted date.

        E.g. '2026-04-04' becomes '4th April 2026'.
        """
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(d.day % 20, "th")
        return f"{d.day}{suffix} {d.strftime('%B %Y')}"

    @staticmethod
    def _calver_edition(d: date, count: int = 1, revision: int = 0) -> str:
        """
        CalVer edition (year/month), plus a cumulative resource count within the month and optional resource revision.

        Intended for resources released roughly (but not exclusively) monthly, that may (but probably won't) be revised.

        E.g.:
        - the initial revision of the first resource within April 2014 would become: '2014-4.1'
        - subsequent revisions of the same resource would be: '2014-4.1 (1)', '2014-4.1 (2)', '2014-4.1 (3)', etc.
        - the third revision of a second resource for the same month would be: '2014-4.2 (2)'

        I.e.:
        - the monthly resource count counts from 1 and is always present
        - The revision for a resource starts at 0 (no revision) and only shown above 0 (the first revision)

        Note this method does not calculate the per-month resource count or per-resource revision count.

        https://calver.org
        """
        base = f"{d.year}.{d.month}.{count}"
        return f"{base} ({revision})" if revision > 0 else base


# Generic helper methods


def _iter_coordinate_pairs(value: object) -> Iterator[tuple[float, float]]:
    """
    Yield longitude/latitude pairs from nested GeoJSON coordinates.

    Intended for generating bboxes from GeoTIFF images.
    """
    if isinstance(value, list):
        if len(value) >= 2 and isinstance(value[0], int | float) and isinstance(value[1], int | float):  # noqa: PLR2004
            yield float(value[0]), float(value[1])
        else:
            for child in value:
                yield from _iter_coordinate_pairs(child)


def _get_geotiff_bbox(logger: logging.Logger, source_path: Path) -> tuple[float, float, float, float]:
    """
    Get bounding box from a GeoTIFF image.

    Returned in the form: min_x, max_x, min_y, max_y.

    Coordinates are returned in the GeoTIFF's native coordinate reference system, not necessarily WGS84.
    """
    logger.info("Getting bbox for: %s", str(source_path.resolve()))

    info_result = subprocess.run(  # noqa: S603
        [
            "gdalinfo",
            "-json",
            "--config",
            "GDAL_DISABLE_READDIR_ON_OPEN",
            "YES",
            str(source_path.resolve()),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if info_result.returncode != 0:
        logger.error("`gdalinfo` failed: %s", info_result.stderr.strip())
        raise RuntimeError() from None

    try:
        info = json.loads(info_result.stdout)
        wgs84_extent = info["wgs84Extent"]
        coordinate_pairs = list(_iter_coordinate_pairs(wgs84_extent["coordinates"]))
    except (KeyError, TypeError, json.JSONDecodeError) as e:
        logger.exception("Could not parse WGS84 extent from `gdalinfo`: %s", exc_info=e)
        raise RuntimeError() from e

    if not coordinate_pairs:
        logger.error("`gdalinfo` returned an empty WGS84 extent")
        raise RuntimeError() from None

    longitudes = [longitude for longitude, _ in coordinate_pairs]
    latitudes = [latitude for _, latitude in coordinate_pairs]
    return (
        min(longitudes),
        max(longitudes),
        min(latitudes),
        max(latitudes),
    )


# Workflow helper methods


def _ensure_external_overviews(logger: logging.Logger, source_path: Path) -> None:
    """
    Ensure a GeoTIFF image has external overviews, replacing any internal overviews if necessary.

    `gdalinfo` supports showing if a GeoTIFF contains overviews but does not indicate whether they are internal or
    external (via a .ovr` file). The `GDAL_DISABLE_READDIR_ON_OPEN` option should (but doesn't) limit reading to the
    current file (and so exclude external overviews) but doesn't in practice (using 3.13.3 on macOS at least).

    To work around this, an external overviews file is first renamed if it exists, then checked and restored.
    """
    logger.info("Ensuring overviews for: %s", str(source_path.resolve()))

    overviews_file = source_path.with_name(source_path.name + ".ovr")
    not_overviews_file = overviews_file.with_suffix(".x")
    logger.debug("Potential overviews file: %s", str(overviews_file.resolve()))

    # avoid `gdalinfo` checking external overviews
    if overviews_file.exists():
        logger.info("Renaming external overviews file to ensure accurate internal overviews check")
        overviews_file.replace(not_overviews_file)

    # ensure internal overviews don't exist
    info_result = subprocess.run(  # noqa: S603
        ["gdalinfo", "--config", "GDAL_DISABLE_READDIR_ON_OPEN", "YES", str(source_path.resolve())],
        capture_output=True,
        text=True,
        check=False,
    )
    if not_overviews_file.exists():
        # ensure external overviews are restored, even if `gdalinfo` returns an error
        logger.info("Restoring external overviews file following internal overviews check")
        not_overviews_file.replace(overviews_file)
    if info_result.returncode != 0:
        logger.error("`gdalinfo` failed: %s", info_result.stderr.strip())
        raise RuntimeError() from None

    if "Overview" in info_result.stdout:
        logger.warning("Removing internal overviews to prevent incompatibility with ArcGIS Server.")
        clean_result = subprocess.run(  # noqa: S603
            ["gdaladdo", "-clean", str(source_path.resolve())],
            capture_output=True,
            text=True,
            check=False,
        )
        if clean_result.returncode != 0:
            logger.error("`gdaladdo` failed: %s", clean_result.stderr.strip())
            raise RuntimeError() from None

    # ensure external overviews exist
    if overviews_file.exists():
        logger.info("External overviews already exist")
        return

    # `-ro` opens the dataset read-only, which forces `gdaladdo` to write overviews to a .ovr file.
    build_result = subprocess.run(  # noqa: S603
        ["gdaladdo", "-ro", "-r", "average", str(source_path.resolve()), "2", "4", "8", "16", "32"],
        capture_output=True,
        text=True,
        check=False,
    )
    if build_result.returncode != 0:
        logger.error("`gdaladdo` failed: %s", build_result.stderr.strip())
        raise RuntimeError() from None


def _ensure_jpeg_image(logger: logging.Logger, source_path: Path) -> Path:
    """Convert GeoTIFF to JPEG."""
    jpeg_path = source_path.with_suffix(".jpg")
    logger.info("Checking for JPEG image at: %s", jpeg_path.resolve())
    if jpeg_path.exists():
        if ArtefactFormats.get_file_format(jpeg_path).label != ArtefactFormatLabel.JPEG:
            logger.error("JPEG image exists but is not a recognised JPEG.")
            raise RuntimeError() from None

        logger.info("JPEG image exists: %s", jpeg_path.resolve())
        return jpeg_path

    logger.info("Converting '%s' to '%s'.", source_path, jpeg_path)
    translate_result = subprocess.run(  # noqa: S603
        [
            "gdal_translate",
            "-of",
            "JPEG",
            "-co",
            "QUALITY=95",
            "--config",
            "GDAL_PAM_ENABLED=NO",
            str(source_path.resolve()),
            str(jpeg_path.resolve()),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if translate_result.returncode != 0:
        logger.error("`gdal_translate` failed: %s", translate_result.stderr.strip())
        raise RuntimeError() from None

    return jpeg_path


def _ensure_thumbnail_image(logger: logging.Logger, source_path: Path) -> Path:
    """Generate thumbnail overview image from larger JPEG."""
    target_size = 300_000  # 300kb
    target_path = source_path.parent / "overview.jpg"

    logger.info("Checking for thumbnail image at: %s", target_path.resolve())
    if target_path.exists():
        if ArtefactFormats.get_file_format(target_path).label != ArtefactFormatLabel.JPEG:
            logger.error("Thumbnail image exists but is not a recognised JPEG.")
            raise RuntimeError() from None

        logger.info("Thumbnail image exists: %s", target_path.resolve())
        return target_path

    logger.info("Downsampling '%s' to '%s'.", source_path, target_path)

    info_result = subprocess.run(  # noqa: S603
        ["gdalinfo", "-json", str(source_path.resolve())],
        capture_output=True,
        text=True,
        check=False,
    )
    if info_result.returncode != 0:
        logger.error("`gdal_info` failed: %s", info_result.stderr.strip())
        raise RuntimeError() from None
    try:
        info = json.loads(info_result.stdout)
        source_width, source_height = info["size"]
    except (KeyError, json.JSONDecodeError) as e:
        logger.exception("Could not get source JPEG dimensions", exc_info=e)
        raise RuntimeError() from e

    # Estimate target dimensions where JPEG size is approximately proportional to pixel count
    source_size_bytes = source_path.stat().st_size
    scale = ((target_size / source_size_bytes) ** 0.5) * 0.9  # safety factor
    target_width = max(1, round(source_width * scale))
    target_height = max(1, round(source_height * scale))

    translate_result = subprocess.run(  # noqa: S603
        [
            "gdal_translate",
            "-q",
            "-of",
            "JPEG",
            "-r",
            "bilinear",
            "-outsize",
            str(target_width),
            str(target_height),
            "-co",
            "QUALITY=50",
            "--config",
            "GDAL_PAM_ENABLED=NO",
            str(source_path.resolve()),
            str(target_path.resolve()),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if translate_result.returncode != 0:
        logger.error("`gdal_translate` failed: %s", translate_result.stderr.strip())
        raise RuntimeError() from None

    result_size = target_path.stat().st_size
    if result_size > target_size:
        logger.warning("Downsampled thumbnail image above target size (%s vs %s target)", result_size, target_size)
        raise RuntimeWarning() from None

    return target_path


def _supersede_records(logger: logging.Logger, events: list[EventProvisioned]) -> None:
    """
    Set successor and predecessor resource for each event within records.

    E.g.: or three events [('A', 2014-04-01), ('B',2024-02-01), ('C',2014-05-01)] (deliberately processed out of order):
    - event A is succeeded by C (when sorted by date from earliest to latest)
    - event B succeeds C
    - event C succeeds 1 and is succeeded by B

    I.e. A -> C -> B, or:
    - neighbours: list[tuple[str | None, str, str | None]] = [(None, "A", "C"), ("C", "B", None), ("A", "C", "B")]
    - where each neighbour gives predecessor, subject, successor

    Predecessor resources are indicated by `revisionOf` aggregations. Successor resources are indicated by an inline
    note within the abstract (as there isn't a 'isRevisedBy' or similar aggregation association).
    """
    logger.info("Determining succession order for %s events", len(events))

    ordered_events = sorted(events, key=lambda event: event.acquisition_date)
    neighbours: list[tuple[EventProvisioned | None, EventProvisioned, EventProvisioned | None]] = [
        (
            ordered_events[index - 1] if index > 0 else None,
            event,
            ordered_events[index + 1] if index + 1 < len(ordered_events) else None,
        )
        for index, event in enumerate(ordered_events)
    ]
    for predecessor, subject, successor in neighbours:
        logger.debug(
            "%s is preceded by %s and followed by %s",
            subject.file_identifier,
            predecessor.file_identifier if predecessor else "Nothing",
            successor.file_identifier if successor else "Nothing",
        )
        if predecessor:
            process_predecessor(logger=logger, record=predecessor.record, successor=subject.record, replace=False)  # ty: ignore[invalid-argument-type]
        if successor:
            process_successor(logger=logger, record=successor.record, predecessor=subject.record, replace=False)  # ty: ignore[invalid-argument-type]


def _file_artefact_distribution_options(event: EventProvisioned) -> None:
    """Add distribution options for file artefacts inplace within an event."""
    for artefact in [event.geotiff_file_artefact, event.jpeg_file_artefact]:
        cde_ref = event.cde_ref_geotiff if artefact.format_label == ArtefactFormatLabel.GEOTIFF else event.cde_ref_jpeg
        description = f"BAS Construction Partners CDE reference: {cde_ref}" if cde_ref else None
        dist_opt = Distribution(
            format=artefact.distribution_format,
            distributor=MICROSOFT_DISTRIBUTOR,
            transfer_option=TransferOption(
                size=Size(unit="bytes", magnitude=artefact.size_bytes),
                online_resource=OnlineResource(
                    href=artefact.url, description=description, function=OnlineResourceFunctionCode.DOWNLOAD
                ),
            ),
        )
        event.record.distribution.ensure(dist_opt)


def _service_artefact_distribution_options(event: EventProvisioned) -> None:
    """Add distribution options for service artefacts inplace within an event."""


def _categorise_events(  # noqa: C901, PLR0912
    logger: logging.Logger,
    data_area_path: Path,
    manifest_events: list[EventManifest] | None = None,
    processed_events: list[EventProcessed] | None = None,
    record_events: list[EventRecord] | None = None,
    deposited_events: list[EventDeposited] | None = None,
    provisioned_events: list[EventProvisioned] | None = None,
    finished_events: list[EventFinished] | None = None,
) -> dict[Path, EventStage]:
    """Determine the processing stage for each directory/event."""
    results = {}

    logger.info("Categorising process status of image products")
    logger.info("Data base path: %s", data_area_path.resolve())

    for path in data_area_path.iterdir():
        if not path.is_dir() or "Rothera_Station" not in path.name:
            logger.debug("%s is not a directory or not for Rothera Station, skipping", path.resolve())
            continue
        logger.info("Evaluating %s", path.resolve())
        results[path] = EventStage.NOT_INITIALISED

    event_map = {}  # maps file identifiers to results keys
    if manifest_events:
        for event in manifest_events:
            event_path = data_area_path / f"{event.acquisition_date.isoformat()}_Rothera_Station"
            results[event_path] = EventStage.MANIFEST
            event_map[event.file_identifier] = event_path
    if processed_events:
        for event in processed_events:
            results[event_map[event.file_identifier]] = EventStage.PROCESSED
    if record_events:
        for event in record_events:
            results[event_map[event.file_identifier]] = EventStage.RECORD
    if deposited_events:
        for event in deposited_events:
            results[event_map[event.file_identifier]] = EventStage.DEPOSITED
    if provisioned_events:
        for event in provisioned_events:
            results[event_map[event.file_identifier]] = EventStage.PROVISIONED
    if finished_events:
        for event in finished_events:
            results[event_map[event.file_identifier]] = EventStage.FINISHED

    return results


# Workflow stages


def _load_manifest(logger: logging.Logger, manifest_path: Path) -> list[EventManifest]:
    """
    Load manifest of images from CSV data.

    Example input:

    ```csv
    file_identifier,acquisition_date,cde_geotiff,cde_jpeg
    dcfe0427-d8c3-4db0-b022-e06a06b982a9,2026-04-02,AIMP-BAS-ZZZ-XX-I-Y-0012,AIMP-BAS-ZZZ-XX-I-Y-0011
    ```

    Example output:

    ```python
    [
        EventPropertiesManifest(
            file_identifier='dcfe0427-d8c3-4db0-b022-e06a06b982a9',
            acquisition_date=datetime.date(2026, 4, 2),
            cde_ref_geotiff='AIMP-BAS-ZZZ-XX-I-Y-0011',
            cde_ref_jpeg='AIMP-BAS-ZZZ-XX-I-Y-0012',
        )
    ]
    ```
    """
    logger.info("Loading image properties from CSV manifest")
    logger.info("Manifest path: %s", manifest_path.resolve())

    with manifest_path.open() as f:
        data = list(csv.DictReader(f))
    logger.info("Loaded %s rows from manifest CSV", len(data))
    if len(data) == 0:
        logger.info("No data loaded, aborting load.")
        return []
    logger.debug("first row:")
    logger.debug(data[0])
    logger.debug("last row:")
    logger.debug(data[-1])

    events = []

    for row in data:
        if "acquisition_date" not in row:
            logger.warning("No acquisition_date in CSV row, skipping row")
            logger.debug("Skipped row:")
            logger.debug(row)
            continue
        try:
            acquisition_date = date.fromisoformat(row["acquisition_date"])
        except TypeError, ValueError:
            logger.warning(
                "Row date '%s' cannot be parsed as a date, ensure ISO YYYY-MM-DD format.",
                row["image_date"],
            )
            continue

        if "file_identifier" not in row:
            logger.warning("No file identifier in CSV row, skipping row")
            logger.debug("Skipped row:")
            logger.debug(row)
            continue

        events.append(
            EventManifest(
                file_identifier=row["file_identifier"],
                acquisition_date=acquisition_date,
                cde_ref_geotiff=row.get("cde_geotiff"),
                cde_ref_jpeg=row.get("cde_jpeg"),
            )
        )

    logger.info("Loaded %s well-formed events from manifest.", len(events))
    return events


def _process_images(logger: logging.Logger, data_area_path: Path, events: list[EventManifest]) -> list[EventProcessed]:
    """
    Ensure a source GeoTff, converted JPEG and (JPEG) thumbnail exists for each event.

    Providing the source GeoTIFF exists, converted and thumbnail JPEG images are created automatically if missing:
    - source image     : any size (typically between 200MB to 1.5GB)
    - converted image  : any size (typically 50% of source and < 1GB)
    - thumbnail image  : target of under 300KB, very lossy, 50% quality

    External overviews for source GeoTIFFs are created automatically if needed (replacing conflicting internal
    overviews if necessary) for compatibility with ArcGIS Server.

    Paths to images are assumed (then validated) to be contained in predicable folders from a common root.

    Rejects non-georeferenced GeoTIFFs and other invalid files.
    """
    logger.info("Processing images for %s events", len(events))
    logger.info("Image files base path: %s", data_area_path.resolve())

    processed_events = []
    for event in events:
        logger.info(
            "Processing images for event [%s] (%s)",
            event.file_identifier,
            event.acquisition_date,
        )

        event_path = data_area_path / f"{event.acquisition_date.isoformat()}_Rothera_Station"
        source_image = event_path / f"rothera_orthomosaic_{event.acquisition_date.isoformat()}.tif"
        logger.info("Expected event base path: %s", event_path.resolve())
        logger.info("Expected source image (GeoTIFF): %s", source_image.resolve())

        if not source_image.exists():
            logger.error(
                "Source image for [%s] at path '%s' does not exist, skipping event.",
                event.file_identifier,
                source_image.resolve(),
            )
            continue
        if ArtefactFormats.get_file_format(source_image).label != ArtefactFormatLabel.GEOTIFF:
            logger.error(
                "Source image for [%s] at path '%s' is not a recognised GeoTIFF, skipping event.",
                event.file_identifier,
                source_image.resolve(),
            )
            continue

        try:
            bbox = _get_geotiff_bbox(logger=logger, source_path=source_image)
        except RuntimeError:
            logger.warning("Error getting bbox from GeoTIFF, skipping event.")
            continue
        try:
            _ensure_external_overviews(logger=logger, source_path=source_image)
        except RuntimeError:
            logger.warning("Error generating GeoTIFF overviews, skipping event.")
            continue
        try:
            converted_image = _ensure_jpeg_image(logger=logger, source_path=source_image)
        except RuntimeError:
            logger.warning("Error converting image, skipping event.")
            continue
        try:
            thumbnail_image = _ensure_thumbnail_image(logger=logger, source_path=converted_image)
        except RuntimeError:
            logger.warning("Error generating thumbnail, skipping event.")
            continue

        processed_events.append(
            EventProcessed(
                **asdict(event),
                geotiff_path=source_image,
                geotiff_bbox=bbox,
                jpeg_path=converted_image,
                thumbnail_path=thumbnail_image,
            )
        )

    logger.info("Processed images for %s events (%s skipped).", len(processed_events), len(events))
    return processed_events


def _generate_records(
    logger: logging.Logger,
    admin_keys: AdministrationKeys,
    collection_id: str,
    events: list[EventProcessed],
    now: datetime,
) -> list[EventRecord]:
    """
    Generate valid, templated, records for each event.

    Processed events are used to filter out events with invalid images.

    Determines the per-month count for resource editions based on other records (i.e. the second resource in May).

    Distribution options will be added after deposit/provisioning in `_finish_records()`.
    """
    logger.info("Generating records for %s events", len(events))

    event_count = {}
    monthly_counts = defaultdict(int)
    # group events by year and month to determine the count value for record edition
    for event in sorted(events, key=lambda event: event.acquisition_date):
        year_month = (event.acquisition_date.year, event.acquisition_date.month)
        monthly_counts[year_month] += 1
        event_count[event.file_identifier] = monthly_counts[year_month]

    record_events = []
    for event in events:
        logger.info(
            "Generating record for event [%s] (%s)",
            event.file_identifier,
            event.acquisition_date,
        )
        record = RecordEvent(
            admin_keys=admin_keys,
            now=now,
            collection_id=collection_id,
            event=event,
            edition_count=event_count[event.file_identifier],
        )
        try:
            record.validate()
        except RecordInvalidError as e:
            logger.exception("Generated record does not validate, skipping event.", exc_info=e)
            continue

        record_events.append(EventRecord(**asdict(event), record=record))

    logger.info("Generated records for %s events (%s skipped).", len(record_events), len(events))
    return record_events


def _deposit_files(
    logger: logging.Logger,
    cdn_client: S3Exporter,
    sp_client: MagicResourceDistributionClient,
    admin_keys: AdministrationKeys,
    access_groups_mapping: dict[str, list[str]],
    cdn_base_key: str,
    cdn_endpoint: str,
    events: list[EventRecord],
) -> list[EventDeposited]:
    """
    Deposit event images as file artefacts.

    Record events are used to filter out events with invalid records.

    Includes depositing thumbnails in the BAS CDN for consistency. The thumbnail media type is assumed/locked to
    JPEG made in processing step.
    """
    logger.info("Depositing artefacts for %s events", len(events))
    logger.info("CDN base key: %s", cdn_base_key)

    deposit_events = []
    for event in events:
        access_groups, unrestricted = get_permissions(
            admin_keys=admin_keys, record=event.record, groups_mapping=access_groups_mapping
        )

        event_artefacts = []  # expected order: source artefact, converted artefact
        for artefact_path in [event.geotiff_path, event.jpeg_path]:
            logger.info("Depositing %s as a file artefact", artefact_path.resolve())

            artefact = ArtefactLocalFile(resource_id=event.file_identifier, artefact_path=artefact_path)
            if not artefact.validate():
                logger.error("File artefact does not validate, skipping event.")
                continue

            sp_artefact = sp_client.deposit_artefact(
                artefact=artefact, access_groups=access_groups, unrestricted=unrestricted
            )
            event_artefacts.append(sp_artefact)

        logger.info("Uploading %s as an item thumbnail", event.thumbnail_path.resolve())
        event_key = f"{cdn_base_key}/{event.file_identifier}"
        thumbnail_key = f"{event_key}/{event.thumbnail_path.name}"
        thumbnail_url = f"{cdn_endpoint}/{thumbnail_key}"
        with event.thumbnail_path.open(mode="rb") as f:
            cdn_client._upload_object(
                s3=cdn_client._get_client(), key=thumbnail_key, content_type="image/jpeg", body=f.read()
            )

        deposit_event = EventDeposited(
            **asdict(event),
            geotiff_file_artefact=event_artefacts[0],
            jpeg_file_artefact=event_artefacts[1],
            thumbnail_file_url=thumbnail_url,
        )
        deposit_event.record = event.record  # prevent conversion to dict
        deposit_events.append(deposit_event)

    logger.info("Deposited artefacts for %s events (%s skipped).", len(deposit_events), len(events))
    return deposit_events


def _provision_services(logger: logging.Logger, events: list[EventDeposited]) -> list[EventProvisioned]:
    """
    Provision event GeoTIFF as a ArcGIS map layer service.

    Deposited events are used to filter out events without file artefacts.
    """
    logger.info("Provisioning service artefacts for %s events", len(events))

    provisioned_events = []
    for event in events:
        provisioned_event = EventProvisioned(**asdict(event), source_service_url="")
        provisioned_event.record = event.record  # prevent conversion to dict
        provisioned_events.append(provisioned_event)

    logger.info("Provisioned services for %s events (%s skipped).", len(provisioned_events), len(events))
    return provisioned_events


def _finish_records(logger: logging.Logger, events: list[EventProvisioned]) -> list[EventFinished]:
    """
    Update event records with distribution options, successor, predecessor and thumbnail.

    Provisioned events are used to filter out events without service artefacts.

    Thumbnail media type is assumed/locked to JPEG made in processing step.
    """
    logger.info("Finishing records for %s events", len(events))

    # set successor, predecessor
    _supersede_records(logger=logger, events=events)

    finished_events = []
    for event in events:
        # thumbnail
        event.record.identification.graphic_overviews = GraphicOverviews(
            [GraphicOverview(identifier="overview", href=event.thumbnail_file_url, mime_type="image/jpeg")]
        )

        # file artefacts with optional CDE references
        _file_artefact_distribution_options(event=event)

        # service artefacts
        _service_artefact_distribution_options(event=event)

        try:
            event.record.validate()
        except RecordInvalidError as e:
            logger.exception("Finished record does not validate, skipping event.", exc_info=e)
            continue

        finished_event = EventFinished(**asdict(event))
        finished_event.record = event.record  # prevent conversion to dict
        finished_events.append(finished_event)

    logger.info("Finished records for %s events (%s skipped).", len(finished_events), len(events))
    return finished_events


def _update_collection(
    logger: logging.Logger, cat: BasCatalogue, collection_id: str, events: list[EventFinished], now: datetime
) -> Record:
    """Update collection for events with finished records as collection members."""
    logger.info("Updating parent collection to include %s events", len(events))

    original = cat.repo.select_record(file_identifier=collection_id)
    logger.debug(
        "Current/original collection edition '%s', date_stamp '%s', members '%s'",
        original.identification.edition,
        original.metadata.date_stamp,
        len(original.identification.aggregations.filter(associations=AggregationAssociationCode.IS_COMPOSED_OF)),
    )

    collection = deepcopy(original)
    for event in events:
        collection.identification.aggregations.ensure(make_bas_cat_collection_member(event.file_identifier))
    if collection != original:
        revise_collection(time=now, collection=collection)
    return collection


def _dump_records(
    logger: logging.Logger, records_base_path: Path, events: list[EventFinished], collection: Record
) -> None:
    """
    Deposit event images as file artefacts.

    Finished record events are used to filter out incomplete events.
    """
    logger.info("Dumping finished records for %s events + collection", len(events))
    logger.info("Record configs base path: %s", records_base_path.resolve())

    records: list[Record] = [e.record for e in events] + [collection]  # ty: ignore[invalid-assignment]
    dump_records(logger=logger, output_path=records_base_path, records=records)

    logger.info("Dumped finished records for %s events.", len(events))


def _report_events(categorised_events: dict[Path, EventStage]) -> None:
    """Print formatted stage of each event or source image."""
    blocks = {
        EventStage.NOT_INITIALISED: 0,
        EventStage.MANIFEST: 1,
        EventStage.PROCESSED: 2,
        EventStage.RECORD: 3,
        EventStage.DEPOSITED: 4,
        EventStage.PROVISIONED: 5,
        EventStage.FINISHED: 6,
    }
    colours = {
        EventStage.NOT_INITIALISED: "bright_black",
        EventStage.MANIFEST: "red",
        EventStage.PROCESSED: "yellow",
        EventStage.RECORD: "magenta",
        EventStage.DEPOSITED: "cyan",
        EventStage.PROVISIONED: "blue",
        EventStage.FINISHED: "green",
    }

    table = Table(title="Rothera Drone Images", expand=True)
    table.add_column("Path", style="blue")
    table.add_column("Stage", no_wrap=True)
    table.add_column("Progress", no_wrap=True, ratio=1)
    progress_max = len(blocks) - 1

    for path, stage in categorised_events.items():
        progress = ProgressBar(
            total=progress_max,
            completed=blocks[stage],
            width=None,
            style="bright_black",
            complete_style=colours[stage],
            finished_style=colours[stage],
        )

        table.add_row(str(path.resolve()), stage.name, progress)

    console = Console()
    console.print(table)


# Control methods


def _get_cli_args() -> tuple[bool, Path, Path, Path]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Process Rothera progress monitoring orthomosaics for distribution.")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force branch to set value or default, and selection of records to CLI argument or all.",
    )
    parser.add_argument(
        "--manifest",
        "-m",
        type=Path,
        default=Path("./exp/rothera-orthos.csv"),
        help="Path to events manifest. Will use default if omitted.",
    )
    parser.add_argument(
        "--data",
        "-d",
        type=Path,
        default=Path("./exp/SAN"),
        help="Path to data area. Will use default if omitted.",
    )
    parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=Path("./import"),
        help="Directory to save generated records to. Will use default if omitted.",
    )
    args = parser.parse_args()
    return args.force, args.manifest, args.data, args.path


def _get_args(cli_args: tuple[bool, Path, Path, Path]) -> tuple[Path, Path, Path, str, str, str, str, datetime, str]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_manifest, cli_data_area, cli_output = cli_args

    manifest = cli_manifest
    data_area = cli_data_area
    output = cli_output

    # static
    cdn_bucket = "cdn.web.bas.ac.uk"
    cdn_base_key = "add-catalogue/0.0.0/img/items"
    cdn_endpoint = f"https://{cdn_bucket}"
    collection_id = "7344d437-4d9b-4e8c-a6f8-36c3e1b80a71"
    now = datetime.now(tz=UTC)

    if not cli_force:
        manifest = Path(
            inquirer.path("Events manifest path", path_type=InquirerPath.FILE, exists=True, default=str(manifest))
        )
        data_area = Path(
            inquirer.path("Data area path", path_type=InquirerPath.DIRECTORY, exists=True, default=data_area)
        )
        output = Path(
            inquirer.path("Records output path", path_type=InquirerPath.DIRECTORY, exists=True, default=output)
        )

    params = f"task workflow-rothera-orthos --force --manifest {manifest.resolve()} --data {data_area.resolve()} --path {output.resolve()}"
    return manifest, data_area, output, cdn_bucket, cdn_base_key, cdn_endpoint, collection_id, now, params


def _run(
    logger: logging.Logger,
    cat: BasCatalogue,
    cdn_client: S3Exporter,
    deposit_client: MagicResourceDistributionClient,
    admin_keys: AdministrationKeys,
    deposit_groups_mapping: dict,
    manifest_path: Path,
    data_area_path: Path,
    records_path: Path,
    cdn_base_key: str,
    cdn_endpoint: str,
    collection_id: str,
    now: datetime,
) -> None:
    """Run workflow."""
    manifest = _load_manifest(logger=logger, manifest_path=manifest_path)
    images = _process_images(logger=logger, data_area_path=data_area_path, events=manifest)
    records = _generate_records(
        logger=logger, admin_keys=admin_keys, collection_id=collection_id, events=images, now=now
    )
    deposited = _deposit_files(
        logger=logger,
        cdn_client=cdn_client,
        sp_client=deposit_client,
        admin_keys=admin_keys,
        access_groups_mapping=deposit_groups_mapping,
        cdn_endpoint=cdn_endpoint,
        cdn_base_key=cdn_base_key,
        events=records,
    )
    provisioned = _provision_services(logger=logger, events=deposited)
    finished = _finish_records(logger=logger, events=provisioned)
    collection = _update_collection(logger=logger, cat=cat, collection_id=collection_id, events=finished, now=now)

    _dump_records(logger=logger, records_base_path=records_path, events=finished, collection=collection)

    results = _categorise_events(
        logger=logger,
        data_area_path=data_area_path,
        manifest_events=manifest,
        processed_events=images,
        record_events=records,
        deposited_events=deposited,
        provisioned_events=provisioned,
        finished_events=finished,
    )
    _report_events(categorised_events=results)


def main() -> None:
    """Entrypoint."""
    logger, config, catalogue = init()

    cli_args = _get_cli_args()
    manifest_path, data_path, records_path, cdn_bucket, cdn_base_key, cdn_endpoint, collection_id, now, params = (
        _get_args(cli_args=cli_args)
    )

    s3 = init_s3(config)
    cdn_client = S3Exporter(logger=logger, s3=s3, bucket=cdn_bucket, parallel_jobs=1)
    deposit_client = MagicResourceDistributionClient(
        tenant_id=config.DEPOSIT_TENANT_ID,
        app_client_id=config.DEPOSIT_CLIENT_ID,
        app_client_secret=config.DEPOSIT_CLIENT_SECRET,
        site_id=config.DEPOSIT_SITE_ID,
        library_name=config.DEPOSIT_LIBRARY_NAME,
        proxy_url=None,
    )

    _run(
        logger=logger,
        cat=catalogue,
        cdn_client=cdn_client,
        deposit_client=deposit_client,
        admin_keys=config.ADMIN_METADATA_KEYS_RW,
        deposit_groups_mapping=config.DEPOSIT_GROUPS_MAPPING,
        manifest_path=manifest_path,
        data_area_path=data_path,
        records_path=records_path,
        cdn_base_key=cdn_base_key,
        cdn_endpoint=cdn_endpoint,
        collection_id=collection_id,
        now=now,
    )

    logger.info("Re-run as: '%s'", params)


if __name__ == "__main__":
    main()
