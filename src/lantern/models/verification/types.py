from typing import NotRequired, TypedDict


class VerificationContext(TypedDict):
    """Recognised keys and types for verification job context`."""

    BASE_URL: str
    SHAREPOINT_PROXY_ENDPOINT: str
    SAN_PROXY_ENDPOINT: str

    CHECK_FUNC: NotRequired[str]
    URL: NotRequired[str]
    TARGET: NotRequired[int]
    METHOD: NotRequired[str]
    HEADERS: NotRequired[dict]
    JSON: NotRequired[dict]
    EXPECTED_LENGTH: NotRequired[int]
    EXPECTED_STATUS: NotRequired[int]
