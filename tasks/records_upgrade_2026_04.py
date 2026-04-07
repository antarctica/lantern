import json
import logging
import random
from datetime import UTC, datetime
from pathlib import Path

from tasks._config import ExtraConfig
from tasks._shared import dump_records, init

from lantern.lib.metadata_library.models.record.enums import (
    ConstraintTypeCode,
    ContactRoleCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)
from lantern.lib.metadata_library.models.record.record import Record, RecordInvalidError
from lantern.models.item.catalogue.const import CONTAINER_SUPER_TYPES
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.record.record import Record as CatRecord
from lantern.models.record.revision import RecordRevision as CatRecordRevision
from lantern.stores.gitlab import GitLabStore
from lantern.utils import get_jinja_env


class RecordUpgrade:
    """Wrapper around record as part of an upgrade."""

    def __init__(self, logger: logging.Logger, record: Record, original_sha1: str) -> None:
        """Initialise."""
        self.logger = logger
        self.record = record
        self.changes: list[str] = []
        self._original_sha1 = original_sha1
        self._fid = self.record.file_identifier

    @property
    def _container_super_type(self) -> bool:
        """Whether record is a container super type."""
        return self.record.hierarchy_level in CONTAINER_SUPER_TYPES

    def _update_catalogue_identifier(self) -> None:
        """Scope catalogue identifier to Lantern."""
        old = "data.bas.ac.uk"
        if self.record.identification.identifiers.filter(namespace=CATALOGUE_NAMESPACE):
            self.logger.debug(
                f"[{self.record.file_identifier}] update catalogue identifier: has new namespace - skipping."
            )
            return

        for identifier in self.record.identification.identifiers:
            if identifier.namespace == old:
                if identifier.href:
                    identifier.href = identifier.href.replace(old, CATALOGUE_NAMESPACE)
                identifier.namespace = CATALOGUE_NAMESPACE
                self.changes.append("Updated catalogue identifier namespace and href.")
                return

        self.logger.debug(
            f"[{self.record.file_identifier}] update catalogue identifier: identifier not found - skipping."
        )

    def _update_alias_identifiers(self) -> None:
        """Scope aliases identifiers to Lantern."""
        old = "alias.data.bas.ac.uk"
        if not self.record.identification.identifiers.filter(namespace=old):
            self.logger.debug(
                f"[{self.record.file_identifier}] update alias identifiers: no alias identifiers - skipping."
            )
            return

        count = 0
        for identifier in self.record.identification.identifiers:
            if identifier.namespace == old:
                if identifier.href:
                    identifier.href = identifier.href.replace("data.bas.ac.uk", CATALOGUE_NAMESPACE)
                identifier.namespace = ALIAS_NAMESPACE
                count += 1

        if count > 0:
            self.changes.append(f"Updated {count} alias identifier(s) namespace and href.")

    def _update_aggregation_identifiers(self) -> None:
        """Scope aggregation identifiers to Lantern."""
        old = "data.bas.ac.uk"
        if not self.record.identification.aggregations:
            self.logger.debug(
                f"[{self.record.file_identifier}] update aggregation identifiers: no aggregations - skipping."
            )
            return

        count = 0
        for aggregation in self.record.identification.aggregations:
            if aggregation.identifier.namespace == old:
                if aggregation.identifier.href:
                    aggregation.identifier.href = aggregation.identifier.href.replace(old, CATALOGUE_NAMESPACE)
                aggregation.identifier.namespace = CATALOGUE_NAMESPACE
                count += 1

        if count > 0:
            self.changes.append(f"Updated {count} aggregation identifier(s) namespace and href.")

    def _add_publisher(self) -> None:
        """Add MAGIC as a publisher if needed."""
        if self.record.identification.contacts.filter(roles=ContactRoleCode.PUBLISHER):
            self.logger.debug(f"[{self.record.file_identifier}] add publisher: has publisher - skipping.")
            return

        for contact in self.record.identification.contacts:
            if contact.name == "Mapping and Geographic Information Centre, British Antarctic Survey":
                contact.role.add(ContactRoleCode.PUBLISHER)
                self.changes.append("Added publisher role to MAGIC contact.")
                return

    def _add_metadata_maintenance(self) -> None:
        """Add complete / asNeeded if missing."""
        if not self.record.metadata.maintenance.progress:
            self.record.metadata.maintenance.progress = ProgressCode.COMPLETED
            self.changes.append("Added completed metadata maintenance progress.")
        else:
            self.logger.debug(f"[{self.record.file_identifier}] metadata maintenance: has progress - no change.")
        if not self.record.metadata.maintenance.maintenance_frequency:
            self.record.metadata.maintenance.maintenance_frequency = MaintenanceFrequencyCode.AS_NEEDED
            self.changes.append("Added 'as needed' metadata maintenance frequency.")
        else:
            self.logger.debug(f"[{self.record.file_identifier}] metadata maintenance: has frequency - no change.")

    def _update_published_maps_link(self) -> None:
        """Update purchasing information link in published map records if needed."""
        if not self.record.distribution:
            self.logger.debug(f"[{self.record.file_identifier}] published map link: no distributions - skipping.")
            return

        found = False
        for do in self.record.distribution:
            if (
                do.transfer_option.online_resource.href
                == "https://www.bas.ac.uk/data/our-data/maps/how-to-order-a-map/"
            ):
                do.transfer_option.online_resource.href = "https://data.bas.ac.uk/guides/map-purchasing/"
                self.changes.append("Updated published maps purchasing link.")
                found = True
                break

        if not found:
            self.logger.debug(
                f"[{self.record.file_identifier}] published map link: no matching distribution - skipping."
            )

    def _fix_personal_contacts(self) -> None:
        """Remove known personal emails from contacts if needed."""
        emails = []  # DO NOT COMMIT
        flag = False
        for contact in self.record.identification.contacts:
            if contact.email in emails:
                flag = True
                contact.email = None
                self.changes.append("Removed personal email from contact.")
        if not flag:
            self.logger.debug(f"[{self.record.file_identifier}] personal contacts: none found - skipping.")

    def _remove_legacy_permissions(self) -> None:
        """Remove legacy access permissions and update statements in constraints if needed."""
        found_permissions = False
        found_statement = False
        bas_access = ["55818e99-b5a9-4898-a05b-5d90699bf000", "edd5c12f-4483-4c82-af39-29045e51c881"]

        for con in self.record.identification.constraints:
            if con.type == ConstraintTypeCode.ACCESS:
                if con.href:
                    con.href = None
                    found_permissions = True
                if con.statement == "Closed Access (NERC)":
                    con.statement = "Closed Access (As Needed)"
                    if self.record.file_identifier in bas_access:
                        con.statement = "Closed Access (BAS)"
                    found_statement = True

        if found_permissions:
            self.changes.append("Legacy permissions removed from access constraints.")
        else:
            self.logger.debug(
                f"[{self.record.file_identifier}] legacy constraints: no matching permissions values - skipping."
            )
        if found_statement:
            self.changes.append("Access statement updated in constraints.")
        else:
            self.logger.debug(
                f"[{self.record.file_identifier}] legacy constraints: no matching statement values - skipping."
            )

    def _warn_long_purpose(self) -> None:
        """Warn if purpose/summary is greater than ArcGIS snippet max length."""
        if not self.record.identification.purpose:
            self.logger.debug(f"[{self.record.file_identifier}] max purpose: no purpose - skipping.")
            return

        if len(self.record.identification.purpose) > 250:
            self.logger.warning(f"[{self.record.file_identifier}] max purpose: length > ArcGIS snippet max length!")

    def _revise(self) -> None:
        """Update date stamp in record if needed."""
        if self.record.sha1 == self._original_sha1:
            self.logger.debug(f"[{self.record.file_identifier}] revision: record not changed - skipping.")
            return

        now = datetime.now(tz=UTC)
        self.record.metadata.date_stamp = datetime.now(tz=UTC).date()
        if self._container_super_type:
            self.record.identification.dates.revision.date = now  # ty:ignore[invalid-assignment]
        self.logger.debug(f"[{self.record.file_identifier}] revision: record changed - revised.")

    def upgrade(self) -> None:
        """Upgrade record."""
        self._update_catalogue_identifier()
        self._update_alias_identifiers()
        self._update_aggregation_identifiers()
        self._add_publisher()
        self._add_metadata_maintenance()
        self._update_published_maps_link()
        self._remove_legacy_permissions()
        self._fix_personal_contacts()
        self._warn_long_purpose()
        self._revise()

    def validate(self) -> None:
        """Validate record against standard, any declared profiles and data catalogue specific requirements."""
        cat_record = CatRecord.loads(self.record.dumps(strip_admin=False))
        cat_record.validate()


