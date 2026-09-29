import os
from pathlib import Path
from test_types import key_click, key_clicks, required

import pytest
from PyQt6 import QtCore, QtGui, QtSvg, QtTest, QtWidgets
from rc_metastudio.analysis_results import PlotCapability, parse_analysis_result
from rc_metastudio.analysis_adapter import make_analysis_request
from rc_metastudio.analysis_snapshot import BinaryInputSnapshot, BinaryStudyInput
from rc_metastudio.cumulative_analysis import (
    CumulativeOrderSpec,
    freeze_cumulative_input,
    run_cumulative_analysis,
)
from rc_metastudio.leave_one_out import (
    LeaveOneOutEstimate,
    LeaveOneOutNumber,
    run_leave_one_out,
)
from rc_metastudio.plot_text import normalize_plot_text_value

pytestmark = pytest.mark.qsettings


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("RCMS_QT6_BUILD_ROOT", str(ROOT / "build" / "qt6-verification"))
from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()
from rc_metastudio import plot_editor_dialog, plot_service, results_window


def _empty_results(summary="Summary text"):
    return _analysis_result({"texts": {"Summary": summary}})


def _sequential_snapshot():
    return BinaryInputSnapshot(
        1, "Mortality", "12 months", ("Treatment", "Control"), "OR", False,
        (
            BinaryStudyInput(1, "First", 2020, 0.1, 0.2, None, None, None, None),
            BinaryStudyInput(2, "Second", 2021, 0.3, 0.2, None, None, None, None),
        ),
        (),
    )


def test_sequential_native_tables_keep_baseline_and_final_step_copyable(qapp):
    snapshot = _sequential_snapshot()
    cumulative = freeze_cumulative_input(
        snapshot, CumulativeOrderSpec("project_order", "descending")
    )
    request = make_analysis_request(
        data_type="binary", workflow="cumulative", method="binary.random",
        metric="OR", parameters={},
    )
    cumulative_result = run_cumulative_analysis(
        cumulative, request,
        lambda prefix, _request: {
            "res": {
                "b": 0.2, "ci.lb": 0.1, "ci.ub": 0.3,
                "se": 0.05, "pval": 0.01, "k": len(prefix.studies),
            }
        },
    )
    window = results_window.ResultsWindow(
        _analysis_result({"cumulative_numerics": cumulative_result.to_mapping()}),
        context={
            "outcome": "Mortality",
            "time_point": "12 months",
            "direction": "Treatment versus Control",
            "measure": "OR",
            "workflow": "cumulative",
            "method": "binary.random",
            "effective_settings": {"CI": "95%"},
        },
    )
    try:
        table = window.binary_study_table
        assert table.rowCount() == 2
        assert table.item(0, 1).text() == "Second"
        assert "final all-included" in table.item(1, 1).text()
        for detail in (
            "Cumulative result: complete",
            "Outcome: Mortality",
            "Measure: OR",
            "Workflow: cumulative",
            "Method: binary.random",
            "Effective settings: CI: 95%",
            "Order: project order, descending",
        ):
            assert detail in table.accessibleDescription()
        heading = next(
            label
            for label in window.binary_study_table.parentWidget().findChildren(
                QtWidgets.QLabel
            )
            if label.accessibleName() == "Cumulative analysis details"
        )
        assert "Method: binary.random" in heading.accessibleDescription()
        window._copy_binary_study_table()
        clipboard = QtWidgets.QApplication.clipboard()
        assert clipboard is not None
        assert "Study added" in clipboard.text()
        assert "Second" in clipboard.text()
    finally:
        window.close()

    def fit(subset):
        value = 0.2 if len(subset.studies) == 2 else 0.1
        return LeaveOneOutEstimate(
            "RCMetaR OR analysis scale",
            LeaveOneOutNumber.available(value),
            LeaveOneOutNumber.available(value - 0.1),
            LeaveOneOutNumber.available(value + 0.1),
        )

    report = run_leave_one_out(
        snapshot, fit, data_type="binary", method="binary.random",
        effect_scale="RCMetaR OR analysis scale",
    )
    window = results_window.ResultsWindow(
        _analysis_result({"leave_one_out_numerics": report.to_mapping()})
    )
    try:
        table = window.binary_study_table
        assert table.rowCount() == 3
        assert table.item(0, 0).text() == "All included studies"
        assert table.item(1, 0).text() == "Omitting First"
        assert "Measure: OR" in table.accessibleDescription()
        assert "Method: binary.random" in table.accessibleDescription()
        assert "RCMetaR OR analysis scale" in table.accessibleDescription()
        window._copy_binary_study_table()
        assert "Change from baseline" in clipboard.text()
        assert "Omitting Second" in clipboard.text()
    finally:
        window.close()


def _analysis_result(payload):
    """Build the complete result contract used by ResultsWindow fixtures."""
    payload = dict(payload)
    payload.setdefault("version", 1)
    text_titles = list(payload.get("texts", {}))
    image_titles = list(payload.get("images", {}))
    payload.setdefault(
        "sections",
        [
            {
                "id": f"fixture.text.{index}",
                "kind": "text",
                "order": index,
                "title": title,
                "source_key": title,
            }
            for index, title in enumerate(text_titles)
        ]
        + [
            {
                "id": f"fixture.image.{index}",
                "kind": "image",
                "order": len(text_titles) + index,
                "title": title,
                "source_key": title,
            }
            for index, title in enumerate(image_titles)
        ],
    )
    return parse_analysis_result(payload)


def test_results_navigation_uses_keyboard_selection_and_enters_section_actions(
    qapp, tmp_path, monkeypatch
):
    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(
        _analysis_result(
            {"binary_numerics": _binary_numerics(), "texts": {"Summary": "Result text."}}
        )
    )
    centers = []
    monkeypatch.setattr(
        window.graphics_view, "centerOn", lambda position: centers.append(position)
    )
    try:
        window.showNormal()
        window.resize(620, 430)
        window.show()
        qapp.processEvents()

        results_item = required(window.nav_tree.topLevelItem(0), "binary results item")
        summary_item = required(window.nav_tree.topLevelItem(1), "summary item")
        assert results_item.text(0) == "Binary Results"
        assert "binary results" in results_item.data(
            0, QtCore.Qt.ItemDataRole.AccessibleDescriptionRole
        ).lower()

        window.nav_tree.setCurrentItem(results_item)
        window.nav_tree.setFocus()
        key_click(window.nav_tree, QtCore.Qt.Key.Key_Return)
        qapp.processEvents()
        copy_button = next(
            button
            for button in window.binary_results_panel.findChildren(
                QtWidgets.QPushButton
            )
            if button.accessibleName() == "Copy binary study table"
        )
        assert copy_button.hasFocus(), [
            child.accessibleName()
            for child in window.binary_results_panel.findChildren(QtWidgets.QWidget)
            if child.hasFocus()
        ]

        centers.clear()
        window.nav_tree.setFocus()
        key_click(window.nav_tree, QtCore.Qt.Key.Key_Down)
        qapp.processEvents()

        assert window.nav_tree.currentItem() is summary_item
        assert window.nav_tree.hasFocus()
        assert centers == [window.items_to_coords[id(summary_item)]]
        assert summary_item.data(
            0, QtCore.Qt.ItemDataRole.AccessibleDescriptionRole
        ) == "Result text."
    finally:
        _dispose(window, qapp)


def test_narrow_results_table_remains_keyboard_scrollable(qapp, tmp_path):
    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(
        _analysis_result({"binary_numerics": _binary_numerics()})
    )
    try:
        window.showNormal()
        window.resize(460, 360)
        window.show()
        qapp.processEvents()

        table = window.binary_study_table
        horizontal = table.horizontalScrollBar()
        assert table.isVisible()
        assert horizontal.isVisible()
        assert horizontal.maximum() > 0

        table.setCurrentCell(0, 0)
        table.setFocus()
        for _ in range(table.columnCount() - 1):
            QtTest.QTest.keyClick(table, QtCore.Qt.Key.Key_Right)
        qapp.processEvents()

        assert table.currentColumn() == table.columnCount() - 1
        assert horizontal.value() > 0
        assert table.accessibleName() == "Binary study results"
    finally:
        _dispose(window, qapp)


