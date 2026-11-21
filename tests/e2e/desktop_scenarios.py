"""Desktop scenarios, with one dispatch and qualification declaration per case."""

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from types import ModuleType


@dataclass(frozen=True)
class Scenario:
    run: Callable[[ModuleType, object, object, str], None]
    timeout_seconds: int = 120
    qualifies: bool = True


def local(function: str, *args: str):
    def run(driver, app, window, _name):
        getattr(driver, function)(app, window, *args)
    return run


def external(module: str, arguments, **options):
    def run(driver, app, window, name):
        import_module(f"tests.e2e.{module}").run(*arguments(driver, app, window, name), **options)
    return run


def skill(module: str):
    def run(driver, app, window, name):
        import_module(module).run(app, window, name, driver.record_step)
    return run


def standard_args(driver, app, window, _name):
    return app, window, driver.WORK, driver.ROOT, driver.record_step, driver.analyze


def review_args(driver, app, window, _name):
    return app, window, driver.ROOT, driver.record_step, driver.analyze


def rm5_args(driver, app, window, _name):
    return app, window, driver.ROOT, driver.WORK, driver.record_step


def presentation_args(driver, app, window, name):
    return app, window, driver.WORK, driver.record_step, name


def readiness(_driver, _app, _window, _name) -> None:
    pass


AUDIT_FAMILIES = (
    "onearm-proportion", "onearm-mean", "reg-coef", "generic-effect", "twoarm-proportion",
    "twoarm-mean", "twoarm-smd", "diagnostic", "hr", "irr", "references", "precision",
    "round5", "bubble-metrics", "irr-context", "arm-names",
    *("presentation-" + family for family in (
        "diagnostic", "onearm-proportion", "twoarm-proportion", "twoarm-mean", "twoarm-smd",
        "reg-coef", "generic-effect", "sequential", "transforms",
    )),
)
GOLDEN = (
    "amino-binary-cumulative",
    "amino-binary-leave-one-out",
    "continuous-cumulative",
    "continuous-leave-one-out",
    "amino-binary-meta-regression",
    "continuous-meta-regression",
    "amino-binary-subgroup",
    "continuous-subgroup",
)
FIXED = (
    "binary.fixed.inv.var",
    "binary.fixed.mh",
    "binary.fixed.peto",
    "continuous.fixed",
    "diagnostic.fixed.inv.var",
    "diagnostic.fixed.mh",
    "diagnostic.fixed.peto",
)
DATA_TYPES = {
    "onearm-proportion": (
        "onearm_proportion_Button",
        "binary",
        "proportion",
        "PR",
        [4, 20],
    ),
    "onearm-mean": ("onearm_mean_Button", "continuous", "mean", "Mean", [20, 4, 2]),
    "reg-coef": (
        "onearm_single_reg_coef_Button",
        "continuous",
        "reg_coef",
        "Mean",
        None,
    ),
    "generic-effect": (
        "onearm_generic_effect_size_Button",
        "continuous",
        "generic_effect",
        "Mean",
        None,
    ),
    "twoarm-proportion": (
        "twoarm_proportions_Button",
        "binary",
        "proportions",
        "OR",
        [4, 20, 6, 22],
    ),
    "twoarm-mean": (
        "twoarm_means_Button",
        "continuous",
        "means",
        "MD",
        [20, 4, 2, 22, 3, 2.5],
    ),
    "twoarm-smd": (
        "twoarm_smds_Button",
        "continuous",
        "smd",
        "SMD",
        [20, 4, 2, 22, 3, 2.5],
    ),
    "diagnostic": ("diagnostic_Button", "diagnostic", None, None, [19, 10, 1, 81]),
}
ANALYSIS_SCENARIOS = (
    *("analysis-" + case for case in GOLDEN),
    *("analysis-" + method for method in FIXED),
    "analysis-category-factor",
    "analysis-category-multiple",
    "analysis-diagnostic-joint",
    "analysis-diagnostic-combined",
    "analysis-diagnostic-cumulative",
    "analysis-diagnostic-leave-one-out",
    "analysis-diagnostic-subgroup",
    "analysis-diagnostic-regression-continuous",
    "analysis-diagnostic-regression-factor",
    "analysis-diagnostic-regression-multiple",
    *("analysis-data-" + name for name in DATA_TYPES),
    "small-study-binary-extended",
    "small-study-continuous-extended",
    "small-study-diagnostic",
)

PLOT_PRODUCERS = {
    "forest": "analysis-binary.fixed.inv.var",
    "cumulative": "analysis-amino-binary-cumulative",
    "leave-one-out": "analysis-amino-binary-leave-one-out",
    "subgroup": "analysis-amino-binary-subgroup",
    "regression": "analysis-amino-binary-meta-regression",
    "sroc": "analysis-diagnostic-joint",
    "coefficient": "analysis-diagnostic-regression-continuous",
    "funnel": "small-study-binary-extended",
    "contour": "small-study-binary-extended",
    "trimfill": "small-study-binary-extended",
    "deeks": "small-study-diagnostic",
    "trial-sequential": "tsa-bcg",
}

def advanced(timeout_seconds: int = 120) -> Scenario:
    return Scenario(skill("advanced_workflows"), timeout_seconds)


