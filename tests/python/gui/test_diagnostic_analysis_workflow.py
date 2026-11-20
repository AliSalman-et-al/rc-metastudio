"""Diagnostic analysis workflow behavior."""

import os
import sys
from pathlib import Path
from collections.abc import Callable

from rc_metastudio import automation

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.abspath("src"))


REPO_ROOT = os.getcwd()
ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("RCMS_QT6_BUILD_ROOT", str(ROOT / "build" / "qt6-verification"))
from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()


def _set_backend(
    monkeypatch, backend: object, name: str, replacement: Callable[..., object]
) -> None:
    """Patch one dynamic R backend function at the test seam."""

    monkeypatch.setattr(backend, name, replacement, raising=False)


def _create_diagnostic_dataset(window):
    window._handle_wizard_results(
        {
            "path": "new_dataset",
            "outcome_info": {
                "arms": "two",
                "data_type": "diagnostic",
                "sub_type": None,
                "effect": "Sens",
                "metric_choices": [],
                "name": "Accuracy",
            },
        }
    )


def test_diagnostic_next_surfaces_specs_failure_instead_of_silent_dead_end():

    app, window = automation.start_automation()
    main_window = sys.modules["rc_metastudio.main_window"]
    from rc_metastudio.analysis import diagnostic_metrics_dialog
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog

    original_specs = analysis_setup_dialog.AnalysisSetupDialog
    original_critical = main_window.QMessageBox.critical
    shown = []
    try:
        _create_diagnostic_dataset(window)

        # Simulate a Method & Parameters construction failure raised after the
        # diagnostic metrics dialog hands off to the shared builder.
        def _boom(*args, **kwargs):
            raise ValueError("simulated preparation failure")

        setattr(analysis_setup_dialog, "AnalysisSetupDialog", _boom)
        # QMessageBox.critical (a modal exec) aborts under the offscreen
        # platform, so record the call instead of actually showing it.
        setattr(
            main_window.QMessageBox,
            "critical",
            staticmethod(lambda *args, **kwargs: shown.append(args)),
        )

        window._launch_analysis()
        form = window.findChild(diagnostic_metrics_dialog.DiagnosticMetricsDialog)
        assert form is not None

        # The bug: this used to raise out of the slot with no user feedback.
        form.ok()

        assert shown, "diagnostic next > swallowed the backend error silently"
        assert shown[0][1] == "Could not prepare analysis"
        assert "simulated preparation failure" in shown[0][2]
        assert "backend is not available" not in shown[0][2]
        assert form.isVisible()
    finally:
        analysis_setup_dialog.AnalysisSetupDialog = original_specs
        main_window.QMessageBox.critical = original_critical
        _close_without_prompt(app, window)


def test_diagnostic_backend_failure_does_not_open_empty_results(monkeypatch):

    app, window = automation.start_automation()
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog

    backend = analysis_setup_dialog.analysis_adapter.r_bridge
    saved = {
        name: getattr(backend, name)
        for name in (
            "get_available_methods",
            "get_params",
            "dataset_to_simple_diagnostic_r_object",
            "run_versioned_analysis_requests",
        )
    }
    shown = []
    results = []
    try:
        _create_diagnostic_dataset(window)

        _set_backend(
            monkeypatch,
            backend,
            "dataset_to_simple_diagnostic_r_object",
            lambda model, **kwargs: None,
        )
        _set_backend(
            monkeypatch,
            backend,
            "get_available_methods",
            lambda **kwargs: {
                "Random-effects": "diagnostic.random",
            },
        )
        _set_backend(
            monkeypatch, backend, "get_params", lambda method: ({}, {}, [], {})
        )
        monkeypatch.setattr(
            backend,
            "get_analysis_plot_capabilities",
            lambda *args, **kwargs: [],
            raising=False,
        )
        _set_backend(
            monkeypatch,
            backend,
            "run_versioned_analysis_requests",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                RuntimeError("simulated diagnostic failure")
            ),
        )
        monkeypatch.setattr(
            analysis_setup_dialog.QMessageBox,
            "critical",
            lambda *args, **kwargs: shown.append(args),
        )
        monkeypatch.setattr(window, "analysis", lambda result, **_kwargs: results.append(result))

        form = window._build_analysis_specs_dialog(
            diagnostic_metrics=["lr", "dor"],
            confidence_level=window.model.get_confidence_level(),
        )

        form.run_ma()

        assert not shown
        assert form.analysis_error_label.text() == "No studies are included. Select Include for at least one study with complete data."
        assert form.analysis_error_details.isHidden()
        assert "simulated diagnostic failure" in form.analysis_error_details.toPlainText()
        form.analysis_error_toggle.click()
        assert not form.analysis_error_details.isHidden()
        assert not form.analysis_error_label.isHidden()
        assert results == []
    finally:
        for name, value in saved.items():
            setattr(backend, name, value)
        _close_without_prompt(app, window)


