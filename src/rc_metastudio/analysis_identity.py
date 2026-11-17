"""Presentation labels for the selected dataset; backend metric keys stay intact."""

from rc_metastudio import analysis_catalog
from rc_metastudio.analysis_method_labels import parameter_value_display_label

CUMULATIVE_SEQUENCES = (("Table order", "table"),
    ("Publication year (earliest first)", "year"), ("Study effect size (smallest first)", "effect"))
LOO_ROW_ORDERS = (("Current table order", "table"), ("Year (earliest first)", "year"),
    ("Pooled effect after omission (smallest first)", "effect"), ("I² after omission (lowest first)", "i2"))
FOREST_STUDY_ORDERS = (("Current table order", "table"), ("Year (earliest first)", "year"),
    ("Effect size (smallest first)", "effect"), ("Weight (largest first)", "weight"))


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
        sequence = dict((key, label) for label, key in CUMULATIVE_SEQUENCES).get(parameters.get("cum_sequence", "table"), "Table order")
        details.append(f"Sequence: {sequence}; each step adds a study to the preceding studies.")
    elif workflow == "leave-one-out":
        details.append("Each omission row excludes the named study; compare with the all-studies estimate.")
    elif workflow == "subgroup":
        details.append(f"Subgroups defined by {parameters.get('cov_name', 'selected covariate')}. Use the test of subgroup differences to compare groups.")
    elif workflow == "meta-regression":
        details.append("Moderators: " + ", ".join(moderators))
        if model.get_current_data_type() != "diagnostic":
            details.append("Bubble size increases with model weight; sizes are rescaled for legibility and do not show exact relative weights.")
    effect = model.current_effect
    if effect in {"OR", "RR", "HR", "IRR"}:
        quantity = {"OR": "odds", "RR": "risks", "HR": "hazards", "IRR": "event rates"}[effect]
        groups = " and ".join(model.arm_names)
        details.append(f"{effect} = 1 means equal {quantity} in {groups}; estimates are fitted on the log scale.")
    elif effect in {"MD", "SMD"}:
        units = "SD units" if effect == "SMD" else "outcome units"
        groups = " minus ".join(model.arm_names)
        details.append(f"{effect}: {groups}, in {units}; 0 indicates no difference.")
    if fits:
        details.extend(_fitted_configuration_details(fits))
    else:
        details = configuration_details(model_label, parameters) + details
    return header, "\n".join(details)


def _fitted_configuration_details(fits):
    details = []
    joint_seen = False
    for metric, method, parameters in fits:
        if "reitsma" in method.casefold():
            if joint_seen:
                continue
            joint_seen = True
            metric = "Joint model"
        details.append("\n" + metric)
        details.extend(configuration_details(method, parameters))
    return details


def metric_label(model, metric=None):
    subtype = model.get_current_data_subtype()
    metric = metric or model.current_effect
    if metric == "Mean":
        return {"mean": "Mean", "reg_coef": "Regression coefficient", "generic_effect": "Entered effect"}.get(subtype, "Mean")
    return analysis_catalog.ALL_METRIC_NAMES.get(metric, metric)


def dataset_label(model):
    return {
        "proportion": "Single-arm proportion", "proportions": "Two-arm binary",
        "mean": "Single-arm mean", "means": "Two-arm continuous",
        "smd": "Two-arm continuous", "reg_coef": "Regression coefficient",
        "generic_effect": "Entered effect estimate", "hazard_ratio": "Time-to-event",
        "incidence_rate_ratio": "Event rates",
    }.get(model.get_current_data_subtype(), str(model.get_current_data_type() or "Dataset").title())


def dataset_identity(model, metric=None):
    comparison = model.current_effect in analysis_catalog.TWO_ARM_METRICS
    groups = " / ".join(model.arm_names if comparison else model.arm_names[:1])
    group_label = "Index test" if model.get_current_data_type() == "diagnostic" else "Comparison" if comparison else "Arm"
    labels = [model.current_sheet.name, dataset_label(model)]
    quantity = metric or metric_label(model)
    if quantity and model.current_effect != "Mean" and quantity.casefold() != labels[-1].casefold():
        labels.append(quantity)
    context = []
    default_name = "Index test" if model.get_current_data_type() == "diagnostic" else "Group"
    if comparison or groups != default_name:
        context.append(f"{group_label}: {groups}")
    return " · ".join(labels) + "\n" + " · ".join(context)


def plot_caption(model, workflow, caption=None):
    caption = caption or dataset_identity(model)
    return caption
