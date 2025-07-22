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
with a local cache for performance.

Records are stored in a hashed directory structure as both BAS 19115 JSON and ISO 19139 XML files. For example a Record
with a file identifier `123abc` is stored as `/records/12/3a/123abc.json` and `/records/12/3a/123abc.xml`.

### Loading remote records

`GitLabStore` instances are initially empty. Use `store.populate()` to load Records from the remote repository via the
[Local Cache](#local-cache). Supports optional filtering to:

- include specific file identifiers (and optionally records related to these selections)
- exclude specific file identifiers

These options cannot be used together. By default, all records are selected. Including related records is needed where
full rather than Summary Records are needed. For example to build physical maps, full Records are needed for each side.

> [!NOTE]
> The `GitLabStore` can be later emptied using `store.purge()`.

### Committing records

Records can be added or updated using `store.push()`. Internally this creates a commit to the remote repository and
requires:

- a list of new or updated Records
- a commit title and message
- an author name and email tuple

Commits include both the author and the Catalogue application as the committer.

The [Local Cache](#local-cache) is invalidated and recreated where:

- the list of Records is not empty
- and at least one Record has a different hash to those in the remote repository

### Local cache

For performance, `GitLabStore` instances maintain a local cache of Records and Record Summaries automatically. The
cache contains:

```
├── records/
├── head_commit.json
├── index.json
└── summaries.json
```

| Path               | Description                                                                     |
|--------------------|---------------------------------------------------------------------------------|
| `records/`         | Record configurations in BAS 19115 JSON format                                  |
| `head_commit.json` | Details of the head commit from remote repository when the cache was created    |
| `index.json`       | SHA1 checksums for each Record indexed by file identifier                       |
| `summaries.json`   | List of dicts with properties needed to create Record Summaries for all Records |

A cache is created by:

- extracting an archive of the remote repository, to avoid downloading each record or iterating through each commit
- storing details of the current head commit, to later determine whether the cache is stale
- hashing the contents of each record and indexing by their file identifier, to later determine if a record has changed
- storing subsets of each record needed to create Record Summaries, to avoiding needing to load full Records later

The store will automatically try to check whether the cache is stale before [Populating](#loading-remote-records) it,
or [Committing](#committing-records) records by checking the `head_commit.json` file against the remote repository's
current head commit. If the remote repository is unavailable (due to being offline for example), a warning is logged.