def test_diagnostic_multi_metric_failure_keeps_independent_results(monkeypatch):
    app, window = automation.start_automation()
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog

    backend = analysis_setup_dialog.analysis_adapter.r_bridge
    saved = {
        name: getattr(backend, name)
        for name in (
            "get_available_methods",
            "get_params",
            "dataset_to_simple_diagnostic_r_object",
            "run_versioned_analysis_requests",
        )
    }
    shown = []
    results = []
    try:
        _create_diagnostic_dataset(window)

        _set_backend(
            monkeypatch,
            backend,
            "dataset_to_simple_diagnostic_r_object",
            lambda model, **kwargs: None,
        )
        _set_backend(
            monkeypatch,
            backend,
            "get_available_methods",
            lambda **kwargs: {
                "Reitsma bivariate model": "diagnostic.reitsma",
                "Random-effects": "diagnostic.random",
            },
        )
        _set_backend(
            monkeypatch, backend, "get_params", lambda method: ({}, {}, [], {})
        )
        monkeypatch.setattr(
            backend,
            "get_analysis_plot_capabilities",
            lambda *args, **kwargs: [],
            raising=False,
        )

        def run_metric(requests, data):
            assert [request["metric"] for request in requests] == ["Sens", "NLR", "PLR", "DOR"]
            texts = {"Sens Error": "Reitsma bivariate model failed to converge"}
            texts.update({f"{metric} Summary": f"{metric} ok" for metric in ("NLR", "PLR", "DOR")})
            images = {f"{metric} Forest plot": f"{metric.lower()}.png" for metric in ("NLR", "PLR", "DOR")}
            return {
                "version": 1, "texts": texts, "images": images, "image_order": list(images),
                "plot_capabilities": {title: {"plot_kind": "forest", "editable": False,
                    "styleable": True, "composition": "single", "regenerator": "forest"} for title in images},
                "sections": [
                    {"id": f"diagnostic.{i}", "kind": kind, "order": i, "title": title, "source_key": title}
                    for i, (kind, title) in enumerate([*(('text', t) for t in texts), *(('image', t) for t in images)])
                ],
            }

        _set_backend(
            monkeypatch, backend, "run_versioned_analysis_requests", run_metric
        )
        monkeypatch.setattr(
            analysis_setup_dialog.QMessageBox,
            "critical",
            lambda *args, **kwargs: shown.append(args),
        )
        monkeypatch.setattr(window, "analysis", lambda result, **_kwargs: results.append(result))

        form = window._build_analysis_specs_dialog(
            diagnostic_metrics=["sens", "lr", "dor"],
            confidence_level=window.model.get_confidence_level(),
        )
        form.diagnostic_analysis_details = {
            "Sens": ("diagnostic.reitsma", {"conf.level": 95.0}),
            "DOR": ("diagnostic.random", {"conf.level": 95.0}),
            "PLR": ("diagnostic.random", {"conf.level": 95.0}),
            "NLR": ("diagnostic.random", {"conf.level": 95.0}),
        }
        form.sens_spec = False
        form.lr_dor = True

        form.run_ma()

        assert shown == []
        assert len(results) == 1
        assert results[0].texts["Sens Error"] == "Reitsma bivariate model failed to converge"
        assert results[0].texts["DOR Summary"] == "DOR ok"
        assert results[0].texts["PLR Summary"] == "PLR ok"
        assert results[0].texts["NLR Summary"] == "NLR ok"
        assert results[0].image_order == (
            "NLR Forest plot",
            "PLR Forest plot",
            "DOR Forest plot",
        )
    finally:
        for name, value in saved.items():
            setattr(backend, name, value)
        _close_without_prompt(app, window)


