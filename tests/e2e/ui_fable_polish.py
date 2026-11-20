"""Real dialog and executed-report checks for Fable's concrete findings."""
import json

from PyQt6 import QtCore, QtWidgets
from tests.python.gui.qt_test_support import required, wait


def run(app, window, work, root, record, analyze):
    from rc_metastudio.about_legal_dialog import AboutLegalDialog
    from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
    from rc_metastudio.calculators.continuous_dialog import ContinuousDataDialog
    from rc_metastudio.calculators.binary_dialog import BinaryDataDialog
    from rc_metastudio.calculators.diagnostic_dialog import DiagnosticDataDialog

    observations = {}
    failures = []
    original_scheme = app.styleHints().colorScheme()
    window.showNormal()
    window.resize(1280, 800)
    about = AboutLegalDialog(window)
    about.show()
    for name, scheme in (("light", QtCore.Qt.ColorScheme.Light), ("dark", QtCore.Qt.ColorScheme.Dark)):
        app.styleHints().setColorScheme(scheme)
        wait(200)
        image = about.content_scroll_area.grab().toImage()
        longest = 0
        for y in range(image.height() // 3):
            run_length = 0
            for x in range(image.width()):
                color = image.pixelColor(x, y)
                run_length = run_length + 1 if min(color.red(), color.green(), color.blue()) > 245 else 0
                longest = max(longest, run_length)
        observations['about-' + name] = dict(white_run=longest, width=image.width())
        record('fable-about-' + name, about, **observations['about-' + name])
        if longest <= image.width() * .5:
            failures.append('About wordmark is missing its white background in ' + name + ' mode')
    about.close()
    app.styleHints().setColorScheme(original_scheme)

    assert window.open(str(root / 'sample_projects/continuous.rcms'), raise_on_error=True)
    model = window.model
    calculator = ContinuousDataDialog(model.get_current_analysis_unit_for_study(0),
        model.arm_names, model.get_current_arm_key(), model.current_effect,
        confidence_level=95, parent=window)
    calculator.show()
    wait(150)
    calculator.input_mode_combo.setCurrentIndex(calculator.input_mode_combo.findData('pre-post'))
    wait(250)
    viewport = required(calculator.content_scroll.viewport())
    rectangles = [QtCore.QRect(table.mapTo(viewport, QtCore.QPoint()), table.size())
                  for table in (calculator.g1_pre_post_table, calculator.g2_pre_post_table)]
    observations['pre-post-initial'] = dict(height=calculator.height(), viewport=viewport.height(),
        scroll=required(calculator.content_scroll.verticalScrollBar()).value(),
        tables=[rect.getRect() for rect in rectangles])
    record('fable-pre-post-before-scroll', calculator, **observations['pre-post-initial'])
    if not viewport.rect().contains(rectangles[0]):
        failures.append('Pre/post first arm is not visible on mode entry')
    available = required(calculator.screen()).availableGeometry()
    needed = calculator.height() + max(0, rectangles[1].bottom() - viewport.height() + 1)
    if needed < available.height() * .9 and not viewport.rect().contains(rectangles[1]):
        failures.append('Pre/post second arm is clipped despite available screen height')
    calculator.reject()

    for project in ('amino', 'continuous', 'lymph'):
        window.workspace.mark_saved()
        assert window.open(str(root / f'sample_projects/{project}.rcms'), raise_on_error=True)
        model = window.model
        args = (model.get_current_analysis_unit_for_study(0), model.arm_names, model.get_current_arm_key())
        if project == 'lymph':
            calculator = DiagnosticDataDialog(*args, confidence_level=95, parent=window)
        elif project == 'amino':
            calculator = BinaryDataDialog(*args, model.current_effect, confidence_level=95, parent=window)
        else:
            calculator = ContinuousDataDialog(*args, model.current_effect, confidence_level=95, parent=window)
        calculator.show()
        wait(150)
        estimate = calculator.effect_text_box
        lower = calculator.lower_text_box
        upper = calculator.upper_text_box
        x = lambda field: field.mapTo(calculator, QtCore.QPoint()).x()
        if abs(x(estimate) - x(lower)) > 1 or lower.y() != upper.y():
            failures.append(project + ' calculator interval does not share the estimate field column')
        if abs(lower.width() - upper.width()) > 2:
            failures.append(project + ' calculator interval fields have unequal widths')
        if isinstance(calculator, ContinuousDataDialog) and any(label.font().italic() for label in
                (calculator.group_one_label, calculator.group_two_label)):
            failures.append('Continuous arm headings are italic')
        record('fable-calculator-alignment-' + project, calculator,
               estimate_x=x(estimate), lower_x=x(lower), upper_x=x(upper))
        calculator.reject()

    window.workspace.mark_saved()
    assert window.open(str(root / 'sample_projects/amino.rcms'), raise_on_error=True)
    window.model.add_covariate('Dose', 'continuous')
    regression = AnalysisSetupDialog(window.model, parent=window, confidence_level=95, analysis_type='meta-regression')
    regression.show()
    wait(150)
    active = required(regression.specs_tab.currentWidget())
    active_layout = required(active.layout())
    if regression.height() > active_layout.sizeHint().height() + regression.fontMetrics().height() * 12:
        failures.append('Regression first tab retains space for a taller hidden tab')
    record('fable-regression-first-tab', regression, height=regression.height(), content_height=active_layout.sizeHint().height())
    regression.reject()
    setup = AnalysisSetupDialog(window.model, parent=window, confidence_level=95, on_result=window.analysis)
    setup.show()
    setup.advanced_toggle.setChecked(False)
    wait(150)
    parameter_layout = required(setup.parameter_grp_box.layout())
    assert isinstance(parameter_layout, QtWidgets.QGridLayout)
    field = required(required(parameter_layout.itemAtPosition(0, 1)).widget())
    method_x = setup.method_cbo_box.mapTo(setup, QtCore.QPoint()).x()
    parameter_x = field.mapTo(setup, QtCore.QPoint()).x()
    if abs(method_x - parameter_x) > 1:
        failures.append('Analysis method and parameter fields do not share a column')
    for row in range(len(window.model.get_studies(False))):
        assert window.model.setData(window.model.index(row, window.model.INCLUDE_STUDY),
            QtCore.Qt.CheckState.Unchecked.value, QtCore.Qt.ItemDataRole.CheckStateRole)
    setup.run_ma()
    wait(200)
    assert setup.analysis_error_panel.isVisible()
    if setup.specs_tab.tabText(setup.specs_tab.indexOf(setup.plot_tab)) != 'Forest plot':
        failures.append('Forest-only setup has a generic Plots tab')
    for expanded in (False, True):
        setup.analysis_error_toggle.setChecked(expanded)
        wait(200)
        viewport = required(setup.content_scroll_area.viewport())
        advanced = QtCore.QRect(setup.advanced_toggle.mapTo(viewport, QtCore.QPoint()), setup.advanced_toggle.size())
        state = dict(height=setup.height(), viewport=viewport.height(), advanced=advanced.getRect())
        observations['error-' + str(expanded)] = state
        record('fable-analysis-error-' + str(expanded), setup, **state)
        if expanded and setup.analysis_error_details.height() > setup.analysis_error_details.fontMetrics().lineSpacing() * 8 + 2 * setup.analysis_error_details.frameWidth() + 8:
            failures.append('Technical error details occupy more than eight lines')
        if not viewport.rect().contains(advanced):
            failures.append('Method controls are clipped after analysis error, expanded=' + str(expanded))
    setup.reject()

    window.workspace.mark_saved()
    assert window.open(str(root / 'sample_projects/lymph.rcms'), raise_on_error=True)
    combined = AnalysisSetupDialog(window.model, parent=window, confidence_level=95, diagnostic_metrics=['sens', 'spec', 'dor'])
    combined.show()
    combined.advanced_toggle.setChecked(True)
    wait(250)
    for theme, scheme in (("light", QtCore.Qt.ColorScheme.Light), ("dark", QtCore.Qt.ColorScheme.Dark)):
        app.styleHints().setColorScheme(scheme)
        wait(150)
        fields = [field for field in combined.methods_tab.findChildren(QtWidgets.QWidget)
                  if field.isVisible() and isinstance(field, (QtWidgets.QComboBox, QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox))]
        xs = [field.mapTo(combined, QtCore.QPoint()).x() for field in fields]
        if max(xs) - min(xs) > 1:
            failures.append('Combined diagnostic and Advanced fields do not share a column')
        record('fable-combined-field-alignment-' + theme, combined, field_xs=xs)
    app.styleHints().setColorScheme(original_scheme)
    combined.reject()
    view = analyze(app, window, 'diagnostic.reitsma')
    strip = view.result_facts.accessibleDescription()
    if strip.count('Reitsma bivariate model') != 1 or '95% CI' not in strip:
        failures.append('Diagnostic identity repeats a shared fit or omits the CI label')
    title = view.results.manuscript_title
    methods = view.results.manuscript_methods
    observations['diagnostic'] = dict(title=title, methods=methods)
    record('fable-diagnostic-title', view, **observations['diagnostic'])
    if 'Reitsma' not in title:
        failures.append('Executed manuscript title lowercases Reitsma')
    if 'applied to All studies' in methods:
        failures.append('Correction prose uses a capitalised option label mid-sentence')
    view.close()
    (work / 'fable-observations.json').write_text(json.dumps(observations, indent=2), encoding='utf-8')
    assert not failures, failures

