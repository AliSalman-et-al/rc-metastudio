# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Stable data-family IDs, supported metrics and default arm names."""



BINARY_TWO_ARM_METRICS = ["OR", "RD", "RR", "AS", "YUQ", "YUY"]


BINARY_ONE_ARM_METRICS = ["PR", "PLN", "PLO", "PAS", "PFT"]


BINARY_METRIC_NAMES = {
    "OR": "Odds ratio",
    "RD": "Risk difference",
    "RR": "Risk ratio",
    "AS": "Arcsine difference",
    "YUQ": "Yule's Q",
    "YUY": "Yule's Y",
    "PR": "Untransformed proportion",
    "PLN": "Natural logarithm transformed proportion",
    "PLO": "Logit transformed proportion",
    "PAS": "Arcsine transformed proportion",
    "PFT": "Freeman-Tukey transformed proportion",
}


CONTINUOUS_TWO_ARM_METRICS = ["MD", "SMD"]


CONTINUOUS_ONE_ARM_METRICS = ["Mean"]


LEGACY_MEAN_METRIC_NAMES = ("TX Mean", "TXMean", "TX.Mean")


def canonical_metric_name(metric: str) -> str:
    """Resolve historical one-arm mean identifiers at input boundaries."""
    return "Mean" if metric in LEGACY_MEAN_METRIC_NAMES else metric


CONTINUOUS_METRIC_NAMES = {
    "MD": "Mean difference",
    "SMD": "Standardized mean difference",
    "Mean": "Mean",
}


DEFAULT_CONTINUOUS_ONE_ARM = "Mean"


ONE_ARM_METRICS = BINARY_ONE_ARM_METRICS + CONTINUOUS_ONE_ARM_METRICS


TWO_ARM_METRICS = BINARY_TWO_ARM_METRICS + CONTINUOUS_TWO_ARM_METRICS


DIAGNOSTIC_METRICS = ["Sens", "Spec", "PLR", "NLR", "DOR"]


DIAGNOSTIC_METRIC_LABELS = {
    "Sens": "Sensitivity",
    "Spec": "Specificity",
    "PLR": "Positive likelihood ratio",
    "NLR": "Negative likelihood ratio",
    "DOR": "Diagnostic odds ratio",
}


ALL_METRIC_NAMES = {}


ALL_METRIC_NAMES.update(BINARY_METRIC_NAMES)


ALL_METRIC_NAMES.update(CONTINUOUS_METRIC_NAMES)


ALL_METRIC_NAMES.update(DIAGNOSTIC_METRIC_LABELS)


RATIO_METRIC_NAMES = {"HR": "Hazard ratio", "IRR": "Incidence rate ratio"}


ALL_METRIC_NAMES.update(RATIO_METRIC_NAMES)


TWO_ARM_METRICS += ["HR", "IRR"]


BINARY, CONTINUOUS, DIAGNOSTIC, OTHER = range(4)


FACTOR = 4


TIME_TO_EVENT, EVENT_RATES = 5, 6


RATIO_DATA_TYPES = (TIME_TO_EVENT, EVENT_RATES)


STR_TO_TYPE_DICT = {
    "time_to_event": TIME_TO_EVENT,
    "event_rates": EVENT_RATES,
    "binary": BINARY,
    "continuous": CONTINUOUS,
    "diagnostic": DIAGNOSTIC,
    "OTHER": OTHER,
}


TYPE_TO_STR_DICT = {
    TIME_TO_EVENT: "time_to_event",
    EVENT_RATES: "event_rates",
    BINARY: "binary",
    CONTINUOUS: "continuous",
    DIAGNOSTIC: "diagnostic",
    OTHER: "OTHER",
    FACTOR: "factor",
}


DIAGNOSTIC_METRIC_GROUPS = {
    "sens": ["Sens"],
    "spec": ["Spec"],
    "dor": ["DOR"],
    "lr": ["PLR", "NLR"],
}


DIAG_FIELDS_TO_RAW_INDICES = {"TP": 0, "FN": 1, "FP": 2, "TN": 3}


DEFAULT_ARM_NAMES = ["Intervention", "Control"]


def default_arm_names(data_type, sub_type=None):
    if data_type == DIAGNOSTIC:
        return ["Index test"]
    if sub_type in {"proportion", "mean", "reg_coef", "generic_effect"}:
        return ["Group", "Other group"]
    return list(DEFAULT_ARM_NAMES)