class RecordsReport:
    """Report on changes made to a set of record."""

    def __init__(self, logger: logging.Logger, records: list[RecordUpgrade]) -> None:
        """Initialise."""
        self._logger = logger
        self._records = records

    @property
    def _data(self) -> dict[str, dict]:
        """Changes for record as a dict indexed by record file identifier."""
        return {
            c.record.file_identifier: {
                "id": c.record.file_identifier,
                "type": c.record.hierarchy_level.name,
                "title": c.record.identification.title,
                "edition": c.record.identification.edition,
                "changes": c.changes,
            }
            for c in self._records
        }  # ty:ignore[invalid-return-type]

    @property
    def _context(self) -> dict[str, str | dict]:
        """Data for Jinja template."""
        return {
            "timestamp": datetime.now(tz=UTC).replace(microsecond=0).isoformat(),
            "count": str(len(self._data)),
            "changed_count": str(sum(1 for r in self._records if r.changes)),
            "items": self._data,
        }

    @property
    def _template(self) -> str:
        """Jinja template."""
        return """
# Records upgrade report

Run at: {{ timestamp }}

Records: {{ count }} (of which {{ changed_count }} were changed)

{% for file_identifier, data in items.items() %}
## {{ data.title }} (Ed: {{ data.edition }})

({{ file_identifier }} / {{ data.type }})

{% for change in data.changes %}
- {{ change }}
{% endfor %}
{% endfor %}
        """

    def _render(self) -> str:
        """Render jinja template."""
        jinja = get_jinja_env()
        return jinja.from_string(self._template).render(**self._context)

    def dump_data(self, path: Path) -> None:
        """Dump report data to path."""
        with path.open("w") as f:
            json.dump(self._data, f, indent=2)

    def dump_rendered(self, path: Path) -> None:
        """Dump rendered report to path."""
        with path.open("w") as f:
            f.write(self._render())


