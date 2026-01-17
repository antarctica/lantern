import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import PropertyMock

import pytest
from freezegun.api import FrozenDateTimeFactory
from pytest_mock import MockerFixture

from lantern.config import Config
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys
from lantern.models.item.base.elements import Link
from lantern.models.item.catalogue.elements import FormattedDate
from lantern.models.site import ExportMeta, OpenGraphMeta, SchemaOrgAuthor, SchemaOrgMeta, SiteMeta, SitePageMeta
from lantern.stores.gitlab import GitLabStore


class TestOpenGraphMeta:
    """Test Open Graph metadata."""

    def test_init(self):
        """Can create an Open Graph metadata instance with required values."""
        expected = "x"
        meta = OpenGraphMeta(title=expected, url=expected)
        assert meta.title == expected
        assert meta.url == expected
        assert meta.locale is not None
        assert meta.site_name is not None
        assert meta.type_ is not None
        assert meta.description is None
        assert meta.image is None
        assert meta.published_at is None

    def test_all(self):
        """Can create an Open Graph metadata instance with all possible values."""
        expected = "x"
        meta = OpenGraphMeta(
            locale=expected,
            site_name=expected,
            type_=expected,
            title=expected,
            url=expected,
            description=expected,
            image=expected,
            published_at=expected,
        )
        assert meta.title == expected
        assert meta.url == expected
        assert meta.locale == expected
        assert meta.site_name == expected
        assert meta.type_ == expected
        assert meta.description == expected
        assert meta.image == expected
        assert meta.published_at == expected


class TestSchemaOrgAuthor:
    """Test Schema.org author element."""

    def test_init(self):
        """Can create a Schema.org author instance with required values."""
        expected = "x"
        expected_type = "Person"
        # noinspection PyTypeChecker
        author = SchemaOrgAuthor(
            type_=expected_type,
            name=expected,
        )
        assert author.type_ == expected_type
        assert author.name == expected
        assert author.url is None

    def test_all(self):
        """Can create a Schema.org author instance with all possible values."""
        expected = "x"
        expected_type = "Organization"
        # noinspection PyTypeChecker
        author = SchemaOrgAuthor(
            type_=expected_type,
            name=expected,
            url=expected,
        )
        assert author.type_ == expected_type
        assert author.name == expected
        assert author.url == expected

    def test_dumps(self):
        """Can dump a Schema.org author instance as a dict with correct keys."""
        expected = {"@type": "Person", "name": "x", "url": "x"}
        # noinspection PyTypeChecker
        author = SchemaOrgAuthor(
            type_=expected["@type"],
            name=expected["name"],
            url=expected["url"],
        )
        assert author.dumps() == expected


class TestSchemaOrgMeta:
    """Test Schema.org metadata."""

    def test_init(self):
        """Can create a Schema.org metadata instance with required values."""
        expected = "x"
        meta = SchemaOrgMeta(
            headline=expected,
            url=expected,
        )
        assert meta.headline == expected
        assert meta.url == expected
        assert meta.context == "https://schema.org/"
        assert meta.type_ is not None
        assert meta.name is not None
        assert meta.description is None
        assert meta.image is None
        assert len(meta.creator) == 0

    def test_all(self):
        """Can create a Schema.org metadata instance with all possible values."""
        expected = "x"
        expected_type = "Article"
        # noinspection PyTypeChecker
        meta = SchemaOrgMeta(
            type_=expected_type,
            name=expected,
            headline=expected,
            url=expected,
            description=expected,
            image=expected,
            creator=[SchemaOrgAuthor(type_="Person", name=expected)],
        )
        assert meta.type_ == expected_type
        assert meta.name == expected
        assert meta.headline == expected
        assert meta.url == expected
        assert meta.description == expected
        assert meta.image == expected
        assert len(meta.creator) == 1

    def test_dumps(self):
        """Can dump a Schema.org metadata instance as a dict with correct keys."""
        expected = {
            "@context": "https://schema.org/",
            "@type": "Article",
            "name": "x",
            "headline": "x",
            "url": "x",
            "description": "x",
            "image": "x",
            "creator": [{"@type": "Person", "name": "x"}],
        }
        # noinspection PyTypeChecker
        meta = SchemaOrgMeta(
            type_=expected["@type"],
            name=expected["name"],
            headline=expected["headline"],
            url=expected["url"],
            description=expected["description"],
            image=expected["image"],
            creator=[SchemaOrgAuthor(type_=expected["creator"][0]["@type"], name=expected["creator"][0]["name"])],
        )
        assert meta._dumps() == expected

        # noinspection PyTypeChecker
        meta_no_list = SchemaOrgMeta(
            type_=expected["@type"],
            name=expected["name"],
            headline=expected["headline"],
            url=expected["url"],
            description=expected["description"],
            image=expected["image"],
        )
        assert "creator" not in meta_no_list._dumps()

    def test_str(self):
        """Can encode a Schema.org metadata instance as a string for use in templates."""
        expected = {
            "@context": "https://schema.org/",
            "@type": "Article",
            "name": "x",
            "headline": "x",
            "url": "x",
            "description": "x",
            "image": "x",
            "creator": [{"@type": "Person", "name": "x"}],
        }
        # noinspection PyTypeChecker
        meta = SchemaOrgMeta(
            type_=expected["@type"],
            name=expected["name"],
            headline=expected["headline"],
            url=expected["url"],
            description=expected["description"],
            image=expected["image"],
            creator=[SchemaOrgAuthor(type_=expected["creator"][0]["@type"], name=expected["creator"][0]["name"])],
        )
        assert str(meta) == json.dumps(expected, indent=2)


