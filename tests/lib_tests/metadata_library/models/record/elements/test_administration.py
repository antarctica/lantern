import json
from datetime import UTC, datetime

import cattrs
import pytest

from lantern.lib.metadata_library.models.record.elements.administration import Administration, Permission
from lantern.lib.metadata_library.models.record.utils.clean import clean_dict


class TestPermission:
    """Test permission element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"directory": "x", "group": "x"},
            {"directory": "x", "group": "x", "expiry": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)},
            {"directory": "x", "group": "x", "comments": "x"},
        ],
    )
    def test_init(self, values: dict):
        """Can create a Permission element from directly assigned properties."""
        permission = Permission(**values)

        assert permission.directory == values["directory"]
        assert permission.group == values["group"]
        assert permission.expiry == values["expiry"] if "expiry" in values else datetime.max.replace(tzinfo=UTC)
        if "comments" in values:
            assert permission.comments == values["comments"]
        else:
            assert permission.comments is None

    @pytest.mark.parametrize(
        ("a", "b", "expected"),
        [
            (Permission(directory="x", group="x"), Permission(directory="x", group="x"), True),
            (Permission(directory="x", group="x"), Permission(directory="x", group="y"), False),
            (Permission(directory="x", group="x"), Permission(directory="y", group="x"), False),
            (Permission(directory="x", group="x", comments="x"), Permission(directory="x", group="x"), True),
            (
                Permission(directory="x", group="x", comments="x"),
                Permission(directory="x", group="x", comments="y"),
                True,
            ),
        ],
    )
    def test_eq(self, a: Permission, b: Permission, expected: bool):
        """Can compare two Permission elements."""
        result = a == b
        assert result == expected

    @pytest.mark.cov()
    def test_eq_invalid(self):
        """Cannot compare non-Permission elements."""
        with pytest.raises(TypeError):
            _ = Permission(directory="x", group="x") == "x"


class TestAdministration:
    """Test administration element."""

    _schema = (
        "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/magic-admin-v1.json"
    )

    @pytest.mark.parametrize(
        "values",
        [
            {"id": "x"},
            {"id": "x", "gitlab_issues": ["x"]},
            {"id": "x", "access_permissions": [Permission(directory="x", group="x")]},
            {
                "id": "x",
                "gitlab_issues": ["x"],
                "access_permissions": [Permission(directory="x", group="x")],
            },
        ],
    )
    def test_init(self, values: dict):
        """Can create an Administration element from directly assigned properties."""
        administration = Administration(**values)

        assert administration.id == values["id"]
        if "gitlab_issues" in values:
            assert administration.gitlab_issues == values["gitlab_issues"]
        else:
            assert administration.gitlab_issues == []
        if "access_permissions" in values:
            assert administration.access_permissions == values["access_permissions"]
        else:
            assert administration.access_permissions == []

    def test_structure_cattrs(self):
        """Can use Cattrs to create an Administration instance from plain types."""
        expected_date = datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)

        value = {
            "$schema": self._schema,
            "id": "x",
            "gitlab_issues": ["x"],
            "access_permissions": [{"directory": "x", "group": "x", "expiry": expected_date.isoformat()}],
        }
        expected = Administration(
            id="x",
            gitlab_issues=["x"],
            access_permissions=[Permission(directory="x", group="x", expiry=expected_date)],
        )

        converter = cattrs.Converter()
        converter.register_structure_hook(Administration, lambda d, t: Administration.structure(d))
        result = converter.structure(value, Administration)

        assert result == expected

    @pytest.mark.cov()
    def test_structure_invalid_schema(self):
        """Cannot create an Administration instance from plain types with the wrong schema."""
        converter = cattrs.Converter()
        converter.register_structure_hook(Administration, lambda d, t: Administration.structure(d))

        with pytest.raises(ValueError, match=r"Unsupported JSON Schema in data."):
            converter.structure({"$schema": "x"}, Administration)

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert a DataQuality instance into plain types."""
        expected_date = datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)
        value = Administration(
            id="x",
            gitlab_issues=["x"],
            access_permissions=[Permission(directory="x", group="x", expiry=expected_date)],
        )
        expected = {
            "id": "x",
            "gitlab_issues": ["x"],
            "access_permissions": [{"directory": "x", "group": "x", "expiry": expected_date.isoformat()}],
        }

        converter = cattrs.Converter()
        converter.register_unstructure_hook(Administration, lambda d: d.unstructure())
        result = clean_dict(converter.unstructure(value))

        assert result == expected

    def test_json_dumps_loads(self):
        """Can convert an Administration instance to/from a JSON encoded string."""
        expected_date = datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)
        value = Administration(
            id="x",
            gitlab_issues=["x"],
            access_permissions=[Permission(directory="x", group="x", expiry=expected_date)],
        )

        result = value.dumps_json()
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["$schema"] == self._schema

        loop = Administration.loads_json(result)
        assert loop == value