def test_diagnostic_direct_effects_build_analysis_data_per_metric(monkeypatch):

    app, window = automation.start_automation()
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog

    backend = analysis_setup_dialog.analysis_adapter.r_bridge
    saved = {
        name: getattr(backend, name, None)
        for name in (
            "get_available_methods",
            "get_params",
            "diagnostic_data_arguments",
            "dataset_to_simple_diagnostic_r_object",
            "run_versioned_analysis_requests",
        )
    }
    built_metrics = []
    multi_calls = []
    results = []
    try:
        _create_diagnostic_dataset(window)

        monkeypatch.setattr(
            window.model, "included_studies_have_raw_data", lambda: False
        )
        monkeypatch.setattr(
            window.model,
            "included_studies_have_point_estimates",
            lambda effect=None: effect in ("Sens", "Spec"),
        )

        _set_backend(
            monkeypatch,
            backend,
            "get_available_methods",
            lambda **kwargs: {
                "Random-effects": "diagnostic.random",
            },
        )
        _set_backend(
            monkeypatch, backend, "get_params", lambda method: ({}, {}, [], {})
        )
        monkeypatch.setattr(
            backend,
            "get_analysis_plot_capabilities",
            lambda *args, **kwargs: [],
            raising=False,
        )

        def build_metric(_model, *, metric):
            built_metrics.append(metric)
            return {"y": [-0.1] if metric == "Sens" else [0.7], "SE": [0.2]}

        def run_metric(requests, *, metric_data):
            multi_calls.append([request["params"]["measure"] for request in requests])
            assert [entry["y"] for entry in metric_data] == [[-0.1], [0.7]]
            texts = {f"{metric} Summary": "ok" for metric in multi_calls[-1]}
            return {
                "version": 1, "texts": texts, "images": {},
                "sections": [
                    {"id": f"diagnostic.{i}", "kind": "text", "order": i, "title": title, "source_key": title}
                    for i, title in enumerate(texts)
                ],
            }

        _set_backend(monkeypatch, backend, "dataset_to_simple_diagnostic_r_object", lambda *_args, **_kwargs: None)
        _set_backend(monkeypatch, backend, "diagnostic_data_arguments", build_metric)
        _set_backend(
            monkeypatch, backend, "run_versioned_analysis_requests", run_metric
        )
        monkeypatch.setattr(window, "analysis", lambda result, **_kwargs: results.append(result))

        form = window._build_analysis_specs_dialog(
            diagnostic_metrics=["sens", "spec"],
            confidence_level=window.model.get_confidence_level(),
        )
        built_metrics[:] = []

        form.run_ma()

        assert built_metrics == ["Sens", "Spec"]
        assert multi_calls == [["Sens", "Spec"]]
        assert results and sorted(results[0].texts) == [
            "Sens Summary",
            "Spec Summary",
        ]
    finally:
        for name, value in saved.items():
            if value is None:
                try:
                    delattr(backend, name)
                except AttributeError:
                    pass
            else:
                setattr(backend, name, value)
        _close_without_prompt(app, window)


def test_diagnostic_metric_dialog_does_not_run_without_selected_metrics(monkeypatch):

    app, window = automation.start_automation()
    from rc_metastudio.analysis import diagnostic_metrics_dialog

    warnings = []
    captured = []

    try:
        _create_diagnostic_dataset(window)

        monkeypatch.setattr(
            window.model, "included_studies_have_raw_data", lambda: False
        )
        monkeypatch.setattr(
            window.model,
            "included_studies_have_point_estimates",
            lambda effect=None: False,
        )
        monkeypatch.setattr(
            diagnostic_metrics_dialog.QMessageBox,
            "warning",
            lambda *args: warnings.append(args),
        )

        def open_settings(metrics):
            captured.extend(metrics)
            return True

        form = diagnostic_metrics_dialog.DiagnosticMetricsDialog(
            window.model, open_settings, parent=window
        )

        assert form.get_selected_metrics() == []
        assert form.btn_ok.isEnabled() is False

        form.ok()

        assert captured == []
        assert warnings
        assert warnings[0][1:3] == (
            "No diagnostic metric selected",
            "Select at least one available diagnostic metric before running analysis.",
        )
    finally:
        _close_without_prompt(app, window)


