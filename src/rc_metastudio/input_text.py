import math


def to_native_text(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return str(value, encoding="utf8")
    return str(value)


def is_blank(value):
    return to_native_text(value).strip() == ""


def parse_decimal(value):
    """Parse deliberate dot- or comma-decimal interface input.

    Project and R boundaries remain dot-decimal.  The interface accepts one
    decimal convention at a time and rejects ambiguous thousands/grouping
    syntax rather than silently changing a scientific value.
    """
    number, valid = parse_optional_decimal(value)
    return (number, True) if valid and number is not None else (0.0, False)


def parse_optional_decimal(value: object) -> tuple[float | None, bool]:
    parsed = _decimal_input(value)
    return (parsed[1], True) if parsed is not None else (None, False)


def normalize_decimal_text(value):
    """Return unambiguous finite numeric text in dot-decimal form."""
    parsed = _decimal_input(value)
    return (parsed[0], True) if parsed is not None else ("", False)


def _decimal_input(value: object) -> tuple[str, float | None] | None:
    text = to_native_text(value).strip()
    if not text:
        return "", None
    if "," in text:
        if "." in text or text.count(",") != 1:
            return None
        text = text.replace(",", ".")
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    return (text, number) if math.isfinite(number) else None
