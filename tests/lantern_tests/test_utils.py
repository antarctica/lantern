import pytest
from jinja2 import Environment

from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.utils import get_jinja_env, get_record_aliases, prettify_html


@pytest.mark.cov()
class TestUtils:
    """Test app utils not tested elsewhere."""

    def test_get_record_aliases(self, fx_revision_model_min: RecordRevision):
        """Can get any aliases in a record."""
        alias = Identifier(identifier="x", href=f"https://{CATALOGUE_NAMESPACE}/datasets/x", namespace=ALIAS_NAMESPACE)

        fx_revision_model_min.identification.identifiers.append(alias)
        result = get_record_aliases(fx_revision_model_min)
        assert len(result) == 1
        assert result[0] == alias

    def test_get_jinja_env(self):
        """Can get app Jinja environment."""
        result = get_jinja_env()
        assert isinstance(result, Environment)
        assert "_macros/common.html.j2" in result.loader.list_templates()

    def test_prettify_html(self):
        """Can format HTML."""
        assert (
            prettify_html(html="<html>\n\n\n\n\n<body><p>...</p></body></html>")
            == "<html>\n<body><p>...</p></body></html>"
        )
