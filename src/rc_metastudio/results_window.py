# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render and export meta-analysis results."""

import csv
import gzip
import io
import re
import shutil
import tempfile
import uuid
from collections import namedtuple
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, cast
from PyQt6.QtCore import (
    QByteArray,
    QEvent,
    QObject,
    QPointF,
    pyqtSignal,
    QRectF,
    QTimer,
    Qt,
)
from PyQt6.QtGui import (
    QAction,
    QCloseEvent,
    QFont,
    QFontDatabase,
    QFontMetricsF,
    QImage,
    QImageReader,
    QImageWriter,
    QKeyEvent,
    QPainter,
    QPixmap,
    QResizeEvent,
    QShowEvent,
    QTextOption,
    QTransform,
)
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QFileDialog,
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsProxyWidget,
    QGraphicsScene,
    QGraphicsTextItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QHeaderView,
    QSizePolicy,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
import os
import sys
from rc_metastudio import (
    adaptive_window,
    app_error_handler,
    plot_capabilities,
)
from rc_metastudio.analysis_results import (
    AnalysisResult,
    BinaryNumericValue,
    BinaryNumerics,
    BinaryProportionNumerics,
    PlotCapability,
    parse_analysis_result,
)
from rc_metastudio.funnel_plot_editor_dialog import FunnelPlotEditorDialog
from rc_metastudio.plot_editor_dialog import EditPlotDialog
from rc_metastudio.plot_service import PlotService
from rc_metastudio.qt_geometry import logical_extent_to_physical_pixels
from rc_metastudio.settings import (
    restore_results_window_state,
    save_results_window_state,
)
from rc_metastudio.meta_globals import BINARY_METRIC_NAMES

if TYPE_CHECKING:
    from ui_results_window import Ui_ResultsWindow
else:
    from rc_metastudio.ui_results_window import Ui_ResultsWindow

PageSize = (612, 792)
padding = 25
horizontal_padding = 75
PlotExportFormat = namedtuple("PlotExportFormat", ["extension", "label", "qt_format"])
PLOT_EXPORT_FORMATS = (
    PlotExportFormat("pdf", "PDF", None),
    PlotExportFormat("png", "PNG", "PNG"),
    PlotExportFormat("tiff", "TIFF", "TIFF"),
    PlotExportFormat("svg", "SVG", None),
)
PLOT_EXPORT_FORMATS_BY_EXTENSION = {
    export_format.extension: export_format for export_format in PLOT_EXPORT_FORMATS
}
PLOT_EXPORT_EXTENSION_ALIASES = {
    "pdf": (".pdf",),
    "png": (".png",),
    "tiff": (".tif", ".tiff"),
    "svg": (".svg", ".svgz"),
}
PLOT_EXPORT_GUIDANCE = {
    "pdf": "Recommended vector format for journal submission and print workflows.",
    "svg": "Scalable vector format; ideal for editing and lossless resizing.",
    "tiff": "Publication-grade 600 dpi raster export with lossless compression.",
    "png": "Publication-grade 600 dpi raster export for compatible submission systems.",
}
NO_RESULTS_MESSAGE = "No results could be computed for this analysis."
ROW_HEIGHT = 15  # by trial-and-error; seems to work very well
SECTION_SPACING = ROW_HEIGHT
MAX_VECTOR_PLOT_SCALE = 4.0
QGraphicsSvgItem = None
QSvgRenderer = None


def _fit_result_table_rows(
    table: QTableWidget,
    *,
    maximum_height: int = 300,
    minimum_cap: int | None = None,
    visible_rows: int = 8,
    base_height: int = 48,
) -> None:
    """Show a bounded set of rows while keeping longer result tables scrollable."""
    # layout-audit: allow=compact-table-overflow; reason=Show short tables fully and scroll longer result tables.
    table.setMinimumHeight(
        min(
            minimum_cap or maximum_height,
            base_height + min(table.rowCount(), visible_rows) * 28,
        )
    )
    # layout-audit: allow=compact-table-overflow; reason=Keep long result tables within the visible result section.
    table.setMaximumHeight(maximum_height)


def _svg_item_class():
    global QGraphicsSvgItem
    if QGraphicsSvgItem is None:
        from PyQt6.QtSvgWidgets import QGraphicsSvgItem as _QGraphicsSvgItem

        class OpaqueGraphicsSvgItem(_QGraphicsSvgItem):
            """Paint SVG plots on paper instead of the themed scene canvas."""

            def paint(self, painter, option, widget=None):
                painter.fillRect(self.boundingRect(), Qt.GlobalColor.white)
                super().paint(painter, option, widget)

        QGraphicsSvgItem = OpaqueGraphicsSvgItem
    return QGraphicsSvgItem


def _svg_renderer_class():
    global QSvgRenderer
    if QSvgRenderer is None:
        from PyQt6.QtSvg import QSvgRenderer as _QSvgRenderer

        QSvgRenderer = _QSvgRenderer
    return QSvgRenderer


def _path_with_export_extension(file_path, export_format, *, allow_svgz=True):
    if (
        export_format.extension == "svg"
        and not allow_svgz
        and os.path.splitext(str(file_path))[1].lower() == ".svgz"
    ):
        raise ValueError(
            "SVGZ export is not supported for funnel plots; use SVG instead."
        )
    aliases = PLOT_EXPORT_EXTENSION_ALIASES[export_format.extension]
    if os.path.splitext(str(file_path))[1].lower() in aliases:
        return file_path
    return "%s.%s" % (file_path, export_format.extension)


def _raw_number_text(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _format_count(value):
    return str(int(value))


def _format_metric(value):
    return format(float(value), ".4g")


def _format_percent(value):
    return "%s%%" % format(float(value), ".2f")


def _format_probability(value):
    return format(float(value), ".3g")


def _binary_numeric_text(value: BinaryNumericValue, formatter) -> str:
    if value.status == "available":
        return formatter(value.value)
    if value.status == "not_estimable":
        return "Not estimable"
    return "Not available"


def _family_numeric_text(value):
    if isinstance(value, Mapping):
        if value.get("status") == "available":
            return _raw_number_text(value.get("value"))
        if value.get("status") == "not_estimable":
            status = "Not estimable"
        else:
            status = "Not available"
        reason = value.get("reason")
        return "%s: %s" % (status, reason) if isinstance(reason, str) and reason else status
    if value is None:
        return "Not available"
    return _raw_number_text(value)


def _numeric_accessible_description(value):
    if not isinstance(value, Mapping) or value.get("status") == "available":
        return ""
    status = (
        "Not estimable"
        if value.get("status") == "not_estimable"
        else "Not available"
    )
    reason = value.get("reason")
    return "%s: %s" % (status, reason) if isinstance(reason, str) and reason else status


def _cumulative_figure_caption(numerics):
    ordering = numerics["ordering"]
    field = str(ordering["field"]).replace("_", " ")
    lines = [
        "Cumulative sequence (%s, %s):"
        % (field, ordering["direction"])
    ]
    for step in numerics["steps"]:
        value = step["ordering_value"]
        order_value = "Missing" if value is None else str(value)
        final = "; final all-included estimate" if step["is_final"] else ""
        lines.append(
            "Step %s: included studies n=%s; added study %s; %s=%s; "
            "estimate %s; interval %s to %s%s."
            % (
                step["order"] + 1,
                step["included_study_count"],
                step["study_name"],
                field,
                order_value,
                _family_numeric_text(step["estimate"]),
                _family_numeric_text(step["lower_bound"]),
                _family_numeric_text(step["upper_bound"]),
                final,
            )
        )
    return "\n".join(lines)


def _meta_regression_cell(value):
    if isinstance(value, Mapping) and value.get("status") in {
        "available", "not_estimable", "not_available"
    }:
        status = value.get("status")
        if status == "available":
            raw = value.get("value")
            if raw is None:
                return "Not reported", None, "Not reported", ""
            return str(raw), raw, str(raw), ""
        display = "Not estimable" if status == "not_estimable" else "Not available"
        reason = value.get("reason")
        tooltip = str(reason) if isinstance(reason, str) and reason else ""
        copy_text = display + (": " + tooltip if tooltip else "")
        return display, None, copy_text, tooltip
    if value is None:
        return "Not reported", None, "Not reported", ""
    return str(value), value, str(value), ""


def _generic_meta_regression_details(numerics):
    eligible = numerics["eligible_study_ids"]
    excluded = numerics["excluded_studies"]
    moderators = []
    for coding in numerics["moderators"]:
        parts = [str(coding["kind"])]
        if coding.get("unit"):
            parts.append("unit %s" % coding["unit"])
        if coding.get("unit_step") not in (None, 1):
            parts.append("source step %s" % coding["unit_step"])
        if coding.get("levels"):
            parts.append("levels %s" % ", ".join(map(str, coding["levels"])))
        if coding.get("reference_level") is not None:
            parts.append("reference %s" % coding["reference_level"])
        moderators.append("%s (%s)" % (coding["name"], "; ".join(parts)))
    exclusion_text = "; ".join(
        "%s: %s (missing: %s)"
        % (
            item.get("label", item["id"]),
            item["id"],
            ", ".join(map(str, item["missing_moderators"])),
        )
        for item in excluded
    ) or "None"
    return "\n".join(
        (
            "Formula: %s" % numerics["formula"],
            "Measure: %s; heterogeneity method: %s; inference method: %s; "
            "confidence level: %s; missing moderator policy: %s."
            % (
                numerics["metric"],
                numerics["heterogeneity_method"],
                numerics["inference_method"],
                numerics["confidence_level"],
                numerics["missing_moderator_policy"],
            ),
            "Included study IDs (%s): %s; excluded studies (%s): %s."
            % (len(eligible), ", ".join(map(str, eligible)), len(excluded), exclusion_text),
            "Moderators: " + "; ".join(moderators),
        )
    )


def _generic_meta_regression_tables(numerics):
    coefficients = [
        (
            item["term"]["label"],
            item["estimate"],
            item["standard_error"],
            item["lower"],
            item["upper"],
            item["statistic_name"],
            item["statistic"],
            item["degrees_of_freedom"],
            item["p_value"],
        )
        for item in numerics["coefficients"]
    ]
    test_records = [numerics["overall_test"], *numerics["moderator_tests"]]
    tests = [
        (
            item["label"], item["statistic_name"], item["statistic"],
            item["numerator_degrees_of_freedom"],
            item["denominator_degrees_of_freedom"], item["p_value"],
        )
        for item in test_records
    ]
    heterogeneity = numerics["residual_heterogeneity"]
    heterogeneity_rows = [
        ("Tau squared", heterogeneity["tau_squared"]),
        ("Tau squared standard error", heterogeneity["tau_squared_standard_error"]),
        ("I squared (%)", heterogeneity["i_squared_percent"]),
        ("H squared", heterogeneity["h_squared"]),
        ("Explained heterogeneity (%)", heterogeneity["explained_percent"]),
        ("Q", heterogeneity["q"]),
        ("Q degrees of freedom", heterogeneity["q_degrees_of_freedom"]),
        ("Q p-value", heterogeneity["q_p_value"]),
    ]
    return (
        (
            "Coefficient estimates",
            "meta_regression_coefficient_table",
            (
                "Term", "Estimate", "Standard error", "Lower bound", "Upper bound",
                "Statistic type", "Statistic", "Degrees of freedom", "P-value",
            ),
            coefficients,
        ),
        (
            "Overall and moderator tests",
            "meta_regression_test_table",
            (
                "Test", "Statistic type", "Statistic", "Numerator degrees of freedom",
                "Denominator degrees of freedom", "P-value",
            ),
            tests,
        ),
        (
            "Residual heterogeneity",
            "meta_regression_heterogeneity_table",
            ("Measure", "Authority result"),
            heterogeneity_rows,
        ),
    )


def _reitsma_meta_regression_details(numerics):
    correction = numerics["correction"]
    coding = []
    for item in numerics["moderator_coding"]:
        description = item["kind"]
        if item.get("levels"):
            description += "; levels: " + ", ".join(map(str, item["levels"]))
        if item.get("reference_level") is not None:
            description += "; reference: " + str(item["reference_level"])
        if item.get("observed_range") is not None:
            description += "; observed range: " + ", ".join(
                map(str, item["observed_range"])
            )
        coding.append("%s (%s)" % (item["name"], description))
    exclusions = "; ".join(
        "%s: %s" % (item["study_id"], item["reason"])
        for item in numerics["exclusions"]
    ) or "None"
    unavailable = "; ".join(
        "%s: %s" % (item["name"], item["reason"])
        for item in numerics["unavailable_outputs"]
    ) or "None"
    eligible = numerics["eligible_study_ids"]
    return "\n".join(
        (
            "Formula: %s" % numerics["formula"],
            "Joint Reitsma model; estimator: %s; correction: %s (factor %s); "
            "mada version: %s; converged: %s."
            % (
                numerics["estimator"], correction["policy"], correction["factor"],
                numerics["package_version"], numerics["converged"],
            ),
            "Eligible study IDs (%s): %s; exclusions (%s): %s."
            % (len(eligible), ", ".join(map(str, eligible)), len(numerics["exclusions"]), exclusions),
            "Moderator coding: " + "; ".join(coding),
            "Unavailable conditional outputs: " + unavailable,
        )
    )


def _reitsma_coefficient_rows(coefficients):
    return [
        (
            item["term"], item["model_estimate"], item["standard_error"],
            item["model_statistic"], item["p_value"], item["model_ci_lower"],
            item["model_ci_upper"], item["reported_odds_ratio"],
            item["odds_ratio_ci_lower"], item["odds_ratio_ci_upper"],
        )
        for item in coefficients
    ]


def _reitsma_meta_regression_tables(numerics):
    common_coefficient_headers = (
        "Term", "Model log-odds estimate", "Standard error", "Model statistic",
        "P-value", "Model CI lower", "Model CI upper",
    )
    overall = numerics["overall_ml_likelihood_ratio_test"]
    test_records = [overall, *numerics["moderator_block_ml_tests"]]
    tests = [
        (
            item["label"], item["comparison"], item["fit_estimator"],
            item["statistic"], item["degrees_of_freedom"], item["p_value"],
            len(item["included_study_ids"]),
        )
        for item in test_records
    ]
    return (
        (
            "Sensitivity coefficient model (log odds)",
            "reitsma_sensitivity_coefficient_table",
            common_coefficient_headers + (
                "Sensitivity odds ratio", "Sensitivity odds-ratio CI lower",
                "Sensitivity odds-ratio CI upper",
            ),
            _reitsma_coefficient_rows(numerics["sensitivity_coefficients"]),
        ),
        (
            "False-positive-rate coefficient model (specificity direction)",
            "reitsma_false_positive_rate_coefficient_table",
            common_coefficient_headers + (
                "Specificity odds ratio (authority display)",
                "Specificity odds-ratio CI lower", "Specificity odds-ratio CI upper",
            ),
            _reitsma_coefficient_rows(numerics["false_positive_rate_coefficients"]),
        ),
        (
            "Likelihood-ratio tests (ML fits)",
            "reitsma_meta_regression_test_table",
            (
                "Test", "Comparison", "Fit estimator", "Likelihood-ratio statistic",
                "Degrees of freedom", "P-value", "Included studies",
            ),
            tests,
        ),
    )


def _set_binary_table_item(
    table, row, column, text, sort_value, raw_value, *, tooltip="", copy_text=None
):
    item = _BinaryResultTableItem(
        text, sort_value=sort_value, raw_value=raw_value, copy_text=copy_text
    )
    if tooltip:
        item.setToolTip(tooltip)
        item.setData(Qt.ItemDataRole.AccessibleDescriptionRole, tooltip)
    table.setItem(row, column, item)


def _set_binary_numeric_cell(table, row, column, value, formatter):
    if value.status == "available":
        _set_binary_table_item(
            table,
            row,
            column,
            formatter(value.value),
            (0, float(value.value)),
            value.value,
        )
        return
    display = _binary_numeric_text(value, formatter)
    copy_text = display
    if value.reason:
        copy_text += ": " + value.reason
    _set_binary_table_item(
        table,
        row,
        column,
        display,
        (1, display),
        None,
        tooltip=value.reason or "",
        copy_text=copy_text,
    )


def _binary_context_text(context: Mapping[str, object]) -> str:
    rows = []
    for key, label in (
        ("outcome", "Outcome"),
        ("time_point", "Time point"),
        ("direction", "Direction"),
        ("measure", "Measure"),
        ("workflow", "Workflow"),
        ("method", "Method"),
        ("status", "Saved result status"),
    ):
        value = context.get(key)
        if value is not None and str(value).strip():
            rows.append("%s: %s" % (label, value))

    settings = context.get("effective_settings")
    if isinstance(settings, Mapping) and settings:
        displayed_settings = {
            key: value
            for key, value in settings.items()
            if not (
                key in {"workflow", "method"} and context.get(key) is not None
            )
        }
        if displayed_settings:
            setting_text = "; ".join(
                "%s: %s" % (key, displayed_settings[key])
                for key in sorted(displayed_settings)
            )
            rows.append("Effective settings: " + setting_text)
    return "\n".join(rows)


class PlotArtifact(object):
    def __init__(
        self,
        title,
        image_path,
        capability: PlotCapability,
        params_path=None,
        display_path=None,
    ):
        self.title = title
        self.image_path = str(image_path)
        self.params_path = params_path
        self.capability = capability
        self.plot_kind = capability.plot_kind
        self.display_image_path = str(display_path or self.image_path)

    def display_path(self):
        if os.path.exists(self.display_image_path):
            return self.display_image_path
        return self.image_path

    def has_vector_display(self):
        return self.display_path().lower().endswith((".svg", ".svgz"))

    def can_display(self):
        try:
            if self.has_vector_display():
                item = _svg_item_class()(self.display_path())
                return item.renderer().isValid()
            return not QPixmap(self.image_path).isNull()
        except (OSError, ValueError):
            return False

    def can_regenerate(self):
        return bool(self.params_path) and self.capability.regenerator != "none"

    def can_edit(self):
        return (
            self.capability.editable
            and self.can_regenerate()
            and bool(plot_capabilities.option_groups(self.plot_kind))
        )

    def export_formats(self):
        return tuple(
            export_format
            for export_format in PLOT_EXPORT_FORMATS
            if self.can_export_with_stored_renderer(export_format.extension)
            or self._can_export_with_regenerator(export_format.extension)
        )

    def can_export_with_stored_renderer(self, extension):
        if not self.can_display():
            return False
        if extension == "svg":
            return self.has_vector_display()
        if extension in ("png", "tiff"):
            export_format = PLOT_EXPORT_FORMATS_BY_EXTENSION[extension]
            return _qt_supports_image_format(export_format.qt_format)
        return False

    def _can_export_with_regenerator(self, extension):
        if not self.can_regenerate():
            return False
        if extension in ("png", "tiff"):
            return True
        return self.has_vector_display() and extension in ("pdf", "svg")

    def requires_engine_for_export(self, extension):
        return self._can_export_with_regenerator(
            extension
        ) and not self.can_export_with_stored_renderer(extension)


def _qt_supports_image_format(image_format):
    normalized = image_format.lower().encode("ascii")
    return normalized in QImageWriter.supportedImageFormats()


class SelectableResultsTextItem(QGraphicsTextItem):
    def __init__(self, text, results_window):
        super(SelectableResultsTextItem, self).__init__(text)
        self._results_window = results_window

    def contextMenuEvent(self, event):
        try:
            self._results_window._show_text_context_menu(self, event)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            app_error_handler.handle_exception(
                type(e), e, e.__traceback__, parent=self._results_window
            )
            event.accept()


class ResponsivePixmapItem(QGraphicsPixmapItem):
    def __init__(self, source_pixmap):
        super(ResponsivePixmapItem, self).__init__()
        self.source_pixmap = QPixmap(source_pixmap)
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)

    def replace_source(self, source_pixmap):
        self.source_pixmap = QPixmap(source_pixmap)

    def setPixmap(self, pixmap):
        super().setPixmap(_pixmap_with_white_background(pixmap))

    def paint(self, painter, option, widget=None):
        painter.fillRect(self.boundingRect(), Qt.GlobalColor.white)
        super().paint(painter, option, widget)


