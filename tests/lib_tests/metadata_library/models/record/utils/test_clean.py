import pytest

from lantern.lib.metadata_library.models.record.utils.clean import clean_dict, clean_list


class TestCleanDict:
    """Test clean_dict util function."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ({}, {}),
            ({"foo": None}, {}),
            ({"zero": 0, "flag": False}, {"zero": 0, "flag": False}),
            ({"foo": []}, {}),
            ({"foo": {}}, {}),
            ({"foo": None, "bar": [], "baz": {}}, {}),
            ({"foo": {"bar": "x"}}, {"foo": {"bar": "x"}}),
            ({"foo": {"bar": {}}}, {}),
            ({"foo": {"bar": []}}, {}),
            ({"foo": {"bar": None}}, {}),
            ({"foo": {"bar": [None]}}, {}),
            ({"foo": ""}, {"foo": ""}),
        ],
    )
    def test_clean_dict(self, value: dict, expected: dict):
        """Can clean a dictionary containing None values."""
        result = clean_dict(value)
        assert result == expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ({}, {}),
            ({"foo": ""}, {}),
            ({"foo": " "}, {"foo": " "}),
            ({"foo": {"bar": ""}}, {}),
            ({"foo": {"bar": [""]}}, {}),
        ],
    )
    def test_clean_dict_strip_empty_str(self, value: dict, expected: dict):
        """Can optionally clean empty strings from a dict."""
        result = clean_dict(value, strip_empty_str=True)
        assert result == expected

    # noinspection PyTypeChecker
    @pytest.mark.cov()
    def test_clean_dict_wrong(self):
        """Cannot clean a non-dict."""
        with pytest.raises(TypeError, match=r"Value must be a dict"):
            # noinspection PyTypeChecker
            clean_dict([])


class TestCleanList:
    """Test clean_list util function."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ([], []),
            ([None], []),
            ([0, False], [0, False]),
            ([{}], []),
            ([None, [], {}], []),
            ([{"foo": None}], []),
            ([{"foo": []}], []),
            ([{"foo": {}}], []),
            ([{"foo": {"bar": "x"}}], [{"foo": {"bar": "x"}}]),
            ([{"foo": {"bar": {}}}], []),
            ([""], [""]),
        ],
    )
    def test_clean_list(self, value: list, expected: list):
        """Can clean a list containing None values."""
        result = clean_list(value)
        assert result == expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("value", "expected"), [([], []), ([""], []), ([" "], [" "]), ([{"foo": {"bar": ""}}, "x"], ["x"])]
    )
    def test_clean_list_strip_empty_str(self, value: list, expected: list):
        """Can optionally clean empty strings from a list."""
        result = clean_list(value, strip_empty_str=True)
        assert result == expected

    @pytest.mark.cov()
    def test_clean_list_wrong(self):
        """Cannot clean a non-list."""
        with pytest.raises(TypeError, match=r"Value must be a list"):
            # noinspection PyTypeChecker
            clean_list({})
