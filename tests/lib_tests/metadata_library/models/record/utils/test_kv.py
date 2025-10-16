import json

import pytest

from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.kv import get_kv, set_kv


class TestKv:
    """Tests for key-value utils."""

    @pytest.mark.parametrize(("value", "expected"), [(None, {}), ("", {}), (json.dumps({"x": "x"}), {"x": "x"})])
    def test_get_kv(self, fx_lib_record_model_min_iso: Record, value: str | None, expected: dict):
        """Can parse key-values from JSON string."""
        fx_lib_record_model_min_iso.identification.supplemental_information = value
        result = get_kv(fx_lib_record_model_min_iso)
        assert result == expected

    def test_get_kv_non_json(self, fx_lib_record_model_min_iso: Record):
        """Cannot parse key-values from non-JSON string."""
        fx_lib_record_model_min_iso.identification.supplemental_information = "x"
        with pytest.raises(ValueError, match="Supplemental information isn't JSON parsable."):
            get_kv(fx_lib_record_model_min_iso)

    def test_get_kv_non_dict(self, fx_lib_record_model_min_iso: Record):
        """Cannot parse key-values from non-dict JSON string."""
        fx_lib_record_model_min_iso.identification.supplemental_information = json.dumps(["x"])
        with pytest.raises(TypeError, match="Supplemental information isn't parsed as a dict."):
            get_kv(fx_lib_record_model_min_iso)

    @pytest.mark.parametrize(
        ("value", "existing_value", "replace", "expected_raw"),
        [
            ({}, None, False, None),
            ({}, json.dumps({}), False, None),
            ({"x": "x"}, json.dumps({"y": "y"}), False, json.dumps({"y": "y", "x": "x"})),
            ({"y": "x"}, json.dumps({"y": "y"}), False, json.dumps({"y": "x"})),
            ({"x": "x"}, json.dumps({"y": "y"}), True, json.dumps({"x": "x"})),
        ],
    )
    def test_set_kv(
        self,
        fx_lib_record_model_min_iso: Record,
        value: dict,
        existing_value: str | None,
        replace: bool,
        expected_raw: str,
    ):
        """Can encode key-values to a JSON string."""
        fx_lib_record_model_min_iso.identification.supplemental_information = existing_value
        set_kv(value, fx_lib_record_model_min_iso, replace=replace)
        result = fx_lib_record_model_min_iso.identification.supplemental_information
        assert result == expected_raw