class TestSitePageMeta:
    """Test site page metadata."""

    def test_init(self):
        """Can create a SitePageMeta instance with required values."""
        expected = "x"
        page_meta = SitePageMeta(
            title=expected,
            url=expected,
        )

        assert page_meta.title == expected
        assert page_meta.url == expected
        assert page_meta.description is None
        assert page_meta.inc_meta is True
        assert isinstance(page_meta.open_graph, OpenGraphMeta)
        assert isinstance(page_meta.schema_org, SchemaOrgMeta)

    def test_all(self):
        """Can create a SitePageMeta instance with all possible values."""
        expected = "x"
        page_meta = SitePageMeta(title=expected, url=expected, description=expected, inc_meta=False)

        assert page_meta.title == expected
        assert page_meta.url == expected
        assert page_meta.description == expected
        assert page_meta.inc_meta is False
        assert page_meta.open_graph is None
        assert page_meta.schema_org is None


class TestSiteMetadata:
    """Test site metadata/context."""

    def test_init(self, freezer: FrozenDateTimeFactory, fx_freezer_time: datetime):
        """Can create a SiteMetadata instance with required values."""
        freezer.move_to(fx_freezer_time)
        expected = "x"
        meta = SiteMeta(
            base_url=expected,
            build_key=expected,
            html_title=expected,
            sentry_src=expected,
            plausible_domain=expected,
            embedded_maps_endpoint=expected,
            items_enquires_endpoint=expected,
            items_enquires_turnstile_key=expected,
            generator=expected,
            version=expected,
        )

        assert meta.base_url == expected
        assert meta.build_key == expected
        assert meta.html_title == expected
        assert meta.sentry_src == expected
        assert meta.plausible_domain == expected
        assert meta.embedded_maps_endpoint == expected
        assert meta.items_enquires_endpoint == expected
        assert meta.items_enquires_turnstile_key == expected
        assert meta.generator == expected
        assert meta.version == expected
        assert meta.build_time == fx_freezer_time
        assert meta.fallback_email == "magic@bas.ac.uk"
        assert meta.build_repo_ref is None
        assert meta.build_repo_base_url is None
        assert meta.html_open_graph is None
        assert meta.html_schema_org is None
        assert meta.html_description is None

    def test_all(self):
        """Can create a SiteMetadata instance with all possible values."""
        expected_str = "x"
        expected_open_graph = OpenGraphMeta(title=expected_str, url=expected_str)
        expected_schema_org = SchemaOrgMeta(headline=expected_str, url=expected_str)
        expected_time = datetime(2014, 6, 30, 14, 30, 45, tzinfo=UTC)

        meta = SiteMeta(
            base_url=expected_str,
            build_key=expected_str,
            html_title=expected_str,
            sentry_src=expected_str,
            plausible_domain=expected_str,
            embedded_maps_endpoint=expected_str,
            items_enquires_endpoint=expected_str,
            items_enquires_turnstile_key=expected_str,
            generator=expected_str,
            version=expected_str,
            build_time=expected_time,
            fallback_email=expected_str,
            build_repo_ref=expected_str,
            build_repo_base_url=expected_str,
            html_open_graph=expected_open_graph,
            html_schema_org=expected_schema_org,
            html_description=expected_str,
        )

        assert meta.build_time == expected_time
        assert meta.fallback_email == expected_str
        assert meta.build_repo_ref == expected_str
        assert meta.build_repo_base_url == expected_str
        assert meta.html_open_graph == expected_open_graph
        assert meta.html_schema_org == expected_schema_org
        assert meta.html_description == expected_str

    def test_html_title_suffixed(self, fx_site_meta: SiteMeta):
        """Can get HTML title with site name."""
        fx_site_meta.html_title = "x"
        assert fx_site_meta.html_title_suffixed == "x | BAS Data Catalogue"

    @pytest.mark.parametrize("value", [None, "1234567890"])
    def test_build_ref(self, fx_site_meta: SiteMeta, value: str | None):
        """Can get link to commit if values set."""
        fx_site_meta.build_repo_ref = value
        fx_site_meta.build_repo_base_url = "y"

        result = fx_site_meta.build_ref
        if value is not None:
            assert isinstance(result, Link)
            assert result.value == value[:8]
        else:
            assert result is None

    def test_build_time_formatted(self, fx_site_meta: SiteMeta):
        """Can get build time as formatted date."""
        assert isinstance(fx_site_meta.build_time_fmt, FormattedDate)

    @pytest.mark.parametrize("has_value", [False, True])
    def test_html_open_graph_tags(self, fx_site_meta: SiteMeta, has_value: str):
        """Can get Open Graph tags as a dict, if set."""
        fx_site_meta.html_open_graph = OpenGraphMeta(title="x", url="x") if has_value else None
        if has_value:
            assert isinstance(fx_site_meta.html_open_graph_tags, dict)
            return
        assert fx_site_meta.html_open_graph_tags is None

    @pytest.mark.parametrize("has_value", [False, True])
    def test_html_schema_org_content(self, fx_site_meta: SiteMeta, has_value: str):
        """Can get Schema.org metadata as a str, if set."""
        fx_site_meta.html_schema_org = SchemaOrgMeta(headline="x", url="x") if has_value else None
        if has_value:
            assert isinstance(fx_site_meta.html_schema_org_content, str)
            return
        assert fx_site_meta.html_schema_org_content is None

    def test_from_page_meta(self, fx_site_meta: SiteMeta, fx_site_page_meta: SitePageMeta):
        """Can apply page metadata."""
        fx_site_meta.apply_page_meta(fx_site_page_meta)
        assert fx_site_meta.html_title == fx_site_page_meta.title
        assert fx_site_meta.html_description == fx_site_page_meta.description

    @pytest.mark.parametrize(("has_store", "kwargs"), [(False, {"fallback_email": "y"}), (True, {})])
    def test_from_config_store(
        self, mocker: MockerFixture, fx_config: Config, fx_gitlab_store: GitLabStore, has_store: bool, kwargs: dict
    ):
        """Can create site metadata from config and optional store."""
        mocker.patch.object(type(fx_gitlab_store), "head_commit", new_callable=PropertyMock, return_value="x")
        store = fx_gitlab_store if has_store else None

        result = SiteMeta.from_config_store(config=fx_config, store=store, **kwargs)
        assert isinstance(result, SiteMeta)
        assert result.build_repo_ref == None if not has_store else fx_gitlab_store.head_commit  # noqa: E711
        for key, value in kwargs.items():
            assert getattr(result, key) == value