def test_diagnostic_direct_effects_do_not_offer_count_based_methods(monkeypatch):

    app, window = automation.start_automation()
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog

    backend = analysis_setup_dialog.analysis_adapter.r_bridge
    saved = {
        name: getattr(backend, name)
        for name in (
            "get_available_methods",
            "get_params",
            "dataset_to_simple_diagnostic_r_object",
        )
    }
    try:
        _create_diagnostic_dataset(window)

        monkeypatch.setattr(
            window.model, "included_studies_have_raw_data", lambda: False
        )
        monkeypatch.setattr(
            window.model,
            "included_studies_have_point_estimates",
            lambda effect=None: effect in ("Sens", "Spec"),
        )

        _set_backend(
            monkeypatch,
            backend,
            "dataset_to_simple_diagnostic_r_object",
            lambda model, **kwargs: None,
        )
        _set_backend(
            monkeypatch,
            backend,
            "get_available_methods",
            lambda **kwargs: {
                "Reitsma bivariate model": "diagnostic.reitsma",
                "Random-effects": "diagnostic.random",
                "Fixed-effect inverse-variance": "diagnostic.fixed.inv.var",
            },
        )
        _set_backend(
            monkeypatch, backend, "get_params", lambda method: ({}, {}, [], {})
        )
        monkeypatch.setattr(
            backend,
            "get_analysis_plot_capabilities",
            lambda *args, **kwargs: [],
            raising=False,
        )

        form = window._build_analysis_specs_dialog(
            diagnostic_metrics=["sens", "spec"],
            confidence_level=window.model.get_confidence_level(),
        )

        method_names = [
            str(form.method_cbo_box.itemText(index))
            for index in range(form.method_cbo_box.count())
        ]

        assert "Reitsma bivariate model" not in method_names
        assert method_names == [
            "Random-effects",
            "Fixed-effect inverse-variance",
        ]
    finally:
        for name, value in saved.items():
            setattr(backend, name, value)
        _close_without_prompt(app, window)


def test_diagnostic_method_selector_exposes_full_choices_without_root_cap(monkeypatch):
    from rc_metastudio import adaptive_controls
    from rc_metastudio import adaptive_window
    from PyQt6 import QtCore, QtWidgets

    app, window = automation.start_automation()
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog

    backend = sys.modules.get(
        "rc_metastudio.r_bridge", analysis_setup_dialog.analysis_adapter.r_bridge
    )
    saved = {
        name: getattr(backend, name)
        for name in (
            "get_available_methods",
            "get_params",
            "dataset_to_simple_diagnostic_r_object",
        )
    }
    try:
        _create_diagnostic_dataset(window)

        _set_backend(
            monkeypatch,
            backend,
            "dataset_to_simple_diagnostic_r_object",
            lambda model, **kwargs: None,
        )
        _set_backend(
            monkeypatch,
            backend,
            "get_available_methods",
            lambda **kwargs: {
                "Random-effects": "diagnostic.random",
                "Fixed-effect inverse-variance": "diagnostic.fixed.inv.var",
            },
        )
        _set_backend(
            monkeypatch, backend, "get_params", lambda method: ({}, {}, [], {})
        )
        monkeypatch.setattr(
            backend,
            "get_analysis_plot_capabilities",
            lambda *_args, **_kwargs: [],
            raising=False,
        )

        form = window._build_analysis_specs_dialog(
            diagnostic_metrics=["sens", "spec"],
            confidence_level=window.model.get_confidence_level(),
        )
        form.show()
        app.processEvents()

        label = "Fixed-effect inverse-variance"
        label_index = form.method_cbo_box.findText(label)
        assert label_index >= 0
        adaptive_controls.configure_choice_control(
            form.method_cbo_box, visible_characters=28
        )
        app.processEvents()
        form.method_cbo_box.showPopup()
        settle = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(20, settle.quit)
        settle.exec()

        popup = form.method_cbo_box.view().window()
        available = adaptive_controls.available_geometry_for_choice_control(
            form.method_cbo_box
        )
        assert available.contains(popup.frameGeometry())
        if (
            form.method_cbo_box.view().sizeHintForColumn(0)
            > form.method_cbo_box.view().viewport().width()
        ):
            assert form.method_cbo_box.view().horizontalScrollBar().maximum() > 0
        assert (
            form.method_cbo_box.itemData(
                label_index, QtCore.Qt.ItemDataRole.ToolTipRole
            )
            == label
        )
        assert form.method_cbo_box.toolTip() == form.method_cbo_box.currentText()
        form.method_cbo_box.hidePopup()
        assert form.method_cbo_box.maximumWidth() == QtWidgets.QWIDGETSIZE_MAX
        assert (
            adaptive_window.adaptive_window_state(form).policy.archetype
            is adaptive_window.WindowArchetype.TRANSACTIONAL
        )
    finally:
        for name, value in saved.items():
            setattr(backend, name, value)
        _close_without_prompt(app, window)


def _close_without_prompt(app, window):
    window.workspace.mark_saved()
    window.close()
    app.processEvents()
    os.chdir(REPO_ROOT)
