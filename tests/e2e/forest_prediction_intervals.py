"""Prediction-interval settings, rendering and persistence workflows."""

import json
import os
import re
from xml.etree import ElementTree as ET
from PyQt6 import QtCore
from tests.python.gui.qt_test_support import mouse_click
from tests.e2e.plot_workflow_support import check_table_surface, close, labels
from tests.e2e.plot_observations import load_saved_analysis


def run_predictions(app, window, work, record):
    from analysis_matrix import run as matrix
    from rc_metastudio import r_bridge
    from tests.e2e.analysis_result_checks import check_report
    baseline = bool(os.environ.get('RCMS_REVIEWER_BASELINE'))
    for measure, workflow in [('PFT', 'standard'), ('PLO', 'standard'), ('PAS', 'standard'),
                               ('PFT', 'cumulative'), ('PFT', 'leave-one-out'), ('PFT', 'subgroup')]:
        for style in ('default', 'revman', 'bmj'):
            def prepare(target):
                if workflow == 'subgroup':
                    target.model.add_covariate('Region', 'factor',
                        {s.label: 'A' if i % 2 else 'B' for i,s in enumerate(target.model.get_studies(False))})
                    target.model.reset_model()
                    target.refresh_analysis_actions()
            window.workspace.mark_saved()
            view = matrix(app, window, 'analysis-data-onearm-proportion', record, keep_results=True,
                          metric_override=measure, workflow_override=workflow, prepare=prepare,
                          parameters={'fp_style':style, 'digits':3})
            artifact = next(iter(view._plots.values())).artifact
            load_saved_analysis(artifact.params_path, include_plot_data=True)
            # Independent package fit from the exact entered counts, never the app inverse.
            reference = json.loads(str(r_bridge.execute_r_string('''jsonlite::toJSON(local({
                subsets <- if (identical(plot.data$forest_variant, "subgroup")) list(c(1,3,5),c(2,4,6),1:6) else list(1:6)
                lapply(subsets,function(index) {
                    n <- (20:25)[index]; events <- (4:9)[index]
                    counts <- metafor::escalc(measure=as.character(params$measure),xi=events,ni=n)
                    fit <- metafor::rma.uni(counts$yi,counts$vi,method="DL",level=95)
                    p <- predict(fit)
                    raw <- c(p$pi.lb,p$pi.ub)
                    expected <- switch(as.character(params$measure),PFT=metafor::transf.ipft.hm(raw,list(ni=n)),
                        PLO=plogis(raw),PAS=metafor::transf.iarcsin(raw))
                    list(index=index,n=n,harmonic_n=1/mean(1/n),raw=raw,expected=expected,
                         display=sprintf("%.3f",expected),
                         metafor=as.character(packageVersion("metafor")))
                })
            }),digits=16)''')[0]))
            text = view.manuscript_text.toPlainText()
            figure = labels(artifact.display_path())
            record('reviewer-prediction-before' if baseline else 'reviewer-prediction-observed', view,
                   measure=measure, workflow=workflow, style=style, reference=reference,
                   figure_text=figure, report=text, plots={artifact.title:artifact.display_path()})
            if not baseline:
                # Sequential reports do not display PI rows; their forest footer uses the full fit.
                if workflow in ('standard', 'subgroup'):
                    tables = [t for s in view.results.sections for t in s.tables if t.title == 'Prediction interval']
                    assert tables, (workflow, text)
                    observed = [list(row[-2:]) for t in tables for row in t.rows]
                    assert observed == [item['display'] for item in reference], (observed, reference)
                    assert 'sample size is unspecified' not in text
                if style == 'bmj' and workflow in ('standard', 'subgroup'):
                    assert 'Events / total' in figure, figure
                if workflow == 'subgroup' and style != 'default':
                    svg = ET.parse(artifact.display_path())
                    study_rows = [float(node.attrib['y']) for node in svg.iter('{http://www.w3.org/2000/svg}text')
                                  if ''.join(node.itertext()).startswith('Fixture ')]
                    lines = [node for node in svg.iter('{http://www.w3.org/2000/svg}line')
                             if abs(float(node.attrib['y1']) - float(node.attrib['y2'])) < .02
                             and any(0 <= y - float(node.attrib['y1']) <= 4 for y in study_rows)]
                    colours = [match[1].upper() if (match := re.search(r'\bstroke:\s*(#[0-9A-Fa-f]{6})', node.get('style', '')))
                               else node.get('stroke') for node in lines]
                    expected_colour = '#5F4C9A' if style == 'bmj' else '#000000'
                    assert len(study_rows) == 6 and colours == [expected_colour] * 6, (style, colours)
                footer = [line for line in figure if 'prediction interval:' in line]
                assert footer, (workflow, style, figure)
                assert len(footer) == len(reference), (footer,reference)
                for item, line in zip(reference, footer, strict=True):
                    lower, upper = item['display']
                    limits = f'({lower} to {upper})' if style == 'bmj' else f'[{lower}, {upper}]'
                    assert line.endswith(limits), (line, limits, reference)
                assert 'Freeman' not in footer[-1]
                if measure == 'PFT':
                    assert 'Freeman–Tukey transformed proportion = 0' in ' '.join(figure), figure
                check_report(app, view, work, record)
                if workflow in ('standard','subgroup'):
                    check_table_surface(app,view,work,record,'Prediction interval',f'PI-{measure}-{workflow}-{style}')
                exported = work / f'reviewer-{measure}-{workflow}-{style}.svg'
                view.plot_service.export(regenerator='forest', params_path=artifact.params_path, output_path=str(exported))
                assert [x for x in labels(exported) if 'prediction interval:' in x] == footer
                plot_item = next(entry.navigation_item for entry in view._plots.values() if entry.artifact is artifact)
                view.nav_tree.scrollToItem(plot_item)
                mouse_click(view.nav_tree.viewport(),QtCore.Qt.MouseButton.LeftButton,
                                 pos=view.nav_tree.visualItemRect(plot_item).center())
                app.processEvents()
                assert view._selected_plot()[0] is artifact
                assert not view.report_action.isChecked()
                assert view.content_stack.currentWidget() is view.figure_page and view.figure_page.isVisible(), 'plot selected but figure page hidden'
                record('reviewer-prediction-after', view, measure=measure, workflow=workflow, style=style,
                       reference=reference, plots={artifact.title:artifact.display_path()}, export=str(exported))
                if workflow == 'subgroup':
                    view.graphics_view.verticalScrollBar().setValue(view.graphics_view.verticalScrollBar().maximum())
                    app.processEvents()
                    record('reviewer-prediction-footer',view,measure=measure,workflow=workflow,style=style,
                           reference=reference,plots={artifact.title:artifact.display_path()})
            close(app, view)
