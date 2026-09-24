from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import inquirer
from inquirer import Path as InquirerPath
from PIL import Image, ImageOps
from tasks._shared import dump_records, init, init_s3, parse_records, pick_local_record

from lantern.exporters.s3 import S3Exporter
from lantern.lib.magic_distribution.formats import (
    ArtefactFormatLabel,
    ArtefactFormatNotSupportedError,
    ArtefactFormats,
    ArtefactFormatUnknownError,
)
from lantern.lib.metadata_library.models.record.elements.identification import GraphicOverview, GraphicOverviews
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.utils.admin import get_admin
from lantern.models.record.record import Record

if TYPE_CHECKING:
    import logging

    from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys


def _get_cli_args() -> tuple[bool, bool, Path, Path | None, Path | None]:
    """Get command line arguments."""
    parser = ArgumentParser(
        description="Upload a source image as a resized thumbnail for an item, with optional downsampling."
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force target record path, records path and source image path to CLI argument.",
    )
    parser.add_argument(
        "--downsample",
        "-d",
        action="store_true",
        help="Additionally downsample quality of the thumbnail for sensitive resources, defaults to False.",
    )
    parser.add_argument(
        "--records",
        "-p",
        type=Path,
        default=Path("./import"),
        help="Directory to save current and successor records to. Will use default if omitted.",
    )
    parser.add_argument(
        "--record",
        "-r",
        type=Path,
        help="Optional path to target record config file. Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "--image",
        "-i",
        type=Path,
        help="Optional path to source thumbnail image. Will interactively prompt if omitted.",
    )
    args = parser.parse_args()
    return args.force, args.downsample, args.records, args.record, args.image


def _get_args(  # noqa: C901, PLR0912, PLR0915
    logger: logging.Logger, admin_keys: AdministrationKeys, cli_args: tuple[bool, bool, Path, Path | None, Path | None]
) -> tuple[Path, Path, Record, bool, str, str, str, str]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_downsample, cli_records_path, cli_record_path, cli_image_path = cli_args

    # static
    cdn_bucket = "cdn.web.bas.ac.uk"
    cdn_base_key = "add-catalogue/0.0.0/img/items"
    cdn_endpoint = f"https://{cdn_bucket}"

    output_path = cli_records_path
    record_path = cli_record_path
    image_path = cli_image_path
    downsample = cli_downsample
    record: Record | None = None

    logger.info("Loading records from: '%s'", output_path.resolve())
    _record_paths: list[tuple[Record, Path]] = parse_records(
        logger=logger, search_path=output_path, validate_catalogue=True
    )
    _record_lookup = {rp[1].resolve(): rp[0] for rp in _record_paths}
    _path_lookup = {rp[0].file_identifier: rp[1] for rp in _record_paths}

    if not cli_force:
        output_path = Path(
            inquirer.path("Import path", path_type=InquirerPath.DIRECTORY, exists=True, default=output_path)
        )
        if not record_path:
            record = pick_local_record(logger=logger, records=[rp[0] for rp in _record_paths])  # ty: ignore[invalid-assignment]
        image_path = Path(inquirer.path("Image path", path_type=InquirerPath.FILE, exists=True, default=image_path))

        # default downsample to true where record is not open access
        admin_meta = get_admin(keys=admin_keys, record=record)  # ty: ignore[invalid-argument-type]
        if admin_meta and admin_meta.resource_permissions != [OPEN_ACCESS]:
            downsample = True
        downsample: bool = (
            inquirer.list_input(
                "Downsample thumbnail for sensitive resources?",
                choices=["Yes", "No"],
                default="Yes" if downsample else "No",
            )
            == "Yes"
        )

    else:
        if cli_record_path is None:
            msg = "Record path must be set when using --force option for this task."
            raise RuntimeError(msg) from None
        if cli_image_path is None:
            msg = "Image path must be set when using --force option for this task."
            raise RuntimeError(msg) from None
        try:
            record = _record_lookup[cli_record_path.resolve()]
        except KeyError:
            raise FileNotFoundError() from None

    msg = "Record, records path and image path MUST be set for this task."
    if not isinstance(output_path, Path):
        raise TypeError(msg) from None
    if not isinstance(record, Record):
        raise TypeError(msg) from None
    if not isinstance(image_path, Path):
        raise TypeError(msg) from None
    try:
        fmt = ArtefactFormats.get_file_format(file=image_path)
    except (ArtefactFormatUnknownError, ArtefactFormatNotSupportedError) as e:
        msg = "Image format unknown"
        raise RuntimeError(msg) from e
    else:
        if fmt.label not in [ArtefactFormatLabel.JPEG, ArtefactFormatLabel.PNG]:
            msg = "Image format not supported (must be JPEG/PNG)"
            raise RuntimeError(msg) from None

    try:
        record_path = _path_lookup[record.file_identifier]
    except KeyError:
        msg = f"File for record '{record.file_identifier}' not found"
        raise FileNotFoundError(msg) from None
    _downsample = "--downsample" if downsample else ""
    params = f"task upload-thumbnail --force {_downsample} --records {output_path.resolve()} --record {record_path.resolve()} --image {image_path.resolve()}"

    return image_path, output_path, record, downsample, cdn_bucket, cdn_base_key, cdn_endpoint, params


