"""Recoverable contour-level validation through the small-study dialog."""

from pathlib import Path
from PyQt6 import QtWidgets


def run(app, window, work, record):
    from advanced_workflows import modal, click
    from rc_metastudio.results import window as results_window
    from rc_metastudio.analysis.small_study_effects_dialog import SmallStudyEffectsDialog
    root = Path(__file__).resolve().parents[2]
    window.workspace.mark_saved()
    assert window.open(str(root / 'sample_projects/NielWeise2008-IRR.rcms'), raise_on_error=True)
    def small_study(dialog):
        explanation = dialog.automatic_test_label.text()
        assert '10' in explanation and '9 eligible' in dialog.context_label.text(), explanation
        assert 'Mixed-effects Egger' in explanation, explanation
        dialog.contour_funnel_check.setChecked(True)
        for invalid in ('abc', '90,,95', '0,101', ''):
            dialog.contour_levels_edit.setText(invalid)
            click(app, dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
            assert dialog.isVisible() and dialog.failure_label.isVisible()
            assert 'Contour' in dialog.failure_label.text()
            assert dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()
            record('contour-inline-validation', dialog, input=invalid,
                   failure=dialog.failure_label.text(), eligibility=explanation)
        dialog.contour_levels_edit.setText('90,95,99')
        click(app, dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    modal(app, SmallStudyEffectsDialog, small_study, window.action_publication_bias.trigger)
    view = next(widget for widget in app.topLevelWidgets() if isinstance(widget, results_window.ResultsWindow) and widget.isVisible())
    assert any('contour' in title.lower() for title in view.results.images)
    record('contour-validation-recovered', view, texts=dict(view.texts), plots=dict(view.results.display_images))
    view.close()
