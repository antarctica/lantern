from dataclasses import dataclass
from typing import NamedTuple


@dataclass(kw_only=True)
class UpsertResults:
    """Minimum properties for results from an upsert operation."""

    new_identifiers: list[str]
    updated_identifiers: list[str]


class GitUpsertContext(NamedTuple):
    """Context needed for commits in Git like stores."""

    title: str
    message: str
    author_name: str
    author_email: str
    branch: str | None = None


@dataclass
class GitUpsertResults(UpsertResults):
    """Extended results for upserts into Git like stores."""

    branch: str
    commit: str | None