def _resize_image(logger: logging.Logger, source_path: Path, output_path: Path, size: tuple[int, int]) -> None:
    """Resize a copy of the source image to suit catalogue item pages."""
    logger.info("Resizing image '%s' to fit within %sx%s", source_path.resolve(), *size)
    with Image.open(source_path) as source_image:
        image = ImageOps.exif_transpose(source_image)
        image.thumbnail(size, Image.Resampling.LANCZOS)
        image.save(output_path)


def _convert_image(logger: logging.Logger, image_path: Path) -> None:
    """Convert image from PNG to JPEG for consistency."""
    output_path = image_path.with_suffix(".jpg")
    logger.info("Converting image '%s' to JPEG '%s'", image_path.resolve(), output_path.resolve())
    with Image.open(image_path) as source_image:
        image = ImageOps.exif_transpose(source_image)
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, "white")
            background.paste(rgba, mask=rgba.getchannel("A"))
            output_image = background
        else:
            output_image = image.convert("RGB")
        output_image.save(output_path, format="JPEG")


def upload_image(
    logger: logging.Logger,
    cdn_client: S3Exporter,
    cdn_base_key: str,
    cdn_endpoint: str,
    file_identifier: str,
    image_path: Path,
) -> GraphicOverview:
    """Upload image to S3 and return as a record graphic overview."""
    logger.info("Uploading %s as an item thumbnail", image_path.resolve())
    event_key = f"{cdn_base_key}/{file_identifier}"
    thumbnail_key = f"{event_key}/{image_path.name}"
    with image_path.open(mode="rb") as f:
        cdn_client._upload_object(
            s3=cdn_client._get_client(), key=thumbnail_key, content_type="image/jpeg", body=f.read()
        )

    thumbnail_url = f"{cdn_endpoint}/{thumbnail_key}"
    return GraphicOverview(
        identifier="overview", href=thumbnail_url, description="General overview of resource", mime_type="image/jpeg"
    )


def main() -> None:
    """Entrypoint."""
    logger, config, _catalogue = init()

    cli_args = _get_cli_args()
    image_path, output_path, record, downsample, cdn_bucket, cdn_base_key, cdn_endpoint, params = _get_args(
        logger=logger, admin_keys=config.ADMIN_METADATA_KEYS, cli_args=cli_args
    )

    s3 = init_s3(config)
    cdn_client = S3Exporter(logger=logger, s3=s3, bucket=cdn_bucket, parallel_jobs=1)

    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        target_path = tmp_path / f"overview{image_path.suffix}"
        target_size: tuple[int, int] = (300, 300) if downsample else (800, 800)

        _resize_image(logger=logger, source_path=image_path, output_path=target_path, size=target_size)
        if image_path.suffix == ".png":
            _convert_image(logger=logger, image_path=target_path)
            target_path = target_path.with_suffix(".jpg")
        graphic = upload_image(
            logger=logger,
            cdn_client=cdn_client,
            cdn_base_key=cdn_base_key,
            cdn_endpoint=cdn_endpoint,
            file_identifier=record.file_identifier,
            image_path=target_path,
        )

    record.identification.graphic_overviews = GraphicOverviews([graphic])
    dump_records(logger=logger, output_path=output_path, records=[record])

    logger.info("Re-run as: '%s'", params)


if __name__ == "__main__":
    main()