class TestExportMetadata:
    """Test export metadata/context as an exception to SiteMetadata."""

    def test_init(
        self, freezer: FrozenDateTimeFactory, fx_freezer_time: datetime, fx_admin_meta_keys: AdministrationKeys
    ):
        """Can create a SiteMetadata instance with required values."""
        freezer.move_to(fx_freezer_time)
        expected_str = "x"
        expected_int = 1
        expected_path = Path("./x")
        meta = ExportMeta(
            base_url=expected_str,
            build_key=expected_str,
            html_title=expected_str,
            sentry_src=expected_str,
            plausible_domain=expected_str,
            embedded_maps_endpoint=expected_str,
            items_enquires_endpoint=expected_str,
            items_enquires_turnstile_key=expected_str,
            generator=expected_str,
            version=expected_str,
            export_path=expected_path,
            s3_bucket=expected_str,
            parallel_jobs=expected_int,
            admin_meta_keys=fx_admin_meta_keys,
        )

        assert meta.base_url == expected_str
        assert meta.export_path == expected_path
        assert meta.s3_bucket == expected_str
        assert meta.parallel_jobs == expected_int
        assert meta.admin_meta_keys == fx_admin_meta_keys
        assert meta.trusted is False  # default

    def test_from_config_store(self, fx_config: Config):
        """Can create export metadata from config."""
        result = ExportMeta.from_config_store(config=fx_config)
        assert isinstance(result, ExportMeta)
        assert result.embedded_maps_endpoint == fx_config.TEMPLATES_ITEM_MAPS_ENDPOINT

    def test_as_site_metadata(self, fx_export_meta: ExportMeta):
        """Can create derived site metadata."""
        result = fx_export_meta.site_metadata
        assert not isinstance(result, ExportMeta)
        assert isinstance(result, SiteMeta)

        with pytest.raises(AttributeError):
            # noinspection PyUnresolvedReferences
            _ = result.export_path
