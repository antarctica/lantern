# Deposit one or more artefacts related to an existing record in the MAGIC Resource Distribution service (SharePoint)

from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

import inquirer
from inquirer import Path as InquirerPath
from tasks._shared import dump_records, init, parse_records, pick_local_record

from lantern.lib.magic_distribution.client import MagicResourceDistributionClient
from lantern.lib.magic_distribution.models.artefact import ArtefactLocalFile, ArtefactSharePointFile
from lantern.lib.metadata_library.models.record.elements.common import OnlineResource
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Size, TransferOption
from lantern.lib.metadata_library.models.record.enums import OnlineResourceFunctionCode
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.presets.contacts import MICROSOFT_DISTRIBUTOR
from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import get_admin

if TYPE_CHECKING:
    import logging

    from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
    from tasks._config import ExtraConfig


def _get_cli_args() -> tuple[bool, Path, Path, Path | None, bool]:
    """Get command line arguments."""
    parser = ArgumentParser(
        description="Deposit file artefacts for a resource in the MAGIC Resource Distribution service."
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force artefacts and records path to defaults, and record path to CLI argument.",
    )
    parser.add_argument(
        "--artefacts-path",
        "-a",
        type=Path,
        default=Path("./artefacts"),
        help="Directory containing artefact files to deposit. Will use default if omitted.",
    )
    parser.add_argument(
        "--records-path",
        "-i",
        type=Path,
        default=Path("./import"),
        help="Directory containing record files to update. Will use default if omitted.",
    )
    parser.add_argument(
        "--record",
        "-r",
        type=Path,
        default=None,
        help="Set specific record config file to update. Will prompt for files in records directory if omitted.",
    )
    parser.add_argument(
        "--clean-deposited",
        "-c",
        action="store_true",
        help="Delete deposited artefacts after a successful deposit. Originals are kept by default.",
    )
    args = parser.parse_args()
    return args.force, args.artefacts_path, args.records_path, args.record, args.clean_deposited


def _get_args(
    logger: logging.Logger,
    cli_args: tuple[bool, Path, Path, Path | None, bool],
) -> tuple[Path, Path, Record, bool, str]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_artefacts_path, cli_records_path, cli_record_path, cli_clean_deposited = cli_args

    artefacts_path = cli_artefacts_path
    records_path = cli_records_path
    record_path: Path | None = cli_record_path
    clean_deposited = cli_clean_deposited

    if cli_force and not record_path:
        msg = "A record path must be set when using --force option for this task."
        raise RuntimeError(msg) from None
    if cli_force and isinstance(record_path, Path):
        logger.info("Loading record from: '%s'", record_path.resolve())
        r = parse_records(
            logger=logger, glob_pattern=record_path.name, search_path=record_path.parent, validate_catalogue=True
        )
        record = r[0][0]

        clean_flag = " --clean-deposited" if clean_deposited else ""
        params = f"task artefacts-deposit --force --artefacts-path {artefacts_path.resolve()} --records-path {records_path.resolve()} --path {record_path.resolve()}{clean_flag}"
        return artefacts_path, records_path, record, clean_deposited, params

    artefacts_path = Path(
        inquirer.path("Artefacts path", path_type=InquirerPath.DIRECTORY, exists=True, default=artefacts_path)
    )
    records_path = Path(
        inquirer.path("Records path", path_type=InquirerPath.DIRECTORY, exists=True, default=records_path)
    )

    logger.info("Loading records from: '%s'", records_path.resolve())
    _record_paths = parse_records(logger=logger, search_path=records_path)
    record = pick_local_record(logger=logger, records=[rp[0] for rp in _record_paths])

    _records_lookup = {rp[0].file_identifier: rp[1].resolve() for rp in _record_paths}
    try:
        record_path = _records_lookup[record.file_identifier]
    except KeyError:
        msg = f"File for record '{record.file_identifier}' not found"
        raise FileNotFoundError(msg) from None

    clean_deposited = inquirer.confirm(
        "Delete local files for successfully deposited artefacts?", default=clean_deposited
    )

    msg = "Artefacts path, records path and record MUST be set for this task."
    if not isinstance(artefacts_path, Path):
        raise TypeError(msg) from None
    if not isinstance(records_path, Path):
        raise TypeError(msg) from None
    if not isinstance(record_path, Path):
        raise TypeError(msg) from None
    if not isinstance(record, Record):
        raise TypeError(msg) from None

    clean_flag = " --clean-deposited" if clean_deposited else ""
    params = f"task artefacts-deposit --force --artefacts-path {artefacts_path.resolve()} --records-path {records_path.resolve()} --path {record_path.resolve()}{clean_flag}"
    return artefacts_path, records_path, record, clean_deposited, params


def _get_permissions(
    admin_keys: AdministrationKeys, record: Record, groups_mapping: dict[str, list[str]]
) -> tuple[set[str], bool]:
    """
    Convert resource permissions into sharing groups or whether unrestricted access is allowed.

    Open access permissions MUST be exclusive based on well-known permission.

    The directory of any other permissions MUST match the tenancy of the deposit SharePoint site (i.e. NERC).

    Permissions targeting other directories are ignored. Permission expiry date times are also ignored.

    Permission referencing well-known group aliases (e.g. `~bas-staff`) need to be resolved to real Entra groups using
    the provided mapping (where aliases CAN resolve to multiple Entra groups, e.g. `{'x': ['123', '234']}`).
    """
    admin_meta = get_admin(keys=admin_keys, record=record)
    if not admin_meta:
        return set(), False
    if admin_meta.resource_permissions == [OPEN_ACCESS]:
        return set(), True

    # filter out permissions for other directories
    groups = {p.group for p in admin_meta.resource_permissions if p.directory == "~nerc"}
    # resolve any group mappings
    groups = {mapped_group for group in groups for mapped_group in groups_mapping.get(group, [group])}

    return groups, False


