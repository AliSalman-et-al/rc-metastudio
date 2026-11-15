"""Real dialog and executed-report checks for Fable's concrete findings."""
import json

from PyQt6 import QtCore
from tests.python.gui.qt_test_support import required, wait


def run(app, window, work, root, record, analyze):
    from rc_metastudio.about_legal_dialog import AboutLegalDialog
    from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
    from rc_metastudio.continuous_data_dialog import ContinuousDataDialog

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
        if name == 'dark' and longest > image.width() * .5:
            failures.append('About wordmark has a white panel in dark mode')
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

    window.workspace.mark_saved()
    assert window.open(str(root / 'sample_projects/amino.rcms'), raise_on_error=True)
    setup = AnalysisSetupDialog(window.model, parent=window, confidence_level=95)
    setup.show()
    setup.advanced_toggle.setChecked(False)
    wait(150)
    for row in range(len(window.model.get_studies(False))):
        assert window.model.setData(window.model.index(row, window.model.INCLUDE_STUDY),
            QtCore.Qt.CheckState.Unchecked.value, QtCore.Qt.ItemDataRole.CheckStateRole)
    setup.run_ma()
    wait(200)
    assert setup.analysis_error_panel.isVisible()
    for expanded in (False, True):
        setup.analysis_error_toggle.setChecked(expanded)
        wait(200)
        viewport = required(setup.content_scroll_area.viewport())
        advanced = QtCore.QRect(setup.advanced_toggle.mapTo(viewport, QtCore.QPoint()), setup.advanced_toggle.size())
        state = dict(height=setup.height(), viewport=viewport.height(), advanced=advanced.getRect())
        observations['error-' + str(expanded)] = state
        record('fable-analysis-error-' + str(expanded), setup, **state)
        if not viewport.rect().contains(advanced):
            failures.append('Method controls are clipped after analysis error, expanded=' + str(expanded))
    setup.reject()

    window.workspace.mark_saved()
    assert window.open(str(root / 'sample_projects/lymph.rcms'), raise_on_error=True)
    view = analyze(app, window, 'diagnostic.reitsma')
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