def _plot_capability(
    plot_kind="forest", editable=True, styleable=True, regenerator="forest"
):
    return {
        "plot_kind": plot_kind,
        "editable": editable,
        "styleable": styleable,
        "regenerator": regenerator,
        "composition": "single",
    }


def _plot_capability_model(
    plot_kind="forest", editable=True, styleable=True, regenerator="forest"
):
    return PlotCapability(
        plot_kind=plot_kind,
        editable=editable,
        styleable=styleable,
        regenerator=regenerator,
        composition="single",
    )


def _binary_number(value, status="available", reason=None):
    return {"status": status, "value": value, "reason": reason}


def _binary_estimate(estimate, lower, upper):
    return {
        "estimate": _binary_number(estimate),
        "lower": _binary_number(lower),
        "upper": _binary_number(upper),
    }


def _binary_numerics():
    return {
        "version": 1,
        "metric": "OR",
        "calculation_scale": "log",
        "display_scale": "ratio",
        "weight_scale": "percent",
        "calculation_null_value": 0,
        "display_null_value": 1,
        "pooled": {
            "calculation": _binary_estimate(0.75, 0.05, 1.4),
            "display": _binary_estimate(
                2.123456789, 1.051271096, 4.055199967
            ),
            "study_count": _binary_number(2),
            "p_value": _binary_number(0.04),
        },
        "studies": [
            {
                "order": 0,
                "label": "Study high",
                "treatment_events": _binary_number(11),
                "treatment_total": _binary_number(20),
                "control_events": _binary_number(3),
                "control_total": _binary_number(20),
                "weight": _binary_number(60.0),
                "p_value": _binary_number(
                    None, "not_available", "The model does not return per-study p-values."
                ),
                "calculation": _binary_estimate(2.314, 1.2, 3.8),
                "display": _binary_estimate(
                    10.123456789, 3.320116923, 44.70118449
                ),
            },
            {
                "order": 1,
                "label": "Study low",
                "treatment_events": _binary_number(4),
                "treatment_total": _binary_number(20),
                "control_events": _binary_number(8),
                "control_total": _binary_number(20),
                "weight": _binary_number(40.0),
                "p_value": _binary_number(0.2),
                "calculation": _binary_estimate(0.753, 0.3, 1.4),
                "display": _binary_estimate(
                    2.123456789, 1.349858808, 4.055199967
                ),
            },
            {
                "order": 2,
                "label": "Study omitted",
                "treatment_events": _binary_number(0),
                "treatment_total": _binary_number(20),
                "control_events": _binary_number(0),
                "control_total": _binary_number(20),
                "weight": _binary_number(
                    None, "not_estimable", "The model omitted this zero-event study."
                ),
                "p_value": _binary_number(
                    None, "not_available", "The model does not return per-study p-values."
                ),
                "calculation": {
                    "estimate": _binary_number(
                        None, "not_estimable", "The model omitted this zero-event study."
                    ),
                    "lower": _binary_number(
                        None, "not_estimable", "The model omitted this zero-event study."
                    ),
                    "upper": _binary_number(
                        None, "not_estimable", "The model omitted this zero-event study."
                    ),
                },
                "display": {
                    "estimate": _binary_number(
                        None, "not_estimable", "The model omitted this zero-event study."
                    ),
                    "lower": _binary_number(
                        None, "not_estimable", "The model omitted this zero-event study."
                    ),
                    "upper": _binary_number(
                        None, "not_estimable", "The model omitted this zero-event study."
                    ),
                },
            },
        ],
    }


def _use_isolated_settings(tmp_path):
    QtCore.QSettings.setPath(
        QtCore.QSettings.Format.IniFormat,
        QtCore.QSettings.Scope.UserScope,
        str(tmp_path),
    )
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
    store = QtCore.QSettings()
    store.clear()
    store.sync()


def _dispose(widget, qapp):
    widget.close()
    widget.deleteLater()
    qapp.processEvents()


class _IdlePlotWorker(QtCore.QObject):
    plotProgress = QtCore.pyqtSignal(str, str, object, str)
    plotCompleted = QtCore.pyqtSignal(str, str, object, object)
    plotFailed = QtCore.pyqtSignal(str, str, object, object)

    @property
    def is_busy(self):
        return False


def test_typed_binary_results_show_context_and_keep_numeric_copy_and_export(
    qapp, tmp_path, monkeypatch
):
    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {},
                "binary_numerics": _binary_numerics(),
            }
        ),
        context={
            "outcome": "Relapse",
            "time_point": "12 months",
            "direction": "Treatment versus control",
            "measure": "Odds Ratio",
            "effective_settings": {"method": "Random effects", "CI": "95%"},
        },
        edit_copy_spec={"copied": True},
    )
    export_path = tmp_path / "binary-results.csv"
    monkeypatch.setattr(
        results_window.QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(export_path), "CSV files (*.csv)"),
    )
    try:
        assert window.results.binary_numerics is not None
        assert window.binary_study_table.rowCount() == 3
        panel = window.binary_results_panel
        assert panel.findChild(QtWidgets.QLabel, "binary_result_metric").text() == (
            "Measure: Odds Ratio (ratio scale, null = 1). "
            "Calculations: log scale, null = 0."
        )
        context = required(
            panel.findChild(QtWidgets.QLabel, "binary_result_context"),
            "binary analysis context",
        ).text()
        assert "Outcome: Relapse" in context
        assert "Time point: 12 months" in context
        assert "Direction: Treatment versus control" in context
        assert "Effective settings: CI: 95%; method: Random effects" in context
        assert "Pooled estimate: 2.123" in panel.findChild(
            QtWidgets.QLabel, "binary_pooled_estimate"
        ).text()
        assert "Included studies: 2" in panel.findChild(
            QtWidgets.QLabel, "binary_study_count"
        ).text()

        table = window.binary_study_table
        assert table.horizontalHeaderItem(5).text() == (
            "Odds Ratio estimate (ratio scale; null = 1)"
        )
        assert table.item(0, 5).text() == "10.12"
        assert table.item(0, 5).data(QtCore.Qt.ItemDataRole.UserRole) == pytest.approx(
            10.123456789
        )
        assert table.item(0, 9).text() == "Not available"
        assert "per-study p-values" in table.item(0, 9).toolTip()

        table.sortItems(5, QtCore.Qt.SortOrder.AscendingOrder)
        assert table.item(0, 0).text() == "Study low"
        assert table.item(1, 0).text() == "Study high"
        assert table.item(2, 0).text() == "Study omitted"
        assert table.item(2, 5).text() == "Not estimable"
        assert "omitted this zero-event study" in table.item(2, 5).toolTip()

        copy_button = next(
            button
            for button in panel.findChildren(QtWidgets.QPushButton)
            if button.text() == "Copy table"
        )
        copy_button.click()
        clipboard = required(QtWidgets.QApplication.clipboard(), "clipboard")
        copied = clipboard.text()
        assert "2.123456789" in copied
        assert "10.123456789" in copied
        assert "Not available: The model does not return per-study p-values." in copied
        assert "Not estimable: The model omitted this zero-event study." in copied

        export_button = next(
            button
            for button in panel.findChildren(QtWidgets.QPushButton)
            if button.text() == "Export CSV"
        )
        export_button.click()
        exported = export_path.read_text(encoding="utf-8")
        assert "2.123456789" in exported
        assert "10.123456789" in exported

        received_specs = []
        window.edit_copy_requested.connect(received_specs.append)
        edit_copy_button = next(
            button
            for button in panel.findChildren(QtWidgets.QPushButton)
            if button.text() == "Edit a copy"
        )
        edit_copy_button.click()
        assert received_specs == [{"copied": True}]
    finally:
        _dispose(window, qapp)