class _BinaryResultTableItem(QTableWidgetItem):
    """Keep display text separate from the numeric value used for sort/copy."""

    def __init__(self, text, *, sort_value=None, raw_value=None, copy_text=None):
        super().__init__(text)
        self._sort_value = sort_value
        self._copy_text = str(raw_value) if copy_text is None else copy_text
        self.setData(Qt.ItemDataRole.UserRole, raw_value)

    def __lt__(self, other):
        if isinstance(other, _BinaryResultTableItem):
            return self._sort_value < other._sort_value
        return super().__lt__(other)

    def copy_text(self):
        return self._copy_text


def _pixmap_with_white_background(pixmap):
    if pixmap.isNull():
        return QPixmap(pixmap)
    opaque = QPixmap(pixmap.size())
    opaque.setDevicePixelRatio(pixmap.devicePixelRatioF())
    opaque.fill(Qt.GlobalColor.white)
    painter = QPainter(opaque)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return opaque


def _svg_bytes_with_white_background(path):
    opener = gzip.open if str(path).lower().endswith(".svgz") else open
    with opener(path, "rb") as svg_file:
        svg = svg_file.read()
    root = re.search(rb"<svg\b[^>]*>", svg, flags=re.IGNORECASE)
    if root is None:
        return svg
    white_canvas = b'<rect width="100%" height="100%" fill="#ffffff"/>'
    return svg[: root.end()] + white_canvas + svg[root.end() :]


def _opaque_svg_renderer(path, parent):
    return _svg_renderer_class()(
        QByteArray(_svg_bytes_with_white_background(path)), parent
    )


