import logging
from dataclasses import asdict, dataclass
from functools import cached_property

import requests
from mypy_boto3_s3 import S3Client
from requests.auth import HTTPBasicAuth

from lantern.config import Config
from lantern.exporters.base import Exporter
from lantern.lib.metadata_library.models.record.enums import AggregationAssociationCode
from lantern.models.item.website.search import ItemWebsiteSearch
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision


@dataclass(kw_only=True)
class WordPressSearchItem:
    """
    Workaround class for items within WordPress.

    Needed because there is a disconnect between the ItemWebsiteSearch and the prototype WordPress custom post type.
    Specifically the ItemWebsiteSearch class assumed a sync API would be used to aggregate in-scope items between
    catalogues, and a plugin within WordPress would determine which of these items existed, needed creating or removing.

    This class represents an experient to simplify this process by syncing items as a custom post type directly with
    WordPress via its REST API. This avoids the aggregation API and allows for a reduced WordPress plugin.

    If this approach is adopted, the ItemWebsiteSearch class should be updated accordingly and this class removed.

    Differences (ItemWebsiteSearch -> WordPressSearchItem):
    - id -> file_identifier
    - revision -> file_revision
    - type -> hierarchy_level
    - description -> content (to match WordPress core field)
    - date -> publication_date (should change back to date as it may not represent publication)
    - version -> edition
    - keywords -> **not included**
    - thumbnail_href -> href_thumbnail
    (These changes bring fields much closer to the original (ISO) record properties, much may or may not be better.)
    """

    # WordPress core fields
    title: str
    content: str

    # Additional meta fields
    file_identifier: str
    file_revision: str
    href: str
    hierarchy_level: str
    publication_date: str
    source: str
    edition: str | None = None
    href_thumbnail: str | None = None

    @classmethod
    def loads(cls, item: ItemWebsiteSearch) -> "WordPressSearchItem":
        """Create from ItemWebsiteSearch."""
        data = item.dumps()
        return cls(
            file_identifier=data["content"]["id"],
            file_revision=data["content"]["revision"],
            href=data["content"]["href"],
            title=data["content"]["title"],
            content=data["content"]["description"],
            hierarchy_level=data["content"]["type"],
            publication_date=data["content"]["date"],
            edition=data["content"]["version"],
            source=data["source"],
            href_thumbnail=data["content"]["thumbnail_href"],
        )


class WordPressClient:
    """
    Simple WordPress client.

    Intended for manging posts of a single type. Limited to the logic needed for the Public Website search exporter.
    """

    def __init__(self, logger: logging.Logger, config: Config) -> None:
        """Initialise client."""
        self._config = config
        self._logger = logger

        self._base_url = f"{self._config.PUBLIC_WEBSITE_ENDPOINT}/{self._config.PUBLIC_WEBSITE_POST_TYPE}"
        self._auth = HTTPBasicAuth(
            username=self._config.PUBLIC_WEBSITE_USERNAME, password=self._config.PUBLIC_WEBSITE_PASSWORD
        )

    @cached_property
    def posts(self) -> dict[str, dict]:
        """Posts indexed by WordPress post ID."""
        return {post["id"]: post for post in self._fetch_posts()}

    def _fetch_posts(self) -> list[dict]:
        """
        All posts of relevant type.

        Includes basic pagination support.
        """
        _posts = []
        page = 1
        params = {
            "per_page": 100,
            "orderby": "id",
            "order": "asc",
        }

        self._logger.info("Fetching existing posts from WordPress.")
        while True:
            params["page"] = page
            r = requests.get(auth=self._auth, timeout=10, url=self._base_url, params=params)
            r.raise_for_status()
            posts = r.json()
            _posts.extend(posts)
            if int(r.headers["X-WP-TotalPages"]) <= page:
                break
            page += 1

        return _posts

    def upsert(self, fields: dict, post_id: str | None = None) -> str | None:
        """
        Insert or update a post.

        If a post ID is provided it is updated, otherwise a new post is created.

        Posts are always set as published.
        """
        url = self._base_url
        params = {}
        fields["status"] = "publish"
        if post_id:
            url = f"{url}/{post_id}"
            params["context"] = "edit"
        r = requests.post(auth=self._auth, timeout=10, url=url, params=params, data=fields)
        r.raise_for_status()

    def delete(self, post_id: str) -> None:
        """Delete a post."""
        url = f"{self._base_url}/{post_id}"
        params = {}
        r = requests.delete(auth=self._auth, timeout=10, url=url, params=params)
        r.raise_for_status()