def test_result_table_copy_uses_selected_rows_and_cells_expose_missing_reasons(
    qapp, tmp_path, monkeypatch
):
    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(
        _analysis_result(
            {"texts": {}, "images": {}, "binary_numerics": _binary_numerics()}
        )
    )
    export_path = tmp_path / "binary-results.csv"
    monkeypatch.setattr(
        results_window.QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(export_path), "CSV files (*.csv)"),
    )
    try:
        table = window.binary_study_table
        reason = table.item(0, 9).data(
            QtCore.Qt.ItemDataRole.AccessibleDescriptionRole
        )
        assert reason == "The model does not return per-study p-values."
        copy_button = next(
            button
            for button in window.binary_results_panel.findChildren(
                QtWidgets.QPushButton
            )
            if button.accessibleName() == "Copy binary study table"
        )
        assert "Copy selected rows" in copy_button.toolTip()

        table.selectRow(1)
        window._copy_binary_study_table()
        clipboard = required(QtWidgets.QApplication.clipboard(), "clipboard")
        copied_rows = clipboard.text()
        assert "Study low" in copied_rows
        assert "Study high" not in copied_rows
        assert "Study omitted" not in copied_rows
        assert "2.123456789" in copied_rows

        window._export_binary_study_table()
        exported = export_path.read_text(encoding="utf-8")
        assert "Study high" in exported
        assert "Study low" in exported
        assert "Study omitted" in exported
        assert "10.123456789" in exported
    finally:
        _dispose(window, qapp)


def test_binary_results_omit_edit_copy_without_an_editable_copy_spec(qapp, tmp_path):
    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {},
                "binary_numerics": _binary_numerics(),
            }
        ),
        worker_client=_IdlePlotWorker(),
    )
    try:
        assert window.binary_results_panel.findChild(
            QtWidgets.QLabel, "binary_result_context"
        ) is None
        assert all(
            button.text() != "Edit a copy"
            for button in window.binary_results_panel.findChildren(
                QtWidgets.QPushButton
            )
        )
    finally:
        _dispose(window, qapp)


@pytest.mark.parametrize(
    "placeholder",
    ["", "[default]", "[Default]", "<default>", "(default)", "default"],
)
def test_untouched_plot_default_placeholder_is_unset(placeholder):
    assert normalize_plot_text_value(placeholder) is None


def test_edited_plot_default_placeholder_remains_user_text():
    assert normalize_plot_text_value("[default]", was_edited=True) == "[default]"


def test_qtsvg_renders_materialized_default_black_plot_stroke():
    svg = b"""<svg xmlns='http://www.w3.org/2000/svg' width='100' height='40' viewBox='0 0 100 40'>
    <g class='svglite'><line x1='10' y1='20' x2='90' y2='20' stroke='#000000' fill='none'
    stroke-linecap='round' stroke-linejoin='round' stroke-miterlimit='10.00'/></g></svg>"""
    renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(svg))
    assert renderer.isValid()

    image = QtGui.QImage(100, 40, QtGui.QImage.Format.Format_ARGB32)
    image.fill(QtCore.Qt.GlobalColor.white)
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    painter.end()

    assert (
        sum(
            image.pixelColor(x, 20) != QtGui.QColor(QtCore.Qt.GlobalColor.white)
            for x in range(100)
        )
        >= 75
    )


def test_plot_graphics_items_paint_an_opaque_white_canvas(qapp, tmp_path):
    from rc_metastudio import results_window

    svg_path = tmp_path / "svglite-shaped-transparent.svg"
    svg_path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="1127.12pt" '
        'height="360.00pt" viewBox="0 0 1127.12 360.00">'
        '<g class="svglite"><line x1="20" y1="20" x2="1100" y2="20" '
        'stroke="#000000"/></g></svg>',
        encoding="utf-8",
    )

    svg_item = results_window._svg_item_class()(str(svg_path))
    raster_source = QtGui.QPixmap(100, 40)
    raster_source.fill(QtCore.Qt.GlobalColor.transparent)
    raster_item = results_window.ResponsivePixmapItem(raster_source)
    raster_item.setPixmap(raster_source)

    for item in (svg_item, raster_item):
        bounds = item.boundingRect()
        rendered = QtGui.QImage(
            max(1, int(bounds.width())),
            max(1, int(bounds.height())),
            QtGui.QImage.Format.Format_ARGB32,
        )
        rendered.fill(QtGui.QColor("#2b2b2b"))
        painter = QtGui.QPainter(rendered)
        item.paint(painter, QtWidgets.QStyleOptionGraphicsItem())
        painter.end()

        assert rendered.pixelColor(rendered.width() - 1, rendered.height() - 1) == (
            QtGui.QColor(QtCore.Qt.GlobalColor.white)
        )


@pytest.mark.parametrize("plot_format", ("svg", "png"))
def test_results_plot_preview_is_opaque_white_on_dark_theme(
    qapp, tmp_path, plot_format
):
    _use_isolated_settings(tmp_path)
    plot_path = tmp_path / ("transparent-plot." + plot_format)
    if plot_format == "svg":
        plot_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="40" '
            'viewBox="0 0 100 40"><line x1="10" y1="20" x2="90" y2="20" '
            'stroke="black"/></svg>',
            encoding="utf-8",
        )
    else:
        source = QtGui.QImage(100, 40, QtGui.QImage.Format.Format_ARGB32)
        source.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(source)
        painter.setPen(QtGui.QColor(QtCore.Qt.GlobalColor.black))
        painter.drawLine(10, 20, 90, 20)
        painter.end()
        assert source.save(str(plot_path), "PNG")

    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {"Plot": str(plot_path)},
                "plot_capabilities": {
                    "Plot": _plot_capability(
                        plot_kind="other",
                        editable=False,
                        styleable=False,
                        regenerator="none",
                    )
                },
            }
        )
    )
    try:
        plot_item = (
            window._svg_plot_items[0]
            if plot_format == "svg"
            else window._raster_plot_items[0]
        )
        preview = QtGui.QImage(100, 40, QtGui.QImage.Format.Format_ARGB32)
        preview.fill(QtGui.QColor("#2b2b2b"))
        painter = QtGui.QPainter(preview)
        if plot_format == "svg":
            plot_item.renderer().render(painter, QtCore.QRectF(0, 0, 100, 40))
        else:
            painter.drawPixmap(QtCore.QRect(0, 0, 100, 40), plot_item.pixmap())
        painter.end()

        white = QtGui.QColor(QtCore.Qt.GlobalColor.white)
        white_pixels = sum(
            preview.pixelColor(x, y) == white
            for y in range(preview.height())
            for x in range(preview.width())
        )
        assert white_pixels >= 3500, white_pixels
        assert all(
            preview.pixelColor(x, y) == white
            for x, y in ((0, 0), (99, 0), (0, 39), (99, 39))
        )
    finally:
        _dispose(window, qapp)


def test_results_workspace_defaults_maximized_and_restores_screen_safe_state(
    qapp, tmp_path
):
    from rc_metastudio import adaptive_window
    from rc_metastudio import results_window
    from rc_metastudio import settings

    _use_isolated_settings(tmp_path)
    fresh = results_window.ResultsWindow(_empty_results())
    try:
        state = adaptive_window.adaptive_window_state(fresh)
        assert state.policy.archetype is adaptive_window.WindowArchetype.WORKSPACE
        assert state.role is adaptive_window.WindowRole.RESULTS
        assert fresh.isMaximized()

        fresh.showNormal()
        fresh.setGeometry(90, 70, 620, 410)
        fresh.results_nav_splitter.setSizes([180, 540])
    finally:
        _dispose(fresh, qapp)

    restored = results_window.ResultsWindow(_empty_results())
    try:
        assert not restored.isMaximized()
        restored.show()
        qapp.processEvents()
        placement = settings.load_results_window_state(
            available_geometries=[QtCore.QRect(0, 0, 800, 600)]
        )
        assert QtCore.QRect(0, 0, 800, 600).contains(placement["frame_geometry"])
        sizes = restored.results_nav_splitter.sizes()
        total_size = sum(sizes)
        assert total_size > 0
        if total_size == 0:
            pytest.fail("results splitter has no allocated space")
        assert sizes[0] / total_size == pytest.approx(0.25, abs=0.03)
    finally:
        _dispose(restored, qapp)


