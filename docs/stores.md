# Lantern - Stores

Stores act as containers for [Records](/docs/data-model.md#records) and typically relate to a storage system such as a
database, file system or object store. Stores provide a consistent public interface to access Records.

## Stores usage

All stores implement a [Common Interface](#store-classes) supporting:

- accessing some or all available Records using `store.select()`
- accessing a specific Record by file identifier using `store.select_one()`
- configuring a Store as [Frozen](#frozen-stores) (read-only)

Stores MAY support additional functionality, such as persisting new or updated Records in a backing system.

## Stores configuration

Stores use these options from the app `lantern.Config` class:

- `STORE_GITLAB_BRANCH`: remote branch name for [GitLab Store](#gitlab-store), will be created if it does not exist
- `STORE_GITLAB_STORE_CACHE_PATH`: local path for [GitLab Cached Store](#gitlab-cached-store), will be created if it
  does not exist
- `STORE_GITLAB_STORE_ENDPOINT`: API endpoint of a GitLab instance for [GitLab Store](#gitlab-store)
- `STORE_GITLAB_STORE_PROJECT_ID`: project ID within GitLab instance set by `STORE_GITLAB_STORE_ENDPOINT` for
  [GitLab Store](#gitlab-store)
- `STORE_GITLAB_TOKEN`: GitLab access token for [GitLab Store](#gitlab-store)
  - MUST be granted the `api` scope with at least *developer* access to the GitLab project set by
    `STORE_GITLAB_STORE_PROJECT_ID`

See the [Config](/docs/config.md#config-options) docs for how to set these config options.

See the [Infrastructure](/docs/infrastructure.md#exporters) docs for credentials used by stores.

## Store classes

All exporters inherit from the `lantern.stores.base.Store` abstract base class and MUST implement its minimal
public interface to:

- select Records
- configure a Store as [Frozen](#frozen-stores)

## Frozen stores

Stores can typically be created as frozen (read-only), by setting a `frozen` parameter on instantiation, which MAY
implement more efficient access to Records. Frozen stores are intended for data integrity and fast access is critical,
such as in distributed [Exporters](/docs/architecture.md#exporters).

> [!WARNING]
> Stores that do not support freezing will raise a `lantern.stores.exceptions.StoreFrozenUnsupportedError`.
>
> Frozen stores will raise a `lantern.stores.exceptions.StoreFrozenError` for any operations that would cause
> modifications, including possible remote retrievals.

## GitLab store

`lantern.stores.gitlab.GitLabStore`

Stores Records in a [GitLab](/docs/architecture.md#gitlab) project repository using
[`python-gitlab`](https://python-gitlab.readthedocs.io/en/stable/).

Supports reading, creating and updating Records. Does not support deleting or moving Records, or
[Freezing](#frozen-stores) as Records are accessed directly from GitLab.

> [!NOTE]
> This store only supports reading the latest (head) revision of records.

Records are stored in the remote repository in a given branch. A hashed directory structure is used to store records as
in BAS 19115 JSON and ISO 19139 XML formats. For example a Record with file identifier `123abc` is stored as
`/records/12/3a/123abc.json` and `/records/12/3a/123abc.xml`.

> [!TIP]
> The `GitLabStore` is a very inefficient if accessing large numbers of Records (e.g. for building the
> [Static Site](/docs/architecture.md#static-site)), due to the number of GitLab API calls.
>
> It is highly recommended to use a [`GitLabCachedStore`](#gitlab-cached-store) instead for these use cases.

### GitLab store branches

`GitLabStore` instances track a given branch. Multiple branches can be used to maintain different sets of Records for:

- drafting new or updated Records to be merging back into the conventional `main` branch when approved
- keeping records that change frequently (via automation) separate from other records, either as a long-lived parallel
  branch, or periodically merged and rebased back into `main`

Branches will be created automatically from `main` if they don't exist when [Committing Records](#gitlab-store-commits).

### GitLab store commits

Records can be added or updated using `store.push()`, which creates and pushes a commit to the remote repository.

> [!IMPORTANT]
> Records cannot be deleted, removed or moved using this store, as records should generally be marked as withdrawn or
> replaced and otherwise retained.

Pushing a set of changes requires:

- a list of new or updated Records
- a commit title and message
- an author (name and email tuple)

> [!NOTE]
> The GitLab user associated with the access token will be set as the committer, in addition to the author.

## GitLab cached store

`lantern.stores.gitlab_cache.GitLabCachedStore`

For increased read performance, GitLab cached stores extend [`GitLabStore`](#gitlab-store) with an automatically
maintained SQLite Records cache and support [Freezing](#frozen-stores).

> [!TIP]
> This backing cache is refreshed automatically when accessing records unless [Frozen](#frozen-stores).

A cache is created by:

- fetching record configurations, their latest commit ID, and the latest overall commit ID from GitLab
- storing pickled versions of each record as RecordRevisions, details of latest commits and configured GitLab info

A cache is refreshed by:

- checking the current branch and configured instance match the cached details
- fetching any commits since the cached last commit, and configurations for records these contain
- updating any relevant records and the head commit as described in the creation process

<!-- pyml disable md028 -->
> [!WARNING]
> Cached stores are branch and GitLab instance specific. Changing either will automatically invalidate the cache to
> avoid inconsistency errors. Separate, or replacement, (non-cached) stores SHOULD be used to switch branches.

> [!WARNING]
> If deleted, renamed or moved records are detected when refreshing, the cache is automatically purged and recreated in
> full to ensure consistency.

> [!NOTE]
> Where 50 or more commits have passed since the last cache update, the local cache will also be purged and recreated
> as this will be quicker than incrementally processing commits to refresh the cache.
<!-- pyml enable md028 -->

For testing, a [pre-populated cache database](/docs/dev.md#test-gitlab-local-cache) is available.
