def _clean_val(value: dict | list | str | float) -> dict | list | str | int | float | None:
    if isinstance(value, dict):
        cleaned_dict = {k: _clean_val(v) for k, v in value.items() if v not in (None, [], {})}
        return {k: v for k, v in cleaned_dict.items() if v not in (None, [], {})}
    if isinstance(value, list):
        cleaned_list = [_clean_val(v) for v in value if v not in (None, [], {})]
        return cleaned_list if cleaned_list else None
    return value


def clean_dict(d: dict) -> dict:
    """Remove any None or empty list/dict values from a dict."""
    cleaned = _clean_val(d)
    if not isinstance(cleaned, dict):
        msg = "Value must be a dict"
        raise TypeError(msg) from None
    return {k: v for k, v in cleaned.items() if v not in (None, [], {})}


def clean_list(l: list) -> list:  # noqa: E741
    """Remove any None or empty list/dict values from a list."""
    cleaned = _clean_val(l)
    if cleaned is None:
        cleaned = []
    if not isinstance(cleaned, list):
        msg = "Value must be a list"
        raise TypeError(msg) from None
    return [v for v in cleaned if v not in (None, [], {})]
