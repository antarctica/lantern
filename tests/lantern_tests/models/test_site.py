import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from freezegun.api import FrozenDateTimeFactory

from lantern.config import Config
from lantern.models.item.base.elements import Link
from lantern.models.item.catalogue.elements import FormattedDate
from lantern.models.site import ExportMeta, SiteMeta
from lantern.stores.gitlab import GitLabStore


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
        )

        assert meta.base_url == expected
        assert meta.build_key == expected
        assert meta.build_time == fx_freezer_time
        assert meta.html_title == expected
        assert meta.sentry_src == expected
        assert meta.plausible_domain == expected
        assert meta.embedded_maps_endpoint == expected
        assert meta.items_enquires_endpoint == expected
        assert meta.fallback_email == "magic@bas.ac.uk"
        assert meta.build_repo_ref is None
        assert meta.build_repo_base_url is None
        assert meta.html_open_graph == {}
        assert meta.html_schema_org is None

    def test_all(self):
        """Can create a SiteMetadata instance with all possible values."""
        expected_str = "x"
        expected_dict = {"x": "y"}
        expected_time = datetime(2014, 6, 30, 14, 30, 45, tzinfo=UTC)

        meta = SiteMeta(
            base_url=expected_str,
            build_key=expected_str,
            html_title=expected_str,
            sentry_src=expected_str,
            plausible_domain=expected_str,
            embedded_maps_endpoint=expected_str,
            items_enquires_endpoint=expected_str,
            build_time=expected_time,
            fallback_email=expected_str,
            build_repo_ref=expected_str,
            build_repo_base_url=expected_str,
            html_open_graph=expected_dict,
            html_schema_org=json.dumps(expected_dict),
        )

        assert meta.build_time == expected_time
        assert meta.fallback_email == expected_str
        assert meta.build_repo_ref == expected_str
        assert meta.build_repo_base_url == expected_str
        assert meta.html_open_graph == expected_dict
        assert json.loads(meta.html_schema_org) == expected_dict

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

    @pytest.mark.parametrize(("has_store", "kwargs"), [(False, {"fallback_email": "y"}), (True, {})])
    def test_from_config_store(
        self, fx_config: Config, fx_gitlab_store_cached: GitLabStore, has_store: bool, kwargs: dict
    ):
        """Can create site metadata from config and optional store."""
        store = fx_gitlab_store_cached if has_store else None
        result = SiteMeta.from_config_store(config=fx_config, store=store, **kwargs)
        assert isinstance(result, SiteMeta)
        assert result.build_repo_ref == None if not has_store else fx_gitlab_store_cached.head_commit  # noqa: E711
        for key, value in kwargs.items():
            assert getattr(result, key) == value


class TestExportMetadata:
    """Test export metadata/context as an exception to SiteMetadata."""

    def test_init(self, freezer: FrozenDateTimeFactory, fx_freezer_time: datetime):
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
            export_path=expected_path,
            s3_bucket=expected_str,
            parallel_jobs=expected_int,
            source=expected_str,
        )

        assert meta.base_url == expected_str
        assert meta.export_path == expected_path
        assert meta.s3_bucket == expected_str
        assert meta.parallel_jobs == expected_int
        assert meta.source == expected_str

    def test_from_config_store(self, fx_config: Config):
        """Can create export metadata from config."""
        result = ExportMeta.from_config_store(config=fx_config)
        assert isinstance(result, ExportMeta)
        assert result.embedded_maps_endpoint == fx_config.TEMPLATES_ITEM_MAPS_ENDPOINT
        assert result.source == fx_config.NAME

    def test_as_site_metadata(self, fx_export_meta: ExportMeta):
        """Can create derived site metadata."""
        result = fx_export_meta.site_metadata
        assert not isinstance(result, ExportMeta)
        assert isinstance(result, SiteMeta)

        with pytest.raises(AttributeError):
            # noinspection PyUnresolvedReferences
            _ = result.export_path