def test_results_splitter_default_gives_analysis_content_most_space(qapp, tmp_path):
    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(_empty_results())
    try:
        window.show()
        qapp.processEvents()

        sizes = window.results_nav_splitter.sizes()
        total_size = sum(sizes)
        if total_size == 0:
            pytest.fail("results splitter has no allocated space")
        assert sizes[0] / total_size == pytest.approx(0.25, abs=0.03)
        assert sizes[1] / total_size >= 0.70
    finally:
        _dispose(window, qapp)


def test_results_splitter_restores_a_valid_wide_navigation_preference(
    qapp, tmp_path
):
    from rc_metastudio import settings

    _use_isolated_settings(tmp_path)
    store = QtCore.QSettings()
    store.setValue("workspace_layout/schema_version", 2)
    store.setValue(
        "workspace_layout/results/splitter_proportions", '[0.65,0.35]'
    )
    store.sync()

    window = results_window.ResultsWindow(_empty_results())
    try:
        window.show()
        qapp.processEvents()

        sizes = window.results_nav_splitter.sizes()
        total_size = sum(sizes)
        if total_size == 0:
            pytest.fail("results splitter has no allocated space")
        assert sizes[0] / total_size == pytest.approx(0.65, abs=0.03)
        assert settings.load_results_window_state().splitter_proportions == pytest.approx(
            (0.65, 0.35)
        )
    finally:
        _dispose(window, qapp)


def test_results_splitter_proportions_persist_independently_of_outer_geometry(
    qapp, tmp_path
):
    from rc_metastudio import results_window
    from rc_metastudio import settings

    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(_empty_results())
    try:
        window.showNormal()
        window.resize(900, 500)
        window.results_nav_splitter.setSizes([315, 585])
        settings.save_results_window_state(window)

        stored = settings.load_results_window_state(
            available_geometries=[QtCore.QRect(0, 0, 640, 480)]
        )
        assert stored["splitter_proportions"] == pytest.approx([0.35, 0.65], abs=0.002)
        assert stored["frame_geometry"].width() <= 640
        assert stored["frame_geometry"].height() <= 480
    finally:
        _dispose(window, qapp)


def test_results_long_text_reflows_inside_constrained_viewport_without_window_growth(
    qapp, tmp_path
):
    _use_isolated_settings(tmp_path)
    long_summary = " ".join(["Long analysis summary"] * 120)
    window = results_window.ResultsWindow(_empty_results(long_summary))
    try:
        window.showNormal()
        window.resize(560, 420)
        window.show()
        qapp.processEvents()
        before = QtCore.QRect(window.geometry())

        window.results_nav_splitter.setSizes([280, 280])
        for _ in range(8):
            window._schedule_viewport_refit()
        qapp.processEvents()

        text_item = next(
            item
            for item in window.scene.items()
            if isinstance(item, results_window.SelectableResultsTextItem)
        )
        assert window.geometry() == before
        assert text_item.textWidth() > 0
        viewport = required(window.graphics_view.viewport(), "graphics viewport")
        assert text_item.textWidth() <= viewport.width()
        assert window.scene.width() <= viewport.width() + 2
    finally:
        _dispose(window, qapp)


def test_results_resize_burst_runs_one_expensive_reflow_per_event_loop_turn(
    qapp, monkeypatch, tmp_path
):
    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(_empty_results())
    calls = []
    monkeypatch.setattr(window, "_refit_viewport_items", lambda: calls.append("reflow"))
    try:
        window.show()
        qapp.processEvents()
        calls.clear()
        for _ in range(20):
            window.resize(window.width() + 1, window.height())
            window._schedule_viewport_refit()
        assert calls == []
        qapp.processEvents()
        assert calls == ["reflow"]
    finally:
        _dispose(window, qapp)


def test_results_first_show_runs_one_scheduled_expensive_reflow(
    qapp, monkeypatch, tmp_path
):
    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(_empty_results())
    calls = []
    monkeypatch.setattr(window, "_refit_viewport_items", lambda: calls.append("reflow"))
    try:
        window.show()
        assert calls == []
        qapp.processEvents()
        assert calls == ["reflow"]
    finally:
        _dispose(window, qapp)


def test_results_refit_does_not_dispatch_unrelated_layout_requests(
    qapp, monkeypatch, tmp_path
):
    from rc_metastudio import results_window

    class LayoutRequestProbe(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            self.layout_requests = 0

        # The Qt runtime dispatches this override correctly; the bundled
        # stubs expose an incompatible descriptor signature.
        def event(self, event: QtCore.QEvent) -> bool:  # ty: ignore[invalid-method-override]
            if event.type() == QtCore.QEvent.Type.LayoutRequest:
                self.layout_requests += 1
            return super().event(event)

    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(_empty_results())
    probe = LayoutRequestProbe()
    probe_layout = QtWidgets.QVBoxLayout(probe)
    calls = []
    monkeypatch.setattr(window, "_refit_viewport_items", lambda: calls.append("reflow"))
    try:
        window.show()
        probe.show()
        qapp.processEvents()
        calls.clear()
        probe.layout_requests = 0

        probe_layout.addWidget(QtWidgets.QLabel("pending unrelated layout", probe))
        window._viewport_refit_pending = True
        window._run_scheduled_viewport_refit()

        assert calls == ["reflow"]
        assert probe.layout_requests == 0
        qapp.processEvents()
        assert probe.layout_requests == 1
    finally:
        probe.close()
        probe.deleteLater()
        _dispose(window, qapp)


def test_results_regeneration_burst_runs_one_scheduled_expensive_reflow(
    qapp, monkeypatch, tmp_path
):
    _use_isolated_settings(tmp_path)
    plot_path = tmp_path / "plot.png"
    image = results_window.QImage(600, 300, results_window.QImage.Format.Format_RGB32)
    image.fill(results_window.Qt.GlobalColor.white)
    assert image.save(str(plot_path), "PNG")
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {"Plot": str(plot_path)},
                "plot_capabilities": {
                    "Plot": {
                        "plot_kind": "other",
                        "editable": False,
                        "styleable": False,
                        "regenerator": "none",
                        "composition": "single",
                    }
                },
            }
        )
    )
    try:
        window.show()
        qapp.processEvents()
        item = next(
            item
            for item in window._raster_plot_items
            if isinstance(item, results_window.ResponsivePixmapItem)
        )
        artifact = window.create_plot_artifact("Plot", str(plot_path))
        calls = []
        monkeypatch.setattr(
            window, "_refit_viewport_items", lambda: calls.append("reflow")
        )

        window._refresh_plot_item(item, artifact, str(plot_path))
        window._refresh_plot_item(item, artifact, str(plot_path))
        assert calls == []
        qapp.processEvents()
        assert calls == ["reflow"]
    finally:
        _dispose(window, qapp)


def test_dpr_raster_uses_device_independent_dimensions_for_viewport_fit(qapp, tmp_path):
    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(_empty_results())
    try:
        window.showNormal()
        window.resize(560, 420)
        window.show()
        qapp.processEvents()

        source = results_window.QPixmap(1200, 600)
        source.fill(results_window.Qt.GlobalColor.white)
        source.setDevicePixelRatio(2.0)
        item = results_window.ResponsivePixmapItem(source)
        item.setPixmap(source)
        window.scene.addItem(item)
        window._raster_plot_items.append(item)

        window._refit_raster_plot_items()

        intended_width = min(600.0, float(window._plot_viewport_width()))
        displayed = item.sceneBoundingRect()
        assert item.source_pixmap.width() == 1200
        assert item.source_pixmap.devicePixelRatioF() == pytest.approx(2.0)
        assert displayed.width() == pytest.approx(intended_width, abs=1.0)
        assert displayed.width() / displayed.height() == pytest.approx(2.0)
    finally:
        _dispose(window, qapp)


