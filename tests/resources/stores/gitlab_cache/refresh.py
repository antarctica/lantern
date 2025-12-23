import json
from pathlib import Path

from sqlorm import SQL, Engine

from lantern.stores.gitlab import GitLabLocalCache, ProcessedRecord


def _load_record(record_path: Path, commit_id: str) -> ProcessedRecord:
    with record_path.open() as f:
        record_data = f.read()
    return ProcessedRecord(logger=None, config_str=record_data, commit_id=commit_id)


def _init_db(db_path: Path, record: ProcessedRecord, meta: dict) -> None:
    if db_path.exists():
        db_path.unlink()
    engine = Engine.from_uri(f"sqlite://{db_path.resolve()}")
    # noinspection PyProtectedMember
    GitLabLocalCache._init_db(engine)
    with engine as tx:
        tx.execute(
            SQL.insert(
                table="record",
                values={
                    "record_pickled": record.pickled,
                    "record_jsonb": SQL.funcs.jsonb(json.dumps(record.config)),
                    "sha1": record.record.sha1,
                },
            )
        )
        tx.execute(SQL.insert(table="meta", values={"key": "source_ref", "value": meta["ref"]}))
        tx.execute(SQL.insert(table="meta", values={"key": "source_project", "value": meta["project_id"]}))
        tx.execute(SQL.insert(table="meta", values={"key": "source_instance", "value": meta["instance"]}))
        tx.execute(SQL.insert(table="meta", values={"key": "head_commit", "value": meta["id"]}))


def main() -> None:
    """Entrypoint."""
    meta = {"instance": "gitlab.example.com", "project_id": "1234", "ref": "main", "id": "abc123"}
    base_path = Path("tests/resources/stores/gitlab_cache")
    record_path = base_path / "record.json"
    cache_path = base_path / "cache.db"

    record = _load_record(record_path, meta["id"])
    _init_db(db_path=cache_path, record=record, meta=meta)


if __name__ == "__main__":
    main()
