"""Exact values through real R, manuscript transformations and Qt CSV actions."""
from dataclasses import asdict
import json
import shutil
import sys
import math
import subprocess
from pathlib import Path
from tests.e2e.results_presentation import check_values_export


def run(app, window, work, root, record, analyze):
    from rc_metastudio import r_bridge
    from tests.e2e.analysis_presentation_workflows import analyze_existing
    sys.path.insert(0, str(root / '.agents/skills/verify-rcms/scripts'))
    # Failure obligations at the real R/Python boundary: residue and tiny values,
    # infinities, missingness and bounded P must survive without display parsing.
    edge = r_bridge.ro.r('''local({
      x <- rbind(c("Estimate", "Lower", "Upper", "P", "Unavailable"),
                 c("0.000", "0.000", "Inf", "< 0.001", "Not estimable"))
      RCMetaR:::rcmetar.numeric.fields(x, 1:5,
        c("estimate", "ci_lower", "ci_upper", "p", "value"),
        c(2.2e-17, 1e-19, Inf, 1e-8, NA_real_),
        c("display", "display", "display", "", ""), c(NA, 90, 90, NA, NA))
    })''')
    from rc_metastudio.analysis_results import _report_content
    _, parsed = _report_content({'paragraphs': [], 'tables': [r_bridge._structured_matrix('Boundary', edge, [], first_row_headers=True)]})
    cells = parsed[0].quantities[0]
    assert [q[0].value for q in cells] == [2.2e-17, 1e-19, math.inf, 1e-8, None]
    try:
        r_bridge.ro.r('RCMetaR:::rcmetar.numeric.fields(matrix("", 2, 2), 1:2, c("value", "value"), 1)')
    except r_bridge.RRuntimeError:
        pass
    else:
        raise AssertionError('R accepted misaligned quantities')
    record('numeric-boundary-states', values=asdict(parsed[0]))

    def inspect(view, label):
        view.tables_action.trigger()
        check_values_export(view, work, record, label)
        source = [t for s in view.results.sections for t in s.tables]
        primary = view.manuscript.sections[0].tables[0]
        assert primary.quantities and primary.rows, label
        quantities = [q for t in source for row in t.quantities for cell in row for q in cell]
        intervals = [q for q in quantities if q.role in ('ci_lower', 'ci_upper', 'pi_lower', 'pi_upper')]
        assert intervals and all(q.level == 90.0 for q in intervals), (label, intervals)
        for t in view._report_tables:
            for row in t.quantities:
                for cell in row:
                    if len(cell) == 2 and cell[0].role in ('ci_lower', 'pi_lower'):
                        assert cell[0] in quantities and cell[1] in quantities
        if label in ('binary', 'HR', 'IRR'):
            assert any(q.role == 'estimate' and q.scale == 'display' for q in quantities)
            assert any(q.role == 'se' and q.scale == 'log' for q in quantities)
            assert all(q.scale == '' for q in quantities if q.role == 'statistic')
        bundle = work / label
        bundle.mkdir()
        (bundle / 'tables.json').write_text(json.dumps([asdict(t) for t in source], indent=2), encoding='utf-8')
        for index, prefix in enumerate(view.params_paths.values()):
            for suffix in ('.data', '.params', '.res', '.plotdata'):
                path = Path(str(prefix)+suffix)
                if path.is_file():
                    shutil.copyfile(path, bundle / (str(index)+suffix))
        record('numeric-result-boundary', view, analysis=label, quantities=len(quantities), intervals=len(intervals))
        view.close()
        app.processEvents()

    for sample, method, label in (
        ('amino', 'binary.random', 'binary'),
        ('continuous', 'continuous.random', 'continuous'),
        ('Pignon2000-HR', 'time_to_event.random', 'HR'),
        ('NielWeise2008-IRR', 'event_rates.random', 'IRR'),
        ('lymph', 'diagnostic.reitsma', 'Reitsma'),
    ):
        window.workspace.mark_saved()
        assert window.open(str(root / 'sample_projects' / (sample+'.rcms')), raise_on_error=True)
        inspect(analyze(app, window, method, confidence=90), label)

    for workflow in ('cumulative', 'leave-one-out', 'subgroup', 'meta-regression', 'adjusted-means'):
        window.workspace.mark_saved()
        assert window.open(str(root / 'sample_projects/amino.rcms'), raise_on_error=True)
        studies = window.model.get_studies()
        window.model.add_covariate('Group', 'factor', {s.label: 'A' if i % 2 else 'B' for i, s in enumerate(studies)})
        window.model.add_covariate('Dose', 'continuous', {s.label: float(i+1) for i, s in enumerate(studies)})
        window.model.reset_model()
        window.enable_menu_options_that_require_dataset()
        inspect(analyze_existing(app, window, 'meta-regression' if workflow == 'adjusted-means' else workflow, 'binary.random', record,
                                 parameters={'digits': 3, 'conf.level': 90},
                                 covariates=('Group',) if workflow == 'adjusted-means' else ('Dose',)), workflow)
    from scripts.r_verification_support import resolve_rscript
    rscript = resolve_rscript('Rscript')
    assert rscript is not None
    command = [str(rscript), str(root / 'tests/e2e/results_values_reference.R'), str(work)]
    (work / 'public-reference-command.json').write_text(json.dumps(command), encoding='utf-8')
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
    (work / 'public-reference.log').write_text(process.stdout, encoding='utf-8')
    assert process.returncode == 0, process.stdout
    references = json.loads((work / 'public-values-reference.json').read_text(encoding='utf-8'))
    for observation in references:
        actual, expected = float(observation['actual']), float(observation['reference'])
        assert actual == expected or abs(actual-expected) <= max(math.ulp(actual), math.ulp(expected)), observation
    record('public-values-reference', comparisons=len(references))
