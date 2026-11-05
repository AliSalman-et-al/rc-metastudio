"""Boundary formatting for references and R identifier labels."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping


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
        "Zhou.Dendukuri": "Zhou-Dendukuri",
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
        return mantissa.rstrip("0").rstrip(".") + separator + exponent
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