def test_plot_editor_is_screen_bounded_transactional_dialog_with_fixed_actions(
    qapp, tmp_path
):
    from rc_metastudio import adaptive_window

    _use_isolated_settings(tmp_path)
    dialog = plot_editor_dialog.EditPlotDialog({}, "forest.png")
    try:
        dialog.show()
        qapp.processEvents()
        state = adaptive_window.adaptive_window_state(dialog)
        assert state.policy.archetype is adaptive_window.WindowArchetype.TRANSACTIONAL
        assert state.role is adaptive_window.WindowRole.TRANSACTIONAL
        assert isinstance(dialog.content_scroll, QtWidgets.QScrollArea)
        assert dialog.content_scroll.widgetResizable()
        assert not dialog.content_scroll.isAncestorOf(dialog.buttonBox)
        available = required(dialog.screen(), "dialog screen").availableGeometry()
        assert dialog.frameGeometry().width() <= int(available.width() * 0.9) + 1
        assert dialog.frameGeometry().height() <= int(available.height() * 0.9) + 1
        assert dialog.buttonBox.isVisible()
        assert required(
            dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Apply),
            "apply button",
        ).isVisible()
        assert required(
            dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok),
            "ok button",
        ).isVisible()
    finally:
        _dispose(dialog, qapp)


def test_sroc_plot_editor_keeps_dynamic_controls_inside_scrollable_content(
    qapp, tmp_path
):
    _use_isolated_settings(tmp_path)
    dialog = plot_editor_dialog.EditPlotDialog({}, "sroc.svg", plot_type="sroc")
    try:
        high_font = QtGui.QFont(dialog.font())
        high_font.setPointSize(18)
        dialog.setFont(high_font)
        dialog.resize(600, 450)
        dialog.show()
        qapp.processEvents()
        sroc_options = dialog.findChild(QtWidgets.QWidget, "sroc_options")
        assert sroc_options is not None
        assert dialog.content_scroll.isAncestorOf(sroc_options)
        assert dialog.content_layout.indexOf(sroc_options) >= 0
        content_viewport = required(
            dialog.content_scroll.viewport(), "content viewport"
        )
        content_scrollbar = required(
            dialog.content_scroll.verticalScrollBar(), "content scrollbar"
        )
        assert content_viewport.height() > 0
        assert content_scrollbar.maximum() > 0
        assert dialog.content_scroll.isAncestorOf(dialog.buttonBox) is False
    finally:
        _dispose(dialog, qapp)


def test_reitsma_coefficient_editor_hides_inapplicable_forest_controls(qapp):
    from rc_metastudio import plot_editor_dialog

    dialog = plot_editor_dialog.EditPlotDialog(
        {
            "reitsma.coefficient.scale": "Sensitivity",
            "reitsma.moderator.coding": {"quality": {"reference": "A"}},
            "fp_xlabel": "Odds ratio",
            "fp_plot_lb": "0.5",
            "fp_plot_ub": "3",
            "fp_xticks": "0.5, 1, 2, 3",
        },
        "coefficients.svg",
    )
    try:
        assert not dialog.groupBox.isVisible()
        assert not dialog.default_panel.isVisible()
        params = dialog.plot_params()
        assert params["reitsma.coefficient.scale"] == "Sensitivity"
        assert params["reitsma.moderator.coding"]["quality"]["reference"] == "A"
        assert params["fp_xlabel"] == "Odds ratio"
    finally:
        dialog.close()
        qapp.processEvents()


@pytest.mark.parametrize(
    "plot_type, parameter_name",
    [("forest", "fp_xlabel"), ("regression", "bp_xlabel"), ("sroc", "fp_xlabel")],
)
def test_plot_editor_omits_unedited_default_axis_label_sentinel(
    qapp, tmp_path, plot_type, parameter_name
):
    _use_isolated_settings(tmp_path)
    dialog = plot_editor_dialog.EditPlotDialog(
        {parameter_name: "[default]"}, "plot.svg", plot_type=plot_type
    )
    try:
        assert dialog.x_lbl_le.text() == ""
        assert dialog.plot_params()[parameter_name] is None
        dialog.x_lbl_le.setFocus()
        key_clicks(dialog.x_lbl_le, "Specific axis label")
        assert dialog.plot_params()[parameter_name] == "Specific axis label"
    finally:
        _dispose(dialog, qapp)


def test_sroc_plot_editor_uses_acronym_safe_browse_title(qapp, tmp_path, monkeypatch):
    _use_isolated_settings(tmp_path)
    dialog = plot_editor_dialog.EditPlotDialog({}, "sroc.svg", plot_type="sroc")
    titles = []

    monkeypatch.setattr(
        plot_editor_dialog.QFileDialog,
        "getSaveFileName",
        lambda _parent, title, *_args: titles.append(title) or ("", ""),
    )
    try:
        dialog.save_btn.click()
        assert titles == ["Save SROC Plot Image"]
    finally:
        _dispose(dialog, qapp)


def test_results_window_presents_summary_references_and_vector_plot_artifacts(
    qapp, tmp_path
):
    _use_isolated_settings(tmp_path)
    svg_path = tmp_path / "forest.display.svg"
    svg_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="801.5" height="400.75" '
        'viewBox="0 0 801.5 400.75"><rect width="801.5" height="400.75" '
        'fill="white"/><text x="24" y="48">Forest Plot</text></svg>',
        encoding="utf-8",
    )
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {
                    "Summary": "Random-effects model\nEstimate  Lower bound  Upper bound",
                    "References": "A maintained analysis reference.",
                },
                "images": {"Forest Plot": str(svg_path)},
                "display_images": {"Forest Plot": str(svg_path)},
                "image_params_paths": {"Forest Plot": str(tmp_path / "forest")},
                "image_order": ["Forest Plot"],
                "plot_capabilities": {"Forest Plot": _plot_capability()},
            }
        )
    )
    try:
        window.show()
        qapp.processEvents()
        nav_titles = [
            required(window.nav_tree.topLevelItem(index), "navigation item").text(0)
            for index in range(window.nav_tree.topLevelItemCount())
        ]
        assert nav_titles == ["Summary", "References", "Forest Plot"]
        svg_items = [
            item
            for item in window.scene.items()
            if isinstance(item, results_window._svg_item_class())
        ]
        assert len(svg_items) == 1
        assert svg_items[0].renderer().isValid()
        assert svg_items[0].sceneBoundingRect().width() > 0.0
        assert all(
            isinstance(position, QtCore.QPointF)
            for position in window.items_to_coords.values()
        )
        assert window.graphics_view.scene() is window.scene
    finally:
        _dispose(window, qapp)


