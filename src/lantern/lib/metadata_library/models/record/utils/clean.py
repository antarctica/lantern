def _clean_val(value: dict | list | str | float, strip_empty_str: bool) -> dict | list | str | int | float | None:
    def _is_empty(v: object) -> bool:
        if v is None:
            return True
        if v == [] or v == {}:
            return True
        return bool(strip_empty_str and v == "")

    if isinstance(value, dict):
        cleaned_dict = {k: _clean_val(v, strip_empty_str) for k, v in value.items() if not _is_empty(v)}
        return {k: v for k, v in cleaned_dict.items() if not _is_empty(v)}
    if isinstance(value, list):
        cleaned_list = [_clean_val(v, strip_empty_str) for v in value if not _is_empty(v)]
        return cleaned_list if cleaned_list else None
    return value


def clean_dict(d: dict, strip_empty_str: bool = False) -> dict:
    """
    Remove any None or empty list/dict values from a dict.

    Optionally strip empty strings.
    """
    cleaned = _clean_val(d, strip_empty_str=strip_empty_str)
    if not isinstance(cleaned, dict):
        msg = "Value must be a dict"
        raise TypeError(msg) from None
    return cleaned


def clean_list(l: list, strip_empty_str: bool = False) -> list:  # noqa: E741
    """
    Remove any None or empty list/dict values from a list.

    Optionally strip empty strings.
    """
    cleaned = _clean_val(l, strip_empty_str=strip_empty_str)
    if cleaned is None:
        cleaned = []
    if not isinstance(cleaned, list):
        msg = "Value must be a list"
        raise TypeError(msg) from None
    return [v for v in cleaned if v not in (None, [], {})]
