"""Presentation labels for the selected dataset; backend metric keys stay intact."""

from rc_metastudio import meta_globals
from rc_metastudio.analysis_method_labels import parameter_value_display_label


def workflow_label(workflow):
    return {
        "cumulative": "Cumulative meta-analysis",
        "leave-one-out": "Leave-one-out meta-analysis",
        "subgroup": "Subgroup meta-analysis",
        "meta-regression": "Meta-regression",
    }.get(workflow, "Meta-analysis")


def result_identity(model, workflow, metric, model_label, parameters, confidence, moderators):
    """Build the compact result header and the report's selected configuration."""
    header = workflow_label(workflow) + " — " + dataset_identity(model, metric)
    details = ["Model: " + model_label,
               f"Confidence level: {parameters.get('conf.level', confidence)}%"]
    for key, label in (("rm.method", "Estimator"), ("estimator", "Estimator"), ("inference.method", "Inference")):
        if key in parameters:
            details.append(f"{label}: {parameter_value_display_label(key, parameters[key])}")
    if workflow == "cumulative":
        details.append("Order: current study order; each row adds a study to the preceding studies.")
    elif workflow == "leave-one-out":
        details.append("Each row omits the named study; compare with the all-studies estimate.")
    elif workflow == "subgroup":
        details.append(f"Subgroups by {parameters.get('cov_name', 'selected covariate')}. Use the test of subgroup differences to compare groups.")
    elif workflow == "meta-regression":
        details.append("Moderators: " + ", ".join(moderators))
    effect = model.current_effect
    if effect in {"OR", "RR", "HR", "IRR"}:
        details.append(f"{effect} = 1 indicates equal values for the comparison; estimates are fitted on the log scale.")
    elif effect in {"MD", "SMD"}:
        units = "SD units" if effect == "SMD" else "outcome units"
        details.append(f"{effect}: first group minus second group, in {units}; 0 indicates no difference.")
    return header, "\n".join(details)


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
    single_arm = model.current_effect in meta_globals.ONE_ARM_METRICS
    groups = " / ".join(model.current_groups[:1] if single_arm else model.current_groups)
    group_label = "Group" if single_arm else "Comparison"
    follow_up = model.get_current_follow_up_name()
    return f"{model.current_outcome_name} · {dataset_label(model)} · {metric or metric_label(model)}\n{group_label}: {groups} · Follow-up: {follow_up}"
