import json
import pickle

import pytest
from cryptography.hazmat.primitives.keywrap import InvalidUnwrap
from jwskate import InvalidClaim, InvalidSignature, Jwk, JwtSigner

from lantern.lib.metadata_library.models.record.elements.administration import Administration
from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import (
    AdministrationKeys,
    AdministrationWrapper,
    AdministrativeMetadataIntegrityError,
    AdministrativeMetadataSubjectMismatchError,
    get_admin,
    set_admin,
)


class TestAdministrationKeys:
    """Tests for Administrative metadata keys container."""

    signing_key_private = Jwk.generate(alg="ES256", kid="signing_key")
    signing_key_public = signing_key_private.public_jwk()
    encryption_key_private = Jwk.generate(alg="ECDH-ES+A128KW", crv="P-256", kid="encryption_key")

    @pytest.mark.parametrize(
        ("signing_private", "signing_public"),
        [(signing_key_private, None), (None, signing_key_public), (signing_key_private, signing_key_public)],
    )
    def test_init(self, signing_private: Jwk | None, signing_public: Jwk | None):
        """Can create administrative key's container."""
        result = AdministrationKeys(
            signing_public=signing_public,
            signing_private=signing_private,
            encryption_private=self.encryption_key_private,
        )
        assert result.encryption_private == self.encryption_key_private
        assert result.signing_private == signing_private
        assert result.signing_public == signing_public if signing_public else self.signing_key_public

    def test_init_no_signing(self):
        """Cannot create administrative key's container without a signing key."""
        with pytest.raises(TypeError, match=r"Public or private signing_key must be provided."):
            AdministrationKeys(
                signing_public=None,
                signing_private=None,
                encryption_private=self.encryption_key_private,
            )

    @pytest.mark.parametrize("signing_private", [signing_key_private, None])
    def test_pickle(self, signing_private: Jwk | None):
        """Can pickle/unpickle keys to JSON."""
        public = self.signing_key_public if signing_private is None else None
        keys = AdministrationKeys(
            signing_private=signing_private,
            signing_public=public,
            encryption_private=self.encryption_key_private,
        )

        pickled = pickle.dumps(keys, pickle.HIGHEST_PROTOCOL)
        result: AdministrationKeys = pickle.loads(pickled)  # noqa: S301
        assert result.encryption_private == keys.encryption_private
        assert result.signing_private == keys.signing_private
        assert result.signing_public == keys.signing_public

    @pytest.mark.cov()
    def test_not_eq(self, fx_admin_meta_keys: AdministrationKeys):
        """Cannot compare if non-keys instances are equal."""
        assert fx_admin_meta_keys != 1


class TestAdministrationSeal:
    """Tests for Administrative metadata signing/encryption wrapper."""

    def test_init(self, fx_admin_meta_keys: AdministrationKeys):
        """Can create administrative metadata wrapper."""
        seal = AdministrationWrapper(fx_admin_meta_keys)
        assert seal._keys == fx_admin_meta_keys

    def test_encode(self, fx_admin_wrapper: AdministrationWrapper, fx_admin_meta_element: Administration):
        """Can sign and encrypt administrative metadata."""
        result = fx_admin_wrapper.encode(fx_admin_meta_element)
        assert isinstance(result, str)

    @pytest.mark.cov()
    def test_encode_no_keys(self, fx_admin_wrapper: AdministrationWrapper, fx_admin_meta_element: Administration):
        """Cannot sign administrative metadata without private signing key."""
        wrapper = AdministrationWrapper(
            keys=AdministrationKeys(
                encryption_private=fx_admin_wrapper._keys.encryption_private,
                signing_public=fx_admin_wrapper._keys.signing_public,
            )
        )
        with pytest.raises(ValueError, match=r"Private signing key is required for writing metadata."):
            wrapper.encode(fx_admin_meta_element)

    def test_decode(self, fx_admin_wrapper: AdministrationWrapper, fx_admin_meta_element: Administration):
        """Can sign and encrypt administrative metadata."""
        value = fx_admin_wrapper.encode(fx_admin_meta_element)

        result = fx_admin_wrapper.decode(value)
        assert isinstance(result, Administration)

    def test_decode_bad_encryption(
        self, fx_admin_wrapper: AdministrationWrapper, fx_admin_meta_element: Administration
    ):
        """Cannot decrypt administrative metadata with the wrong encryption key."""
        alt_encryption_key = Jwk.generate(alg="ECDH-ES+A128KW", crv="P-256", kid="alt_encryption_key")
        alt_keys = AdministrationKeys(
            signing_public=fx_admin_wrapper._keys.signing_public,
            signing_private=fx_admin_wrapper._keys.signing_private,
            encryption_private=alt_encryption_key,
        )
        alt_wrapper = AdministrationWrapper(alt_keys)
        value = alt_wrapper.encode(fx_admin_meta_element)

        with pytest.raises(InvalidUnwrap):
            fx_admin_wrapper.decode(value)

    def test_decode_bad_validate_key(
        self, fx_admin_wrapper: AdministrationWrapper, fx_admin_meta_element: Administration
    ):
        """Cannot validate administrative metadata with the wrong public signing key."""
        value = fx_admin_wrapper.encode(fx_admin_meta_element)

        alt_verify_key = Jwk.generate(alg="ES256", kid="alt_signing_key").public_jwk()
        alt_keys = AdministrationKeys(
            signing_public=alt_verify_key,
            signing_private=None,
            encryption_private=fx_admin_wrapper._keys.encryption_private,
        )
        alt_wrapper = AdministrationWrapper(alt_keys)

        with pytest.raises(InvalidSignature):
            alt_wrapper.decode(value)

    def test_decode_bad_issuer(self, fx_admin_wrapper: AdministrationWrapper, fx_admin_meta_element: Administration):
        """Cannot validate administrative metadata with the wrong issuer."""
        alt_signer = JwtSigner(issuer="x", key=fx_admin_wrapper._keys.signing_private)
        value = str(
            alt_signer.sign(
                subject=fx_admin_meta_element.id,
                audience=fx_admin_wrapper._audience,
                extra_claims={"pyd": fx_admin_meta_element.dumps_json()},
            ).encrypt(key=fx_admin_wrapper._keys.encryption_private.public_jwk(), enc=fx_admin_wrapper._enc_alg)
        )

        with pytest.raises(InvalidClaim) as e:
            fx_admin_wrapper.decode(value)
        assert e.value.args[1] == "iss"

    def test_decode_bad_audience(self, fx_admin_wrapper: AdministrationWrapper, fx_admin_meta_element: Administration):
        """Cannot validate administrative metadata with the wrong audience."""
        alt_signer = JwtSigner(issuer=fx_admin_wrapper._issuer, key=fx_admin_wrapper._keys.signing_private)
        value = str(
            alt_signer.sign(
                subject=fx_admin_meta_element.id,
                audience="x",
                extra_claims={"pyd": fx_admin_meta_element.dumps_json()},
            ).encrypt(key=fx_admin_wrapper._keys.encryption_private.public_jwk(), enc=fx_admin_wrapper._enc_alg)
        )

        with pytest.raises(InvalidClaim) as e:
            fx_admin_wrapper.decode(value)
        assert e.value.args[1] == "aud"

    def test_decode_bad_subject(self, fx_admin_wrapper: AdministrationWrapper, fx_admin_meta_element: Administration):
        """Cannot validate administrative metadata with the wrong audience."""
        signer = JwtSigner(issuer=fx_admin_wrapper._issuer, key=fx_admin_wrapper._keys.signing_private)
        value = str(
            signer.sign(
                subject="invalid",
                audience=fx_admin_wrapper._audience,
                extra_claims={"pyd": fx_admin_meta_element.dumps_json()},
            ).encrypt(key=fx_admin_wrapper._keys.encryption_private.public_jwk(), enc=fx_admin_wrapper._enc_alg)
        )

        with pytest.raises(AdministrativeMetadataIntegrityError):
            fx_admin_wrapper.decode(value)


