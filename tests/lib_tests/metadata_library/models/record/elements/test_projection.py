from datetime import UTC, date, datetime

import cattrs
import pytest

from lantern.lib.metadata_library.models.record.elements.common import (
    Citation,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
)
from lantern.lib.metadata_library.models.record.elements.projection import Code, ReferenceSystemInfo
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode
from lantern.lib.metadata_library.models.record.utils.clean import clean_dict


class TestCode:
    """Test Code element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"value": "x"},
            {"value": "x", "href": "x"},
        ],
    )
    def test_init(self, values: dict):
        """Can create a Code element from directly assigned properties."""
        code = Code(**values)

        assert code.value == values["value"]

        if "href" in values:
            assert code.href == values["href"]
        else:
            assert code.href is None


class TestReferenceSystemInfo:
    """Test ReferenceSystemInfo element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"code": Code(value="x", href="x")},
            {"code": Code(value="x", href="x"), "version": "x"},
            {
                "code": Identifier(identifier="x", href="x", namespace="x"),
                "version": "x",
                "authority": Citation(
                    title="x", dates=Dates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)))
                ),
            },
        ],
    )
    def test_init(self, values: dict):
        """Can create a ReferenceSystemInfo element from directly assigned properties."""
        projection = ReferenceSystemInfo(**values)

        assert projection.code == values["code"]

        if "version" in values:
            assert projection.version == values["version"]
        else:
            assert projection.version is None

        if "authority" in values:
            assert projection.authority == values["authority"]
        else:
            assert projection.authority is None

    def test_structure_cattrs(self):
        """Can use Cattrs to create a ReferenceSystemInfo instance from plain types."""
        expected_date = date(2014, 6, 30)
        value = {
            "code": {"value": "x", "href": "x"},
            "version": "x",
            "authority": {
                "title": {"value": "x", "href": "x"},
                "dates": {"creation": expected_date.isoformat()},
                "contact": {"organisation": {"name": "x"}, "role": [ContactRoleCode.PUBLISHER.value]},
            },
        }
        expected = ReferenceSystemInfo(
            code=Code(value="x", href="x"),
            version="x",
            authority=Citation(
                title="x",
                href="x",
                dates=Dates(creation=Date(date=expected_date)),
                contacts=Contacts([Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.PUBLISHER})]),
            ),
        )

        converter = cattrs.Converter()
        converter.register_structure_hook(ReferenceSystemInfo, lambda d, t: ReferenceSystemInfo.structure(d))
        result = converter.structure(value, ReferenceSystemInfo)

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert a ReferenceSystemInfo instance into plain types."""
        expected_date = date(2014, 6, 30)
        value = ReferenceSystemInfo(
            code=Code(value="x", href="x"),
            version="x",
            authority=Citation(
                title="x",
                href="x",
                dates=Dates(creation=Date(date=expected_date)),
                contacts=Contacts([Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.PUBLISHER})]),
            ),
        )
        expected = {
            "code": {"value": "x", "href": "x"},
            "version": "x",
            "authority": {
                "title": {"value": "x", "href": "x"},
                "dates": {"creation": expected_date.isoformat()},
                "contact": {"organisation": {"name": "x"}, "role": [ContactRoleCode.PUBLISHER.value]},
            },
        }

        converter = cattrs.Converter()
        converter.register_unstructure_hook(ReferenceSystemInfo, lambda d: d.unstructure())
        result = clean_dict(converter.unstructure(value))

        assert result == expected