class RecordsIO:
    """Manages a set of records as underlying files."""

    def __init__(self, logger: logging.Logger, store: GitLabStore, base_path: Path) -> None:
        """Initialise."""
        self.logger = logger
        self.store = store
        self.base = base_path
        self.records: list[RecordUpgrade] = []

    @staticmethod
    def _write_hashes(records: list[Record | CatRecordRevision], path: Path) -> None:
        data = {record.file_identifier: record.sha1 for record in records}
        with path.open("w") as f:
            json.dump(data, f, indent=2)

    @property
    def initialised(self) -> bool:
        """Check if local records set exists."""
        return self.base.exists()

    def prep(self) -> None:
        """Dump all records from store."""
        self.base.mkdir(parents=True, exist_ok=True)
        records_path = self.base / "records"
        hashes_path = self.base / "hashes_original.json"

        records = self.store.select()
        dump_records(logger=self.logger, output_path=records_path, records=records)
        self.logger.info(f"{len(records)} records dumped to {self.base.resolve()}.")

        self._write_hashes(records=records, path=hashes_path)  # ty:ignore[invalid-argument-type]
        self.logger.info(f"Original record hashes dumped to {hashes_path.resolve()}.")

    def dump(self) -> None:
        """Dump records to path."""
        records_ = [r.record for r in self.records]
        records_path = self.base / "records"
        dump_records(logger=self.logger, output_path=records_path, records=records_)
        self.logger.info(f"{len(self.records)} records dumped to {self.base.resolve()}.")

        hashes_path = self.base / "hashes_working.json"
        self._write_hashes(records=records_, path=hashes_path)
        self.logger.info(f"Working record hashes dumped to {hashes_path.resolve()}.")

    def load(self, random_subset: int = 0) -> None:
        """Load (some) records from path."""
        originals_path = self.base / "hashes_original.json"
        with originals_path.open("r") as f:
            original_hashes = json.load(f)

        record_paths = list(self.base.glob("records/*.json"))
        self.logger.info(f"{len(record_paths)} records in {self.base.resolve()}.")

        subset_paths = record_paths
        if 0 < random_subset < len(record_paths):
            self.logger.info(f"Selecting {random_subset} random records as a subset.")
            random.seed(764)  # 764/4
            subset_paths = random.sample(record_paths, random_subset)

        self.logger.info(f"Loading {len(record_paths)} records.")
        self.records = []
        for record_path in subset_paths:
            with record_path.open("r") as f:
                record = Record.loads(json.load(f))
                self.records.append(
                    RecordUpgrade(
                        logger=self.logger, record=record, original_sha1=original_hashes[record.file_identifier]
                    )
                )

    def list(self) -> None:
        """List or summarise loaded records."""
        if len(self.records) < 20:
            self.logger.info("Loaded records:")
            for container in self.records:
                r = container.record
                self.logger.info(
                    f"* {r.file_identifier} [{r.hierarchy_level.name}] '{r.identification.title}' ({r.identification.edition})"
                )
            return
        self.logger.info(f"{len(self.records)} records.")


