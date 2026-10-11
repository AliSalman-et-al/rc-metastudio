"""Compare fixed and multimetric sequential UI workflows with public fits."""

import json
import math

from analysis_matrix import run as matrix


def references(window, method, workflow, metric):
    from rc_metastudio import r_bridge
    from tests.analysis_regression.golden.support.golden_analysis import _result_row_key

    studies = window.model.get_studies(only_if_included=True)
    rows = window.model.get_current_raw_data()
    columns = len(rows[0])
    values = ",".join(str(value) for row in rows for value in row)
    if method.startswith("binary"):
        fitter = "rma.peto" if method.endswith("peto") else "rma.mh"
        fit = (
            f"metafor::{fitter}(ai=d[i,1], n1i=d[i,2], ci=d[i,3], n2i=d[i,4], "
            'add=c(.5,.5), to=c("only0","only0"), drop00=FALSE, level=95)'
        )
        fit = (
            "if (length(i) > 1) "
            + fit
            + ' else { e <- metafor::escalc("OR", ai=d[i,1], n1i=d[i,2], ci=d[i,3], n2i=d[i,4], '
            'add=.5, to="only0"); list(b=e$yi, se=sqrt(e$vi), '
            "ci.lb=e$yi-qnorm(.975)*sqrt(e$vi), ci.ub=e$yi+qnorm(.975)*sqrt(e$vi)) }"
        )
        transform = "exp"
    else:
        if method.startswith("continuous"):
            effects = (
                f'metafor::escalc("{metric}", n1i=d[,1], m1i=d[,2], sd1i=d[,3], '
                "n2i=d[,4], m2i=d[,5], sd2i=d[,6])"
            )
            transform = "identity"
        else:
            numerator, other = (1, 2) if metric == "Sens" else (4, 3)
            effects = (
                "{ corrected <- d; zero <- apply(d == 0, 1, any); corrected[zero,] <- corrected[zero,] + .5; "
                f'metafor::escalc("PLO", xi=corrected[,{numerator}], '
                f"ni=corrected[,{numerator}]+corrected[,{other}], add=0) }}"
            )
            transform = "plogis"
        estimator = (
            "FE"
            if method.endswith("fixed.inv.var") or method == "continuous.fixed"
            else "DL"
        )
        fit = (
            f'if (length(i) > 1) metafor::rma.uni(e$yi[i], vi=e$vi[i], method="{estimator}", level=95) '
            "else list(b=e$yi[i], se=sqrt(e$vi[i]), ci.lb=e$yi[i]-qnorm(.975)*sqrt(e$vi[i]), "
            "ci.ub=e$yi[i]+qnorm(.975)*sqrt(e$vi[i]))"
        )
        fit = f"{{ e <- {effects}; {fit} }}"
    n = len(studies)
    if workflow == "cumulative":
        subsets = [list(range(1, index + 2)) for index in range(n)]
        labels = [
            study.name if index == 0 else "+ " + study.name
            for index, study in enumerate(studies)
        ]
    elif workflow == "leave-one-out":
        subsets = [
            list(range(1, n + 1)),
            *[
                [index + 1 for index in range(n) if index != omitted]
                for omitted in range(n)
            ],
        ]
        labels = ["Overall", *["- " + study.name for study in studies]]
    else:
        subsets = [
            [index + 1 for index in range(n) if index % 2 == parity]
            for parity in (1, 0)
        ]
        subsets.append(list(range(1, n + 1)))
        labels = ["Subgroup A", "Subgroup B", "Overall"]
    indices = ",".join("c(" + ",".join(map(str, subset)) + ")" for subset in subsets)
    expression = (
        f"local({{ d <- matrix(c({values}), ncol={columns}, byrow=TRUE); "
        f"fits <- lapply(list({indices}), function(i) {{ f <- {fit}; "
        f"list(estimate={transform}(as.numeric(f$b)), lower_bound={transform}(f$ci.lb), "
        f"upper_bound={transform}(f$ci.ub), standard_error=f$se) }}); "
        "jsonlite::toJSON(fits, auto_unbox=TRUE, digits=16) })"
    )
    expected = json.loads(str(r_bridge.ro.r(expression)[0]))
    return {
        "model." + _result_row_key(label) + "." + field: value
        for label, result in zip(labels, expected, strict=True)
        for field, value in result.items()
    }


def run(app, window, scenario, record):
    from rc_metastudio.analysis_dataset import Covariate
    from tests.analysis_regression.golden.support.golden_analysis import (
        parsed_numeric_sections,
    )

    suffix = scenario.removeprefix("analysis-sequential-")
    family, workflow = suffix.split("-", 1)
    methods = (
        ("binary.fixed.mh", "binary.fixed.peto", "continuous.fixed")
        if family == "fixed"
        else ("diagnostic.fixed.inv.var", "diagnostic.random")
    )

    def prepare(target):
        if workflow == "subgroup":
            studies = target.model.get_studies(only_if_included=True)
            target.model.dataset.add_covariate(
                Covariate("Group", "factor"),
                {
                    study.name: "A" if index % 2 else "B"
                    for index, study in enumerate(studies)
                },
            )
            target.model.reset_model()
            target.enable_menu_options_that_require_dataset()

    for method in methods:
        window.workspace.mark_saved()
        diagnostic = method.startswith("diagnostic")
        view = matrix(
            app,
            window,
            "analysis-diagnostic-cumulative"
            if method == "diagnostic.random"
            else "analysis-" + method,
            record,
            keep_results=True,
            workflow_override=workflow,
            metrics_override=("sens", "spec") if diagnostic else None,
            parameters={"digits": 6},
            prepare=prepare,
        )
        sections = parsed_numeric_sections(view.results)
        for metric in (
            ("Sens", "Spec") if diagnostic else (window.model.current_effect,)
        ):
            expected = references(window, method, workflow, metric)
            candidates = [
                values
                for title, values in sections.items()
                if all(key in values for key in expected)
                and (
                    not diagnostic
                    or ("Sensitivity" if metric == "Sens" else "Specificity") in title
                )
            ]
            assert len(candidates) == 1, (metric, sections, expected)
            actual = candidates[0]
            for key, value in expected.items():
                assert math.isclose(actual[key], value, abs_tol=1e-6, rel_tol=0), (
                    method,
                    metric,
                    key,
                    actual[key],
                    value,
                )
            record(
                "sequential-public-authority",
                view,
                method=method,
                workflow=workflow,
                metric=metric,
                actual=actual,
                expected=expected,
                oracle="public metafor fits reconstructed from included raw rows",
                tolerance=1e-6,
            )
        view.close()
