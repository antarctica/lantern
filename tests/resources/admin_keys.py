from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from jwskate import Jwk


def test_keys() -> AdministrationKeys:
    """
    BAS Metadata Library administration metadata test encryption and signing keys.

    These test keys are not secret and so not sensitive.
    """
    SIGNING_KEY_PUBLIC = {  # noqa: N806
        "kty": "EC",
        "kid": "bas_metadata_testing_signing_key",
        "alg": "ES256",
        "crv": "P-256",
        "x": "FzxBM1ZPO5W2bYlhT9AjZUKz5_oH5vIh4_k4aEZ64rM",
        "y": "vmK5PWOoIA9eO0ntLh37AMpVODyj0NWf842FwoN-GRs",
    }
    SIGNING_KEY_PRIVATE = {  # noqa: N806
        "kty": "EC",
        "kid": "bas_metadata_testing_signing_key",
        "alg": "ES256",
        "crv": "P-256",
        "x": "FzxBM1ZPO5W2bYlhT9AjZUKz5_oH5vIh4_k4aEZ64rM",
        "y": "vmK5PWOoIA9eO0ntLh37AMpVODyj0NWf842FwoN-GRs",
        "d": "FdxFSRF2zAAfn7_GaDk81T8PdBGlzZpRtxd10-kc4PE",
    }
    ENCRYPTION_KEY_PRIVATE = {  # noqa: N806
        "kty": "EC",
        "kid": "bas_metadata_testing_encryption_key",
        "alg": "ECDH-ES+A128KW",
        "crv": "P-256",
        "x": "kYiwq6MW8lGN6PB2csVMuMRcISVk5eNUpGkjM-mm8QY",
        "y": "raOTT2xAQhHFKhPHy338L8Ql0hvgsDtHwtEc8pCOf2Q",
        "d": "2lBuUtJK2TcV_b4B-bDCPnRVAqMnYvnLZ41IUguprs8",
    }
    return AdministrationKeys(
        signing_public=Jwk(SIGNING_KEY_PUBLIC),
        signing_private=Jwk(SIGNING_KEY_PRIVATE),
        encryption_private=Jwk(ENCRYPTION_KEY_PRIVATE),
    )
