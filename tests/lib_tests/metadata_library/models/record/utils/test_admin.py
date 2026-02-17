import json

import pytest
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from bas_metadata_library.standards.magic_administration.v1.utils import (
    AdministrationKeys,
    AdministrationMetadataSubjectMismatchError,
    AdministrationWrapper,
)

from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import get_admin, set_admin


class TestAdministrationGetSet:
    """Tests for get/set Administration metadata wrappers."""

    @pytest.mark.parametrize("value", [False, True])
    def test_get(
        self,
        fx_admin_meta_keys: AdministrationKeys,
        fx_admin_meta_element: AdministrationMetadata,
        fx_admin_wrapper: AdministrationWrapper,
        fx_lib_record_model_min_iso: Record,
        value: bool,
    ):
        """Can get administration metadata from a record if present."""
        expected = None
        if value:
            fx_lib_record_model_min_iso.file_identifier = "x"
            fx_admin_meta_element.id = fx_lib_record_model_min_iso.file_identifier
            fx_lib_record_model_min_iso.identification.supplemental_information = json.dumps(
                {"admin_metadata": fx_admin_wrapper.encode(fx_admin_meta_element)}
            )
            expected = fx_admin_meta_element

        result = get_admin(keys=fx_admin_meta_keys, record=fx_lib_record_model_min_iso)
        assert result == expected

    def test_get_mismatched_subject(
        self,
        fx_admin_meta_keys: AdministrationKeys,
        fx_admin_meta_element: AdministrationMetadata,
        fx_admin_wrapper: AdministrationWrapper,
        fx_lib_record_model_min_iso: Record,
    ):
        """Cannot get administration metadata that doesn't relate to the record that contains it."""
        fx_lib_record_model_min_iso.file_identifier = "x"
        fx_admin_meta_element.id = "y"
        fx_lib_record_model_min_iso.identification.supplemental_information = json.dumps(
            {"admin_metadata": fx_admin_wrapper.encode(fx_admin_meta_element)}
        )

        with pytest.raises(AdministrationMetadataSubjectMismatchError):
            get_admin(keys=fx_admin_meta_keys, record=fx_lib_record_model_min_iso)

    def test_set(
        self,
        fx_admin_meta_keys: AdministrationKeys,
        fx_admin_meta_element: AdministrationMetadata,
        fx_admin_wrapper: AdministrationWrapper,
        fx_lib_record_model_min_iso: Record,
    ):
        """Can set administration metadata in a record."""
        fx_lib_record_model_min_iso.file_identifier = "x"
        fx_admin_meta_element.id = fx_lib_record_model_min_iso.file_identifier

        set_admin(keys=fx_admin_meta_keys, record=fx_lib_record_model_min_iso, admin_meta=fx_admin_meta_element)
        result = json.loads(fx_lib_record_model_min_iso.identification.supplemental_information)
        # Can't directly compare tokens as they contain unique headers so check decoded contents.
        assert fx_admin_wrapper.decode(result["admin_metadata"]) == fx_admin_meta_element

    def test_set_mismatched_subject(
        self,
        fx_admin_meta_keys: AdministrationKeys,
        fx_admin_meta_element: AdministrationMetadata,
        fx_admin_wrapper: AdministrationWrapper,
        fx_lib_record_model_min_iso: Record,
    ):
        """Cannot set administration metadata that doesn't relate to the record that contains it."""
        fx_lib_record_model_min_iso.file_identifier = "x"
        fx_admin_meta_element.id = "y"

        with pytest.raises(AdministrationMetadataSubjectMismatchError):
            set_admin(keys=fx_admin_meta_keys, record=fx_lib_record_model_min_iso, admin_meta=fx_admin_meta_element)
