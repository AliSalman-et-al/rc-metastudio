"""Presentation labels for the selected dataset; backend metric keys stay intact."""

from rc_metastudio import meta_globals


def metric_label(model):
    subtype = model.get_current_outcome_subtype()
    if model.current_effect == "TX Mean":
        return {"mean": "Mean", "reg_coef": "Regression coefficient", "generic_effect": "Entered effect"}.get(subtype, "Mean")
    return meta_globals.ALL_METRIC_NAMES.get(model.current_effect, model.current_effect)


def dataset_label(model):
    return {
        "proportion": "Single-arm proportion", "proportions": "Two-arm binary",
        "mean": "Single-arm mean", "means": "Two-arm continuous",
        "smd": "Two-arm continuous", "reg_coef": "Regression coefficient",
        "generic_effect": "Generic entered effect", "hazard_ratio": "Time-to-event",
        "incidence_rate_ratio": "Event rates",
    }.get(model.get_current_outcome_subtype(), str(model.get_current_outcome_type() or "Dataset").title())


def dataset_identity(model, metric=None):
    groups = " / ".join(model.current_groups)
    follow_up = model.get_current_follow_up_name()
    return f"{model.current_outcome_name} · {dataset_label(model)} · {metric or metric_label(model)}\nComparison: {groups} · Follow-up: {follow_up}"
