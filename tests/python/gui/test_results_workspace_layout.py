import os
from pathlib import Path
from qt_test_support import key_click, key_clicks, required

import pytest
from PyQt6 import QtCore, QtGui, QtWidgets
from rc_metastudio.results.contract import parse_analysis_result
from rc_metastudio.results.plot_capabilities import PlotCapability

pytestmark = pytest.mark.qsettings


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("RCMS_QT6_BUILD_ROOT", str(ROOT / "build" / "qt6-verification"))
from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()
from rc_metastudio.results import (
    plot_editor as plot_editor_dialog,
    plot_service,
    window as results_window,
)


def _empty_results(summary="Summary text"):
    return _analysis_result({"texts": {"Summary": summary}})


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
    )


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


@pytest.mark.parametrize("label", ["default", "(default)", "<default>"])
def test_plot_editor_preserves_saved_literal_default_label(qapp, label):
    dialog = plot_editor_dialog.EditPlotDialog({"fp_xlabel": label}, "plot.svg")
    try:
        dialog.col1_str_edit.setText("Unrelated heading change")
        assert dialog.plot_params()["fp_xlabel"] == label
    finally:
        _dispose(dialog, qapp)



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
        window.scene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor("#2b2b2b")))
        painter = QtGui.QPainter(preview)
        window.scene.render(
            painter, QtCore.QRectF(0, 0, 100, 40), plot_item.sceneBoundingRect()
        )
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
            for x, y in ((4, 4), (95, 4), (4, 35), (95, 35))
        )
    finally:
        _dispose(window, qapp)


def test_results_workspace_defaults_maximized_and_restores_screen_safe_state(
    qapp, tmp_path
):
    from rc_metastudio.results import window as results_window
    from rc_metastudio import settings

    _use_isolated_settings(tmp_path)
    fresh = results_window.ResultsWindow(_empty_results())
    try:
        assert fresh.isMaximized()

        fresh.showNormal()
        fresh.setGeometry(90, 70, 620, 410)
        qapp.processEvents()
        fresh.results_nav_splitter.moveSplitter(180, 1)
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
        assert QtCore.QRect(0, 0, 800, 600).contains(placement.placement.frame_geometry)
        sizes = restored.results_nav_splitter.sizes()
        total_size = sum(sizes)
        assert total_size > 0
        assert sizes[0] >= restored.nav_tree.minimumWidth()
        proportions = placement.splitter_proportions
        assert proportions is not None
        assert sizes[0] / total_size == pytest.approx(proportions[0], abs=.02)
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
        assert sizes[0] >= window.nav_tree.minimumWidth()
        assert sizes[1] / total_size >= 0.70
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

    _use_isolated_settings(tmp_path)
    dialog = plot_editor_dialog.EditPlotDialog({}, "forest.png")
    try:
        dialog.show()
        qapp.processEvents()
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
    from rc_metastudio.results import plot_editor as plot_editor_dialog

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
        plot_type="reitsma_coefficient",
    )
    try:
        assert dialog.groupBox.isHidden()
        assert dialog.default_panel.isHidden()
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
        key_clicks(dialog.x_lbl_le, "[default]")
        assert dialog.plot_params()[parameter_name] == "[default]"
    finally:
        _dispose(dialog, qapp)




@pytest.mark.parametrize(
    ("title", "plot_kind", "regenerator", "editable", "has_params"),
    (
        ("Forest Plot", "forest", "forest", True, True),
        ("Cumulative Forest Plot", "cumulative_forest", "forest", True, True),
        ("Leave-one-out Forest Plot", "leave_one_out_forest", "forest", True, True),
        ("Subgroup Forest Plot", "subgroup_forest", "forest", True, True),
        ("Diagnostic Forest Plot", "forest", "forest", True, True),
        ("Meta-Regression Bubble Plot", "regression", "regression", True, True),
        ("A title without a plot hint", "forest", "forest", True, True),
        ("Forest Plot", "other", "none", False, True),
        ("Forest Plot", "forest", "forest", False, False),
    ),
)
def test_plot_context_menu_follows_capabilities_and_available_data(
    qapp, tmp_path, monkeypatch, title, plot_kind, regenerator, editable, has_params
):
    from rc_metastudio.results import window as results_window

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
        _plot_capability_model(plot_kind=plot_kind, regenerator=regenerator, editable=editable),
        params_path=str(tmp_path / "plot-params") if has_params else None,
    )
    try:
        window._make_context_menu(artifact, None)(Event())
        expected = ["Export plot…"]
        if editable:
            expected.insert(0, "Edit plot…")
        if not has_params:
            expected = ["Export plot…"]
        assert captured == [expected]
    finally:
        _dispose(window, qapp)


@pytest.mark.parametrize("extension", ["pdf", "png", "tiff", "svg"])
def test_sroc_export_picker_suggests_format_specific_default_name(
    qapp, tmp_path, monkeypatch, extension
):
    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(_empty_results())
    defaults = []
    artifact = results_window.PlotArtifact(
        "SROC",
        str(tmp_path / "sroc.svg"),
        _plot_capability_model(plot_kind="sroc", regenerator="sroc"),
        params_path=str(tmp_path / "sroc-params"),
    )

    def choose_path(_parent, _title, default_path, *_args):
        defaults.append(default_path)
        return "", ""

    monkeypatch.setattr(results_window.QFileDialog, "getSaveFileName", choose_path)
    try:
        window.save_image_as(artifact, format=extension)
        assert defaults == [f"Analysis results — sroc.{extension}"]
    finally:
        _dispose(window, qapp)


def test_results_window_rejects_svgz_for_funnel_export_before_r(
    monkeypatch, qapp, tmp_path
):
    _use_isolated_settings(tmp_path)
    window = results_window.ResultsWindow(_empty_results())
    artifact = results_window.PlotArtifact(
        "Contour Funnel Plot",
        str(tmp_path / "funnel.png"),
        _plot_capability_model(plot_kind="contour_funnel", regenerator="funnel"),
        params_path=str(tmp_path / "funnel-params"),
    )
    calls = []
    monkeypatch.setattr(
        plot_service.r_operations,
        "render_plot_bundle",
        lambda *args: calls.append(args),
    )
    monkeypatch.setattr(
        results_window.QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(tmp_path / "funnel.svgz"), ""),
    )
    try:
        with pytest.raises(ValueError, match="SVGZ export is not supported"):
            window.save_image_as(artifact, format="svg")
        assert calls == []
    finally:
        _dispose(window, qapp)


@pytest.mark.parametrize("dismissal", ["cancel", "escape", "close"])
def test_plot_editor_dismissal_discards_the_draft(qapp, tmp_path, dismissal):

    _use_isolated_settings(tmp_path)
    committed = []
    dialog = plot_editor_dialog.EditPlotDialog(
        {"fp_xlabel": "Committed label"},
        "plot.svg",
        on_commit=committed.append,
    )
    try:
        dialog.show()
        qapp.processEvents()
        dialog.x_lbl_le.setText("Uncommitted draft")
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
        assert dialog.color_btn.toolTip() == "Open a color picker for the plot accent color."
        assert dialog.color_btn.hasFocus()
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
