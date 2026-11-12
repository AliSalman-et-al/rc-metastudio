"""Forest arm/group labels, styles and persistence workflows."""

import json
import os
from pathlib import Path
from zipfile import ZipFile
from PyQt6 import QtCore, QtWidgets
from tests.python.gui.qt_test_support import mouse_click
from tests.e2e.plot_workflow_support import close, labels


def run_groups(app, window, work, record):
    from analysis_matrix import run as matrix
    from advanced_workflows import modal, click
    from rc_metastudio import __version__, r_bridge
    from rc_metastudio.about_legal_dialog import AboutLegalDialog
    from tests.e2e.analysis_result_checks import check_report
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
                    assert ('Group' not in text) if group == 'Group' else any('Participants' in line for line in text), text
                    exported = work / f'group-{family}-{group}-{style}.svg'
                    view.plot_service.export(regenerator='forest', params_path=artifact.params_path, output_path=str(exported))
                    assert labels(exported) == text
                    check_report(app, view, work, record)
                close(app, view)
    if baseline:
        return
    legacy = Path(__file__).resolve().parents[2] / 'docs/ux-audit/2026-10-16-round6/legacy-default'
    window.workspace.mark_saved()
    assert window.open(str(legacy / 'project-0.4.2.rcms'), raise_on_error=True)
    r_bridge.load_in_r(str(legacy / 'default-0.4.2.params'))
    old_style = str(r_bridge.execute_r_string('as.character(params$fp_style)')[0])
    assert old_style == 'default'
    from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
    from rc_metastudio.results_window import ResultsWindow
    from analysis_matrix import set_parameter
    window.action_go.trigger()
    app.processEvents()
    setup = next(w for w in app.topLevelWidgets() if isinstance(w,AnalysisSetupDialog) and w.isVisible())
    set_parameter(app,setup,'fp_style',old_style)
    plots_index = next(i for i in range(setup.specs_tab.count()) if setup.specs_tab.tabText(i) == 'Plots')
    mouse_click(setup.specs_tab.tabBar(),QtCore.Qt.MouseButton.LeftButton,
                     pos=setup.specs_tab.tabBar().tabRect(plots_index).center())
    app.processEvents()
    assert setup.style_cbo.isVisible() and setup.style_cbo.currentText() == 'Default'
    record('reviewer-legacy-default-setup',setup,legacy_project=str(legacy/'project-0.4.2.rcms'),internal_style=old_style)
    click(app,setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    old_view = next(w for w in app.topLevelWidgets() if isinstance(w,ResultsWindow) and w.isVisible())
    old_view.report_action.setChecked(False)
    old_view._show_report(False)
    app.processEvents()
    record('reviewer-legacy-default-reopened',old_view,internal_style=old_style,plots=dict(old_view.results.display_images))
    close(app,old_view)
    assert str(r_bridge.execute_r_string('as.character(packageVersion("RCMetaR"))')[0]) == __version__
    def about(dialog):
        assert f'RC MetaStudio {__version__}' in dialog.content_scroll_area.toPlainText()
        record('reviewer-about-version', dialog, version=__version__)
        click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Close))
    modal(app, AboutLegalDialog, about, window.action_about_legal.trigger)
    project = work / f'release-{__version__}.rcms'
    window.out_path = str(project)
    assert window.save()
    with ZipFile(project) as archive:
        manifest = json.loads(archive.read('manifest.json'))
    assert manifest['application']['version'] == __version__, manifest
    assert window.open(str(project), raise_on_error=True)
    record('reviewer-version-reopened', window, manifest=manifest, project=str(project))