def test_figure_toolbar_is_visible_named_and_keyboard_reachable(
    qapp, tmp_path, monkeypatch
):
    _use_isolated_settings(tmp_path)
    svg_path = tmp_path / "forest.svg"
    svg_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="160">'
        '<rect width="320" height="160" fill="white"/></svg>',
        encoding="utf-8",
    )
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {"Summary": "Numerical results remain available."},
                "images": {"Forest Plot": str(svg_path)},
                "image_params_paths": {"Forest Plot": str(tmp_path / "forest")},
                "plot_capabilities": {"Forest Plot": _plot_capability()},
            }
        ),
        worker_client=_IdlePlotWorker(),
    )
    action_errors = []
    monkeypatch.setattr(
        results_window.app_error_handler,
        "handle_exception",
        lambda _type, value, _traceback, **_kwargs: action_errors.append(value),
    )
    try:
        window.show()
        qapp.processEvents()
        toolbar = next(
            proxy
            for proxy in window.scene.items()
            if isinstance(proxy, QtWidgets.QGraphicsProxyWidget)
        )
        widget = required(toolbar.widget(), "figure toolbar")
        assert "isolated analysis worker" in widget.accessibleDescription()
        buttons = {
            button.text(): button
            for button in widget.findChildren(QtWidgets.QPushButton)
        }
        assert set(buttons) == {
            "Fit width",
            "Actual size",
            "Edit appearance",
            "Copy image",
        }
        export = required(
            widget.findChild(QtWidgets.QToolButton), "figure export button"
        )
        assert export.text() == "Export"
        assert [action.text() for action in export.menu().actions()] == [
            "Save PDF Image As",
            "Save PNG Image As",
            "Save TIFF Image As",
            "Save SVG Image As",
        ]
        zoom = required(
            widget.findChild(QtWidgets.QSlider), "figure zoom control"
        )
        assert zoom.accessibleName() == "Figure zoom"
        assert buttons["Fit width"].focusPolicy() != QtCore.Qt.FocusPolicy.NoFocus
        buttons["Fit width"].setFocus()
        QtTest.QTest.keyClick(buttons["Fit width"], QtCore.Qt.Key.Key_Tab)
        qapp.processEvents()
        assert buttons["Actual size"].hasFocus()
        plot_item = next(
            item
            for item in window._svg_plot_items
        )
        buttons["Actual size"].click()
        assert plot_item.scale() == pytest.approx(1.0)
        zoom.setValue(150)
        assert plot_item.scale() == pytest.approx(1.5)
        buttons["Fit width"].click()
        assert window._plot_zoom_modes[id(plot_item)] == "fit"
        buttons["Copy image"].click()
        assert action_errors == []
        assert not QtWidgets.QApplication.clipboard().image().isNull()
    finally:
        _dispose(window, qapp)


def test_updated_raster_path_refreshes_export_and_copy_actions(
    qapp, tmp_path, monkeypatch
):
    _use_isolated_settings(tmp_path)
    old_path = tmp_path / "old.png"
    new_path = tmp_path / "new.png"
    export_path = tmp_path / "copied.png"
    old_image = QtGui.QImage(4, 3, QtGui.QImage.Format.Format_ARGB32)
    old_image.fill(QtGui.QColor("red"))
    assert old_image.save(str(old_path), "PNG")

    blue_image = QtGui.QImage(4, 3, QtGui.QImage.Format.Format_ARGB32)
    blue_image.fill(QtGui.QColor("blue"))
    assert blue_image.save(str(new_path), "PNG")

    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {"Forest Plot": str(old_path)},
                "image_params_paths": {"Forest Plot": str(tmp_path / "forest")},
                "plot_capabilities": {"Forest Plot": _plot_capability()},
            }
        ),
        worker_client=_IdlePlotWorker(),
    )
    monkeypatch.setattr(
        results_window.QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(export_path), ""),
    )
    try:
        window.show()
        qapp.processEvents()
        toolbar = next(
            proxy
            for proxy in window.scene.items()
            if isinstance(proxy, QtWidgets.QGraphicsProxyWidget)
            and proxy.widget().accessibleName() == "Figure actions for Forest Plot"
        )
        widget = required(toolbar.widget(), "figure toolbar")
        edit_button = next(
            button
            for button in widget.findChildren(QtWidgets.QPushButton)
            if button.text() == "Edit appearance"
        )
        edited_artifacts = []

        def apply_edit(artifact, plot_item):
            edited_artifacts.append(artifact)
            window._refresh_plot_item(plot_item, artifact, str(new_path))

        window.edit_plot = apply_edit
        edit_button.click()
        artifact = edited_artifacts[0]
        plot_item = window._raster_plot_items[0]

        assert artifact.image_path == str(new_path)
        assert artifact.display_image_path == str(new_path)
        assert window.results.images["Forest Plot"] == str(new_path)
        assert next(
            section.value
            for section in window.results.sections
            if section.source_key == "Forest Plot"
        ) == str(new_path)
        assert plot_item.source_pixmap.toImage().pixelColor(0, 0) == QtGui.QColor(
            "blue"
        )

        copy_button = next(
            button
            for button in widget.findChildren(QtWidgets.QPushButton)
            if button.text() == "Copy image"
        )
        copy_button.click()
        copied = QtWidgets.QApplication.clipboard().image()
        assert copied.pixelColor(0, 0) == QtGui.QColor("blue")

        export_button = required(
            widget.findChild(QtWidgets.QToolButton), "figure export button"
        )
        png_action = next(
            action
            for action in export_button.menu().actions()
            if action.text() == "Save PNG Image As"
        )
        png_action.trigger()
        exported = QtGui.QImage(str(export_path))
        assert exported.pixelColor(0, 0) == QtGui.QColor("blue")
    finally:
        _dispose(window, qapp)


def test_unreadable_plot_without_worker_keeps_named_slot_and_hides_engine_actions(
    qapp, tmp_path
):
    _use_isolated_settings(tmp_path)
    missing_path = tmp_path / "cumulative.png"
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {"Summary": "The numerical result is intact."},
                "images": {"Cumulative Forest Plot": str(missing_path)},
                "image_params_paths": {
                    "Cumulative Forest Plot": str(tmp_path / "cumulative")
                },
                "plot_capabilities": {
                    "Cumulative Forest Plot": _plot_capability(
                        plot_kind="cumulative_forest"
                    )
                },
            }
        )
    )
    try:
        nav_item = window.nav_tree.topLevelItem(1)
        assert nav_item.text(0) == "Cumulative Forest Plot"
        assert "numerical results are still available" in nav_item.toolTip(0).lower()
        placeholder = next(
            item
            for item in window._layout_items
            if isinstance(item, results_window.SelectableResultsTextItem)
            and "Cumulative Forest Plot could not be displayed."
            in item.toPlainText()
        )
        assert "numerical results are still available" in placeholder.toPlainText().lower()
        toolbar = window._missing_plot_slots["Cumulative Forest Plot"][1]
        assert toolbar is None
        assert "figure unavailable" in nav_item.data(
            0, QtCore.Qt.ItemDataRole.AccessibleDescriptionRole
        ).lower()
    finally:
        _dispose(window, qapp)


def test_raster_plot_export_menu_does_not_claim_vector_formats(qapp, tmp_path):
    _use_isolated_settings(tmp_path)
    image = QtGui.QImage(80, 40, QtGui.QImage.Format.Format_ARGB32)
    image.fill(QtCore.Qt.GlobalColor.white)
    path = tmp_path / "raster.png"
    assert image.save(str(path), "PNG")
    artifact = results_window.PlotArtifact(
        "Raster Plot",
        str(path),
        _plot_capability_model(editable=False),
    )
    formats = [item.extension for item in artifact.export_formats()]
    assert "png" in formats
    assert set(formats) <= {"png", "tiff"}


@pytest.mark.parametrize("extension", ("png", "svg"))
def test_regeneratable_svg_uses_stored_export_without_r(
    qapp, tmp_path, monkeypatch, extension
):
    _use_isolated_settings(tmp_path)
    source_path = tmp_path / "forest.svg"
    source_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="40">'
        '<rect width="80" height="40" fill="black"/></svg>',
        encoding="utf-8",
    )
    output_path = tmp_path / ("stored." + extension)

    class NoEngineService:
        def export(self, **_kwargs):
            raise AssertionError("stored-artifact export must not require R")

    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {"Forest Plot": str(source_path)},
                "image_params_paths": {"Forest Plot": str(tmp_path / "forest")},
                "plot_capabilities": {"Forest Plot": _plot_capability()},
            }
        ),
        plot_service=NoEngineService(),
    )
    monkeypatch.setattr(
        results_window.QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(output_path), ""),
    )
    artifact = window.create_plot_artifact("Forest Plot", str(source_path))
    try:
        assert not artifact.requires_engine_for_export(extension)
        window.save_image_as(artifact, format=extension)
        assert output_path.is_file()
        if extension == "png":
            assert not QtGui.QImage(str(output_path)).isNull()
        else:
            assert b"<svg" in output_path.read_bytes()
    finally:
        _dispose(window, qapp)


