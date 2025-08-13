# Lantern - Stores

Stores act as containers for [Records](/docs/data-model.md#records) and typically relate to a storage system such as a
database, file system or object store. Stores provide a consistent public interface to load and access Records and
[Record Summaries](/docs/data-model.md#record-summaries).

## Stores configuration

Stores use these options from the app `lantern.Config` class:

- `STORE_GITLAB_STORE_CACHE_PATH`: local path for [GitLab Store](#gitlab-store) records cache, will be created if it
  does not exist
- `STORE_GITLAB_STORE_ENDPOINT`: API endpoint of a GitLab instance for [GitLab Store](#gitlab-store)
- `STORE_GITLAB_STORE_PROJECT_ID`: project ID within GitLab instance set by `STORE_GITLAB_STORE_ENDPOINT` for
  [GitLab Store](#gitlab-store)
- `STORE_GITLAB_TOKEN`: GitLab access token [GitLab Store](#gitlab-store)
  - SHOULD use a project access token with the `developer` role
  - MUST be granted the `api` scope and have access to the GitLab project set by `STORE_GITLAB_STORE_PROJECT_ID`

See the [Config](/docs/config.md#config-options) docs for how to set these config options.

See the [Infrastructure](/docs/infrastructure.md#exporters) docs for credentials used by stores.

## Store classes

All exporters inherit from the `lantern.stores.base.Store` abstract base class and MUST implement its minimal
public interface to:

- allow access to Records and Record Summaries

### Selecting records

All store classes support selecting Records and Record Summaries via `store.records` and `store.summaries` properties.

A specific Record can be selected by its file identifier using `store.get()`.

## GitLab store

`lantern.stores.gitlab.GitLabStore`

Stores and tracks Records in a [GitLab](/docs/architecture.md#gitlab) project repository.

Supports reading, creating and updating Records using [`python-gitlab`](https://python-gitlab.readthedocs.io/en/stable/)
with a [Local Cache](#gitlab-local-cache) for performance.

Records are stored in the remote repository in a hashed directory structure as both BAS 19115 JSON and ISO 19139 XML.
For example a Record with file identifier `123abc` is stored as `/records/12/3a/123abc.json` and `/records/12/3a/123abc.xml`.

### Loading remote records

`GitLabStore` instances are initially empty. Use `store.populate()` to load Records from the remote repository via the
[Local Cache](#gitlab-local-cache). By default, all records are selected. Alternatively, records can be filtered to:

- only include specific file identifiers (and optionally records related to these selections)
- exclude specific file identifiers

These options cannot be used together. Including related records is needed where full rather than Summary Records are
needed. For example to build physical maps where full Records are needed for each side.

> [!NOTE]
> The `GitLabStore` can be later emptied using `store.purge()`.

### Committing records

Records can be added or updated using `store.push()`. Internally this creates a commit to the remote repository and
requires:

- a list of new or updated Records
- a commit title and message
- an author name and email tuple

Commits include both the author and the Catalogue application as the committer.

The [Local Cache](#gitlab-local-cache) is recreated where a record has changed compared to the remote repository.

### GitLab Local cache

For increased performance, GitLab stores use a `GitLabLocalCache` to automatically maintain a local cache of Records
and Record Summaries. The cache contains:

```
├── records/
│     ├── *.json
│     └── *.pickle
├── commits.json
├── hashes.json
├── head_commit.json
└── summaries.json
```

| Path                | Description                                                                               |
|---------------------|-------------------------------------------------------------------------------------------|
| `records/`          | Record configurations in BAS 19115 JSON format and as pickled Record objects              |
| `commits.json`      | Mapping of record file identifiers to the latest Git commit for the record in remote repo |
| `hashes.json`       | Mapping of record file identifiers to SHA1 checksums of the record contents               |
| `head_commit.json`  | Details of the head commit from remote repository when the cache was created              |
| `summaries.json`    | List of dicts with properties needed to create Record Summaries for all Records           |

A cache is created by:

- fetching:
  - and extracting an archive of the remote repository
  - the latest commit for each record file in this archive
  - details of the current head commit for the overall remote repository
- storing:
  - a JSON version of each record config
  - a pickled version of each record loaded as Record
  - a mapping of each record's contents hash by its file identifier
  - a mapping of each record's latest commit by its file identifier
  - details of the current head commit
  - subsets of each record needed to create Record Summaries

### GitLab Local cache testing

For testing, a pre-populated cache contents can be copied into a cache instance to give reproducible results. To update
this fixed cache update files in `tests/resources/stores/gitlab_cache`, then run:

```
% uv run python tests/resources/stores/gitlab_cache/refresh.py
```