ADVANCED_SCENARIOS = {
    **{
        f"analysis-sequential-{family}-{workflow}": advanced()
        for family in ("fixed", "diagnostic")
        for workflow in ("cumulative", "leave-one-out", "subgroup")
    },
    **{f"options-{family}": advanced() for family in ("binary", "continuous", "diagnostic")},
    "options-confidence-inclusion": advanced(),
    "options-zero-cells": advanced(),
    "plot-workflow-mh-rd": advanced(240),
    "project-structure": Scenario(local("sheets"), qualifies=False),
    "project-table-covariates": advanced(),
    "project-shell": advanced(),
    "project-display-labels": advanced(600),
    "project-round6-polish": advanced(600),
    "project-release-coefficients": advanced(600),
    "project-reviewer-predictions": advanced(600),
    "project-reviewer-groups": advanced(600),
    "project-reviewer-colours": advanced(600),
    "project-axis-proportions": advanced(600),
    "project-axis-others": advanced(600),
    "project-axis-sequential": advanced(600),
    "calculator-grid-precision": advanced(),
    "calculator-ratio-precision": advanced(600),
    **{f"plot-workflow-{family}": advanced(240) for family in PLOT_PRODUCERS},
    **{
        f"calculator-mode-{mode}": advanced()
        for mode in (
            "binary-metrics",
            "continuous-metrics",
            "diagnostic-metrics",
            "onearm-proportion",
            "onearm-mean",
            "entered-binary",
            "entered-continuous",
            "entered-diagnostic",
            "pre-post",
            "back-binary",
            "back-continuous",
            "back-diagnostic",
        )
    },
}


SCENARIOS = {
    **{
        "audit-round3-" + family: Scenario(external("analysis_presentation_workflows", presentation_args), 600)
        for family in AUDIT_FAMILIES
    },
    # The BCG plot workflow also drives the dialog, report exports and in-place reruns.
    **{f"tsa-{case}": Scenario(skill("advanced_workflows"), 240,
                              qualifies=f"tsa-{case}" not in PLOT_PRODUCERS.values())
       for case in ("bcg", "rr-mh", "md", "hr", "smd")},
    "tsa-stress": Scenario(skill("advanced_workflows"), 240, qualifies=False),
    "tsa-peto": Scenario(skill("advanced_workflows"), 240),
    "review1-design": Scenario(external("desktop_navigation_workflows", standard_args)),
    "ui-fine-tuning": Scenario(external("ui_fine_tuning", standard_args), 240),
    "ui-fable-polish": Scenario(external("ui_fable_polish", standard_args)),
    "ui-design-direction": Scenario(external("ui_design_direction", standard_args), 240),
    "review-workflows": Scenario(external("analysis_settings_workflows", review_args), 240),
    "subgroup-image": Scenario(local("subgroup_image", "subgroup-image"), 240),
    "subgroup-image-dark-large": Scenario(local("subgroup_image", "subgroup-image-dark-large"), 240),
    "polish-journeys": Scenario(external("polish_journeys", standard_args), 240),
    "doctor": Scenario(readiness, qualifies=False),
    "hillclimb": Scenario(local("hillclimb"), 600),
    "analysis-dialog": Scenario(local("analysis_dialog")),
    "grid-entry": Scenario(local("grid_entry")),
    "ui-refresh": Scenario(external("ui_refresh", standard_args)),
    "ux-improvements": Scenario(external("ux_workflows", standard_args), 600),
    "results-window": Scenario(external("ux_workflows", standard_args), 600, qualifies=False),
    "manuscript-export-direct": Scenario(external("manuscript_export", standard_args, direct_write=True), 600),
    "manuscript-export": Scenario(external("manuscript_export", standard_args, direct_write=False), 600),
    "manuscript-split-figure": Scenario(external("manuscript_split_figure", standard_args)),
    "results-presentation": Scenario(external("results_presentation", standard_args)),
    "results-values": Scenario(external("results_values", standard_args), 600),
    "amino": Scenario(local("sample_analysis", "amino")),
    "sheets": Scenario(local("sheets")),
    "ui-crawl": Scenario(external("ui_crawl", lambda driver, *_: (driver,)), 600, qualifies=False),
    "rm5-import": Scenario(external("rm5_import", rm5_args), 240),
    "sheets-legacy": Scenario(local("sheets_legacy"), 600),
    "sheets-edges": Scenario(local("sheets_edges")),
    "sheets-persist": Scenario(local("sheets_persist")),
    "sheets-swap": Scenario(local("sheets_swap"), 600),
    "continuous": Scenario(local("sample_analysis", "continuous")),
    "lymph": Scenario(local("sample_analysis", "lymph")),
    "editing": Scenario(local("editing")),
    "csv": Scenario(local("csv_import")),
    "xlsx-import": Scenario(local("xlsx_import")),
    "plot-edit": Scenario(local("plot_edit")),
    "small-study-effects": Scenario(local("small_study_effects")),
    **{f"calculator-{kind}": Scenario(local("calculator", kind)) for kind in ("binary", "continuous", "diagnostic")},
    **{
        name: Scenario(skill("analysis_matrix"), qualifies=name not in PLOT_PRODUCERS.values())
        for name in ANALYSIS_SCENARIOS
    },
    **ADVANCED_SCENARIOS,
    "ratios-hr": Scenario(skill("ratio_workflows"), 600),
    "ratios-irr": Scenario(skill("ratio_workflows"), 1200),
    "ratios-samples": Scenario(skill("ratio_workflows")),
}


QUALIFICATION_SCENARIOS = tuple(name for name, scenario in SCENARIOS.items() if scenario.qualifies)
