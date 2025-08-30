import json
from datetime import UTC, datetime

from freezegun.api import FrozenDateTimeFactory

from lantern.models.templates import PageMetadata


class TestPageMetadata:
    """Test page metadata dataclass."""

    def test_init(self, freezer: FrozenDateTimeFactory, fx_freezer_time: datetime):
        """Can create a PageMetadata instance with required values."""
        freezer.move_to(fx_freezer_time)
        expected = "x"
        meta = PageMetadata(
            build_key=expected,
            build_time=datetime.now(tz=UTC),
            html_title=expected,
            sentry_src=expected,
            plausible_domain=expected,
        )

        assert meta.build_key == expected
        assert meta.build_time == fx_freezer_time
        assert meta.html_title == f"{expected} | BAS Data Catalogue"
        assert meta.sentry_src == expected
        assert meta.plausible_domain == expected
        assert meta.html_open_graph == {}
        assert meta.html_schema_org is None
        assert "@" in meta.fallback_email

    def test_all(self, fx_freezer_time: datetime):
        """Can create a PageMetadata instance with all possible values."""
        expected_str = "x"
        expected_dict = {"x": "y"}
        meta = PageMetadata(
            build_key=expected_str,
            build_time=fx_freezer_time,
            html_title=expected_str,
            sentry_src=expected_str,
            plausible_domain=expected_str,
            html_open_graph=expected_dict,
            html_schema_org=json.dumps(expected_dict),
        )

        assert meta.html_open_graph == expected_dict
        assert json.loads(meta.html_schema_org) == expected_dict