def _get_artefacts(logger: logging.Logger, artefacts_path: Path, resource_id: str) -> list[ArtefactLocalFile]:
    """Generate artefacts for supported file types."""
    logger.info("Searching for artefacts without recursion in: %s", artefacts_path.resolve())
    artefacts = []

    for path in artefacts_path.iterdir():
        if path.is_file():
            logger.info("Evaluating file: %s", path.resolve())
            artefact = ArtefactLocalFile(resource_id=resource_id, artefact_path=path)
            if not artefact.validate():
                logger.warning("%s does not validate as an artefact, skipping.", path.name)
                continue
            artefacts.append(artefact)
            logger.debug(artefact)

    return artefacts


def _deposit_artefacts(
    logger: logging.Logger,
    deposit_client: MagicResourceDistributionClient,
    artefacts: list[ArtefactLocalFile],
    access_groups: set[str],
    unrestricted: bool,
) -> list[ArtefactSharePointFile]:
    """Deposit selected artefacts."""
    deposited = []
    for artefact in artefacts:
        logger.info("Depositing %s ...", repr(artefact))
        deposited.append(
            deposit_client.deposit_artefact(artefact=artefact, access_groups=access_groups, unrestricted=unrestricted)
        )
    return deposited


def _update_record(logger: logging.Logger, record: Record, artefacts: list[ArtefactSharePointFile]) -> None:
    dist_opts: list[tuple[str, int]] = [("🆕 - Add as new", -1)]
    for i, d in enumerate(record.distribution):
        label = f"{d.format.format if d.format else '?'}"
        if d.transfer_option.size:
            label += f", {d.transfer_option.size.magnitude or '?'} {d.transfer_option.size.unit or '-'}"
        dist_opts.append((label, i))

    for artefact in artefacts:
        logger.info("Adding distribution option for %s ...", repr(artefact))
        dist_opt = Distribution(
            format=artefact.distribution_format,
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href=artefact.url,
                    title=artefact.format.name,
                    description=artefact.format.description,
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                ),
                size=Size(unit="bytes", magnitude=artefact.size_bytes),
            ),
            distributor=MICROSOFT_DISTRIBUTOR,
        )

        if dist_opt in record.distribution:
            logger.info("Distribution option is already in record, skipping")
            continue

        dist_index = inquirer.list_input("Distribution option", choices=dist_opts, default="-1")
        if dist_index == -1:
            record.distribution.append(dist_opt)
        else:
            record.distribution[
                dist_index
            ].transfer_option.online_resource.href = dist_opt.transfer_option.online_resource.href
            record.distribution[dist_index].transfer_option.size = dist_opt.transfer_option.size
            record.distribution[dist_index].distributor = dist_opt.distributor


def _clean_deposited(
    logger: logging.Logger, artefacts: list[ArtefactLocalFile], deposited: list[ArtefactSharePointFile]
) -> None:
    """Remove original files for deposited artefacts."""
    hashed_paths = {a.quickxor: (a._artefact, a.artefact_id) for a in artefacts}
    for deposited_hash in [d.quickxor for d in deposited]:
        path, artefact_id = hashed_paths[deposited_hash]
        logger.info("Removing deposited file '%s' for artefact [%s]", path.resolve(), artefact_id)
        path.unlink()


def _run(
    logger: logging.Logger,
    config: ExtraConfig,
    deposit_client: MagicResourceDistributionClient,
    groups_mapping: dict[str, list[str]],
) -> None:
    """Run task."""
    cli_args = _get_cli_args()
    artefacts_path, output_path, record, clean_deposited, params = _get_args(logger=logger, cli_args=cli_args)

    access_groups, unrestricted = _get_permissions(
        admin_keys=config.ADMIN_METADATA_KEYS, record=record, groups_mapping=groups_mapping
    )
    artefacts = _get_artefacts(logger=logger, artefacts_path=artefacts_path, resource_id=record.file_identifier)  # ty: ignore[invalid-argument-type]
    if len(artefacts) == 0:
        logger.info("No supported artefacts, aborting.")
        return

    logger.info("Found %s supported artefacts to deposit:", len(artefacts))
    inquirer.checkbox(message="Artefacts to deposit", choices=[(repr(a), a) for a in artefacts])
    deposited = _deposit_artefacts(
        logger=logger,
        deposit_client=deposit_client,
        artefacts=artefacts,
        access_groups=access_groups,
        unrestricted=unrestricted,
    )

    _update_record(logger=logger, record=record, artefacts=deposited)
    dump_records(logger=logger, output_path=output_path, records=[record])

    if clean_deposited:
        _clean_deposited(logger=logger, artefacts=artefacts, deposited=deposited)

    logger.info("Re-run as: '%s'", params)


def main() -> None:
    """Entrypoint."""
    logger, config, _catalogue = init()
    deposit_client = MagicResourceDistributionClient(
        tenant_id=config.DEPOSIT_TENANT_ID,
        app_client_id=config.DEPOSIT_CLIENT_ID,
        app_client_secret=config.DEPOSIT_CLIENT_SECRET,
        site_id=config.DEPOSIT_SITE_ID,
        library_name=config.DEPOSIT_LIBRARY_NAME,
        proxy_url=config.DEPOSIT_PROXY_URL,
    )

    _run(logger=logger, config=config, deposit_client=deposit_client, groups_mapping=config.DEPOSIT_GROUPS_MAPPING)


if __name__ == "__main__":
    main()
