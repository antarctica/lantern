# run this script if record is changed to re-generated pickle file
import json
import pickle
from pathlib import Path

from lantern.models.record.revision import RecordRevision

base_path = Path("tests/resources/stores/gitlab_cache")
record_path = base_path / "records/a1b2c3.json"

with base_path.joinpath("head_commit.json").open() as f:
    head_commit = json.load(f)

with record_path.open() as f:
    record_data = json.load(f)

record = RecordRevision.loads({"file_revision": head_commit["id"], **record_data})

with record_path.with_suffix(".pickle").open(mode="wb") as f:
    # noinspection PyTypeChecker
    pickle.dump(record, f, pickle.HIGHEST_PROTOCOL)

with base_path.joinpath("commits.json").open(mode="w") as f:
    data = {"commits": {record.file_identifier: record.file_revision}}
    json.dump(data, f, indent=2)

with base_path.joinpath("hashes.json").open(mode="w") as f:
    data = {"hashes": {record.file_identifier: record.sha1}}
    json.dump(data, f, indent=2)
