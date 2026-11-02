"""Real plot editing: axis geometry, unchanged fits, persisted choices and exports."""
import json
import math
import os
from pathlib import Path
from xml.etree import ElementTree as ET

from PyQt6 import QtCore, QtWidgets, sip


GEOMETRY_R = """jsonlite::toJSON(local({
                    yi <- as.numeric(plot.data$res$yi); se <- sqrt(plot.data$res$vi)
                    z <- qnorm(1-(1-as.numeric(params$conf.level)/100)/2)
                    lower <- yi-z*se; upper <- yi+z*se
                    pooled <- c(plot.data$res$b, plot.data$res$ci.lb, plot.data$res$ci.ub)
                    measure <- as.character(params$measure); n <- plot.data$sample_sizes
                    inverse <- function(x, pooled=FALSE) {
                        if (measure %in% c("OR","RR","HR","IRR","DOR","PLR","NLR","PLN")) return(exp(x))
                        if (measure %in% c("PLO","Sens","Spec")) return(plogis(x))
                        if (measure == "PAS") return(metafor::transf.iarcsin(x))
                        if (measure == "PFT") return(metafor::transf.ipft(x, ni=if (pooled) 1/mean(1/n) else n))
                        x
                    }
                    list(fitted=list(lower=lower,upper=upper,pooled=pooled),
                         natural=list(lower=inverse(lower),upper=inverse(upper),pooled=inverse(pooled,TRUE)),
                         weights=as.numeric(weights(plot.data$res)), yi=yi,se=se)
                }),digits=16,auto_unbox=FALSE)"""

def ticks(path):
    rows = {}
    for node in ET.parse(path).iter('{http://www.w3.org/2000/svg}text'):
        try:
            value = float(''.join(node.itertext()))
        except ValueError:
            continue
        y = float(node.attrib['y'])
        # Glyph ascents shift svglite baselines slightly; rounding can split one row.
        baseline = next((baseline for baseline in rows if abs(baseline - y) <= .1), y)
        rows.setdefault(baseline, []).append((value, float(node.attrib['x'])))
    candidates = [(y,row) for y,row in rows.items() if len(row) >= 2 and len({v for v,x in row}) == len(row) and all(a[1] < b[1] for a,b in zip(sorted(row), sorted(row)[1:]))]
    assert candidates, ('axis ticks absent', path, rows)
    return sorted(max(candidates)[1])


def check_axis(path, mode, ratio=False):
    values = ticks(path)
    coordinates = [(math.log(value) if ratio and mode == 'transformed' else value, x) for value,x in values]
    a, b = coordinates[0], coordinates[-1]
    assert b[0] > a[0], values
    for value, x in coordinates:
        expected = a[1] + (b[1]-a[1])*(value-a[0])/(b[0]-a[0])
        assert abs(x-expected) < .15, ('axis spacing', mode, ratio, values, expected)
    if mode == 'natural' and not ratio:
        assert values[0][0] == 0 and values[-1][0] == 1, values
    return values


def check_endpoints(path, axis_ticks, geometry, natural, ratio):
    def coordinate(value):
        return math.log(value) if ratio and not natural else value
    a, b = [(coordinate(value), x) for value,x in (axis_ticks[0],axis_ticks[-1])]
    def pixel(value):
        return a[1] + (b[1]-a[1])*(value-a[0])/(b[0]-a[0])
    expected = geometry['natural' if natural else 'fitted']
    tree = ET.parse(path)
    lines = [(float(n.attrib['x1']),float(n.attrib['x2'])) for n in tree.iter('{http://www.w3.org/2000/svg}line')
             if abs(float(n.attrib['y1'])-float(n.attrib['y2'])) < .02]
    matched = 0
    for lo,hi in zip(expected['lower'],expected['upper'],strict=True):
        left,right = sorted((pixel(lo),pixel(hi)))
        if any(abs(min(x,y)-left) < .2 and abs(max(x,y)-right) < .2 for x,y in lines):
            matched += 1
    assert matched == len(expected['lower']), ('interval endpoint projection', path, matched, expected, lines)
    if expected['pooled'] is None:
        return matched
    lower,upper = pixel(expected['pooled'][1]),pixel(expected['pooled'][2])
    polygons = [[float(point.split(',')[0]) for point in n.attrib['points'].split()]
                for n in tree.iter('{http://www.w3.org/2000/svg}polygon')]
    assert any(abs(min(xs)-min(lower,upper)) < .2 and abs(max(xs)-max(lower,upper)) < .2 for xs in polygons), ('summary endpoint projection',path,expected['pooled'],polygons)
    return matched