class NotInitialisedError(Exception):
    """Raised when local records set does yet not exist."""

    pass


# noinspection SpellCheckingInspection
class Upgradamatron:
    """Upgrade a set of records."""

    def __init__(self, logger: logging.Logger, config: ExtraConfig, store: GitLabStore, path: Path) -> None:
        """Initialise."""
        self.logger = logger
        self.config = config
        self.store = store
        self.base = path

        self.io = RecordsIO(logger=self.logger, store=self.store, base_path=self.base)

    def init(self, random_subset: int = 0) -> None:
        """Initialise local records set."""
        if not self.io.initialised:
            self.io.prep()
            self.logger.info("Init local git repo and commit all records to track changes. Then rerun this task.")
            raise NotInitialisedError() from None
        self.io.load(random_subset=random_subset)

    def list(self) -> None:
        """List or summarise loaded records."""
        self.io.list()

    def run(self) -> None:
        """Upgrade and validate records."""
        for container in self.io.records:
            container.upgrade()
            self.logger.debug(f"[{container.record.file_identifier}] validating")
            try:
                container.validate()
            except RecordInvalidError:
                self.logger.exception(f"[{container.record.file_identifier}] record invalid")

    def dump(self) -> None:
        """Dump records and reports to tracking repo path."""
        self.io.dump()
        report_data_path = self.base / "report_data.json"
        report_rendered_path = self.base / "report_rendered.md"
        reporter = RecordsReport(logger=self.logger, records=self.io.records)
        reporter.dump_data(path=report_data_path)
        reporter.dump_rendered(path=report_rendered_path)
        self.logger.info(f"Report data dumped to {report_data_path.resolve()}.")
        self.logger.info(f"Report rendered dumped to {report_rendered_path.resolve()}.")


def main() -> None:
    """Entrypoint."""
    path = Path("upgrade_2026_04")
    subset = 0
    logger, config, store = init()
    logger.info("Records upgrade script: 2026-04 (0.5.x -> 0.6.0)")

    upgrade = Upgradamatron(logger=logger, config=config, store=store, path=path)
    try:
        upgrade.init(random_subset=subset)
    except NotInitialisedError:
        return
    upgrade.list()
    upgrade.run()
    upgrade.dump()

    logger.info("Upgrade complete.")


if __name__ == "__main__":
    main()