class TestAdministrationGetSet:
    """Tests for get/set Administrative metadata wrappers."""

    @pytest.mark.parametrize("value", [False, True])
    def test_get(
        self,
        fx_admin_meta_keys: AdministrationKeys,
        fx_admin_meta_element: Administration,
        fx_admin_wrapper: AdministrationWrapper,
        fx_lib_record_model_min_iso: Record,
        value: bool,
    ):
        """Can get administrative metadata from a record if present."""
        expected = None
        if value:
            fx_lib_record_model_min_iso.file_identifier = "x"
            fx_admin_meta_element.id = fx_lib_record_model_min_iso.file_identifier
            fx_lib_record_model_min_iso.identification.supplemental_information = json.dumps(
                {"administrative_metadata": fx_admin_wrapper.encode(fx_admin_meta_element)}
            )
            expected = fx_admin_meta_element

        result = get_admin(keys=fx_admin_meta_keys, record=fx_lib_record_model_min_iso)
        assert result == expected

    def test_get_mismatched_subject(
        self,
        fx_admin_meta_keys: AdministrationKeys,
        fx_admin_meta_element: Administration,
        fx_admin_wrapper: AdministrationWrapper,
        fx_lib_record_model_min_iso: Record,
    ):
        """Cannot get administrative metadata that doesn't relate to the record that contains it."""
        fx_lib_record_model_min_iso.file_identifier = "x"
        fx_admin_meta_element.id = "y"
        fx_lib_record_model_min_iso.identification.supplemental_information = json.dumps(
            {"administrative_metadata": fx_admin_wrapper.encode(fx_admin_meta_element)}
        )

        with pytest.raises(AdministrativeMetadataSubjectMismatchError):
            get_admin(keys=fx_admin_meta_keys, record=fx_lib_record_model_min_iso)

    def test_set(
        self,
        fx_admin_meta_keys: AdministrationKeys,
        fx_admin_meta_element: Administration,
        fx_admin_wrapper: AdministrationWrapper,
        fx_lib_record_model_min_iso: Record,
    ):
        """Can set administrative metadata in a record."""
        fx_lib_record_model_min_iso.file_identifier = "x"
        fx_admin_meta_element.id = fx_lib_record_model_min_iso.file_identifier

        set_admin(keys=fx_admin_meta_keys, record=fx_lib_record_model_min_iso, admin_meta=fx_admin_meta_element)
        result = json.loads(fx_lib_record_model_min_iso.identification.supplemental_information)
        # Can't directly compare tokens as they contain unique headers so check decoded contents.
        assert fx_admin_wrapper.decode(result["administrative_metadata"]) == fx_admin_meta_element

    def test_set_mismatched_subject(
        self,
        fx_admin_meta_keys: AdministrationKeys,
        fx_admin_meta_element: Administration,
        fx_admin_wrapper: AdministrationWrapper,
        fx_lib_record_model_min_iso: Record,
    ):
        """Cannot set administrative metadata that doesn't relate to the record that contains it."""
        fx_lib_record_model_min_iso.file_identifier = "x"
        fx_admin_meta_element.id = "y"

        with pytest.raises(AdministrativeMetadataSubjectMismatchError):
            set_admin(keys=fx_admin_meta_keys, record=fx_lib_record_model_min_iso, admin_meta=fx_admin_meta_element)