def run(app, window, work, record, family):
    from analysis_matrix import run as matrix
    from advanced_workflows import modal, click
    from rc_metastudio import r_bridge
    from rc_metastudio.plot_editor_dialog import EditPlotDialog
    baseline = bool(os.environ.get('RCMS_AXIS_BASELINE'))
    cases = [('analysis-data-onearm-proportion', metric) for metric in ('PLO','PAS','PFT','PLN')] if family == 'proportions' else [
        ('analysis-data-twoarm-proportion', 'OR'),
        ('analysis-data-diagnostic', None),
        ('analysis-data-twoarm-mean', 'MD'),
    ]
    for scenario, metric in cases:
        for style in ('default', 'revman', 'bmj'):
            window.workspace.mark_saved()
            view = matrix(app, window, scenario, record, keep_results=True,
                          parameters={'fp_style': style}, metric_override=metric)
            texts = dict(view.texts)
            for section in view.results.sections:
                if section.plot_kind != 'forest':
                    continue
                nav = view.nav_tree.findItems(section.title, QtCore.Qt.MatchFlag.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive)
                assert len(nav) == 1, section.title
                view.nav_tree.setCurrentItem(nav[0])
                view.report_action.setChecked(False)
                view._show_report(False)
                app.processEvents()
                artifact, item = view._selected_plot()
                path = Path(artifact.display_path())
                r_bridge.load_vars_for_plot(artifact.params_path, return_params_dict=True)
                r_bridge.execute_r_string('axis.numeric.before <- lapply(plot.data$res[vapply(plot.data$res, is.numeric, logical(1))], as.numeric); axis.weights.before <- as.numeric(weights(plot.data$res))')
                measure = str(r_bridge.execute_r_string('as.character(params$measure)')[0])
                ratio = measure in ('OR','RR','HR','IRR','DOR','PLR','NLR')
                adjustable = ratio or measure in ('PLO','PAS','PFT','PLN','Sens','Spec')
                geometry = json.loads(str(r_bridge.execute_r_string(GEOMETRY_R)[0]))
                expected_default = 'transformed' if ratio else 'natural'
                observed = ticks(path) if baseline or not adjustable else check_axis(path, expected_default, ratio)
                if not baseline and adjustable:
                    check_endpoints(path, observed, geometry, expected_default == 'natural', ratio)
                record('axis-baseline' if baseline else 'axis-default', view, measure=measure, style=style,
                       ticks=observed, geometry=geometry, plots={artifact.title:str(path)})
                if baseline:
                    continue
                if adjustable:
                    other = 'natural' if ratio else 'transformed'
                    def edit(dialog):
                        assert dialog.axis_scale.currentData() == expected_default
                        dialog.axis_scale.setCurrentIndex(dialog.axis_scale.findData(other))
                        record('axis-edit-choice', dialog, measure=measure, style=style, choice=other)
                        click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
                    modal(app, EditPlotDialog, edit, view.edit_plot_action.trigger)
                    assert dict(view.texts) == texts
                    r_bridge.load_vars_for_plot(artifact.params_path, return_params_dict=True)
                    assert str(r_bridge.execute_r_string('as.character(params$fp_axis_scale)')[0]) == other
                    exact = r_bridge.execute_r_string('identical(axis.numeric.before, lapply(plot.data$res[vapply(plot.data$res, is.numeric, logical(1))], as.numeric), num.eq=FALSE) && identical(axis.weights.before, as.numeric(weights(plot.data$res)), num.eq=FALSE)')
                    assert bool(exact[0]), 'numeric fitted fields or weights changed'

                    def reopen(dialog):
                        assert dialog.axis_scale.currentData() == other
                        dialog.axis_scale.setCurrentIndex(dialog.axis_scale.findData(expected_default))
                        click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel))
                    current = path.read_bytes()
                    modal(app, EditPlotDialog, reopen, view.edit_plot_action.trigger)
                    assert path.read_bytes() == current
                    observed = check_axis(path, other, ratio)
                    if measure == 'PLN' and other == 'transformed':
                        assert all(abs(value * 10 - round(value * 10)) < 1e-8 for value, _ in observed), ('fitted PLN ticks not round', style, observed)
                    check_endpoints(path, observed, geometry, other == 'natural', ratio)
                    record('axis-option-reopened', view, measure=measure, style=style, ticks=observed,
                           plots={artifact.title:str(path)})
                else:
                    other = expected_default
                exported = work / f'axis-{measure}-{style}.svg'
                view.plot_service.export(regenerator='forest', params_path=artifact.params_path, output_path=str(exported))
                observed = check_axis(exported, other, ratio) if adjustable else ticks(exported)
                if adjustable:
                    check_endpoints(exported, observed, geometry, other == 'natural', ratio)
                record('axis-persisted-export', view, measure=measure, style=style, choice=other,
                       ticks=observed, plots={artifact.title:str(path)}, exports={'svg':str(exported)})
                if adjustable:
                    from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
                    from rc_metastudio.results_window import ResultsWindow
                    view.report_action.setChecked(True)
                    app.processEvents()
                    view.change_settings_action.trigger()
                    app.processEvents()
                    setup = next(widget for widget in app.topLevelWidgets() if isinstance(widget, AnalysisSetupDialog) and widget.isVisible())
                    assert setup.current_param_vals.get('fp_axis_scale') == other, ('axis lost on analysis rerun', measure, style)
                    record('axis-analysis-rerun-settings', setup, measure=measure, style=style, choice=other)
                    click(app, setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
                    rerun = next(widget for widget in app.topLevelWidgets() if isinstance(widget, ResultsWindow) and widget.isVisible() and widget is not view)
                    repeated = next(candidate for candidate in rerun._nav_plot_artifacts.values() if candidate.title == artifact.title)
                    assert check_axis(repeated.display_path(), other, ratio)
                    record('axis-analysis-rerun', rerun, measure=measure, style=style, choice=other,
                           plots={repeated.title:repeated.display_path()})
                    rerun.close()
                    app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
                    assert sip.isdeleted(rerun), "closed result keeps its SVG scene alive"
            view.close()
            app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
            assert sip.isdeleted(view), "closed result keeps its SVG scene alive"


def run_sequential(app, window, work, record):
    """PFT inverses use the actual subset behind each cumulative/omission fit."""
    from analysis_matrix import run as matrix
    from rc_metastudio import analysis_dataset, r_bridge
    for workflow in ('cumulative', 'leave-one-out', 'subgroup'):
        def groups(window):
            if workflow == 'subgroup':
                studies = window.model.get_studies(False)
                window.model.add_covariate('Group', 'factor',
                    {s.label: 'A' if index % 2 else 'B' for index,s in enumerate(studies)})
                window.model.reset_model()
                window.enable_menu_options_that_require_dataset()
        window.workspace.mark_saved()
        view = matrix(app, window, 'analysis-data-onearm-proportion', record, keep_results=True,
                      metric_override='PFT', workflow_override=workflow, prepare=groups,
                      parameters={'fp_style':'default'})
        artifact = next(artifact for artifact in view._nav_plot_artifacts.values() if artifact.capability.regenerator == 'forest')
        r_bridge.load_vars_for_plot(artifact.params_path, return_params_dict=True)
        reference = json.loads(str(r_bridge.execute_r_string('''jsonlite::toJSON(local({
            counts <- metafor::escalc(measure="PFT", xi=4:9, ni=20:25)
            subsets <- if (plot.data$forest_variant == "cumulative") lapply(1:6, seq_len) else
                if (plot.data$forest_variant == "leave-one-out") c(list(1:6),lapply(1:6,function(i) (1:6)[-i])) else
                    list(c(2,4,6),c(1,3,5),1:6)
            fits <- lapply(subsets, function(index) metafor::rma.uni(yi=counts$yi[index],vi=counts$vi[index],method="DL",level=95))
            inverse <- function(value,index) metafor::transf.ipft(value,ni=1/mean(1/(20:25)[index]))
            list(subsets=subsets, fitted=lapply(fits,function(fit) c(fit$b,fit$ci.lb,fit$ci.ub)),
                 natural=lapply(seq_along(fits),function(i) inverse(c(fits[[i]]$b,fits[[i]]$ci.lb,fits[[i]]$ci.ub),subsets[[i]])))
        }),digits=16)''')[0]))
        expected = reference['natural']
        path = Path(artifact.display_path())
        axis_ticks = check_axis(path, 'natural')
        if workflow != 'subgroup':
            geometry = {'natural':dict(lower=[row[1] for row in expected],upper=[row[2] for row in expected],pooled=None)}
            check_endpoints(path, axis_ticks, geometry, True, False)
        else:
            tree = ET.parse(path)
            start,end = axis_ticks[0],axis_ticks[-1]
            def pixel(value): return start[1]+(end[1]-start[1])*(value-start[0])/(end[0]-start[0])
            polygons = [[float(point.split(',')[0]) for point in node.attrib['points'].split()]
                        for node in tree.iter('{http://www.w3.org/2000/svg}polygon')]
            for row in expected:
                assert any(abs(min(xs)-pixel(row[1])) < .2 and abs(max(xs)-pixel(row[2])) < .2 for xs in polygons), (workflow,row,polygons)
        record('axis-pft-subset-inverses', view, workflow=workflow, public_reference=reference,
               ticks=axis_ticks, plots={artifact.title:str(path)})
        exported = work / f'axis-pft-{workflow}.svg'
        view.plot_service.export(regenerator='forest', params_path=artifact.params_path, output_path=str(exported))
        assert check_axis(exported, 'natural')
        view.close()
