"""Result numbers, reference lists, identifier labels and plain-text tables."""

from __future__ import annotations

import math
import re
from html import escape
from collections.abc import Iterable, Mapping, Sequence
from typing import overload


NUM_DIGITS = 2
PERCENTAGE_DISPLAY_DIGITS = 1


def numeric_cell(value: str) -> bool:
    digits = r'(?:\d{1,3}(?:,\d{3})+|\d+)'
    number = rf'[+−±-]?(?:(?:{digits}(?:\.\d*)?|\.\d+)(?:[eE][+−-]?\d+)?|inf|∞)%?'
    interval = rf'(?:[<>≤≥]\s*)?{number}(?:\s*(?:to|,|–)\s*{number})?'
    return bool(re.fullmatch(rf'\s*(?:{interval}|{number}\s*\({interval}\))\s*', value, re.IGNORECASE))


def numeric_columns(rows: Sequence[Sequence[str]]) -> tuple[bool, ...]:
    if not rows:
        return ()
    columns = [[row[index] for row in rows if row[index] not in ('', 'NA', '—', 'Not estimable')]
               for index in range(len(rows[0]))]
    return tuple(bool(values) and sum(numeric_cell(value) for value in values) >= len(values) / 2
                 for values in columns)


def report_numbers(text: str) -> str:
    """Keep a sign, interval, or threshold with its number in a report."""
    text = re.sub(r"(?<!\w)-[ \t]*(?=\d|\.\d)|(?<=\de)-(?=\d)", "−", text)
    text = re.sub(r"(?<=\d) +to +(?=[+−]?\d)", "\u00a0to\u00a0", text)
    return re.sub(r"([<>≤≥]) +(?=[+−]?\d)", r"\1" + "\u00a0", text)


def report_cell(value: str) -> str:
    value = report_numbers(value)
    return re.sub(r"^([+−]?)(\d{4,})(%?)$",
                  lambda match: f"{match[1]}{int(match[2]):,}{match[3]}", value)


