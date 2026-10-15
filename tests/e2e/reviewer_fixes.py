"""Round-six reviewer proof through fresh Qt/R analyses and persisted projects."""
import json
import os
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from PyQt6 import QtCore, QtWidgets, sip


def labels(path):
    return [''.join(node.itertext()) for node in ET.parse(path).iter('{http://www.w3.org/2000/svg}text')]


def close(app, view):
    view.close()
    app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    assert sip.isdeleted(view)


def run_predictions(app, window, work, record):
    from analysis_matrix import run as matrix
    from rc_metastudio import analysis_dataset, r_bridge
    from tests.e2e.audit_round3 import check_report
    baseline = bool(os.environ.get('RCMS_REVIEWER_BASELINE'))
    for measure, workflow in [('PFT', 'standard'), ('PLO', 'standard'), ('PAS', 'standard'),
                               ('PFT', 'cumulative'), ('PFT', 'leave-one-out'), ('PFT', 'subgroup')]:
        for style in ('default', 'revman', 'bmj'):
            def prepare(target):
                if workflow == 'subgroup':
                    target.model.dataset.add_covariate(analysis_dataset.Covariate('Region', 'factor'),
                        {s.name: 'A' if i % 2 else 'B' for i,s in enumerate(target.model.dataset.studies)})
                    target.model.reset_model()
                    target.enable_menu_options_that_require_dataset()
            window.workspace.mark_saved()
            view = matrix(app, window, 'analysis-data-onearm-proportion', record, keep_results=True,
                          metric_override=measure, workflow_override=workflow, prepare=prepare,
                          parameters={'fp_style':style, 'digits':3})
            artifact = next(iter(view._nav_plot_artifacts.values()))
            r_bridge.load_vars_for_plot(artifact.params_path, return_params_dict=True)
            # Independent package fit from the exact entered counts, never the app inverse.
            reference = json.loads(str(r_bridge.execute_r_string('''jsonlite::toJSON(local({
                subsets <- if (identical(plot.data$forest_variant, "subgroup")) list(c(2,4,6),c(1,3,5),1:6) else list(1:6)
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
            text = view._plain_text_report()
            figure = labels(artifact.display_path())
            record('reviewer-prediction-before' if baseline else 'reviewer-prediction-observed', view,
                   measure=measure, workflow=workflow, style=style, reference=reference,
                   figure_text=figure, report=text, plots={artifact.title:artifact.display_path()})
            if not baseline:
                # Sequential reports do not display PI rows; their forest footer uses the full fit.
                if workflow in ('standard', 'subgroup'):
                    tables = [t for s in view.results.sections for t in s.tables if t.title == 'Prediction interval']
                    assert tables, (workflow, text)
                    observed = [row[-2:] for t in tables for row in t.rows]
                    assert observed == [item['display'] for item in reference], (observed, reference)
                    assert 'sample size is unspecified' not in text
                footer = [line for line in figure if 'prediction interval:' in line]
                assert footer, (workflow, style, figure)
                assert ', '.join(reference[-1]['display']) in footer[-1], (footer, reference)
                assert 'Freeman' not in footer[-1]
                if measure == 'PFT':
                    assert any('Freeman–Tukey transformed proportion = 0' in line for line in figure), figure
                check_report(app, view, work, record)
                exported = work / f'reviewer-{measure}-{workflow}-{style}.svg'
                view.plot_service.export(regenerator='forest', params_path=artifact.params_path, output_path=str(exported))
                assert [x for x in labels(exported) if 'prediction interval:' in x] == footer
                view.report_action.setChecked(False)
                view._show_report(False)
                app.processEvents()
                record('reviewer-prediction-after', view, measure=measure, workflow=workflow, style=style,
                       reference=reference, plots={artifact.title:artifact.display_path()}, export=str(exported))
            close(app, view)


def run_groups(app, window, work, record):
    from analysis_matrix import run as matrix
    from advanced_workflows import modal, click
    from rc_metastudio import __version__, r_bridge
    from rc_metastudio.about_legal_dialog import AboutLegalDialog
    from tests.e2e.audit_round3 import check_report
    baseline = bool(os.environ.get('RCMS_REVIEWER_BASELINE'))
    for family in ('onearm-proportion', 'onearm-mean'):
        for group in ('Group', 'Participants'):
            for style in ('default', 'revman', 'bmj'):
                window.workspace.mark_saved()
                view = matrix(app, window, 'analysis-data-' + family, record, keep_results=True,
                              group_names=(group,), parameters={'fp_style':style})
                artifact = next(iter(view._nav_plot_artifacts.values()))
                text = labels(artifact.display_path())
                view.report_action.setChecked(False)
                view._show_report(False)
                app.processEvents()
                record('reviewer-group-before' if baseline else 'reviewer-group-after', view,
                       family=family, group=group, style=style, figure_text=text,
                       plots={artifact.title:artifact.display_path()})
                if not baseline:
                    assert ('Group' not in text) if group == 'Group' else ('Participants' in text), text
                    exported = work / f'group-{family}-{group}-{style}.svg'
                    view.plot_service.export(regenerator='forest', params_path=artifact.params_path, output_path=str(exported))
                    assert labels(exported) == text
                    check_report(app, view, work, record)
                close(app, view)
    if baseline:
        return
    assert __version__ == '0.5.0'
    assert str(r_bridge.execute_r_string('as.character(packageVersion("RCMetaR"))')[0]) == __version__
    def about(dialog):
        assert 'RC MetaStudio 0.5.0' in dialog.content_scroll_area.toPlainText()
        record('reviewer-about-version', dialog, version=__version__)
        click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Close))
    modal(app, AboutLegalDialog, about, window.action_about_legal.trigger)
    project = work / 'release-0.5.0.rcms'
    window.out_path = str(project)
    assert window.save()
    with ZipFile(project) as archive:
        manifest = json.loads(archive.read('manifest.json'))
    assert manifest['application']['version'] == '0.5.0', manifest
    assert window.open(str(project), raise_on_error=True)
    record('reviewer-version-reopened', window, manifest=manifest, project=str(project))


def check_colours(path, colour='#2F5597'):
    """Check rendered study boxes, CIs, caps, arrows and summary diamonds."""
    import re
    root = ET.parse(path)
    polygons = list(root.iter('{http://www.w3.org/2000/svg}polygon'))
    assert polygons, path
    y = [float(point.split(',')[1]) for node in polygons for point in node.attrib['points'].split()]
    top, bottom = min(y), max(y)
    def paint(node, name):
        found = re.search(r'(?:^|;)\s*' + name + r':\s*([^;]+)', node.attrib.get('style',''))
        return (found[1] if found else node.attrib.get(name, '#000000')).upper()
    for node in polygons:
        assert paint(node, 'fill') == colour, (path, 'marker/diamond/arrow', node.attrib)
    intervals = []
    caps = []
    for node in root.iter('{http://www.w3.org/2000/svg}line'):
        x1,y1,x2,y2 = (float(node.attrib[k]) for k in ('x1','y1','x2','y2'))
        if top <= y1 <= bottom and top <= y2 <= bottom:
            if abs(y1-y2) < .02 and abs(x1-x2) > 1:
                intervals.append(node)
            elif abs(x1-x2) < .02 and .2 < abs(y1-y2) < 15:
                caps.append(node)
    assert intervals and caps, (path, len(intervals),len(caps))
    for node in intervals + caps:
        assert paint(node,'stroke') == colour, (path, 'CI/cap', node.attrib)
    def luminance(hex_value):
        rgb = [int(hex_value[i:i+2],16)/255 for i in (1,3,5)]
        rgb = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        return sum(a*b for a,b in zip(rgb,(.2126,.7152,.0722),strict=True))
    contrast = {background:(luminance(background)+.05)/(luminance(colour)+.05) for background in ('#FFFFFF','#EEEEEE')}
    assert min(contrast.values()) >= 3, contrast
    return dict(polygons=len(polygons), intervals=len(intervals), caps=len(caps), contrast=contrast)


def run_colours(app, window, work, record):
    from analysis_matrix import run as matrix
    from advanced_workflows import export_formats, modal, click
    from rc_metastudio import r_bridge
    from rc_metastudio.plot_editor_dialog import EditPlotDialog
    from tests.e2e.audit_round3 import analyze_existing
    baseline = bool(os.environ.get('RCMS_REVIEWER_BASELINE'))
    cases = [('analysis-amino-binary-' + workflow, None) for workflow in ('cumulative','leave-one-out','subgroup')]
    cases += [('analysis-data-' + family, metric) for family,metric in
              [('twoarm-proportion','OR'),('onearm-proportion','PFT'),('onearm-mean',None),('diagnostic',None)]]
    cases += [('HR',None),('IRR',None)]
    for scenario,metric in cases:
        window.workspace.mark_saved()
        if scenario in ('HR','IRR'):
            sample = 'Pignon2000-HR' if scenario == 'HR' else 'NielWeise2008-IRR'
            assert window.open(str(Path(__file__).resolve().parents[2]/'sample_projects'/f'{sample}.rcms'),raise_on_error=True)
            view = analyze_existing(app,window,'standard','time_to_event.random' if scenario == 'HR' else 'event_rates.random',record,{'fp_style':'default','digits':3})
        else:
            view = matrix(app,window,scenario,record,keep_results=True,metric_override=metric,parameters={'fp_style':'default'})
        for index,artifact in enumerate(view._nav_plot_artifacts.values()):
            if artifact.capability.regenerator != 'forest':
                continue
            nav = [item for item in view.nav_tree.findItems('',QtCore.Qt.MatchFlag.MatchContains | QtCore.Qt.MatchFlag.MatchRecursive) if view._nav_plot_artifacts.get(id(item)) is artifact]
            view.nav_tree.setCurrentItem(nav[0])
            view.report_action.setChecked(False)
            view._show_report(False)
            app.processEvents()
            record('reviewer-colour-before' if baseline else 'reviewer-colour-after',view,scenario=scenario,title=artifact.title,
                   plots={artifact.title:artifact.display_path()})
            if baseline:
                continue
            observed = check_colours(artifact.display_path())
            r_bridge.load_vars_for_plot(artifact.params_path,return_params_dict=True)
            r_bridge.execute_r_string('reviewer.numeric.before <- lapply(plot.data$res[vapply(plot.data$res,is.numeric,logical(1))],as.numeric)')
            def editor(dialog):
                assert dialog.style_cbo.currentText() == 'Default'
                assert dialog.style_cbo.findText('Default (metafor)') < 0
                record('reviewer-default-style-editor',dialog,scenario=scenario)
                click(app,dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel))
            modal(app,EditPlotDialog,editor,view.edit_plot_action.trigger)
            # One full export set per family, including sequential and clinical variants.
            files = export_formats(app,view,work/f'colour-{scenario}-{index}',scenario,record)
            check_colours(files['svg'])
            r_bridge.load_vars_for_plot(artifact.params_path,return_params_dict=True)
            assert bool(r_bridge.execute_r_string('identical(reviewer.numeric.before,lapply(plot.data$res[vapply(plot.data$res,is.numeric,logical(1))],as.numeric),num.eq=FALSE)')[0])
            record('reviewer-colour-exports',view,scenario=scenario,title=artifact.title,observed=observed,exports=files,
                   plots={artifact.title:artifact.display_path()})
        close(app,view)
