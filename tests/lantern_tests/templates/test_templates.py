import json
from datetime import date

from lantern.models.templates import PageMetadata


class TestPageMetadata:
    """Test page metadata dataclass."""

    def test_init(self):
        """Can create a PageMetadata instance with required values."""
        expected = "x"
        meta = PageMetadata(build_key=expected, html_title=expected, sentry_src=expected, plausible_domain=expected)

        assert meta.build_key == expected
        assert meta.html_title == f"{expected} | BAS Data Catalogue"
        assert meta.sentry_src == expected
        assert meta.plausible_domain == expected
        assert meta.html_open_graph == {}
        assert meta.html_schema_org is None
        assert meta.current_year == date.today().year  # noqa: DTZ011

    def test_all(self):
        """Can create a PageMetadata instance with all possible values."""
        expected_str = "x"
        expected_dict = {"x": "y"}
        expected_int = 666
        meta = PageMetadata(
            build_key=expected_str,
            html_title=expected_str,
            sentry_src=expected_str,
            plausible_domain=expected_str,
            html_open_graph=expected_dict,
            html_schema_org=json.dumps(expected_dict),
            current_year=expected_int,
        )

        assert meta.html_open_graph == expected_dict
        assert json.loads(meta.html_schema_org) == expected_dict
        assert meta.current_year == expected_int