def test_stored_svg_hides_raster_exports_when_qt_cannot_write_them(
    qapp, tmp_path, monkeypatch
):
    _use_isolated_settings(tmp_path)
    svg_path = tmp_path / "forest.svg"
    svg_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="40"/>',
        encoding="utf-8",
    )
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {"Forest Plot": str(svg_path)},
                "plot_capabilities": {
                    "Forest Plot": _plot_capability(
                        editable=False, styleable=False, regenerator="none"
                    )
                },
            }
        )
    )
    monkeypatch.setattr(results_window, "_qt_supports_image_format", lambda _fmt: False)
    try:
        artifact = window.create_plot_artifact("Forest Plot", str(svg_path))
        assert [item.extension for item in artifact.export_formats()] == ["svg"]
    finally:
        _dispose(window, qapp)


def test_unreadable_non_regenerable_figure_has_no_fake_actions(qapp, tmp_path):
    _use_isolated_settings(tmp_path)
    missing_path = tmp_path / "roc.svg"
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {"Summary": "Numerical results remain available."},
                "images": {"ROC Plot": str(missing_path)},
                "plot_capabilities": {
                    "ROC Plot": _plot_capability(
                        plot_kind="roc",
                        editable=False,
                        styleable=False,
                        regenerator="none",
                    )
                },
            }
        )
    )
    try:
        artifact = window.create_plot_artifact("ROC Plot", str(missing_path))
        assert not artifact.can_display()
        assert not artifact.can_regenerate()
        assert artifact.export_formats() == ()
        assert "ROC Plot" in [
            window.nav_tree.topLevelItem(index).text(0)
            for index in range(window.nav_tree.topLevelItemCount())
        ]
        assert window._missing_plot_slots["ROC Plot"][1] is None
    finally:
        _dispose(window, qapp)


def test_missing_figure_regeneration_without_worker_cannot_call_plot_service(
    qapp, tmp_path
):
    _use_isolated_settings(tmp_path)
    missing_path = tmp_path / "forest.png"
    previous_artifact = b"previous unreadable artifact"
    missing_path.write_bytes(previous_artifact)

    service_calls = []

    class NoFallbackService:
        def export(self, **_kwargs):
            service_calls.append("export")

    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {"Summary": "Numerical results remain available."},
                "images": {"Forest Plot": str(missing_path)},
                "image_params_paths": {"Forest Plot": str(tmp_path / "forest")},
                "plot_capabilities": {"Forest Plot": _plot_capability()},
            }
        ),
        plot_service=NoFallbackService(),
    )
    try:
        message, toolbar, nav_item = window._missing_plot_slots["Forest Plot"]
        artifact = window.create_plot_artifact("Forest Plot", str(missing_path))
        with pytest.raises(RuntimeError, match="isolated analysis worker"):
            window._regenerate_missing_plot(artifact, message, nav_item)
        assert service_calls == []
        assert missing_path.read_bytes() == previous_artifact
        assert window._missing_plot_slots["Forest Plot"] == (
            message,
            toolbar,
            nav_item,
        )
        assert "could not be displayed" in message.toPlainText()
    finally:
        _dispose(window, qapp)


def test_plot_parameter_load_without_worker_cannot_call_service(qapp, tmp_path):
    _use_isolated_settings(tmp_path)
    service_calls = []

    class NoFallbackService:
        def load_params(self, *_args, **_kwargs):
            service_calls.append("load")

    window = results_window.ResultsWindow(
        _empty_results(), plot_service=NoFallbackService()
    )
    artifact = results_window.PlotArtifact(
        "Forest Plot",
        str(tmp_path / "forest.svg"),
        _plot_capability_model(),
        params_path=str(tmp_path / "forest-params"),
    )
    try:
        with pytest.raises(RuntimeError, match="isolated analysis worker"):
            window._load_plot_params_then(artifact, lambda _params: None)
        assert service_calls == []
    finally:
        _dispose(window, qapp)


@pytest.mark.parametrize(
    ("title", "plot_kind", "regenerator"),
    (
        ("Forest Plot", "forest", "forest"),
        ("Cumulative Forest Plot", "cumulative_forest", "forest"),
        ("Leave-one-out Forest Plot", "leave_one_out_forest", "forest"),
        ("Subgroup Forest Plot", "subgroup_forest", "forest"),
        ("Diagnostic Forest Plot", "forest", "forest"),
        ("Meta-Regression Bubble Plot", "regression", "regression"),
        ("SROC Plot", "sroc", "sroc"),
    ),
)
def test_regenerable_plot_without_worker_hides_engine_actions(
    qapp, tmp_path, monkeypatch, title, plot_kind, regenerator
):
    from rc_metastudio import results_window

    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(_empty_results())
    captured = []

    class Event:
        def screenPos(self):
            return QtCore.QPoint(20, 30)

        def accept(self):
            pass

    monkeypatch.setattr(
        results_window.app_error_handler,
        "popup_context_menu",
        lambda menu, *_args, **_kwargs: captured.append(
            [action.text() for action in menu.actions()]
        ),
    )
    artifact = results_window.PlotArtifact(
        title,
        str(tmp_path / "plot.svg"),
        _plot_capability_model(plot_kind=plot_kind, regenerator=regenerator),
        params_path=str(tmp_path / "plot-params"),
    )
    try:
        window._make_context_menu(artifact, None)(Event())
        assert captured == [[]]
    finally:
        _dispose(window, qapp)


@pytest.mark.parametrize("extension", ["pdf", "png", "tiff", "svg"])
def test_results_window_rejects_engine_export_without_worker(
    qapp, tmp_path, monkeypatch, extension
):
    _use_isolated_settings(tmp_path)
    service_calls = []
    dialogs = []

    class NoFallbackService:
        def export(self, **_kwargs):
            service_calls.append("export")

    window = results_window.ResultsWindow(
        _empty_results(), plot_service=NoFallbackService()
    )
    artifact = results_window.PlotArtifact(
        "Forest Plot",
        str(tmp_path / "forest.svg"),
        _plot_capability_model(),
        params_path=str(tmp_path / "forest-params"),
    )
    monkeypatch.setattr(
        results_window.QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: dialogs.append("opened") or (str(tmp_path / "out"), ""),
    )
    try:
        with pytest.raises(RuntimeError, match="isolated analysis worker"):
            window.save_image_as(artifact, format=extension)
        assert dialogs == []
        assert service_calls == []
    finally:
        _dispose(window, qapp)


def test_sroc_export_without_worker_cannot_call_plot_service(qapp, tmp_path):
    _use_isolated_settings(tmp_path)
    service_calls = []

    class NoFallbackService:
        def export(self, **_kwargs):
            service_calls.append("export")

    window = results_window.ResultsWindow(
        _empty_results(), plot_service=NoFallbackService()
    )
    artifact = results_window.PlotArtifact(
        "SROC",
        str(tmp_path / "sroc.svg"),
        _plot_capability_model(plot_kind="sroc", regenerator="sroc"),
        params_path=str(tmp_path / "sroc-params"),
    )
    try:
        with pytest.raises(RuntimeError, match="isolated analysis worker"):
            window.save_image_as(artifact, format="svg")
        assert service_calls == []
    finally:
        _dispose(window, qapp)


def test_results_window_rejects_svgz_for_funnel_export_before_r(
    monkeypatch, qapp, tmp_path
):
    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(_empty_results())
    artifact = results_window.PlotArtifact(
        "Contour Funnel Plot",
        str(tmp_path / "funnel.svg"),
        _plot_capability_model(plot_kind="contour_funnel", regenerator="funnel"),
        params_path=str(tmp_path / "funnel-params"),
    )
    calls = []
    monkeypatch.setattr(
        plot_service.r_bridge,
        "load_vars_for_plot",
        lambda path: calls.append(("load", path)),
        raising=False,
    )
    monkeypatch.setattr(
        plot_service.r_bridge,
        "regenerate_small_study_effects_funnel",
        lambda path: calls.append(("generate", path)),
        raising=False,
    )
    monkeypatch.setattr(
        results_window.QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(tmp_path / "funnel.svgz"), ""),
    )
    try:
        with pytest.raises(RuntimeError, match="isolated analysis worker"):
            window.save_image_as(artifact, format="svg")
        assert calls == []
    finally:
        _dispose(window, qapp)


