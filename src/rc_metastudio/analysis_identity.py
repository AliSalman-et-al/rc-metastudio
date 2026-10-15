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


def configuration_details(model_label, parameters):
    lines = ["Model: " + model_label]
    for key, label in (("rm.method", "Estimator"), ("estimator", "Estimator"), ("inference.method", "Inference")):
        if key in parameters:
            lines.append(f"{label}: {parameter_value_display_label(key, parameters[key])}")
    return lines


def result_identity(model, workflow, metric, model_label, parameters, confidence, moderators, fits=()):
    """Build the compact result header and the report's selected configuration."""
    header = workflow_label(workflow) + " — " + dataset_identity(model, metric)
    details = [f"Confidence level: {float(parameters.get('conf.level', confidence)):g}%"]
    if workflow == "cumulative":
        details.append("Order: current study order; each row adds a study to the preceding studies.")
    elif workflow == "leave-one-out":
        if model.get_current_outcome_type() in {"time_to_event", "event_rates"}:
            details.append("Omission-only fits: each row omits the named study. No all-studies fit is included.")
        else:
            details.append("Each row omits the named study; compare with the all-studies estimate.")
    elif workflow == "subgroup":
        details.append(f"Subgroups by {parameters.get('cov_name', 'selected covariate')}. Use the test of subgroup differences to compare groups.")
    elif workflow == "meta-regression":
        details.append("Moderators: " + ", ".join(moderators))
        if model.get_current_outcome_type() != "diagnostic":
            details.append("Bubble size increases with model weight; sizes are rescaled for legibility and do not show exact relative weights.")
    effect = model.current_effect
    if effect in {"OR", "RR", "HR", "IRR"}:
        quantity = {"OR": "odds", "RR": "risks", "HR": "hazards", "IRR": "event rates"}[effect]
        groups = " and ".join(model.current_groups)
        details.append(f"{effect} = 1 means equal {quantity} in {groups}; estimates are fitted on the log scale.")
    elif effect in {"MD", "SMD"}:
        units = "SD units" if effect == "SMD" else "outcome units"
        groups = " minus ".join(model.current_groups)
        details.append(f"{effect}: {groups}, in {units}; 0 indicates no difference.")
    if fits:
        for fitted_metric, fitted_method, fitted_parameters in fits:
            details.append("\n" + fitted_metric)
            details.extend(configuration_details(fitted_method, fitted_parameters))
    else:
        details = configuration_details(model_label, parameters) + details
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
    comparison = model.current_effect in meta_globals.TWO_ARM_METRICS
    groups = " / ".join(model.current_groups if comparison else model.current_groups[:1])
    group_label = "Comparison" if comparison else "Group"
    follow_up = model.get_current_follow_up_name()
    labels = [model.current_outcome_name, dataset_label(model)]
    quantity = metric or metric_label(model)
    if quantity:
        labels.append(quantity)
    return " · ".join(labels) + f"\n{group_label}: {groups} · Follow-up: {follow_up}"
