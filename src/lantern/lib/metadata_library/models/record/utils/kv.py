import json

from lantern.lib.metadata_library.models.record.record import Record


def get_kv(record: Record) -> dict:
    """Get key-value pairs from a JSON encoded string if used in record supplemental information."""
    sinfo = record.identification.supplemental_information
    if not sinfo:
        return {}
    try:
        kv = json.loads(sinfo)
    except json.JSONDecodeError:
        msg = "Supplemental information isn't JSON parsable."
        raise ValueError(msg) from None
    if not isinstance(kv, dict):
        msg = "Supplemental information isn't parsed as a dict."
        raise TypeError(msg) from None
    return kv


def set_kv(kv: dict, record: Record, replace: bool = False) -> None:
    """
    Set key-value pairs in a JSON encoded string for use in record supplemental information.

    Use `replace` to remove existing keys with new value.

    If new value is empty, removes value rather than setting an empty dict.
    """
    kv_ = get_kv(record)
    kv_.update(kv)
    if replace:
        kv_ = kv

    record.identification.supplemental_information = json.dumps(kv_)
    if len(kv_) == 0:
        record.identification.supplemental_information = None