def _image_for_artifact(artifact):
    display_path = artifact.display_path()
    if str(display_path).lower().endswith((".svg", ".svgz")):
        renderer = _opaque_svg_renderer(display_path, None)
        if not renderer.isValid():
            return QImage()
        size = renderer.defaultSize()
        if not size.isValid() or size.width() <= 0 or size.height() <= 0:
            return QImage()
        image = QImage(size, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        return image
    image = QImage(display_path)
    if image.isNull() and display_path != artifact.image_path:
        image = QImage(artifact.image_path)
    return image


def _pixmap_device_independent_size(pixmap):
    """Return a pixmap's logical dimensions without discarding its DPR."""
    dpr = max(1.0, float(pixmap.devicePixelRatioF()))
    return (float(pixmap.width()) / dpr, float(pixmap.height()) / dpr)


class ResultsWindow(QMainWindow, Ui_ResultsWindow):
    edit_copy_requested = pyqtSignal(object)

    def __init__(
        self,
        results: AnalysisResult,
        parent=None,
        plot_service: PlotService | None = None,
        *,
        context: Mapping[str, object] | None = None,
        edit_copy_spec: object | None = None,
        worker_client=None,
    ):

        super(ResultsWindow, self).__init__(parent)
        self.setAccessibleName("Analysis results")
        self._svg_plot_items = []
        self._raster_plot_items = []
        self._refitting_svg_plots = False
        self._viewport_refit_pending = False
        self._viewport_width_override = None
        self._first_show_refit_pending = True
        self._layout_items = []
        self._nav_items_to_sections = {}
        self._nav_items_to_focus_targets = {}
        self._plot_zoom_modes = {}
        self._plot_zoom_values = {}
        self._plot_zoom_controls = {}
        self._missing_plot_slots = {}
        self.setupUi(self)
        self.nav_tree.setAccessibleName("Results navigation")
        self.nav_tree.setAccessibleDescription(
            "Navigate between analysis result sections and plots."
        )
        navigation_viewport = self.nav_tree.viewport()
        if navigation_viewport is None:
            raise RuntimeError("Results navigation has no viewport")
        self.nav_tree.installEventFilter(self)
        navigation_viewport.installEventFilter(self)
        self.graphics_view.setAccessibleName("Results content")
        self.graphics_view.setAccessibleDescription(
            "View analysis summaries, references, and generated plots."
        )
        viewport = self.graphics_view.viewport()
        if viewport is None:
            raise RuntimeError("Results graphics view has no viewport")
        viewport.installEventFilter(self)
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.RESULTS
        )
        restored_state = restore_results_window_state(self)
        self.copied_item = QByteArray()
        self.paste_offset = 5
        self.add_offset = 5
        self.buffer_size = 2
        self.borders = []
        self._active_text_context_menu = None
        self.plot_service = plot_service or PlotService()
        self.worker_client = worker_client
        self._plot_analysis_id = uuid.uuid4().hex
        self._plot_generations = {}
        self._plot_worker_requests = {}
        if self.worker_client is not None:
            self.worker_client.plotProgress.connect(self._plot_worker_progress)
            self.worker_client.plotCompleted.connect(self._plot_worker_completed)
            self.worker_client.plotFailed.connect(self._plot_worker_failed)
        if context is not None and not isinstance(context, Mapping):
            raise TypeError("analysis context must be a mapping")
        self.analysis_context = dict(context or {})
        self._edit_copy_spec = edit_copy_spec

        self.results_nav_splitter.splitterMoved.connect(
            app_error_handler.safe_slot(
                lambda _pos, _index: self._schedule_viewport_refit(), parent=self
            )
        )

        self.nav_tree.setHeaderLabels(["Results"])
        self.nav_tree.setItemsExpandable(True)
        # layout-audit: allow=content-overflow-control; reason=required content may consume available layout width
        self.nav_tree.setMinimumWidth(0)
        self.nav_tree.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        self.graphics_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.results_nav_splitter.setChildrenCollapsible(False)
        self.results_nav_splitter.setStretchFactor(0, 1)
        self.results_nav_splitter.setStretchFactor(1, 1)
        self.x_coord = 5.0
        self.y_coord = 5.0

        self._restored_splitter_proportions = restored_state["splitter_proportions"]
        self._splitter_restore_pending = True

        self.scene = QGraphicsScene(self)

        results = _normalize_results(results)
        self.results = results

        self.images = results.images
        self.display_images = results.display_images
        self.image_order = results.image_order
        self.params_paths = results.image_params_paths
        self.plot_capabilities = results.plot_capabilities

        self.items_to_coords = {}
        self._wrapped_text_items = []
        self.texts = results.texts
        self.references_text = next(
            (
                section.value
                for section in results.sections
                if section.semantic_id == "text:references"
            ),
            None,
        )

        self.add_binary_numerics_section()
        self.add_binary_proportion_numerics_section()
        self.add_family_numerics_section("continuous", self.results.continuous_numerics)
        self.add_family_numerics_section("diagnostic", self.results.diagnostic_numerics)
        self.add_sequential_numerics_section("cumulative", self.results.cumulative_numerics)
        self.add_sequential_numerics_section("leave-one-out", self.results.leave_one_out_numerics)
        self.add_meta_regression_numerics_section(
            "generic", self.results.meta_regression_numerics
        )
        self.add_meta_regression_numerics_section(
            "reitsma", self.results.reitsma_meta_regression_numerics
        )
        self.add_result_sections()
        self.add_reitsma_report()
        self.add_references()
        self._relayout_sections()
        self.nav_tree.currentItemChanged.connect(
            app_error_handler.safe_slot(
                self._navigation_item_changed, parent=self
            )
        )
        self.nav_tree.itemActivated.connect(
            app_error_handler.safe_slot(
                self._activate_navigation_item, parent=self
            )
        )
        if self.nav_tree.topLevelItemCount():
            first_item = self.nav_tree.topLevelItem(0)
            if first_item is not None:
                self.nav_tree.setCurrentItem(first_item)

        # reset the scene
        self.graphics_view.setScene(self.scene)
        self.graphics_view.ensureVisible(QRectF(0, 0, 0, 0))
        # Establish the restored ratio before the first native show/layout pass.
        # QSplitter then preserves that ratio as the window receives its final
        # screen-safe geometry, and the queued refit sees a stable viewport.
        self._apply_restored_splitter_proportions()

    def add_result_sections(self):
        # Ordering and plot capabilities come from the immutable result
        # contract.  The title is used only when painting display text.
        for section in sorted(self.results.sections, key=lambda item: item.order):
            if section.semantic_id == "text:references":
                continue
            if section.kind == "text":
                self.add_text_section(section.source_key, section.title, section.value)
            elif section.kind == "image":
                self.add_image_section(section.source_key, section.title, section.value)

    def add_reitsma_report(self):
        report = self.results.reitsma_report
        if report is None:
            return
        sections = report.get("sections")
        if not isinstance(sections, tuple):
            return

        title = "Joint Reitsma output availability"
        nav_item = self.add_title(title)
        panel = QWidget()
        panel.setObjectName("reitsma_report_panel")
        panel.setAccessibleName(title)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        description = QLabel(
            "Joint model: diagnostic.reitsma. The authority's available text and "
            "SROC sections appear above in report order. Unavailable outputs retain "
            "the authority boundary's reason below.",
            panel,
        )
        description.setWordWrap(True)
        description.setAccessibleName("Joint Reitsma output status")
        layout.addWidget(description)

        table = QTableWidget(len(sections), 3, panel)
        table.setObjectName("reitsma_report_availability_table")
        table.setAccessibleName("Joint Reitsma output availability table")
        table.setAccessibleDescription(
            "Availability of each output returned by the joint Reitsma authority. "
            "Available output content appears in the report sections above; every "
            "unavailable output includes its reason."
        )
        table.setHorizontalHeaderLabels(("Output", "Status", "Availability detail"))
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(False)
        for row_index, value in enumerate(sections):
            if not isinstance(value, Mapping):
                raise ValueError("Reitsma report section must be a mapping")
            section = cast(Mapping[str, object], value)
            key = str(section["key"])
            status = str(section["status"])
            detail = (
                "Shown in the ordered report above."
                if status == "available"
                else str(section["reason"])
            )
            row_values = (
                str(section["title"]),
                "Available" if status == "available" else "Unavailable",
                detail,
            )
            for column, text in enumerate(row_values):
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, key)
                table.setItem(row_index, column, item)
        header = table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        vertical_header = table.verticalHeader()
        if vertical_header is not None:
            vertical_header.setVisible(False)
        _fit_result_table_rows(table, maximum_height=340, visible_rows=10, base_height=50)
        layout.addWidget(table)
        proxy = self._add_action_widget(panel)
        self._nav_items_to_sections[id(nav_item)] = proxy
        self._nav_items_to_focus_targets[id(nav_item)] = proxy
        self.items_to_coords[id(nav_item)] = proxy.scenePos()
        self.reitsma_report_table = table

    def add_binary_numerics_section(self):
        numerics = self.results.binary_numerics
        if numerics is None:
            return

        nav_item = self.add_title("Binary Results")
        panel = self._create_binary_results_panel(numerics)
        self.binary_results_panel = panel
        proxy = self._add_action_widget(panel)
        self._nav_items_to_sections[id(nav_item)] = proxy
        self._nav_items_to_focus_targets[id(nav_item)] = proxy
        self.items_to_coords[id(nav_item)] = proxy.scenePos()

    def add_binary_proportion_numerics_section(self):
        numerics = self.results.binary_proportion_numerics
        if numerics is None:
            return
        nav_item = self.add_title("Binary Proportions")
        panel = self._create_binary_proportion_panel(numerics)
        self.binary_results_panel = panel
        proxy = self._add_action_widget(panel)
        self._nav_items_to_sections[id(nav_item)] = proxy
        self._nav_items_to_focus_targets[id(nav_item)] = proxy
        self.items_to_coords[id(nav_item)] = proxy.scenePos()

    def add_family_numerics_section(self, family, numerics):
        if numerics is None:
            return
        title = "Continuous Results" if family == "continuous" else "Diagnostic Results"
        nav_item = self.add_title(title)
        panel = self._create_family_results_panel(family, numerics)
        proxy = self._add_action_widget(panel)
        self._nav_items_to_sections[id(nav_item)] = proxy
        self._nav_items_to_focus_targets[id(nav_item)] = proxy
        self.items_to_coords[id(nav_item)] = proxy.scenePos()

    def add_sequential_numerics_section(self, workflow, numerics):
        if numerics is None:
            return
        title = "Cumulative steps" if workflow == "cumulative" else "Leave-one-out sensitivity"
        nav_item = self.add_title(title)
        panel = QWidget()
        panel.setObjectName("%s_results_panel" % workflow.replace("-", "_"))
        panel.setAccessibleName(title)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        if workflow == "cumulative":
            ordering = numerics["ordering"]
            heading = "Cumulative result: %s. Order: %s, %s. Missing years: %s." % (
                numerics["status"],
                str(ordering["field"]).replace("_", " "),
                ordering["direction"],
                ordering["missing_year_policy"] or "not applicable",
            )
            headers = (
                "Step", "Study added", "Ordering value", "Included studies",
                "Analyzed studies", "Estimate", "Lower bound", "Upper bound",
                "Standard error", "P-value", "Status and reason",
            )
            rows = []
            for step in numerics["steps"]:
                rows.append((
                    step["order"] + 1,
                    step["study_name"] + (" (final all-included)" if step["is_final"] else ""),
                    step["ordering_value"] if step["ordering_value"] is not None else "Missing",
                    step["included_study_count"],
                    step["analyzed_study_count"],
                    step["estimate"], step["lower_bound"], step["upper_bound"],
                    step["standard_error"], step["p_value"],
                    step["status"] + (": " + step["failure_reason"] if step["failure_reason"] else ""),
                ))
        else:
            heading = (
                "Leave-one-out sensitivity. Measure: %s. Method: %s. Displayed "
                "on the %s scale. Change is omitted minus baseline on %s. "
                "The All included studies row is the figure reference."
                % (
                    numerics["metric"],
                    numerics["method"],
                    numerics["effect_scale"],
                    numerics["effect_scale"],
                )
            )
            headers = (
                "Scenario", "Remaining studies", "Estimate", "Lower bound", "Upper bound",
                "Change from baseline", "Q", "Tau squared", "I squared", "H squared",
                "Status and reason",
            )
            rows = []
            for row in numerics["rows"]:
                heterogeneity = {item["name"]: item["value"] for item in row["heterogeneity"]}
                rows.append((
                    row["label"], row["remaining_study_count"], row["estimate"],
                    row["lower_bound"], row["upper_bound"], row["change_from_baseline"],
                    heterogeneity.get("Q"), heterogeneity.get("tau2"),
                    heterogeneity.get("I2"), heterogeneity.get("H2"),
                    row["status"] + (": " + row["reason"] if row["reason"] else ""),
                ))

        analysis_context = _binary_context_text(self.analysis_context)
        if analysis_context:
            heading += "\nAnalysis context: " + analysis_context.replace("\n", "; ")

        description = QLabel(heading, panel)
        description.setAccessibleName(
            "Cumulative analysis details"
            if workflow == "cumulative"
            else "Leave-one-out analysis details"
        )
        description.setAccessibleDescription(heading)
        description.setWordWrap(True)
        layout.addWidget(description)
        actions = QHBoxLayout()
        copy_button = QPushButton("Copy table", panel)
        copy_button.setAccessibleName("Copy %s result table" % workflow)
        copy_button.setToolTip(
            "Copy selected rows, or the full table when no rows are selected, "
            "with unrounded numeric values."
        )
        copy_button.clicked.connect(self._copy_binary_study_table)
        actions.addWidget(copy_button)
        export_button = QPushButton("Export CSV", panel)
        export_button.setAccessibleName("Export %s result table" % workflow)
        export_button.setToolTip(
            "Export the full result table with unrounded numeric values."
        )
        export_button.clicked.connect(self._export_binary_study_table)
        actions.addWidget(export_button)
        if self._edit_copy_spec is not None:
            edit_copy_button = QPushButton("Edit a copy", panel)
            edit_copy_button.setAccessibleName("Edit a copy of this analysis")
            edit_copy_button.clicked.connect(
                lambda _checked=False: self.edit_copy_requested.emit(self._edit_copy_spec)
            )
            actions.addWidget(edit_copy_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        table = QTableWidget(len(rows), len(headers), panel)
        table.setObjectName("%s_result_table" % workflow.replace("-", "_"))
        table.setAccessibleName(title + " table")
        table.setAccessibleDescription(
            heading
            + " Use arrow keys to move between cells. Copy selected rows, or the "
            "full table when no rows are selected. Each unavailable cell includes "
            "its reason."
        )
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(False)
        for row_index, values in enumerate(rows):
            for column, value in enumerate(values):
                display = _family_numeric_text(value)
                raw = value.get("value") if isinstance(value, Mapping) and value.get("status") == "available" else display
                _set_binary_table_item(
                    table,
                    row_index,
                    column,
                    display,
                    (0, row_index),
                    raw,
                    tooltip=_numeric_accessible_description(value),
                )
        horizontal_header = table.horizontalHeader()
        if horizontal_header is not None:
            horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        vertical_header = table.verticalHeader()
        if vertical_header is not None:
            vertical_header.setVisible(False)
        _fit_result_table_rows(table)
        layout.addWidget(table)
        self.binary_study_table = table
        self._study_table_family = workflow
        proxy = self._add_action_widget(panel)
        self._nav_items_to_sections[id(nav_item)] = proxy
        self._nav_items_to_focus_targets[id(nav_item)] = proxy
        self.items_to_coords[id(nav_item)] = proxy.scenePos()

    def add_meta_regression_numerics_section(self, kind, numerics):
        if numerics is None:
            return
        if kind == "generic":
            title = "Meta-regression coefficients and tests"
            details = _generic_meta_regression_details(numerics)
            tables = _generic_meta_regression_tables(numerics)
        else:
            title = "Reitsma meta-regression coefficients and tests"
            details = _reitsma_meta_regression_details(numerics)
            tables = _reitsma_meta_regression_tables(numerics)

        nav_item = self.add_title(title)
        panel = QWidget()
        panel.setObjectName("%s_meta_regression_results_panel" % kind)
        panel.setAccessibleName(title)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        context = QLabel(details, panel)
        context.setObjectName("%s_meta_regression_details" % kind)
        context.setAccessibleName(title + " details")
        context.setWordWrap(True)
        layout.addWidget(context)
        setattr(self, "%s_meta_regression_details" % kind, context)

        for table_title, object_name, headers, rows in tables:
            self._add_meta_regression_table(
                layout,
                table_title,
                object_name,
                headers,
                rows,
                context=details,
            )

        proxy = self._add_action_widget(panel)
        self._nav_items_to_sections[id(nav_item)] = proxy
        self._nav_items_to_focus_targets[id(nav_item)] = proxy
        self.items_to_coords[id(nav_item)] = proxy.scenePos()

    def _add_meta_regression_table(
        self, layout, title, object_name, headers, rows, *, context
    ):
        section_heading = QLabel(title, layout.parentWidget())
        section_heading.setAccessibleName(title)
        section_heading.setWordWrap(True)
        layout.addWidget(section_heading)

        action_row = QHBoxLayout()
        copy_button = QPushButton("Copy table", layout.parentWidget())
        copy_button.setObjectName(object_name + "_copy_button")
        copy_button.setAccessibleName("Copy " + title)
        copy_button.setToolTip(
            "Copy selected rows, or the full table when no rows are selected. "
            "Numeric values are copied without rounding."
        )
        action_row.addWidget(copy_button)
        export_button = QPushButton("Export CSV", layout.parentWidget())
        export_button.setObjectName(object_name + "_export_button")
        export_button.setAccessibleName("Export " + title + " as CSV")
        export_button.setToolTip("Export the full table with unrounded numeric values.")
        action_row.addWidget(export_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        table = QTableWidget(len(rows), len(headers), layout.parentWidget())
        table.setObjectName(object_name)
        table.setAccessibleName(title)
        table.setAccessibleDescription(
            context
            + "\n"
            + title
            + ". Use arrow keys to move between cells. Copy selected rows, or "
            "the full table when no rows are selected. Values and unavailable "
            "reasons are taken from the saved authority result."
        )
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(False)
        for row_index, values in enumerate(rows):
            for column, value in enumerate(values):
                display, raw, copy_text, tooltip = _meta_regression_cell(value)
                _set_binary_table_item(
                    table,
                    row_index,
                    column,
                    display,
                    (0, display),
                    raw,
                    tooltip=tooltip,
                    copy_text=copy_text,
                )
        horizontal_header = table.horizontalHeader()
        if horizontal_header is not None:
            horizontal_header.setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )
        vertical_header = table.verticalHeader()
        if vertical_header is not None:
            vertical_header.setVisible(False)
        _fit_result_table_rows(table, minimum_cap=260, visible_rows=7)
        layout.addWidget(table)

        copy_button.clicked.connect(
            lambda _checked=False, result_table=table: self._copy_native_result_table(
                result_table
            )
        )
        export_button.clicked.connect(
            lambda _checked=False, result_table=table, result_title=title: self._export_native_result_table(
                result_table, result_title
            )
        )
        setattr(self, object_name, table)

    @staticmethod
    def _native_result_table_text(table, delimiter="\t", *, selected_rows_only=False):
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")
        writer.writerow(
            [
                table.horizontalHeaderItem(column).text()
                for column in range(table.columnCount())
            ]
        )
        rows = range(table.rowCount())
        if selected_rows_only:
            selection = table.selectionModel()
            selected = (
                {index.row() for index in selection.selectedRows()}
                if selection is not None
                else set()
            )
            if selected:
                rows = (row for row in rows if row in selected)
        for row in rows:
            writer.writerow(
                [
                    table.item(row, column).copy_text()
                    for column in range(table.columnCount())
                ]
            )
        return output.getvalue()

    def _copy_native_result_table(self, table):
        clipboard = QApplication.clipboard()
        if clipboard is None:
            raise RuntimeError("Qt application has no clipboard")
        clipboard.setText(
            self._native_result_table_text(table, selected_rows_only=True)
        )

    def _export_native_result_table(self, table, title):
        file_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export " + title,
            "meta-regression-results.csv",
            "CSV files (*.csv)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"
        with open(file_path, "w", encoding="utf-8", newline="") as output_file:
            output_file.write(self._native_result_table_text(table, delimiter=","))

    def _create_family_results_panel(self, family, numerics):
        panel = QWidget()
        panel.setObjectName("%s_results_panel" % family)
        panel.setAccessibleName("%s analysis results" % family.title())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        context_text = _binary_context_text(self.analysis_context)
        if context_text:
            context = QLabel(context_text, panel)
            context.setAccessibleName("Analysis context")
            context.setWordWrap(True)
            layout.addWidget(context)
        metric = str(numerics["metric"])
        scale = str(numerics["effect_scale"] if family == "continuous" else numerics["display_scale"])
        scale_label = QLabel("Measure: %s; displayed on %s scale." % (metric, scale.replace("_", " ")), panel)
        scale_label.setWordWrap(True)
        layout.addWidget(scale_label)
        pooled = numerics["pooled"]
        estimate = pooled if family == "continuous" else pooled["display"]
        lower_key, upper_key = ("lower_bound", "upper_bound") if family == "continuous" else ("lower", "upper")
        pooled_label = QLabel(
            "Pooled estimate: %s; interval: %s to %s" % (
                _family_numeric_text(estimate["estimate"]),
                _family_numeric_text(estimate[lower_key]),
                _family_numeric_text(estimate[upper_key]),
            ),
            panel,
        )
        pooled_label.setObjectName("%s_pooled_estimate" % family)
        pooled_label.setAccessibleName("Pooled estimate and interval")
        pooled_label.setWordWrap(True)
        pooled_reasons = [
            value.get("reason")
            for value in (
                estimate["estimate"],
                estimate[lower_key],
                estimate[upper_key],
            )
            if isinstance(value, Mapping) and value.get("reason")
        ]
        if pooled_reasons:
            pooled_accessible_reason = "\n".join(
                str(reason) for reason in pooled_reasons
            )
            pooled_label.setToolTip(pooled_accessible_reason)
            pooled_label.setAccessibleDescription(pooled_accessible_reason)
        layout.addWidget(pooled_label)

        action_row = QHBoxLayout()
        copy_button = QPushButton("Copy table", panel)
        copy_button.setAccessibleName("Copy %s study results" % family)
        copy_button.setToolTip(
            "Copy selected rows, or the full table when no rows are selected, "
            "with unrounded numeric values."
        )
        copy_button.clicked.connect(self._copy_binary_study_table)
        action_row.addWidget(copy_button)
        export_button = QPushButton("Export CSV", panel)
        export_button.setAccessibleName("Export %s study results" % family)
        export_button.setToolTip(
            "Export the full study table with unrounded numeric values."
        )
        export_button.clicked.connect(self._export_binary_study_table)
        action_row.addWidget(export_button)
        if self._edit_copy_spec is not None:
            edit_copy_button = QPushButton("Edit a copy", panel)
            edit_copy_button.setAccessibleName("Edit a copy of this analysis")
            edit_copy_button.clicked.connect(
                lambda _checked=False: self.edit_copy_requested.emit(self._edit_copy_spec)
            )
            action_row.addWidget(edit_copy_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        if family == "continuous":
            headers = ("Study", "Source", "Estimate", "Standard error", "Arm 1 n", "Arm 1 mean", "Arm 1 SD", "Arm 2 n", "Arm 2 mean", "Arm 2 SD")
        else:
            headers = ("Study", "TP", "FN", "FP", "TN", "Estimate", "Lower bound", "Upper bound", "Weight")
        studies = numerics["studies"]
        table = QTableWidget(len(studies), len(headers), panel)
        table.setObjectName("%s_study_table" % family)
        table.setAccessibleName("%s study results" % family.title())
        table.setAccessibleDescription(
            "Study values and missing-value reasons on the named effect scale. "
            "Use arrow keys to move between cells. Copy selected rows, or the "
            "full table when no rows are selected."
        )
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(False)
        for row_index, study in enumerate(studies):
            if family == "continuous":
                first = study["arm_1"] or {}
                second = study["arm_2"] or {}
                values = (study["label"], study["provenance"], study["estimate"], study["standard_error"], first.get("sample_size"), first.get("mean"), first.get("standard_deviation"), second.get("sample_size"), second.get("mean"), second.get("standard_deviation"))
            else:
                display = study["display"]
                values = (study["label"], study["tp"], study["fn"], study["fp"], study["tn"], display["estimate"], display["lower"], display["upper"], study["weight_fraction"])
            for column, value in enumerate(values):
                raw = _family_numeric_text(value)
                _set_binary_table_item(
                    table,
                    row_index,
                    column,
                    raw,
                    raw,
                    raw,
                    tooltip=_numeric_accessible_description(value),
                )
        header = table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        vertical_header = table.verticalHeader()
        if vertical_header is not None:
            vertical_header.setVisible(False)
        table.setSortingEnabled(True)
        _fit_result_table_rows(table)
        layout.addWidget(table)
        self.binary_study_table = table
        self._study_table_family = family
        return panel

    def _create_binary_proportion_panel(
        self, numerics: BinaryProportionNumerics
    ) -> QWidget:
        panel = QWidget()
        panel.setObjectName("binary_proportion_results_panel")
        panel.setAccessibleName("One-arm binary results")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        context_text = _binary_context_text(self.analysis_context)
        if context_text:
            context_label = QLabel(context_text, panel)
            context_label.setWordWrap(True)
            layout.addWidget(context_label)
        metric = BINARY_METRIC_NAMES.get(numerics.metric, numerics.metric)
        description = QLabel(
            "%s proportion for %s. Calculations: %s scale."
            % (metric, numerics.arm_label, numerics.calculation_scale.replace("_", " ")),
            panel,
        )
        description.setObjectName("binary_proportion_metric")
        description.setWordWrap(True)
        layout.addWidget(description)

        pooled = numerics.pooled
        pooled_label = QLabel(
            "Pooled proportion: %s; interval: %s to %s; included studies: %s"
            % (
                _binary_numeric_text(pooled.display.estimate, _format_metric),
                _binary_numeric_text(pooled.display.lower, _format_metric),
                _binary_numeric_text(pooled.display.upper, _format_metric),
                _binary_numeric_text(pooled.study_count, _format_count),
            ),
            panel,
        )
        pooled_label.setObjectName("binary_proportion_pooled_estimate")
        pooled_label.setAccessibleName("Pooled proportion and interval")
        pooled_label.setWordWrap(True)
        layout.addWidget(pooled_label)

        action_row = QHBoxLayout()
        copy_button = QPushButton("Copy table", panel)
        copy_button.setAccessibleName("Copy one-arm study table")
        copy_button.setToolTip(
            "Copy selected rows, or the full table when no rows are selected, "
            "with unrounded numeric values."
        )
        copy_button.clicked.connect(self._copy_binary_study_table)
        action_row.addWidget(copy_button)
        export_button = QPushButton("Export CSV", panel)
        export_button.setAccessibleName("Export one-arm study table")
        export_button.setToolTip("Export the full study table with unrounded numeric values.")
        export_button.clicked.connect(self._export_binary_study_table)
        action_row.addWidget(export_button)
        if self._edit_copy_spec is not None:
            edit_copy_button = QPushButton("Edit a copy", panel)
            edit_copy_button.setAccessibleName("Edit a copy of this analysis")
            edit_copy_button.clicked.connect(
                lambda _checked=False: self.edit_copy_requested.emit(
                    self._edit_copy_spec
                )
            )
            action_row.addWidget(edit_copy_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        headers = (
            "Study",
            "%s events" % numerics.arm_label,
            "%s total" % numerics.arm_label,
            "Proportion (%s)" % metric,
            "Lower bound",
            "Upper bound",
        )
        table = QTableWidget(len(numerics.studies), len(headers), panel)
        table.setObjectName("binary_proportion_study_table")
        table.setAccessibleName("One-arm proportion study results")
        table.setAccessibleDescription(
            "Per-study population counts, proportion estimates, and intervals. "
            "Use arrow keys to move between cells. Copy selected rows, or the "
            "full table when no rows are selected."
        )
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setAlternatingRowColors(True)
        vertical_header = table.verticalHeader()
        horizontal_header = table.horizontalHeader()
        if vertical_header is None or horizontal_header is None:
            raise RuntimeError("One-arm study table is missing its headers")
        vertical_header.setVisible(False)
        horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.setSortingEnabled(False)
        for row, study in enumerate(numerics.studies):
            _set_binary_table_item(table, row, 0, study.label, study.label, study.label)
            for column, value, formatter in (
                (1, study.events, _format_count),
                (2, study.total, _format_count),
                (3, study.display.estimate, _format_metric),
                (4, study.display.lower, _format_metric),
                (5, study.display.upper, _format_metric),
            ):
                _set_binary_numeric_cell(table, row, column, value, formatter)
        horizontal_header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        table.setSortingEnabled(True)
        _fit_result_table_rows(table)
        layout.addWidget(table)
        self.binary_study_table = table
        self._study_table_family = "binary"
        return panel

    def _create_binary_results_panel(self, numerics: BinaryNumerics) -> QWidget:
        panel = QWidget()
        panel.setObjectName("binary_results_panel")
        panel.setAccessibleName("Typed binary results")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        context_text = _binary_context_text(self.analysis_context)
        if context_text:
            context_label = QLabel(context_text, panel)
            context_label.setObjectName("binary_result_context")
            context_label.setAccessibleName("Analysis context")
            context_label.setWordWrap(True)
            layout.addWidget(context_label)

        metric_name = BINARY_METRIC_NAMES.get(numerics.metric, numerics.metric)
        scale_text = "%s scale, null = %s" % (
            numerics.display_scale.replace("_", " "),
            _raw_number_text(numerics.display_null_value),
        )
        calculation_text = "%s scale, null = %s" % (
            numerics.calculation_scale.replace("_", " "),
            _raw_number_text(numerics.calculation_null_value),
        )
        metric_label = QLabel(
            "Measure: %s (%s). Calculations: %s."
            % (metric_name, scale_text, calculation_text),
            panel,
        )
        metric_label.setObjectName("binary_result_metric")
        metric_label.setAccessibleName("Binary measure and scale")
        metric_label.setWordWrap(True)
        layout.addWidget(metric_label)

        pooled = numerics.pooled
        pooled_label = QLabel(
            "Pooled estimate: %s; interval: %s to %s"
            % (
                _binary_numeric_text(pooled.display.estimate, _format_metric),
                _binary_numeric_text(pooled.display.lower, _format_metric),
                _binary_numeric_text(pooled.display.upper, _format_metric),
            ),
            panel,
        )
        pooled_label.setObjectName("binary_pooled_estimate")
        pooled_label.setAccessibleName("Pooled estimate and interval")
        pooled_label.setWordWrap(True)
        pooled_reasons = [
            value.reason
            for value in (
                pooled.display.estimate,
                pooled.display.lower,
                pooled.display.upper,
            )
            if value.reason
        ]
        if pooled_reasons:
            pooled_label.setToolTip("\n".join(pooled_reasons))
        layout.addWidget(pooled_label)

        count_label = QLabel(
            "Included studies: %s"
            % _binary_numeric_text(pooled.study_count, _format_count),
            panel,
        )
        count_label.setObjectName("binary_study_count")
        count_label.setAccessibleName("Included study count")
        count_label.setWordWrap(True)
        if pooled.study_count.reason:
            count_label.setToolTip(pooled.study_count.reason)
        layout.addWidget(count_label)

        action_row = QHBoxLayout()
        copy_button = QPushButton("Copy table", panel)
        copy_button.setAccessibleName("Copy binary study table")
        copy_button.setToolTip(
            "Copy selected rows, or the full table when no rows are selected, "
            "with unrounded numeric values."
        )
        copy_button.clicked.connect(self._copy_binary_study_table)
        action_row.addWidget(copy_button)

        export_button = QPushButton("Export CSV", panel)
        export_button.setAccessibleName("Export binary study table")
        export_button.setToolTip("Export the full study table with unrounded numeric values.")
        export_button.clicked.connect(self._export_binary_study_table)
        action_row.addWidget(export_button)

        if self._edit_copy_spec is not None:
            edit_copy_button = QPushButton("Edit a copy", panel)
            edit_copy_button.setAccessibleName("Edit a copy of this analysis")
            edit_copy_button.setToolTip(
                "Open an editable copy of the analysis inputs and settings."
            )
            edit_copy_button.clicked.connect(
                lambda _checked=False: self.edit_copy_requested.emit(
                    self._edit_copy_spec
                )
            )
            action_row.addWidget(edit_copy_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        display_scale = numerics.display_scale.replace("_", " ")
        headers = (
            "Study",
            "Treatment events",
            "Treatment total",
            "Control events",
            "Control total",
            "%s estimate (%s scale; null = %s)"
            % (
                metric_name,
                display_scale,
                _raw_number_text(numerics.display_null_value),
            ),
            "Lower bound (%s scale)" % display_scale,
            "Upper bound (%s scale)" % display_scale,
            "Weight (%)",
            "P-value",
        )
        table = QTableWidget(len(numerics.studies), len(headers), panel)
        table.setObjectName("binary_study_table")
        table.setAccessibleName("Binary study results")
        table.setAccessibleDescription(
            "Per-study counts, estimates, interval bounds, weights, and p-values. "
            "Use arrow keys to move between cells. Copy selected rows, or the "
            "full table when no rows are selected. Unavailable cells include "
            "their reasons in the cell description."
        )
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setAlternatingRowColors(True)
        vertical_header = table.verticalHeader()
        horizontal_header = table.horizontalHeader()
        if vertical_header is None or horizontal_header is None:
            raise RuntimeError("Binary study table is missing its headers")
        vertical_header.setVisible(False)
        horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.setSortingEnabled(False)
        for row, study in enumerate(numerics.studies):
            _set_binary_table_item(table, row, 0, study.label, study.label, study.label)
            _set_binary_numeric_cell(
                table, row, 1, study.treatment_events, _format_count
            )
            _set_binary_numeric_cell(
                table, row, 2, study.treatment_total, _format_count
            )
            _set_binary_numeric_cell(
                table, row, 3, study.control_events, _format_count
            )
            _set_binary_numeric_cell(
                table, row, 4, study.control_total, _format_count
            )
            _set_binary_numeric_cell(
                table, row, 5, study.display.estimate, _format_metric
            )
            _set_binary_numeric_cell(
                table, row, 6, study.display.lower, _format_metric
            )
            _set_binary_numeric_cell(
                table, row, 7, study.display.upper, _format_metric
            )
            _set_binary_numeric_cell(table, row, 8, study.weight, _format_percent)
            _set_binary_numeric_cell(table, row, 9, study.p_value, _format_probability)
        horizontal_header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        table.setSortingEnabled(True)
        _fit_result_table_rows(table)
        layout.addWidget(table)
        self.binary_study_table = table
        self._study_table_family = "binary"
        return panel

    def _binary_study_table_text(self, delimiter="\t", *, selected_rows_only=False):
        table = self.binary_study_table
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")
        writer.writerow(
            [table.horizontalHeaderItem(column).text() for column in range(table.columnCount())]
        )
        rows = range(table.rowCount())
        if selected_rows_only:
            selection = table.selectionModel()
            selected = set()
            if selection is not None:
                selected = {index.row() for index in selection.selectedRows()}
            if selected:
                rows = (row for row in rows if row in selected)
        for row in rows:
            writer.writerow(
                [table.item(row, column).copy_text() for column in range(table.columnCount())]
            )
        return output.getvalue()

    def _copy_binary_study_table(self):
        clipboard = QApplication.clipboard()
        if clipboard is None:
            raise RuntimeError("Qt application has no clipboard")
        clipboard.setText(self._binary_study_table_text(selected_rows_only=True))

    def _export_binary_study_table(self):
        family = getattr(self, "_study_table_family", "binary")
        file_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export %s study results" % family,
            "%s-results.csv" % family,
            "CSV files (*.csv)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"
        with open(file_path, "w", encoding="utf-8", newline="") as output_file:
            output_file.write(self._binary_study_table_text(delimiter=","))

    def add_image_section(self, title, display_title, image):
        params_path = None
        if self.params_paths is not None and title in self.params_paths:
            params_path = self.params_paths[title]

        artifact = self.create_plot_artifact(title, image, params_path=params_path)
        qt_item = self.add_title(display_title)
        figure_description = (
            "Figure. %s plot. Use the figure actions for supported zoom, copy, "
            "edit, and export commands." % artifact.plot_kind.replace("_", " ")
        )
        cumulative_caption = None
        if (
            artifact.plot_kind == "cumulative_forest"
            and self.results.cumulative_numerics is not None
        ):
            cumulative_caption = _cumulative_figure_caption(
                self.results.cumulative_numerics
            )
            figure_description += "\n" + cumulative_caption
            _caption_rect, _caption_position = self.create_text_item(
                cumulative_caption, self.position(), wrap=True
            )
            caption_item = self._layout_items[-1]
            caption_item.setData(
                int(Qt.ItemDataRole.AccessibleDescriptionRole),
                "Cumulative sequence figure caption with each added study, ordering value, "
                "included count, and authority estimate.",
            )
            caption_item.setToolTip(figure_description)
        qt_item.setData(
            0,
            Qt.ItemDataRole.AccessibleDescriptionRole,
            figure_description,
        )
        qt_item.setToolTip(0, figure_description)
        if artifact.can_display():
            try:
                _img_shape, pos, plot_item = self.create_plot_item(
                    artifact, self.position()
                )
            except (OSError, ValueError):
                self._add_unavailable_plot_slot(qt_item, display_title, artifact)
                return
            toolbar = self._create_plot_action_bar(artifact, plot_item)
            # Keep controls next to their figure in scene and keyboard order.
            self._layout_items.remove(toolbar)
            plot_index = self._layout_items.index(plot_item)
            self._layout_items.insert(plot_index, toolbar)
            self.items_to_coords[id(qt_item)] = pos
            self._nav_items_to_sections[id(qt_item)] = plot_item
            self._nav_items_to_focus_targets[id(qt_item)] = toolbar
        else:
            self._add_unavailable_plot_slot(qt_item, display_title, artifact)

    def _add_unavailable_plot_slot(self, nav_item, display_title, artifact):
        message = SelectableResultsTextItem(
            "%s could not be displayed.\nThe numerical results are still available."
            % display_title,
            self,
        )
        message.setData(
            int(Qt.ItemDataRole.AccessibleDescriptionRole),
            "The stored figure is missing or unreadable. Numerical results remain available.",
        )
        message.setToolTip(
            "The stored figure is missing or unreadable. The numerical results are still available."
        )
        message.setTextWidth(self._text_wrap_width())
        message.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.scene.addItem(message)
        self._wrapped_text_items.append(message)
        self._layout_items.append(message)
        figure_details = nav_item.data(
            0, Qt.ItemDataRole.AccessibleDescriptionRole
        )
        unavailable = "Stored figure unavailable. The numerical results are still available."
        description = (
            unavailable + "\n" + str(figure_details)
            if figure_details
            else unavailable
        )
        nav_item.setToolTip(0, description)
        nav_item.setData(
            0,
            Qt.ItemDataRole.AccessibleDescriptionRole,
            description,
        )
        self._nav_items_to_sections[id(nav_item)] = message
        toolbar = self._create_missing_plot_action_bar(artifact, message, nav_item)
        self._nav_items_to_focus_targets[id(nav_item)] = toolbar or message
        self._missing_plot_slots[artifact.title] = (message, toolbar, nav_item)
        self.items_to_coords[id(nav_item)] = message.scenePos()

    def create_plot_artifact(self, title, image_path, params_path=None):
        return PlotArtifact(
            title,
            image_path,
            self.plot_capabilities[title],
            params_path=params_path,
            display_path=self.display_images.get(title),
        )

    def add_text_section(self, title, display_title, text):
        qt_item = self.add_title(display_title)
        qt_item.setData(
            0,
            Qt.ItemDataRole.AccessibleDescriptionRole,
            str(text).strip() or "This result section is empty.",
        )
        _, pos = self.create_text_item(str(text), self.position(), wrap=True)
        self.items_to_coords[id(qt_item)] = pos
        self._nav_items_to_sections[id(qt_item)] = self._layout_items[-1]
        self._nav_items_to_focus_targets[id(qt_item)] = self._layout_items[-1]

    def generate_pixmap(self, image):
        # now the image
        pixmap = QPixmap(image)
        if pixmap.isNull():
            return pixmap

        logical_width, logical_height = _pixmap_device_independent_size(pixmap)
        scaled_width, scaled_height = self._fit_size_to_viewport(
            logical_width, logical_height
        )

        if scaled_width > self.scene.width():
            # layout-audit: allow=intrinsic-ratio; reason=scene follows its intrinsic-ratio visual artifact
            self.scene.setSceneRect(
                0, 0, scaled_width + horizontal_padding, self.scene.height()
            )

        dpr = max(1.0, float(pixmap.devicePixelRatioF()))
        pixmap = pixmap.scaled(
            max(1, logical_extent_to_physical_pixels(scaled_width, dpr)),
            max(1, logical_extent_to_physical_pixels(scaled_height, dpr)),
            transformMode=Qt.TransformationMode.SmoothTransformation,
        )
        pixmap.setDevicePixelRatio(dpr)

        return pixmap

    def _fit_size_to_viewport(self, width, height, max_scale=1.0):
        if width <= 0 or height <= 0:
            return (width, height)

        viewport_width = self._plot_viewport_width()
        scale = min(max_scale, float(viewport_width) / float(width))
        return (max(1.0, float(width) * scale), max(1.0, float(height) * scale))

    def _fit_vector_plot_to_viewport(self, svg_item):
        """Fit one SVG item to the current viewport while preserving its ratio."""
        item_width = svg_item.boundingRect().width()
        item_height = svg_item.boundingRect().height()
        if not self.isVisible():
            return item_width, item_height

        mode = self._plot_zoom_modes.get(id(svg_item), "fit")
        if mode == "actual":
            target_scale = 1.0
        elif mode == "custom":
            target_scale = self._plot_zoom_values.get(id(svg_item), 1.0)
        else:
            scaled_width, _scaled_height = self._fit_size_to_viewport(
                item_width,
                item_height,
                max_scale=MAX_VECTOR_PLOT_SCALE,
            )
            target_scale = float(scaled_width) / float(item_width) if item_width else 1.0
        scaled_width = item_width * target_scale
        scaled_height = item_height * target_scale
        if item_width <= 0:
            return scaled_width, scaled_height

        if abs(target_scale - svg_item.scale()) >= 0.001:
            svg_item.setScale(target_scale)
        self._sync_plot_zoom_control(svg_item, target_scale)
        return scaled_width, scaled_height

    def _plot_viewport_width(self):
        viewport_width = self._layout_viewport_width()
        return max(1, viewport_width - self.x_coord - padding)

    def _layout_viewport_width(self):
        if self._viewport_width_override is not None:
            return self._viewport_width_override
        viewport = self.graphics_view.viewport()
        if viewport is None:
            raise RuntimeError("Results graphics view has no viewport")
        viewport_width = viewport.width()
        if viewport_width <= horizontal_padding:
            viewport_width = self.graphics_view.width()
        if viewport_width <= horizontal_padding:
            viewport_width = max(self.results_nav_splitter.width(), self.width())
        return viewport_width

    def add_references(self):
        if self.references_text is None:
            return

        qt_item = self.add_title("References")
        qt_item.setData(
            0,
            Qt.ItemDataRole.AccessibleDescriptionRole,
            str(self.references_text).strip() or "No references are available.",
        )
        text_item_rect, pos = self.create_text_item(
            str(self.references_text), self.position(), wrap=True
        )
        self.items_to_coords[id(qt_item)] = pos
        self._nav_items_to_sections[id(qt_item)] = self._layout_items[-1]
        self._nav_items_to_focus_targets[id(qt_item)] = self._layout_items[-1]

    def add_title(self, title):
        text = QGraphicsTextItem(str(title))
        title_font = QFont(self.font())
        title_font.setBold(True)
        text.setFont(title_font)
        document = text.document()
        if document is None:
            raise RuntimeError("Results title has no text document")
        text_option = document.defaultTextOption()
        text_option.setWrapMode(QTextOption.WrapMode.WordWrap)
        document.setDefaultTextOption(text_option)
        text.setTextWidth(self._text_wrap_width())
        self._wrapped_text_items.append(text)
        self.scene.addItem(text)
        self._layout_items.append(text)
        qt_item = QTreeWidgetItem(self.nav_tree, [title])
        # layout-audit: allow=intrinsic-ratio; reason=scene follows its intrinsic-ratio visual artifact
        self.scene.setSceneRect(
            0,
            0,
            self.scene.width(),
            self.y_coord + text.boundingRect().height() + padding,
        )
        text.setPos(self.position())
        self.y_coord += text.boundingRect().height()
        qt_item.setData(
            0,
            Qt.ItemDataRole.AccessibleDescriptionRole,
            "Navigate to the %s section in results content." % title,
        )
        return qt_item

    def _advance_past_text_item(self, txt_item, text):
        bounding_height = txt_item.boundingRect().height()
        document = txt_item.document()
        if document is None:
            raise RuntimeError("Results text item has no text document")
        document_height = document.size().height()
        line_count = max(1, str(text).count("\n") + 1)
        font_metrics = QFontMetricsF(txt_item.font())
        line_height = (
            line_count * font_metrics.lineSpacing() + 2 * document.documentMargin()
        )
        return max(bounding_height, document_height, line_height)

    def _navigation_item_changed(self, item, _previous_item):
        if item is None:
            return
        position = self.items_to_coords.get(id(item))
        if position is not None:
            self.graphics_view.centerOn(position)

    def _activate_navigation_item(self, item, _column):
        if item is None:
            return
        self._navigation_item_changed(item, None)
        target = self._nav_items_to_focus_targets.get(id(item))
        if target is None:
            return
        if isinstance(target, QGraphicsProxyWidget):
            widget = target.widget()
            if widget is not None:
                for child in widget.findChildren(QWidget):
                    if (
                        child.isEnabled()
                        and child.isVisible()
                        and child.focusPolicy() & Qt.FocusPolicy.TabFocus
                    ):
                        child.setFocus(Qt.FocusReason.TabFocusReason)
                        if child.hasFocus():
                            return
            target.setFocus(Qt.FocusReason.TabFocusReason)
            return
        self.graphics_view.setFocus(Qt.FocusReason.OtherFocusReason)
        self.scene.setFocusItem(target)

    def create_text_item(self, text, position, wrap=False):
        txt_item = SelectableResultsTextItem(text, self)
        txt_item.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        if wrap:
            document = txt_item.document()
            if document is None:
                raise RuntimeError("Results text item has no text document")
            text_option = document.defaultTextOption()
            text_option.setWrapMode(QTextOption.WrapMode.WordWrap)
            document.setDefaultTextOption(text_option)
            txt_item.setTextWidth(self._text_wrap_width())
            self._wrapped_text_items.append(txt_item)
        txt_item.setToolTip(
            "To copy the text:\n"
            "1) Right click on the text and choose select all.\n"
            "2) Right click again and choose copy."
        )
        txt_item.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.scene.addItem(txt_item)
        self._layout_items.append(txt_item)
        text_height = self._advance_past_text_item(txt_item, text)
        # layout-audit: allow=intrinsic-ratio; reason=scene follows its intrinsic-ratio visual artifact
        self.scene.setSceneRect(
            0,
            0,
            max(self.scene.width(), txt_item.boundingRect().size().width()),
            self.y_coord + text_height + SECTION_SPACING + padding,
        )

        self.y_coord += text_height + SECTION_SPACING
        txt_item.setPos(position)

        return (txt_item.boundingRect(), position)

    def _show_text_context_menu(self, text_item, event):
        if self._active_text_context_menu is not None:
            event.accept()
            return

        context_menu = QMenu(self)
        self._active_text_context_menu = context_menu

        select_all_action = QAction("Select All", self)
        select_all_action.triggered.connect(
            app_error_handler.safe_slot(
                lambda _checked=False: self._select_all_text(text_item), parent=self
            )
        )
        context_menu.addAction(select_all_action)

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(
            app_error_handler.safe_slot(
                lambda _checked=False: self._copy_text_selection(text_item),
                parent=self,
            )
        )
        context_menu.addAction(copy_action)

        shown = app_error_handler.popup_context_menu(
            context_menu, event.screenPos(), parent=self, event=event
        )
        if shown:
            context_menu.aboutToHide.connect(self._clear_text_context_menu)
        else:
            self._clear_text_context_menu()

    def _clear_text_context_menu(self):
        self._active_text_context_menu = None

    def _select_all_text(self, text_item):
        cursor = text_item.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        text_item.setTextCursor(cursor)

    def _copy_text_selection(self, text_item):
        selected_text = text_item.textCursor().selectedText()
        if selected_text:
            clipboard = QApplication.clipboard()
            if clipboard is None:
                raise RuntimeError("Qt application has no clipboard")
            clipboard.setText(selected_text.replace("\u2029", "\n"))

    def _text_wrap_width(self):
        viewport_width = self._layout_viewport_width()
        return max(1, viewport_width - self.x_coord - padding)

    def _update_wrapped_text_widths(self):
        if not self._wrapped_text_items:
            return

        wrap_width = self._text_wrap_width()
        scene_width = self.scene.width()
        scene_height = self.scene.height()
        for txt_item in self._wrapped_text_items:
            txt_item.setTextWidth(wrap_width)
            scene_rect = txt_item.sceneBoundingRect()
            scene_width = max(scene_width, scene_rect.right() + padding)
            scene_height = max(scene_height, scene_rect.bottom() + padding)
        # layout-audit: allow=intrinsic-ratio; reason=scene follows its intrinsic-ratio visual artifact
        self.scene.setSceneRect(0, 0, scene_width, scene_height)

    def _refit_viewport_items(self):
        self._update_wrapped_text_widths()
        self._refit_svg_plot_items()
        self._refit_raster_plot_items()
        self._relayout_sections()

    def _schedule_viewport_refit(self):
        if self._viewport_refit_pending:
            return
        self._viewport_refit_pending = True
        QTimer.singleShot(0, self._run_scheduled_viewport_refit)

    def _run_scheduled_viewport_refit(self):
        self._viewport_refit_pending = False
        if self.isVisible():
            if self._first_show_refit_pending:
                self._first_show_refit_pending = False
                self._set_restored_splitter_sizes()
                self._viewport_width_override = self._layout_viewport_width()
            try:
                self._refit_viewport_items()
                self._relayout_sections()
            finally:
                self._viewport_width_override = None

    def eventFilter(  # ty: ignore[invalid-method-override] -- PyQt6 generated-form multiple inheritance
        self, watched: QObject | None, event: QEvent | None
    ) -> bool:
        if (
            watched in (self.nav_tree, self.nav_tree.viewport())
            and isinstance(event, QKeyEvent)
            and event.type() == QEvent.Type.KeyPress
            and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
        ):
            self._activate_navigation_item(self.nav_tree.currentItem(), 0)
            return True
        if (
            event is not None
            and watched is self.graphics_view.viewport()
            and event.type() == QEvent.Type.Resize
        ):
            self._schedule_viewport_refit()
        return super(ResultsWindow, self).eventFilter(watched, event)

    def _refit_svg_plot_items(self):
        if self._refitting_svg_plots:
            return

        self._refitting_svg_plots = True
        try:
            for item in self._svg_plot_items:
                item_width = item.boundingRect().width()
                if item_width <= 0:
                    continue

                self._fit_vector_plot_to_viewport(item)
        finally:
            self._refitting_svg_plots = False

    def _refit_raster_plot_items(self):
        for item in self._raster_plot_items:
            self._refit_raster_plot_item(item)

    def _refit_raster_plot_item(self, item):
        source = item.source_pixmap
        if source.isNull():
            return
        mode = self._plot_zoom_modes.get(id(item), "fit")
        if mode == "actual":
            scale = 1.0
        elif mode == "custom":
            scale = self._plot_zoom_values.get(id(item), 1.0)
        else:
            logical_width, _logical_height = _pixmap_device_independent_size(source)
            scaled_width, _scaled_height = self._fit_size_to_viewport(
                logical_width, _logical_height
            )
            scale = float(scaled_width) / float(logical_width)
        item.setPixmap(source)
        item.setScale(scale)
        self._sync_plot_zoom_control(item, scale)

    def _relayout_sections(self):
        """Place every result item from its current measured size and stored order."""
        next_y = float(self.add_offset)
        for item in self._layout_items:
            item.setPos(self.x_coord, next_y)
            if isinstance(item, SelectableResultsTextItem):
                item_height = self._advance_past_text_item(item, item.toPlainText())
            else:
                item_height = item.sceneBoundingRect().height()
            next_y += item_height
            if not isinstance(item, QGraphicsTextItem) or isinstance(
                item, SelectableResultsTextItem
            ):
                next_y += SECTION_SPACING

        self.y_coord = next_y
        for nav_item_id, section_item in self._nav_items_to_sections.items():
            self.items_to_coords[nav_item_id] = section_item.scenePos()

        scene_bounds = self.scene.itemsBoundingRect()
        # layout-audit: allow=intrinsic-ratio; reason=scene follows its intrinsic-ratio visual artifact
        self.scene.setSceneRect(
            0,
            0,
            max(self._viewport_width(), scene_bounds.right() + padding),
            max(1, scene_bounds.bottom() + padding),
        )

    def showEvent(  # ty: ignore[invalid-method-override] -- PyQt6 generated-form multiple inheritance
        self, event: QShowEvent | None
    ) -> None:
        super(ResultsWindow, self).showEvent(event)
        self._schedule_viewport_refit()

    def _apply_restored_splitter_proportions(self):
        if not self._splitter_restore_pending:
            return
        self._splitter_restore_pending = False
        self._set_restored_splitter_sizes()
        # QSplitter applies child geometry lazily on some Qt platforms.  Refresh
        # it now so the one queued refit observes the final viewport dimensions.
        self.results_nav_splitter.refresh()
        self._schedule_viewport_refit()

    def _set_restored_splitter_sizes(self):
        splitter_extent = max(2, self.results_nav_splitter.width())
        self.results_nav_splitter.setSizes(
            [
                max(1, int(splitter_extent * value))
                for value in self._restored_splitter_proportions
            ]
        )

    def resizeEvent(  # ty: ignore[invalid-method-override] -- PyQt6 generated-form multiple inheritance
        self, event: QResizeEvent | None
    ) -> None:
        super(ResultsWindow, self).resizeEvent(event)
        self._schedule_viewport_refit()

    def closeEvent(  # ty: ignore[invalid-method-override] -- PyQt6 generated-form multiple inheritance
        self, event: QCloseEvent | None
    ) -> None:
        save_results_window_state(self)
        super(ResultsWindow, self).closeEvent(event)

    def create_pixmap_item(
        self, pixmap, position, title, image_path, params_path=None, matrix=QTransform()
    ):
        artifact = self.create_plot_artifact(title, image_path, params_path=params_path)
        item = ResponsivePixmapItem(QPixmap(image_path))
        item.setPixmap(pixmap)
        item.setToolTip(
            'To save the image:\nright-click on the image and choose "save image as".'
        )

        self.y_coord += item.boundingRect().size().height() + SECTION_SPACING
        #        item.setFlags(QGraphicsItem.ItemIsSelectable|
        #                      QGraphicsItem.ItemIsMovable)
        item.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        # layout-audit: allow=intrinsic-ratio; reason=scene follows its intrinsic-ratio visual artifact
        self.scene.setSceneRect(
            0,
            0,
            max(self.scene.width(), item.boundingRect().size().width()),
            self.y_coord + item.boundingRect().size().height() + padding,
        )

        self.scene.clearSelection()
        self.scene.addItem(item)
        self._raster_plot_items.append(item)
        self._layout_items.append(item)
        item.setPos(position)

        # attach event handler for mouse-clicks, i.e., to handle
        # user right-clicks
        item.contextMenuEvent = self._make_context_menu(artifact, item)

        return (item.boundingRect().size(), position, item)

    def create_plot_item(self, artifact, position):
        if artifact.has_vector_display():
            svg_item = self.create_svg_item(artifact, position)
            if svg_item is not None:
                return svg_item

        pixmap = self.generate_pixmap(artifact.image_path)
        return self.create_pixmap_item(
            pixmap,
            position,
            artifact.title,
            artifact.image_path,
            params_path=artifact.params_path,
        )

    def create_svg_item(self, artifact, position):
        renderer = _opaque_svg_renderer(artifact.display_path(), self)
        if not renderer.isValid():
            return None
        item = _svg_item_class()()
        item.setSharedRenderer(renderer)

        item.setToolTip(
            'To save the image:\nright-click on the image and choose "save image as".'
        )
        item.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        scaled_width, scaled_height = self._fit_vector_plot_to_viewport(item)

        self.y_coord += scaled_height + SECTION_SPACING
        # layout-audit: allow=intrinsic-ratio; reason=scene follows its intrinsic-ratio visual artifact
        self.scene.setSceneRect(
            0,
            0,
            max(self.scene.width(), scaled_width),
            self.y_coord + scaled_height + padding,
        )

        self.scene.clearSelection()
        self.scene.addItem(item)
        self._svg_plot_items.append(item)
        self._layout_items.append(item)
        item.setPos(position)
        item.contextMenuEvent = self._make_context_menu(artifact, item)

        return (item.boundingRect().size(), position, item)

    def _create_plot_action_bar(self, artifact, plot_item):
        widget = QWidget()
        widget.setAccessibleName("Figure actions for %s" % artifact.title)
        description = "Fit or zoom the figure, copy it, or export a supported format."
        if self.worker_client is not None and artifact.can_edit():
            description += " Edit appearance through the isolated analysis worker."
        widget.setAccessibleDescription(description)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        fit_button = self._figure_button(
            "Fit width", "Fit the figure to the available content width."
        )
        fit_button.clicked.connect(
            app_error_handler.safe_slot(
                lambda: self._set_plot_zoom(plot_item, "fit"), parent=self
            )
        )
        layout.addWidget(fit_button)

        actual_button = self._figure_button(
            "Actual size", "Show the figure at its original size."
        )
        actual_button.clicked.connect(
            app_error_handler.safe_slot(
                lambda: self._set_plot_zoom(plot_item, "actual"), parent=self
            )
        )
        layout.addWidget(actual_button)

        zoom_label = QLabel("Zoom", widget)
        zoom = QSlider(Qt.Orientation.Horizontal, widget)
        zoom.setRange(25, int(MAX_VECTOR_PLOT_SCALE * 100))
        zoom.setSingleStep(25)
        zoom.setPageStep(50)
        # layout-audit: allow=semantic-slider-control; reason=Reserve room for the visible zoom scale labels.
        zoom.setFixedWidth(115)
        zoom.setAccessibleName("Figure zoom")
        zoom.setAccessibleDescription(
            "Set the figure size from 25 percent to 400 percent of its original size."
        )
        zoom.setToolTip(zoom.accessibleDescription())
        zoom_label.setBuddy(zoom)
        self._plot_zoom_controls[id(plot_item)] = zoom
        zoom.valueChanged.connect(
            app_error_handler.safe_slot(
                lambda value: self._set_plot_zoom(
                    plot_item, "custom", float(value) / 100.0
                ),
                parent=self,
            )
        )
        self._sync_plot_zoom_control(plot_item)
        layout.addWidget(zoom_label)
        layout.addWidget(zoom)

        if self.worker_client is not None and artifact.can_edit():
            edit_button = self._figure_button(
                "Edit appearance",
                "Editing requires a compatible R statistical engine. A failed edit keeps the last saved figure.",
            )
            edit_button.clicked.connect(
                app_error_handler.safe_slot(
                    lambda: self.edit_plot(artifact, plot_item), parent=self
                )
            )
            layout.addWidget(edit_button)

        copy_button = self._figure_button(
            "Copy image", "Copy the displayed figure to the system clipboard."
        )
        copy_button.clicked.connect(
            app_error_handler.safe_slot(
                lambda: self._copy_plot_image(artifact), parent=self
            )
        )
        layout.addWidget(copy_button)

        self._add_export_button(layout, artifact)
        proxy = self._add_action_widget(widget)
        return proxy

    def _create_missing_plot_action_bar(self, artifact, message, nav_item):
        widget = QWidget()
        widget.setAccessibleName("Actions for unavailable figure %s" % artifact.title)
        widget.setAccessibleDescription(
            "The figure is unavailable. Numerical results remain available."
        )
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        if (
            self.worker_client is not None
            and artifact.can_regenerate()
            and self._can_regenerate_in_place(artifact)
        ):
            regenerate_button = self._figure_button(
                "Regenerate figure",
                "Regenerating this figure requires a compatible R statistical engine. The existing result remains available if regeneration fails.",
            )
            regenerate_button.clicked.connect(
                app_error_handler.safe_slot(
                    lambda: self._regenerate_missing_plot(
                        artifact, message, nav_item
                    ),
                    parent=self,
                )
            )
            layout.addWidget(regenerate_button)

        self._add_export_button(layout, artifact)
        if self.worker_client is not None and artifact.can_regenerate():
            engine_note = QLabel(
                "Regeneration and regenerated exports require a compatible R statistical engine.",
                widget,
            )
            engine_note.setWordWrap(True)
            engine_note.setAccessibleName("Statistical engine requirement")
            layout.addWidget(engine_note)

        if not layout.count():
            widget.deleteLater()
            return None
        return self._add_action_widget(widget)

    @staticmethod
    def _figure_button(text, description):
        button = QPushButton(text)
        button.setAccessibleName(text)
        button.setAccessibleDescription(description)
        button.setToolTip(description)
        return button

    def _add_action_widget(self, widget):
        # layout-audit: allow=content-overflow-control; reason=Bound the embedded result section to the readable text width.
        widget.setMaximumWidth(max(1, int(self._text_wrap_width())))
        proxy = QGraphicsProxyWidget()
        proxy.setWidget(widget)
        proxy.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        proxy.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.scene.addItem(proxy)
        self._layout_items.append(proxy)
        return proxy

    def _add_export_button(self, layout, artifact):
        formats = self._available_export_formats(artifact)
        if not formats:
            return
        button = QToolButton(layout.parentWidget())
        button.setText("Export")
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setAccessibleName("Export figure")
        button.setAccessibleDescription(
            "Export this figure in a format supported by its stored artifact and renderer."
        )
        button.setToolTip(button.accessibleDescription())
        menu = QMenu(button)
        for export_format in formats:
            action = QAction("Save %s Image As" % export_format.label, menu)
            description = PLOT_EXPORT_GUIDANCE[export_format.extension]
            if artifact.requires_engine_for_export(export_format.extension):
                description += " Requires a compatible R statistical engine."
            action.setStatusTip(description)
            action.setToolTip(description)
            action.triggered.connect(
                app_error_handler.safe_slot(
                    lambda _checked=False, selected=export_format: self.save_image_as(
                        artifact, format=selected.extension
                    ),
                    parent=self,
                )
            )
            menu.addAction(action)
        button.setMenu(menu)
        layout.addWidget(button)

    @staticmethod
    def _can_regenerate_in_place(artifact):
        suffix = Path(artifact.image_path).suffix.lower().lstrip(".")
        if suffix == "svg":
            return artifact.can_regenerate()
        try:
            qt_suffix = suffix.encode("ascii")
        except UnicodeEncodeError:
            return False
        supported = (
            bytes(image_format).lower()
            for image_format in QImageReader.supportedImageFormats()
        )
        return artifact.can_regenerate() and qt_suffix in supported

    def _require_plot_worker(self, operation):
        if self.worker_client is None:
            raise RuntimeError(
                "%s requires an isolated analysis worker; in-process R execution "
                "is unavailable." % operation
            )

    def _available_export_formats(self, artifact):
        return tuple(
            export_format
            for export_format in artifact.export_formats()
            if self.worker_client is not None
            or not artifact.requires_engine_for_export(export_format.extension)
        )

    def _regenerate_missing_plot(self, artifact, message, nav_item):
        self._require_plot_worker("Regenerating a figure")
        self._regenerate_missing_plot_in_worker(artifact, message, nav_item)

    def _regenerate_missing_plot_in_worker(self, artifact, message, nav_item):
        target = Path(artifact.image_path)
        extension = target.suffix.lower().lstrip(".")
        if extension not in ("pdf", "png", "tif", "tiff", "svg"):
            self._report_plot_failure(
                artifact,
                {"message": "The stored figure format cannot be regenerated."},
            )
            return

        def completed(result, state):
            candidate = _worker_candidate_file(result, "candidate.image_path")
            candidate_artifact = PlotArtifact(
                artifact.title,
                candidate,
                artifact.capability,
                params_path=artifact.params_path,
                display_path=candidate,
            )
            if not candidate_artifact.can_display():
                raise RuntimeError(
                    "The compatible statistical engine did not create a readable figure."
                )
            PlotService.promote_worker_files(
                state["staging_root"], {candidate: target}
            )
            self._set_plot_artifact_paths(artifact, artifact.image_path, artifact.image_path)
            self._replace_missing_plot(artifact, message, nav_item)

        self._request_worker_plot(
            artifact,
            "plot_export",
            lambda run_id, identity, staging: self.worker_client.request_plot_export(
                run_id,
                artifact_identity=identity,
                regenerator=artifact.capability.regenerator,
                params_path=artifact.params_path,
                staging_dir=staging,
                output_extension=extension,
            ),
            completed,
            label="Regenerating %s" % artifact.title,
        )

    def _replace_missing_plot(self, artifact, message, nav_item):
        refreshed_artifact = self.create_plot_artifact(
            artifact.title,
            artifact.image_path,
            params_path=artifact.params_path,
        )

        slot = self._missing_plot_slots.pop(artifact.title, None)
        if slot is None:
            return
        _old_message, old_toolbar, _old_nav = slot
        old_index = min(
            self._layout_items.index(message),
            self._layout_items.index(old_toolbar)
            if old_toolbar is not None
            else self._layout_items.index(message),
        )
        self._layout_items.remove(message)
        self._wrapped_text_items.remove(message)
        self.scene.removeItem(message)
        if old_toolbar is not None:
            self._layout_items.remove(old_toolbar)
            self.scene.removeItem(old_toolbar)
            old_widget = old_toolbar.widget()
            if old_widget is not None:
                old_widget.deleteLater()
            old_toolbar.deleteLater()

        _size, _position, plot_item = self.create_plot_item(
            refreshed_artifact, self.position()
        )
        toolbar = self._create_plot_action_bar(refreshed_artifact, plot_item)
        self._layout_items.remove(plot_item)
        self._layout_items.remove(toolbar)
        self._layout_items[old_index:old_index] = [toolbar, plot_item]
        self._nav_items_to_sections[id(nav_item)] = plot_item
        self._nav_items_to_focus_targets[id(nav_item)] = toolbar
        nav_item.setToolTip(0, "Figure available")
        nav_item.setData(0, Qt.ItemDataRole.AccessibleDescriptionRole, "Figure available")
        self._relayout_sections()
        self._schedule_viewport_refit()

    def _request_worker_plot(
        self,
        artifact,
        operation,
        dispatch,
        on_result,
        *,
        label,
        on_failure=None,
        dialog=None,
    ):
        client = self.worker_client
        if client is None:
            return False
        if client.is_busy:
            error = {"message": "The statistical engine is busy. Try again when it finishes."}
            if on_failure is not None:
                on_failure(error, None)
            else:
                self._report_plot_failure(artifact, error)
            return False

        staging_root = Path(tempfile.mkdtemp(prefix="rcms-plot-request-"))
        generation = self._plot_generations.get(artifact.title, 0) + 1
        self._plot_generations[artifact.title] = generation
        identity = {
            "analysis_id": self._plot_analysis_id,
            "figure_key": artifact.title,
            "generation": generation,
        }
        run_id = "plot-" + uuid.uuid4().hex
        state = {
            "artifact": artifact,
            "dialog": dialog,
            "identity": identity,
            "label": label,
            "on_failure": on_failure,
            "on_result": on_result,
            "operation": operation,
            "staging_root": str(staging_root),
        }
        self._plot_worker_requests[run_id] = state

        def cleanup_request(response_run_id, *_args):
            if response_run_id != run_id:
                return
            shutil.rmtree(staging_root, ignore_errors=True)
            try:
                client.plotCompleted.disconnect(cleanup_request)
            except (TypeError, RuntimeError):
                pass
            try:
                client.plotFailed.disconnect(cleanup_request)
            except (TypeError, RuntimeError):
                pass

        client.plotCompleted.connect(cleanup_request)
        client.plotFailed.connect(cleanup_request)
        if dialog is not None:
            dialog.finished.connect(
                lambda *_args, run=run_id: self._invalidate_plot_dialog_request(run)
            )
        self._set_plot_status(label)
        try:
            dispatch(run_id, identity, str(staging_root))
        except Exception as error:
            self._plot_worker_requests.pop(run_id, None)
            cleanup_request(run_id)
            if on_failure is not None:
                on_failure({"message": str(error)}, state)
            else:
                self._report_plot_failure(artifact, {"message": str(error)})
            return False
        return True

    def _invalidate_plot_dialog_request(self, run_id):
        state = self._plot_worker_requests.get(run_id)
        if state is None:
            return
        artifact = state["artifact"]
        current = self._plot_generations.get(artifact.title, 0)
        if current == state["identity"]["generation"]:
            self._plot_generations[artifact.title] = current + 1

    def _plot_worker_progress(self, run_id, operation, identity, stage):
        state = self._plot_worker_requests.get(run_id)
        if state is None or state["operation"] != operation or state["identity"] != identity:
            return
        if self._plot_generations.get(state["artifact"].title) != identity.get("generation"):
            return
        self._set_plot_status("%s: %s" % (state["label"], stage))

    def _plot_worker_completed(self, run_id, operation, identity, result):
        self._finish_worker_plot(run_id, operation, identity, result=result)

    def _plot_worker_failed(self, run_id, operation, identity, error):
        self._finish_worker_plot(run_id, operation, identity, error=error)

    def _finish_worker_plot(self, run_id, operation, identity, *, result=None, error=None):
        state = self._plot_worker_requests.pop(run_id, None)
        if state is None:
            return
        try:
            current = (
                state["operation"] == operation
                and state["identity"] == identity
                and self._plot_generations.get(state["artifact"].title)
                == identity.get("generation")
            )
            if not current:
                return
            if error is not None:
                raise RuntimeError(_plot_worker_error_text(error))
            if not isinstance(result, Mapping):
                raise ValueError("The plot worker returned an invalid result")
            state["on_result"](result, state)
        except Exception as failure:
            handler = state["on_failure"]
            if handler is not None:
                handler({"message": str(failure)}, state)
            else:
                self._report_plot_failure(
                    state["artifact"], {"message": str(failure)}
                )
        finally:
            shutil.rmtree(state["staging_root"], ignore_errors=True)
            if self.worker_client is not None and not self.worker_client.is_busy:
                self._set_plot_status(None)

    def _set_plot_status(self, message, timeout=0):
        status_bar = self.statusBar()
        if status_bar is None:
            return
        if message is None:
            status_bar.clearMessage()
        else:
            status_bar.showMessage(message, timeout)

    def _report_plot_failure(self, artifact, error):
        detail = _plot_worker_error_text(error)
        QMessageBox.warning(
            self,
            "Figure Operation Failed",
            "%s was not updated.\n\n%s" % (artifact.title, detail),
        )

    def _request_plot_parameters(self, artifact, on_parameters, *, dialog=None):
        def completed(result, _state):
            params = result.get("params")
            if not isinstance(params, Mapping):
                raise ValueError("The statistical engine returned invalid plot settings")
            on_parameters(dict(params))

        return self._request_worker_plot(
            artifact,
            "plot_parameters",
            lambda run_id, identity, staging: self.worker_client.request_plot_parameters(
                run_id,
                artifact_identity=identity,
                regenerator=artifact.capability.regenerator,
                params_path=artifact.params_path,
                staging_dir=staging,
            ),
            completed,
            label="Loading settings for %s" % artifact.title,
            dialog=dialog,
        )

    def _apply_worker_plot_edits(
        self,
        dialog,
        artifact,
        plot_item,
        regenerator,
        updated_params,
        output_path,
        display_path=None,
    ):
        output_path = str(output_path)
        extension = Path(output_path).suffix.lower().lstrip(".")
        if extension not in ("pdf", "png", "tif", "tiff", "svg"):
            raise ValueError("The edited figure must use PDF, PNG, TIFF, or SVG format")

        def failed(error, _state):
            message = _plot_worker_error_text(error)
            if regenerator == "funnel":
                dialog.mark_commit_failed()
                self._set_plot_status(
                    "%s was not updated: %s" % (artifact.title, message), 10000
                )
            else:
                dialog.mark_commit_failed(message)

        def completed(result, state):
            candidate = result.get("candidate")
            if not isinstance(candidate, Mapping):
                raise ValueError("The statistical engine returned no edited figure")
            image_candidate = _worker_candidate_file(result, "candidate.image_path")
            candidate_display = candidate.get("display_path")
            display_candidate = None
            files = {
                image_candidate: output_path,
                _worker_candidate_file(result, "candidate.params_path"):
                    str(artifact.params_path) + ".params",
            }
            if regenerator != "funnel":
                files[_worker_candidate_file(result, "candidate.plotdata_path")] = (
                    str(artifact.params_path) + ".plotdata"
                )
            if candidate_display is not None:
                if not isinstance(display_path, str) or not display_path:
                    raise ValueError("The edited plot has no display destination")
                display_candidate = _worker_candidate_file(
                    result, "candidate.display_path"
                )
                files[display_candidate] = display_path
            candidate_artifact = PlotArtifact(
                artifact.title,
                image_candidate,
                artifact.capability,
                params_path=artifact.params_path,
                display_path=display_candidate or image_candidate,
            )
            if not candidate_artifact.can_display():
                raise RuntimeError("The statistical engine produced an unreadable figure")
            PlotService.promote_worker_files(state["staging_root"], files)
            self._refresh_plot_item(
                plot_item, artifact, output_path, display_path or output_path
            )
            dialog.mark_commit_succeeded()

        if regenerator == "funnel":
            dialog.mark_commit_failed()
        else:
            dialog.mark_commit_failed("Waiting for the statistical engine…")
        self._request_worker_plot(
            artifact,
            "plot_edit",
            lambda run_id, identity, staging: self.worker_client.edit_plot(
                run_id,
                artifact_identity=identity,
                regenerator=regenerator,
                params_path=artifact.params_path,
                staging_dir=staging,
                updated_params=updated_params,
                output_path=output_path,
                output_extension=extension,
                display_path=display_path,
            ),
            completed,
            label="Updating %s" % artifact.title,
            on_failure=failed,
            dialog=dialog,
        )

    def _set_plot_artifact_paths(self, artifact, image_path, display_path):
        image_path = str(image_path)
        display_path = str(display_path)
        artifact.image_path = image_path
        artifact.display_image_path = display_path
        images = dict(self.images)
        images[artifact.title] = image_path
        display_images = dict(self.display_images)
        display_images[artifact.title] = display_path
        self.display_images = MappingProxyType(display_images)
        self.images = MappingProxyType(images)
        sections = tuple(
            replace(section, value=image_path)
            if section.kind == "image" and section.source_key == artifact.title
            else section
            for section in self.results.sections
        )
        self.results = replace(
            self.results,
            images=self.images,
            display_images=self.display_images,
            sections=sections,
        )

    def _set_plot_zoom(self, plot_item, mode, scale=None):
        if mode == "fit":
            self._plot_zoom_modes[id(plot_item)] = "fit"
        elif mode == "actual":
            self._plot_zoom_modes[id(plot_item)] = "actual"
        else:
            self._plot_zoom_modes[id(plot_item)] = "custom"
            self._plot_zoom_values[id(plot_item)] = max(
                0.25, min(MAX_VECTOR_PLOT_SCALE, float(scale or 1.0))
            )

        if isinstance(plot_item, ResponsivePixmapItem):
            self._refit_raster_plot_item(plot_item)
        else:
            self._fit_vector_plot_to_viewport(plot_item)
        self._relayout_sections()

    def _sync_plot_zoom_control(self, plot_item, scale=None):
        zoom = self._plot_zoom_controls.get(id(plot_item))
        if zoom is None:
            return
        if scale is None:
            mode = self._plot_zoom_modes.get(id(plot_item), "fit")
            if mode == "custom":
                scale = self._plot_zoom_values.get(id(plot_item), 1.0)
            elif mode == "actual":
                scale = 1.0
            elif isinstance(plot_item, ResponsivePixmapItem):
                scale = plot_item.scale()
            else:
                scale = plot_item.scale()
        zoom.blockSignals(True)
        zoom.setValue(max(25, min(400, int(round(float(scale) * 100)))))
        zoom.blockSignals(False)

    def _copy_plot_image(self, artifact):
        image = _image_for_artifact(artifact)
        if image.isNull():
            raise RuntimeError("The stored figure could not be copied.")
        clipboard = QApplication.clipboard()
        if clipboard is None:
            raise RuntimeError("Qt has no system clipboard.")
        clipboard.setImage(image)
        self._set_plot_status("Figure copied to the clipboard.", 3000)

    def _make_context_menu(self, artifact, plot_item):
        def _graphics_item_context_menu(event):
            def add_save_as_menu_action(menu, export_format):
                action = QAction("Save %s Image As" % export_format.label, self)
                guidance = (
                    PLOT_EXPORT_GUIDANCE[export_format.extension]
                    if artifact.requires_engine_for_export(export_format.extension)
                    else "Save the displayed figure using its stored image renderer."
                )
                action.setStatusTip(guidance)
                action.setToolTip(guidance)

                def save_action(_checked=False, selected_format=export_format):
                    self.save_image_as(
                        artifact,
                        format=selected_format.extension,
                    )

                action.triggered.connect(
                    app_error_handler.safe_slot(save_action, parent=self)
                )
                menu.addAction(action)

            context_menu = QMenu(self)
            if self.worker_client is not None and artifact.can_edit():
                action = QAction("Edit Plot", self)
                description = (
                    "Edit plot appearance. A compatible R statistical engine is required."
                )
                action.setStatusTip(description)
                action.setToolTip(description)
                action.setWhatsThis(description)
                action.triggered.connect(
                    app_error_handler.safe_slot(
                        lambda _checked=False: self.edit_plot(artifact, plot_item),
                        parent=self,
                    )
                )
                context_menu.addAction(action)
            for export_format in self._available_export_formats(artifact):
                add_save_as_menu_action(context_menu, export_format)

            app_error_handler.popup_context_menu(
                context_menu, event.screenPos(), parent=self, event=event
            )

        return _graphics_item_context_menu

    def edit_plot(self, artifact, plot_item):
        regenerator = artifact.capability.regenerator
        if regenerator == "forest":
            self._edit_forest_plot(artifact, plot_item)
        elif regenerator == "regression":
            self.edit_regression_plot(artifact, plot_item)
        elif regenerator == "funnel":
            self._edit_funnel_plot(artifact, plot_item)
        elif regenerator == "sroc":
            self._edit_sroc_plot(artifact, plot_item)

    def _load_plot_params_then(self, artifact, on_parameters):
        self._require_plot_worker("Editing a figure")
        return self._request_plot_parameters(artifact, on_parameters)

    def _edit_sroc_plot(self, artifact, plot_item):
        self._load_plot_params_then(
            artifact,
            lambda params: self._show_sroc_plot_editor(artifact, plot_item, params),
        )

    def _show_sroc_plot_editor(self, artifact, plot_item, plot_params):
        dialog = EditPlotDialog(
            plot_params, artifact.image_path, parent=self, plot_type="sroc"
        )
        dialog.applied.connect(
            app_error_handler.safe_slot(
                lambda: self._apply_sroc_plot_edits(dialog, artifact, plot_item),
                parent=self,
            )
        )
        dialog.exec()

    def _apply_sroc_plot_edits(self, dialog, artifact, plot_item):
        self._require_plot_worker("Editing a figure")
        updated_params = dialog.plot_params()
        outpath = updated_params.get("fp_outpath") or artifact.image_path
        self._apply_worker_plot_edits(
            dialog,
            artifact,
            plot_item,
            "sroc",
            updated_params,
            outpath,
            updated_params.get("fp_display_path") or outpath,
        )

    def _edit_funnel_plot(self, artifact, plot_item):
        self._load_plot_params_then(
            artifact,
            lambda params: self._show_funnel_plot_editor(
                artifact, plot_item, params
            ),
        )

    def _show_funnel_plot_editor(self, artifact, plot_item, plot_params):
        dialog = FunnelPlotEditorDialog(
            plot_params, artifact.image_path, parent=self, plot_type=artifact.plot_kind
        )
        dialog.applied.connect(
            app_error_handler.safe_slot(
                lambda: self._apply_funnel_plot_edits(dialog, artifact, plot_item),
                parent=self,
            )
        )
        dialog.exec()

    def _apply_funnel_plot_edits(self, dialog, artifact, plot_item):
        self._require_plot_worker("Editing a figure")
        updated_params = dialog.plot_params()
        outpath = updated_params.get("funnel.outpath") or artifact.image_path
        if str(outpath).lower().endswith(".svgz"):
            raise ValueError(
                "SVGZ output is not supported when editing funnel plots; use SVG instead."
            )
        self._apply_worker_plot_edits(
            dialog, artifact, plot_item, "funnel", updated_params, outpath
        )

    def _edit_forest_plot(self, artifact, plot_item):
        self._load_plot_params_then(
            artifact,
            lambda params: self._show_forest_plot_editor(
                artifact, plot_item, params
            ),
        )

    def _show_forest_plot_editor(self, artifact, plot_item, plot_params):
        dialog = EditPlotDialog(
            plot_params,
            artifact.image_path,
            parent=self,
            plot_type=artifact.plot_kind,
        )
        dialog.applied.connect(
            app_error_handler.safe_slot(
                lambda: self._apply_forest_plot_edits(dialog, artifact, plot_item),
                parent=self,
            )
        )
        dialog.exec()

    def edit_regression_plot(self, artifact, plot_item):
        self._load_plot_params_then(
            artifact,
            lambda params: self._show_regression_plot_editor(
                artifact, plot_item, params
            ),
        )

    def _show_regression_plot_editor(self, artifact, plot_item, plot_params):
        dialog = EditPlotDialog(
            plot_params, artifact.image_path, parent=self, plot_type="regression"
        )
        dialog.applied.connect(
            app_error_handler.safe_slot(
                lambda: self._apply_regression_plot_edits(dialog, artifact, plot_item),
                parent=self,
            )
        )
        dialog.exec()

    def _apply_regression_plot_edits(self, dialog, artifact, plot_item):
        self._require_plot_worker("Editing a figure")
        updated_params = dialog.plot_params()
        outpath = updated_params["bp_outpath"] or artifact.image_path
        self._apply_worker_plot_edits(
            dialog,
            artifact,
            plot_item,
            "regression",
            updated_params,
            outpath,
            updated_params.get("bp_display_path") or outpath,
        )

    def _apply_forest_plot_edits(self, dialog, artifact, plot_item):
        self._require_plot_worker("Editing a figure")
        updated_params = dialog.plot_params()
        outpath = updated_params["fp_outpath"] or artifact.image_path
        self._apply_worker_plot_edits(
            dialog,
            artifact,
            plot_item,
            "forest",
            updated_params,
            outpath,
            updated_params.get("fp_display_path") or outpath,
        )

    def _refresh_plot_item(self, plot_item, artifact, outpath, display_path=None):
        if plot_item is None:
            return

        display_path = display_path or outpath
        refreshed_artifact = PlotArtifact(
            artifact.title,
            outpath,
            artifact.capability,
            params_path=artifact.params_path,
            display_path=display_path,
        )
        if (
            isinstance(plot_item, _svg_item_class())
            and refreshed_artifact.has_vector_display()
        ):
            renderer = _opaque_svg_renderer(refreshed_artifact.display_path(), self)
            if not renderer.isValid():
                return
            plot_item.setSharedRenderer(renderer)
            self._schedule_viewport_refit()
            self.scene.update()
        elif isinstance(plot_item, ResponsivePixmapItem):
            source_pixmap = QPixmap(outpath)
            if source_pixmap.isNull():
                return
            plot_item.replace_source(source_pixmap)
            self._schedule_viewport_refit()
        else:
            return

        self._set_plot_artifact_paths(artifact, outpath, display_path)

    def save_image_as(self, artifact, format=None):
        if not isinstance(artifact, PlotArtifact):
            raise TypeError("A plot artifact is required to export a figure")

        if format not in PLOT_EXPORT_FORMATS_BY_EXTENSION:
            valid_formats = ", ".join(PLOT_EXPORT_FORMATS_BY_EXTENSION.keys())
            raise Exception("Invalid format, needs to be one of: %s!" % valid_formats)

        export_format = PLOT_EXPORT_FORMATS_BY_EXTENSION[format]
        if export_format not in artifact.export_formats():
            raise ValueError(
                "%s export is not supported for this figure."
                % export_format.label
            )
        needs_engine = artifact.requires_engine_for_export(export_format.extension)
        if needs_engine:
            self._require_plot_worker("Exporting a figure")

        default_name = (
            {
                "forest": "forest_plot",
                "regression": "regression",
                "funnel": "small_study_effects_funnel",
                "sroc": "sroc",
            }.get(artifact.capability.regenerator, "figure")
            if artifact.can_regenerate()
            else (artifact.title or "figure").replace(" ", "_")
        )
        default_path = "%s.%s" % (default_name, export_format.extension)
        file_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Plot As",
            default_path,
        )
        if not file_path:
            return

        allow_svgz = not needs_engine
        file_path = _path_with_export_extension(
            file_path, export_format, allow_svgz=allow_svgz
        )
        if file_path.lower().endswith(".svgz") and needs_engine:
            raise ValueError(
                "SVGZ export is not supported by the plot renderer; use SVG instead."
            )

        if needs_engine:
            target = Path(file_path)

            def completed(result, state):
                candidate = _worker_candidate_file(
                    result, "candidate.image_path"
                )
                PlotService.promote_worker_files(
                    state["staging_root"], {candidate: target}
                )

            extension = target.suffix.lower().lstrip(".")
            self._request_worker_plot(
                artifact,
                "plot_export",
                lambda run_id, identity, staging: self.worker_client.request_plot_export(
                    run_id,
                    artifact_identity=identity,
                    regenerator=artifact.capability.regenerator,
                    params_path=artifact.params_path,
                    staging_dir=staging,
                    output_extension=extension,
                ),
                completed,
                label="Exporting %s" % artifact.title,
            )
            return

        self._export_from_stored_artifact(
            artifact,
            file_path,
            export_format,
        )

    @staticmethod
    def _export_from_stored_artifact(artifact, output_path, export_format):
        target = Path(output_path)
        transaction_dir = Path(
            tempfile.mkdtemp(prefix=".rcms-figure-export-", dir=str(target.parent))
        )
        temporary_output = transaction_dir / ("export" + target.suffix)
        try:
            if export_format.extension == "svg":
                if not artifact.has_vector_display():
                    raise ValueError("This stored figure has no vector renderer.")
                svg = _svg_bytes_with_white_background(artifact.display_path())
                if str(output_path).lower().endswith(".svgz"):
                    with gzip.open(temporary_output, "wb") as destination:
                        destination.write(svg)
                else:
                    temporary_output.write_bytes(svg)
            else:
                image = _image_for_artifact(artifact)
                if image.isNull():
                    raise ValueError("The stored figure cannot be rendered for export.")
                if not image.save(str(temporary_output), export_format.qt_format):
                    raise OSError(
                        "Qt could not write the %s figure export."
                        % export_format.label
                    )
            os.replace(str(temporary_output), str(target))
        finally:
            shutil.rmtree(transaction_dir, ignore_errors=True)

    def position(self):
        return QPointF(float(self.x_coord), float(self.y_coord))

    def _viewport_width(self) -> int:
        viewport = self.graphics_view.viewport()
        if viewport is None:
            raise RuntimeError("Results graphics view has no viewport")
        return viewport.width()


def _worker_candidate_file(result, key):
    if not isinstance(result, Mapping):
        raise ValueError("The plot worker returned an invalid result")
    if key.startswith("candidate."):
        candidate = result.get("candidate")
        if not isinstance(candidate, Mapping):
            raise ValueError("The plot worker returned no candidate files")
        value = candidate.get(key.removeprefix("candidate."))
    else:
        value = result.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError("The plot worker returned no %s" % key.replace("_", " "))
    return value


def _plot_worker_error_text(error):
    if isinstance(error, Mapping):
        message = error.get("message")
        details = error.get("details")
        if isinstance(message, str) and message:
            return "%s\n\n%s" % (message, details) if details else message
    return str(error)


def _normalize_results(results: AnalysisResult) -> AnalysisResult:
    if results.texts or results.images:
        return results
    normalized: dict[str, object] = {
        "version": results.version,
        "texts": dict(results.texts),
        "images": dict(results.images),
        "display_images": dict(results.display_images),
        "image_var_names": dict(results.image_var_names),
        "image_params_paths": dict(results.image_params_paths),
        "image_order": None
        if results.image_order is None
        else list(results.image_order),
        "plot_capabilities": {},
        "sections": [
            {
                "id": section.semantic_id,
                "kind": section.kind,
                "order": section.order,
                "title": section.title,
                "source_key": section.source_key,
            }
            for section in results.sections
        ],
    }
    if results.reitsma_report is not None:
        normalized["reitsma_report"] = results.reitsma_report

    if (
        not normalized["texts"]
        and not normalized["images"]
        and results.binary_numerics is None
        and results.binary_proportion_numerics is None
        and results.continuous_numerics is None
        and results.diagnostic_numerics is None
        and results.cumulative_numerics is None
        and results.leave_one_out_numerics is None
        and results.reitsma_report is None
    ):
        normalized["texts"]["No Results"] = NO_RESULTS_MESSAGE
        normalized["sections"].append(
            {
                "id": "result.none",
                "kind": "text",
                "order": 0,
                "title": "No Results",
                "source_key": "No Results",
            }
        )

    normalized_result = parse_analysis_result(normalized)
    if results.binary_numerics is not None:
        normalized_result = replace(
            normalized_result, binary_numerics=results.binary_numerics
        )
    if results.binary_proportion_numerics is not None:
        normalized_result = replace(
            normalized_result,
            binary_proportion_numerics=results.binary_proportion_numerics,
        )
    if results.continuous_numerics is not None:
        normalized_result = replace(
            normalized_result, continuous_numerics=results.continuous_numerics
        )
    if results.diagnostic_numerics is not None:
        normalized_result = replace(
            normalized_result, diagnostic_numerics=results.diagnostic_numerics
        )
    if results.cumulative_numerics is not None:
        normalized_result = replace(
            normalized_result, cumulative_numerics=results.cumulative_numerics
        )
    if results.leave_one_out_numerics is not None:
        normalized_result = replace(
            normalized_result, leave_one_out_numerics=results.leave_one_out_numerics
        )
    return normalized_result


if __name__ == "__main__":
    # make test results based on results from when meta-analysis run from amino sample project
    from rc_metastudio import settings
    from rc_metastudio.analysis_results import empty_analysis_result

    test_results: dict[str, object] = {
        "version": 1,
        "images": {},
        "texts": {},
        "display_images": {},
        "image_var_names": {},
        "image_params_paths": {},
        "image_order": None,
        "plot_capabilities": {},
        "sections": [],
    }
    test_results["images"] = {
        "Forest Plot": settings.analysis_output_path("forest.png")
    }
    test_results["texts"] = {
        "Weights": "Study names        Weights\nGonzalez       1993  7.3%\nPrins          1993  6.2%\nGiamarellou    1991  2.1%\nMaller         1993 10.7%\nSturm          1989  2.0%\nMarik          1991 12.2%\nMuijsken       1988  7.5%\nVigano         1992  1.8%\nHansen         1988  5.3%\nDe Vries       1990  6.1%\nMauracher      1989  2.2%\nNordstrom      1990  5.3%\nRozdzinski     1993 10.3%\nTer Braak      1990  8.7%\nTulkens        1988  1.2%\nVan der Auwera 1991  2.0%\nKlastersky     1977  6.0%\nVanhaeverbeek  1993  1.2%\nHollender      1989  1.8%\n",
        "Summary": "Binary Random-Effects Model\n\nMetric: Odds Ratio\n\nModel Results\n Estimate  Lower bound  Upper bound  p-value\n 0.770           0.485        1.222    0.267\n\nHeterogeneity\n    τ²  Q(df=18)  Het. p-value       I²\n 0.378    33.360         0.015  46.000%\n\nCalculation scale: log - estimate: -0.262, lower: -0.724, upper: 0.200, std. error: 0.236\n",
    }
    test_results["sections"] = [
        {
            "id": "result.weights",
            "kind": "text",
            "order": 0,
            "title": "Weights",
            "source_key": "Weights",
        },
        {
            "id": "result.summary",
            "kind": "text",
            "order": 1,
            "title": "Summary",
            "source_key": "Summary",
        },
        {
            "id": "plot.forest",
            "kind": "image",
            "order": 2,
            "title": "Forest Plot",
            "source_key": "Forest Plot",
        },
    ]
    test_results["image_var_names"] = {"forest plot": "forest_plot"}
    test_results["image_params_paths"] = {
        "Forest Plot": settings.analysis_output_path("1369769105.72079")
    }  # change this number as necessary
    test_results["image_order"] = None

    app = app_error_handler.get_or_create_application(sys.argv)
    resultswindow = ResultsWindow(parse_analysis_result(test_results))
    resultswindow.show()
    sys.exit(app.exec())
