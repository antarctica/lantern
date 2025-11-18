# Lantern - Stores

Stores act as containers for [Records](/docs/data-model.md#records) and typically relate to a storage system such as a
database, file system or object store. Stores provide a consistent public interface to load and access Records.

## Stores usage

All stores implement a [Common Interface](#store-classes) supporting:

- accessing all loaded Records using the `store.records` list property
- accessing a specific Record by file identifier using `store.get()`

Stores MAY support additional functionality, such as writing new/updated Records back to a storage system.

> [!TIP]
> Store `get()` methods SHOULD be used as [Exporter](/docs/architecture.md#exporters) record lookup callables.

## Stores configuration

Stores use these options from the app `lantern.Config` class:

- `STORE_GITLAB_BRANCH`: remote branch name for [GitLab Store](#gitlab-store) records cache, will be created if it
  does not exist
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

## GitLab store

`lantern.stores.gitlab.GitLabStore`

Stores and tracks Records in a [GitLab](/docs/architecture.md#gitlab) project repository.

Supports reading, creating and updating Records using [`python-gitlab`](https://python-gitlab.readthedocs.io/en/stable/)
with a [Local Cache](#gitlab-local-cache) for performance.

Records are stored in the remote repository in a given branch. A hashed directory structure is used to store records as
in BAS 19115 JSON and ISO 19139 XML formats. For example a Record with file identifier `123abc` is stored as
`/records/12/3a/123abc.json` and `/records/12/3a/123abc.xml`.

### GitLab store branches

`GitLabStore` instances track a given branch. Multiple branches can be used to maintain different sets of Records.

> [!WARNING]
> The branch for a store SHOULD NOT be changed once initialised to avoid cache inconsistency errors.
>
> A separate, or replacement, store SHOULD be instantiated to switch branches.

Branches will be created automatically from `main` if they don't exist when [Committing Records](#committing-records).

Branches can be used for:

- drafting new or updated Records to be merging back into the conventional `main` branch when approved
- keeping records that change frequently (via automation) separate from other records, either as a long-lived parallel
  branch, or periodically merged and rebased back into `main`

### Loading remote records

`GitLabStore` instances are initially empty. Use `store.populate()` to load Records from the remote repository via the
[Local Cache](#gitlab-local-cache).

### Committing records

Records can be added or updated using `store.push()`. Internally this creates a commit to the remote repository and
requires:

- a list of new or updated Records
- a commit title and message
- an author name and email tuple

Commits include both the author and the Catalogue application as the committer.

<!-- pyml disable md028 -->
> [!TIP]
> The [Local Cache](#gitlab-local-cache) is refreshed automatically to reflect the updated remote repository.

> [!NOTE]
> Records cannot be deleted using the store, as records should generally be marked as withdrawn rather than removed.
> Records can be deleted directly in the remote repository, and local caches purged, if needed.
<!-- pyml enable md028 -->

### GitLab local cache

For increased performance, GitLab stores use a `GitLabLocalCache` to automatically maintain a local cache of Records.

> [!NOTE]
> Local caches are branch specific. Changing branch will automatically invalidate an existing cache.

The cache is a local folder consisting of:

```text
├── records/
│     └── *.pickle
├── commits.json
├── hashes.json
└── head_commit.json
```

| Path                | Description                                                                                  |
|---------------------|----------------------------------------------------------------------------------------------|
| `records/`          | Record configurations as pickled Record objects                                              |
| `commits.json`      | Mapping of record file identifiers to the last known head commit in the remote repository    |
| `hashes.json`       | Mapping of record file identifiers to SHA1 checksums of the record contents                  |
| `head_commit.json`  | Details of the head commit in the branch of the remote repository when the cache was created |

A cache is created by:

- fetching:
  - all record configurations and their latest commit from the given branch in the remote repository
  - details of the current head commit in this branch
- storing:
  - pickled versions of each record configuration loaded as a Record
  - a mapping of each record's SHA1 hash by file identifier
  - a mapping of each record's last known commit by file identifier
  - details of the current head commit and branch name

A cache is refreshed by:

- checking:
  - the current branch name matches the cached name
- fetching:
  - any commits that may have occurred since the last known head commit
  - record configurations from these commits
  - details of the current head commit for the overall remote repository
- storing:
  - updated records and head commit are stored as described above

<!-- pyml disable md028 -->
> [!IMPORTANT]
> Caches do not support moving or deleting files within the related remote repository, or changing branch. If detected
> when refreshing, the local cache is automatically purged and recreated in full to ensure consistency.

> [!NOTE]
> Where 50 or more commits have passed since the last cache update, the local cache will also be purged and recreated
> as this will be quicker than incrementally processing commits to refresh the cache.
<!-- pyml enable md028 -->

### GitLab Local cache testing

For testing, a pre-populated cache can be used to give reproducible results. To update this fixed cache, update files
in `tests/resources/stores/gitlab_cache` and then run:

```shell
% uv run python tests/resources/stores/gitlab_cache/refresh.py
```