class WebsiteSearchExporter(Exporter):
    """
    Proto Public Website search exporter.

    Note: Intended for BAS use only.

    Manages items for searching selected records within the BAS public website (www.bas.ac.uk) to aid discovery. Items
    are stored in WordPress as a custom post type.

    See https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/450 for background information.

    This exporter:

    1. creates Website Search Items from records (which provide methods called during filtering)
    2. filters items locally to those which are:
        1. open access (based on an `unrestricted` access constraint)
        2. not superseded by another record (based on `RevisionOf` aggregations)

    Note: Due to the second filtering condition, this exporter cannot be implemented as a RecordExporter as foreign
    records determine whether a record is superseded rather than each target record independently.
    """

    def __init__(self, config: Config, logger: logging.Logger, s3: S3Client) -> None:
        """Initialise exporter."""
        super().__init__(config, logger, s3)
        self._wordpress_client = WordPressClient(logger=logger, config=config)
        self._records: list[RecordRevision] = []

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Public Website search results"

    def loads(self, records: list[RecordRevision]) -> None:
        """Populate exporter."""
        self._records = records

    @staticmethod
    def _get_superseded_records(records: list[RecordRevision]) -> list[str]:
        """List identifiers of records superseded by other records."""
        supersedes = set()
        for record in records:
            aggregations = record.identification.aggregations.filter(
                namespace=CATALOGUE_NAMESPACE, associations=AggregationAssociationCode.REVISION_OF
            )
            supersedes.update(aggregations.identifiers())
        return list(supersedes)

    @property
    def _items(self) -> list[ItemWebsiteSearch]:
        """Records as website search items."""
        return [
            ItemWebsiteSearch(record=record, source=self._config.NAME, base_url=self._config.BASE_URL)
            for record in self._records
        ]

    @property
    def _in_scope_items(self) -> list[ItemWebsiteSearch]:
        """
        Items in-scope for website search.

        See https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/450/#note_142966 for initial criteria.
        """
        superseded = self._get_superseded_records(self._records)
        return [item for item in self._items if item.resource_id not in superseded and item.open_access]

    @property
    def _in_scope_references(self) -> dict[str, str]:
        """References for in-scope items."""
        return {item.resource_id: item.resource_revision for item in self._in_scope_items}

    @property
    def _remote_references(self) -> dict[str, tuple[str, str]]:
        """
        References for items currently in WordPress.

        Includes file_revision [0] and WordPress post_id [1].
        """
        return {
            post["meta"]["file_identifier"]: (post["meta"]["file_revision"], post["id"])
            for post in self._wordpress_client.posts.values()
        }

    @property
    def _new_outdated_items(self) -> list[ItemWebsiteSearch]:
        """In-scope items which are different to WordPress."""
        new_outdated = []
        for file_identifier, file_revision in self._in_scope_references.items():
            if file_identifier not in self._remote_references or (
                file_identifier in self._remote_references
                and file_revision != self._remote_references[file_identifier][0]
            ):
                new_outdated.append(file_identifier)

        return [item for item in self._in_scope_items if item.resource_id in new_outdated]

    @property
    def _orphaned_items(self) -> dict[str, str]:
        """
        Items in WordPress which are no longer in-scope.

        Returns WordPress post_ids indexed by file_identifier.
        """
        in_scope_ids = self._in_scope_references.keys()
        return {
            file_identifier: post_id
            for file_identifier, (file_revision, post_id) in self._remote_references.items()
            if file_identifier not in in_scope_ids
        }

    def export(self) -> None:
        """Not supported, exporter depends on external system."""
        raise NotImplementedError() from None

    def publish(self) -> None:
        """Publish items to WordPress that are new or outdated and remove orphaned items."""
        remote_references = self._remote_references
        new_outdated = self._new_outdated_items
        for item in new_outdated:
            fields = asdict(WordPressSearchItem.loads(item))
            post_id = remote_references.get(item.resource_id, (None, None))[1]
            self._wordpress_client.upsert(post_id=post_id, fields=fields)
            self._logger.info(f"Synced item for record '{item.resource_id}'")
        for file_identifier, post_id in self._orphaned_items.items():
            self._wordpress_client.delete(post_id=post_id)
            self._logger.info(f"Deleted orphaned item for record '{file_identifier}'")
        for item in self._in_scope_items:
            if item not in new_outdated:
                self._logger.debug(f"Item for record '{item.resource_id}' unchanged, skipped.")