def table_html(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    """Editable, content-sized table for clipboard and manuscript surfaces."""
    numeric = numeric_columns(rows)
    parts = ['<table border="0" cellspacing="0" cellpadding="5">']
    if headers:
        parts.append('<thead><tr>')
        for index, header in enumerate(headers):
            align = 'right' if numeric and numeric[index] else 'left'
            parts.append(f'<th align="{align}" style="font-weight:bold; border-top:1px solid black; border-bottom:1px solid black;">{escape(header)}</th>')
        parts.append('</tr></thead>')
    parts.append('<tbody>')
    for index, row in enumerate(rows):
        parts.append('<tr>')
        for column, value in enumerate(row):
            is_numeric = numeric_cell(value)
            align = 'right' if is_numeric or (value in ('', 'NA', '—', 'Not estimable') and numeric[column]) else 'left'
            wrap = 'nowrap' if is_numeric or numeric[column] else 'pre-wrap'
            if is_numeric:
                value = report_cell(value)
            border = 'border-bottom:1px solid black;' if index == len(rows) - 1 else ''
            parts.append(f'<td align="{align}" style="white-space:{wrap}; {border}">{escape(value).replace(chr(10), "<br>")}</td>')
        parts.append('</tr>')
    parts.append('</tbody></table>')
    return ''.join(parts)


def format_references(references: object) -> str:
    if references is None:
        return ""
    if isinstance(references, Mapping):
        values = references.values()
    elif isinstance(references, str):
        values = (references,)
    else:
        values = list(references) if isinstance(references, Iterable) else (references,)
    entries = dedupe_references_preserving_order(
        _reference_text(reference) for reference in values
    )
    return "".join(f"{index}. {reference}\n" for index, reference in enumerate(entries, 1))


def dedupe_references_preserving_order(references: object) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    if not isinstance(references, Iterable):
        references = (references,)
    for reference in references:
        text = str(reference)
        key = _reference_key(text)
        if key and key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _reference_text(reference: object) -> str:
    if reference is None:
        return ""
    if not isinstance(reference, str):
        values = list(reference) if isinstance(reference, Iterable) else None
        if values is not None:
            if not values:
                return ""
            if len(values) == 1:
                return _reference_text(values[0])
            return "; ".join(_reference_text(value) for value in values)
    text = str(reference).replace("\r\n", "\n").strip()
    text = re.sub(r"^\[\d+\]\s+", "", text)
    return text.strip('"')


def normalize_identifier_label(value: object) -> str:
    """Make a non-executable R identifier readable for display."""
    text = str(value).replace("I\ufffd", "I²").replace("\ufffd", "-")
    replacements = {
        "intrcpt": "Intercept",
        "(Intercept)": "Intercept",
        "Std. Error": "SE (logit scale)",
        "Std Error": "SE (logit scale)",
        "moderator": "Moderator",
        "statistic": "Statistic",
        "tsens": "Sensitivity (logit scale)",
        "tfpr": "False-positive rate (logit scale)",
        "posLR": "Positive Likelihood Ratio",
        "negLR": "Negative Likelihood Ratio",
        "invnegLR": "Inverse Negative Likelihood Ratio",
        "pos.lr": "Positive Likelihood Ratio",
        "neg.lr": "Negative Likelihood Ratio",
        "inv.neg.lr": "Inverse Negative Likelihood Ratio",
        "Zhou.Dendukuri": "Zhou–Dendukuri",
        "Holling.Unadjusted": "Holling (unadjusted)",
        "Holling.Adjusted": "Holling (adjusted)",
        "I.squared": "I²",
        "I_squared": "I²",
        "I2": "I²",
        "tau.squared": "τ²",
        "tau_squared": "τ²",
        "tau2": "τ²",
    }
    for raw, display in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(raw, display)
    text = re.sub(r"\bPr\s*\(>\|[^)]+\)", "p-value", text)
    text = re.sub(r"\b(?:p[._-]?value|pval)\b", "p-value", text, flags=re.I)
    text = re.sub(r"\b(?:z[._-]?value|zval)\b", "z-value", text, flags=re.I)
    text = re.sub(r"\b(?:I[._-]?squared|I2)\b", "I²", text, flags=re.I)
    text = re.sub(r"\b(?:tau[._-]?squared|tau2)\b", "τ²", text, flags=re.I)
    text = re.sub(r"(?<![A-Za-z])([A-Z]{2,})(?=[A-Z][a-z]|\b)", r"\1 ", text)
    text = re.sub(r"\s+", " ", text.replace("_", " ").replace(".", " ")).strip()
    labels = {
        "nlr": "Negative Likelihood Ratio",
        "plr": "Positive Likelihood Ratio",
        "dor": "Diagnostic Odds Ratio",
        "sens": "Sensitivity",
        "spec": "Specificity",
    }
    return " ".join(labels.get(word.lower(), word) for word in text.split())


def _reference_key(reference: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", reference.lower()).strip()


def format_effect_number(value: float, digits: int) -> str:
    if value != 0 and abs(value) < 10 ** (-digits):
        # Keep `digits` significant figures so a small value stays nonzero.
        required = math.ceil(-math.log10(abs(value))) + max(1, digits) - 1
        formatted = f"{value:.{required}f}" if required <= 6 else f"{value:.{max(1, digits)}e}"
        mantissa, separator, exponent = formatted.partition("e")
        return mantissa.rstrip("0").rstrip(".") + separator + exponent if separator else formatted
    return f"{value:.{digits}f}"


_TITLE_PROPER_NAMES = frozenset((
    "Baujat", "Begg", "Bayesian", "DerSimonian-Laird", "Egger", "Galbraith", "Hartung-Knapp",
    "Knapp-Hartung", "Mantel-Haenszel", "Peto", "Reitsma",
))


def sentence_case_title(title: str) -> str:
    def keep(word):
        core = word.strip("()[],:;'’")
        head = core.split("-")[0]
        return (core.removesuffix("'s").removesuffix("’s") in _TITLE_PROPER_NAMES
                or any(c.isupper() for c in core[1:])  # acronyms, DerSimonian, ML
                or (len(head) == 1 and head.isupper()))  # I-squared, H-squared
    return " ".join(word if index == 0 or keep(word) else word.lower()
                    for index, word in enumerate(str(title).split()))


@overload
def tabulate(
    lists: Sequence[Sequence[object]],
    sep: str = " | ",
    return_col_widths: bool = False,
    align: Sequence[str] | None = None,
) -> str: ...


@overload
def tabulate(
    lists: Sequence[Sequence[object]],
    sep: str,
    return_col_widths: bool,
    align: Sequence[str] | None = None,
) -> str | tuple[str, list[int]]: ...


def tabulate(
    lists: Sequence[Sequence[object]],
    sep: str = " | ",
    return_col_widths: bool = False,
    align: Sequence[str] | None = None,
) -> str | tuple[str, list[int]]:
    """Render equally sized columns as a plain-text table."""
    column_alignments = list(align) if align is not None else []
    if len(column_alignments) != len(lists):
        column_alignments = ["L"] * len(lists)

    string_lists = []
    for arg in lists:
        str_arg = [str(x) for x in arg]
        string_lists.append(str_arg)

    max_lengths = []
    for arg in string_lists:
        max_len = max([len(x) for x in arg])
        max_lengths.append(max_len)

    data = zip(*string_lists)
    out = []
    for row in data:
        row_str = [
            "{0:{align}{width}}".format(
                x, width=width, align="<" if row_alignment == "L" else ">"
            )
            for x, width, row_alignment in zip(row, max_lengths, column_alignments)
        ]
        row_str = sep.join(row_str)
        out.append(row_str)
    out_str = "\n".join(out)

    if return_col_widths:
        return (out_str, max_lengths)
    return out_str