@pytest.mark.parametrize("scale", [1.0, 1.25, 1.5, 1.75])
def test_results_plot_geometry_preserves_fractional_logical_coordinates(
    qapp, tmp_path, scale
):
    from rc_metastudio import results_window

    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(_empty_results())
    try:
        window._viewport_width_override = 1003.0 * scale
        width, height = window._fit_size_to_viewport(801.5, 400.75, max_scale=4.0)
        assert isinstance(width, float)
        assert isinstance(height, float)
        assert width / height == pytest.approx(2.0)
        window.x_coord = 5.25
        window.y_coord = 9.75
        assert window.position() == QtCore.QPointF(5.25, 9.75)
    finally:
        _dispose(window, qapp)


def test_plot_editor_apply_signal_fires_exactly_once(qapp, tmp_path):

    _use_isolated_settings(tmp_path)
    dialog = plot_editor_dialog.EditPlotDialog({}, "forest.png")
    try:
        applied = QtTest.QSignalSpy(dialog.applied)
        button = dialog.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Apply
        )
        assert button is not None
        button.click()
        qapp.processEvents()
        assert len(applied) == 1
    finally:
        _dispose(dialog, qapp)


@pytest.mark.parametrize(
    ("plot_type", "field_name", "parameter_name"),
    (
        ("forest", "x_lbl_le", "fp_xlabel"),
        ("regression", "x_lbl_le", "bp_xlabel"),
    ),
)
@pytest.mark.parametrize("dismissal", ["cancel", "escape", "close"])
def test_generated_plot_editor_dismissal_never_commits_or_regenerates(
    qapp, tmp_path, plot_type, field_name, parameter_name, dismissal
):

    _use_isolated_settings(tmp_path)
    dialog = plot_editor_dialog.EditPlotDialog(
        {parameter_name: "Committed label"},
        "plot.svg",
        plot_type=plot_type,
    )
    committed = []
    regenerations = []
    dialog.applied.connect(lambda: committed.append(dialog.plot_params()))
    dialog.applied.connect(lambda: regenerations.append(plot_type))
    try:
        dialog.show()
        qapp.processEvents()
        getattr(dialog, field_name).setText("Uncommitted draft")
        if dismissal == "cancel":
            cancel = dialog.buttonBox.button(
                QtWidgets.QDialogButtonBox.StandardButton.Cancel
            )
            assert cancel is not None
            cancel.click()
        elif dismissal == "escape":
            key_click(dialog, QtCore.Qt.Key.Key_Escape)
        else:
            dialog.close()
        qapp.processEvents()
        assert committed == []
        assert regenerations == []
    finally:
        _dispose(dialog, qapp)


@pytest.mark.parametrize(
    ("plot_type", "parameter_name"),
    (("forest", "fp_xlabel"), ("regression", "bp_xlabel")),
)
def test_generated_plot_editor_apply_then_cancel_preserves_only_committed_draft(
    qapp, tmp_path, plot_type, parameter_name
):

    _use_isolated_settings(tmp_path)
    dialog = plot_editor_dialog.EditPlotDialog(
        {parameter_name: "Original"}, "plot.svg", plot_type=plot_type
    )
    committed = []
    dialog.applied.connect(lambda: committed.append(dialog.plot_params()))
    try:
        dialog.show()
        qapp.processEvents()
        dialog.x_lbl_le.setText("Applied label")
        apply_button = dialog.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Apply
        )
        cancel_button = dialog.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        assert apply_button is not None and cancel_button is not None
        apply_button.click()
        dialog.x_lbl_le.setText("Cancelled later draft")
        cancel_button.click()
        qapp.processEvents()
        assert [entry[parameter_name] for entry in committed] == ["Applied label"]
    finally:
        _dispose(dialog, qapp)


@pytest.mark.parametrize("plot_type", ["forest", "regression"])
def test_generated_plot_editor_ok_commits_once_and_accepts(qapp, tmp_path, plot_type):

    _use_isolated_settings(tmp_path)
    dialog = plot_editor_dialog.EditPlotDialog({}, "plot.svg", plot_type=plot_type)
    applied = QtTest.QSignalSpy(dialog.applied)
    accepted = QtTest.QSignalSpy(dialog.accepted)
    try:
        ok = dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        assert ok is not None
        ok.click()
        qapp.processEvents()
        assert len(applied) == 1
        assert len(accepted) == 1
    finally:
        _dispose(dialog, qapp)


def test_plot_color_chooser_is_named_described_and_keyboard_focusable(qapp, tmp_path):

    _use_isolated_settings(tmp_path)
    dialog = plot_editor_dialog.EditPlotDialog({}, "plot.svg")
    try:
        dialog.show()
        dialog.color_btn.setFocus()
        qapp.processEvents()
        assert dialog.color_btn.accessibleName() == "Choose plot accent color"
        assert "color picker" in dialog.color_btn.accessibleDescription().lower()
        assert dialog.color_btn.toolTip() == "Choose the plot accent color"
        assert dialog.color_btn.hasFocus()
        assert dialog.color_btn.focusPolicy() == QtCore.Qt.FocusPolicy.StrongFocus
    finally:
        _dispose(dialog, qapp)


def test_plot_editor_keeps_scratch_plot_path_internal(qapp, tmp_path):
    _use_isolated_settings(tmp_path)
    for plot_type, prefix in (("forest", "fp"), ("regression", "bp")):
        initial = str(tmp_path / f"{plot_type}-initial.svg")
        dialog = plot_editor_dialog.EditPlotDialog(
            {f"{prefix}_outpath": initial}, "", plot_type=plot_type
        )
        try:
            assert dialog.image_path.text() == initial
            assert dialog.label_3.isHidden()
            assert dialog.image_path.isHidden()
            assert dialog.save_btn.isHidden()
            assert dialog.plot_params()[f"{prefix}_outpath"] == initial
        finally:
            _dispose(dialog, qapp)


def test_plot_editor_path_remains_available_to_internal_plot_parameters(qapp, tmp_path):
    _use_isolated_settings(tmp_path)
    initial = str(tmp_path / "forest-initial.svg")
    dialog = plot_editor_dialog.EditPlotDialog({"fp_outpath": initial}, "")
    try:
        assert dialog.plot_params()["fp_outpath"] == initial
    finally:
        _dispose(dialog, qapp)


@pytest.mark.parametrize(
    ("logical_extent", "device_pixel_ratio", "expected"),
    (
        (0.0, 1.0, 0),
        (0.5, 1.0, 1),
        (2.5, 1.0, 3),
        (515.0, 1.0, 515),
        (515.0, 1.25, 644),
        (515.0, 1.5, 773),
        (515.0, 1.75, 901),
    ),
)
def test_logical_extent_boundary_uses_qt_consistent_half_up_rounding(
    logical_extent, device_pixel_ratio, expected
):
    from rc_metastudio.qt_geometry import logical_extent_to_physical_pixels

    assert (
        logical_extent_to_physical_pixels(logical_extent, device_pixel_ratio)
        == expected
    )


@pytest.mark.parametrize(
    ("logical_extent", "device_pixel_ratio"),
    ((-1.0, 1.0), (1.0, 0.0), (1.0, -1.0), (float("nan"), 1.0), (1.0, float("inf"))),
)
def test_logical_extent_boundary_rejects_invalid_values(
    logical_extent, device_pixel_ratio
):
    from rc_metastudio.qt_geometry import logical_extent_to_physical_pixels

    with pytest.raises(ValueError):
        logical_extent_to_physical_pixels(logical_extent, device_pixel_ratio)
