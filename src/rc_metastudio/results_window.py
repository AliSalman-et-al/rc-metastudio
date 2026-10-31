# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render and export meta-analysis results."""

import gzip
import csv
import io
import re
from html import escape
from pathlib import Path
from collections import namedtuple
from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING, Callable
from PyQt6.QtCore import (
    QByteArray,
    QEvent,
    QObject,
    QPointF,
    QRectF,
    QTimer,
    Qt,
)
from PyQt6.QtGui import (
    QAction,
    QCloseEvent,
    QFont,
    QImage,
    QPainter,
    QPixmap,
    QResizeEvent,
    QShowEvent,
    QTextOption,
    QTransform,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QMainWindow,
    QMenu,
    QSizePolicy,
    QTreeWidgetItem,
    QToolButton,
    QComboBox,
    QLabel,
    QSpinBox,
    QTextBrowser,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QVBoxLayout,
    QToolBar,
    QAbstractItemView,
)
import os
import sys
from rc_metastudio import (
    adaptive_window,
    app_error_handler,
    plot_capabilities,
    qt_layout,
)
from rc_metastudio.analysis_results import (
    AnalysisResult,
    PlotCapability,
    parse_analysis_result,
)
from rc_metastudio.funnel_plot_editor_dialog import FunnelPlotEditorDialog
from rc_metastudio.plot_editor_dialog import EditPlotDialog
from rc_metastudio.plot_service import PlotService
from rc_metastudio.runtime_types import required
from rc_metastudio.qt_geometry import logical_extent_to_physical_pixels
from rc_metastudio.settings import (
    load_plot_export_format,
    save_plot_export_format,
    restore_results_window_state,
    save_results_window_state,
)

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
    PlotExportFormat("tiff", "TIFF", None),
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
        if self.has_vector_display():
            item = _svg_item_class()(self.display_path())
            return item.renderer().isValid()
        return not QPixmap(self.image_path).isNull()

    def export_formats(self):
        if self.params_path:
            return PLOT_EXPORT_FORMATS
        return (PLOT_EXPORT_FORMATS_BY_EXTENSION["png"],)


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


def _pixmap_device_independent_size(pixmap):
    """Return a pixmap's logical dimensions without discarding its DPR."""
    dpr = max(1.0, float(pixmap.devicePixelRatioF()))
    return (float(pixmap.width()) / dpr, float(pixmap.height()) / dpr)


class ResultsWindow(QMainWindow, Ui_ResultsWindow):
    def __init__(
        self,
        results: AnalysisResult,
        parent=None,
        plot_service: PlotService | None = None,
        change_settings: Callable[[str | None], None] | None = None,
    ):

        super(ResultsWindow, self).__init__(parent)
        self._svg_plot_items = []
        self._raster_plot_items = []
        self._refitting_svg_plots = False
        self._viewport_refit_pending = False
        self._viewport_width_override = None
        self._first_show_refit_pending = True
        self._layout_items = []
        self._nav_items_to_sections = {}
        self._nav_plot_artifacts = {}
        self.setupUi(self)
        self.nav_tree.setAccessibleName("Results navigation")
        self.nav_tree.setAccessibleDescription(
            "Navigate between analysis result sections and plots."
        )
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
        self.plot_service = plot_service or PlotService()
        self._change_settings = change_settings

        self.nav_tree.itemClicked.connect(
            app_error_handler.safe_slot(self.item_clicked, parent=self)
        )
        self.results_nav_splitter.splitterMoved.connect(
            app_error_handler.safe_slot(
                lambda _pos, _index: self._schedule_viewport_refit(), parent=self
            )
        )

        self.nav_tree.setHeaderLabels(["Results"])
        self.nav_tree.setAccessibleName("Result sections")
        self.nav_tree.setAccessibleDescription("Choose a figure, the text report, numerical tables or model configuration.")
        self.graphics_view.setAccessibleName("Analysis figures")
        self.graphics_view.setAccessibleDescription("Scrollable figures. Use the results toolbar to edit, zoom or export the selected figure.")
        self.nav_tree.setItemsExpandable(True)
        # layout-audit: allow=content-overflow-control; reason=required content may consume available layout width
        self.nav_tree.setMinimumWidth(0)
        self.nav_tree.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        self.graphics_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.graphics_view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.results_nav_splitter.setChildrenCollapsible(False)
        self.results_nav_splitter.setStretchFactor(0, 1)
        self.results_nav_splitter.setStretchFactor(1, 5)
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
        self.add_result_sections()
        self._relayout_sections()

        # reset the scene
        self.graphics_view.setScene(self.scene)
        self.graphics_view.ensureVisible(QRectF(0, 0, 0, 0))
        # Establish the restored ratio before the first native show/layout pass.
        # QSplitter then preserves that ratio as the window receives its final
        # screen-safe geometry, and the queued refit sees a stable viewport.
        self._apply_restored_splitter_proportions()
        self._setup_report_controls()

    def _setup_report_controls(self):
        self._setup_identity()
        self._setup_report_document()
        self._setup_result_tables()
        self._setup_results_actions()
        self._report_nav_anchors = {}
        entries = [("Text report", ""), ("Tables", None)]
        if self.results.details:
            entries.append(("Settings", "model-configuration"))
        for index, (title, anchor) in enumerate(entries):
            item = QTreeWidgetItem([title])
            if title == "Settings":
                index = 2 + sum(section.kind == "text" and section.source_key != "Weights" and section.semantic_id != "text:references" for section in self.results.sections)
            self.nav_tree.insertTopLevelItem(index, item)
            item.setToolTip(0, "Read the report" if title == "Text report" else "Copy or export numerical tables" if title == "Tables" else "Inspect the executed model and settings")
            item.setDisabled(title == "Tables" and not self._report_tables)
            self._report_nav_anchors[id(item)] = anchor
        self.nav_tree.currentItemChanged.connect(lambda item, _previous: self.item_clicked(item, 0) if item is not None else None)
        self._show_initial_result()

    def _show_initial_result(self):
        self._fit_width_active = True
        first_plot = next((item for item in self.nav_tree.findItems("", Qt.MatchFlag.MatchContains | Qt.MatchFlag.MatchRecursive) if id(item) in self._nav_plot_artifacts), None)
        if first_plot is not None:
            self.nav_tree.setCurrentItem(first_plot)
        clinical = any(section.semantic_id.startswith("diagnostic.reitsma.summary")
                       for section in self.results.sections)
        self.report_action.setChecked(clinical or first_plot is None)
        self._show_report(self.report_action.isChecked())
        if self.report_action.isChecked():
            self._activate_report(True)
        self._set_restored_splitter_sizes()
        if not self.report_action.isChecked():
            self._fit_width()

    def _setup_identity(self):
        identity = self.results.identity or "Analysis results"
        parent = self.parent()
        self._source_sheet = parent.model.current_sheet if parent is not None and hasattr(parent, "model") else None
        sheet_name = self._source_sheet.name if self._source_sheet else "Results"
        self.setWindowTitle(sheet_name + " — " + identity.split(" — ")[0])
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout.setSpacing(4)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

    def _setup_report_document(self):
        self.report_text = QTextBrowser(self.content_stack)
        self.report_text.setAccessibleName("Analysis report")
        self.report_text.setOpenLinks(False)
        required(self.report_text.document(), "report document").setDocumentMargin(20)
        body = []
        for anchor, heading, paragraphs, tables in self._report_blocks():
            body.append(f'<a name="{escape(anchor)}"></a><h2>{escape(_report_heading(heading))}</h2>')
            if anchor == "text:references":
                body.append(_reference_html("\n".join(paragraphs)))
                continue
            for paragraph in paragraphs:
                if paragraph.startswith("Pooled "):
                    body.append("<p>" + escape(paragraph) + "</p>")
            for index, table in enumerate(tables):
                body.append(_report_table_html(table, heading, suppress_title=index == 0 and table.title.endswith("Model Results")))
            body.extend("<p>" + escape(paragraph).replace("\n", "<br>") + "</p>" for paragraph in paragraphs if not paragraph.startswith("Pooled "))
        self._report_html = "".join(body)
        report_font = QFont(self.font())
        report_font.setPointSizeF(max(11.0, self.font().pointSizeF()))
        self._apply_report_typography(report_font)
        self._report_base_font = QFont(report_font)
        self._report_zoom_percent = 100
        self._figure_zoom_percent = 100
        self.content_stack.addWidget(self.report_text)

    def _apply_report_typography(self, font):
        self.report_text.setFont(font)
        size = font.pointSizeF()
        required(self.report_text.document(), "report document").setDefaultStyleSheet(
            f"h2 {{ font-size: {size * 1.18:g}pt; margin-top: 14px; margin-bottom: 6px; }} "
            f"h3 {{ font-size: {size:g}pt; margin-top: 12px; margin-bottom: 6px; }} "
            "p { margin-top: 6px; margin-bottom: 8px; } th { font-weight: bold; }")
        self.report_text.setHtml(self._report_html)

    def _setup_result_tables(self):
        self._report_tables = [table for section in self.results.sections for table in section.tables]
        self.tables_page = QWidget(self.content_stack)
        layout = QVBoxLayout(self.tables_page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self.table_selector = QComboBox(self.tables_page)
        self.table_selector.setAccessibleName("Result table")
        for section in self.results.sections:
            for table in section.tables:
                self.table_selector.addItem(_report_heading(table.title if table.title == section.title or section.title.endswith("Summary") else section.title + " — " + table.title))
        layout.addWidget(self.table_selector)
        self.result_table = QTableWidget(self.tables_page)
        self.result_table.setTabKeyNavigation(False)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setFont(self._report_base_font)
        self.result_table.setAccessibleDescription("Read-only result cells with column headers. Ctrl+C copies selected cells, or the entire table when no cells are selected. Tab moves to the next control.")
        required(self.result_table.verticalHeader(), "result table row header").hide()
        layout.addWidget(self.result_table)
        controls = QToolBar("Table actions", self.tables_page)
        controls.setMovable(False)
        controls.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.copy_table_action = QAction("Copy table", self)
        self.copy_table_action.triggered.connect(self._copy_table)
        copy_shortcut = QAction(self.result_table)
        copy_shortcut.setShortcut("Ctrl+C")
        copy_shortcut.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        copy_shortcut.triggered.connect(self._copy_table)
        self.result_table.addAction(copy_shortcut)
        self.export_table_action = QAction("Export table CSV…", self)
        self.export_table_action.triggered.connect(app_error_handler.safe_slot(self._export_table, parent=self))
        for action in (self.copy_table_action, self.export_table_action):
            controls.addAction(action)
        layout.addWidget(controls)
        self.table_selector.currentIndexChanged.connect(self._select_result_table)
        self.content_stack.addWidget(self.tables_page)
        self._select_result_table(0)

    def _select_result_table(self, index):
        if not 0 <= index < len(self._report_tables):
            return
        table = self._report_tables[index]
        self.result_table.clear()
        self.result_table.setColumnCount(len(table.headers))
        self.result_table.setRowCount(len(table.rows))
        self.result_table.setHorizontalHeaderLabels(list(table.headers))
        self.result_table.setAccessibleName(_report_heading(table.title))
        for row_index, row in enumerate(table.rows):
            for column_index, cell in enumerate(row):
                item = QTableWidgetItem(cell)
                if _numeric_cell(cell):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.result_table.setItem(row_index, column_index, item)
        self.result_table.resizeColumnsToContents()
        for column in range(self.result_table.columnCount()):
            self.result_table.setColumnWidth(column, min(360, self.result_table.columnWidth(column) + 12))
        self.result_table.resizeRowsToContents()

    def _table_payload(self, delimiter, selected=False):
        table = self._report_tables[self.table_selector.currentIndex()]
        rows = [table.headers, *table.rows]
        indexes = self.result_table.selectedIndexes() if selected else []
        if indexes:
            top, bottom = min(item.row() for item in indexes), max(item.row() for item in indexes)
            left, right = min(item.column() for item in indexes), max(item.column() for item in indexes)
            rows = [row[left:right + 1] for row in table.rows[top:bottom + 1]]
        stream = io.StringIO(newline="")
        csv.writer(stream, delimiter=delimiter, lineterminator="\n").writerows(rows)
        return stream.getvalue()

    def _copy_table(self):
        required(QApplication.clipboard(), "system clipboard").setText(self._table_payload("\t", selected=True))
        self.statusbar.showMessage("Table copied")

    def _export_table(self):
        table = self._report_tables[self.table_selector.currentIndex()]
        path, _filter = QFileDialog.getSaveFileName(self, "Export result table", self._export_name(table.title, "csv"), "CSV table (*.csv)")
        if path:
            with Path(path).open("w", encoding="utf-8-sig", newline="") as stream:
                stream.write(self._table_payload(","))
            self.statusbar.showMessage(f"Saved table: {Path(path).resolve()}")

    def _show_tables(self):
        self.report_action.blockSignals(True)
        self.report_action.setChecked(False)
        self.report_action.blockSignals(False)
        self.content_stack.setCurrentWidget(self.tables_page)
        self.fit_width_action.setEnabled(False)
        self.zoom_control.setEnabled(False)
        self.export_plot_action.setEnabled(False)
        self.edit_plot_action.setEnabled(False)
        self.nav_tree.blockSignals(True)
        self.nav_tree.setCurrentItem(self.nav_tree.findItems("Tables", Qt.MatchFlag.MatchExactly)[0])
        self.nav_tree.blockSignals(False)
        self.result_table.setFocus()

    def _activate_report(self, checked):
        item = self.nav_tree.findItems("Text report", Qt.MatchFlag.MatchExactly)[0] if checked else getattr(self, "_last_plot_item", None)
        if item is not None:
            self.nav_tree.setCurrentItem(item)

    def _setup_results_actions(self):
        toolbar = required(self.addToolBar("Results actions"), "results toolbar")
        toolbar.setMovable(False)
        self.report_action = QAction("Text report", self)
        self.report_action.setCheckable(True)
        self.report_action.setShortcut("Ctrl+T")
        self.report_action.toggled.connect(self._show_report)
        self.report_action.triggered.connect(self._activate_report)
        toolbar.addAction(self.report_action)
        self.tables_action = QAction("Tables", self)
        self.tables_action.setShortcut("Ctrl+Shift+T")
        self.tables_action.setEnabled(bool(self._report_tables))
        self.tables_action.triggered.connect(self._show_tables)
        toolbar.addAction(self.tables_action)
        self.copy_report_action = QAction("Copy report", self)
        self.copy_report_action.setShortcut("Ctrl+Shift+C")
        self.copy_report_action.triggered.connect(self._copy_report)
        toolbar.addAction(self.copy_report_action)
        self.export_report_action = QAction("Export report…", self)
        self.export_report_action.setShortcut("Ctrl+Shift+S")
        self.export_report_action.triggered.connect(app_error_handler.safe_slot(self._export_report, parent=self))
        toolbar.addAction(self.export_report_action)
        self.export_plot_action = QAction("Export plot…", self)
        self.export_plot_action.setShortcut("Ctrl+Shift+E")
        self.export_plot_action.setEnabled(False)
        self.export_plot_action.triggered.connect(app_error_handler.safe_slot(self._export_selected_plot, parent=self))
        toolbar.addAction(self.export_plot_action)
        self.export_format_control = QComboBox(self)
        self.export_format_control.setAccessibleName("Plot export format")
        self.export_format_control.setToolTip("Export format; remembered for your next plot and analysis.")
        self.export_format_control.currentIndexChanged.connect(lambda _index: save_plot_export_format(self.export_format_control.currentData()) if self.export_format_control.currentData() else None)
        toolbar.addWidget(self.export_format_control)
        self.edit_plot_action = QAction("Edit plot…", self)
        self.edit_plot_action.setEnabled(False)
        self.edit_plot_action.triggered.connect(app_error_handler.safe_slot(self._edit_selected_plot, parent=self))
        toolbar.addAction(self.edit_plot_action)
        self.change_settings_action = QAction("Change settings…", self)
        self.change_settings_action.setEnabled(self._change_settings is not None)
        self.change_settings_action.setToolTip("Re-run this analysis with its original dataset and changed settings.")
        if self._change_settings is not None:
            self.change_settings_action.triggered.connect(app_error_handler.safe_slot(self._change_analysis_settings, parent=self))
        toolbar.addAction(self.change_settings_action)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Zoom:", self))
        self.zoom_control = QSpinBox(self)
        self.zoom_control.setAccessibleName("Result zoom")
        self.zoom_control.setRange(10, 400)
        self.zoom_control.setSingleStep(25)
        self.zoom_control.setSuffix("%")
        self.zoom_control.setValue(100)
        self.zoom_control.valueChanged.connect(self._set_zoom)
        toolbar.addWidget(self.zoom_control)
        self.fit_width_action = QAction("Fit width", self)
        self.fit_width_action.triggered.connect(self._fit_width)
        toolbar.addAction(self.fit_width_action)
        for button in toolbar.findChildren(QToolButton):
            action = button.defaultAction()
            if action is not None:
                button.setAccessibleName(action.text())
                button.setAccessibleDescription(action.toolTip() or action.text())
                button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setTabOrder(self.nav_tree, self.graphics_view)
        self.setTabOrder(self.table_selector, self.result_table)
        self.setTabOrder(self.result_table, self.nav_tree)
        menu = self.menubar.addMenu("&Results")
        for action in (self.report_action, self.tables_action, self.copy_report_action, self.export_report_action, self.export_plot_action, self.edit_plot_action, self.change_settings_action, self.fit_width_action):
            required(menu, "Results menu").addAction(action)

    def _fit_width(self):
        if self.report_action.isChecked():
            return
        self._fit_width_active = True
        self.graphics_view.resetTransform()
        self._refit_viewport_items()
        self._apply_fit_width()

    def _apply_fit_width(self):
        selected = self._selected_plot()
        width = selected[1].sceneBoundingRect().right() + padding if selected else self.scene.sceneRect().width()
        viewport = required(self.graphics_view.viewport(), "figure viewport")
        scale = max(1, viewport.width() - 2) / max(1, width)
        self.graphics_view.setTransform(QTransform.fromScale(scale, scale))
        self._figure_zoom_percent = round(scale * 100)
        if not self.report_action.isChecked():
            self._update_zoom_control(self._figure_zoom_percent)
        self._scroll_to_section(self.nav_tree.currentItem())

    def _scroll_to_section(self, item):
        required(self.graphics_view.horizontalScrollBar(), "horizontal scrollbar").setValue(0)
        if item is not None:
            section = self._nav_items_to_sections.get(id(item))
            if section is None:
                return
            index = self._layout_items.index(section)
            heading = self._layout_items[max(0, index - 1)]
            required(self.graphics_view.verticalScrollBar(), "figure scrollbar").setValue(round(heading.sceneBoundingRect().top() * self.graphics_view.transform().m22()))

    def _set_zoom(self, percent):
        if self.report_action.isChecked():
            self._report_zoom_percent = percent
            font = QFont(self._report_base_font)
            font.setPointSizeF(self._report_base_font.pointSizeF() * percent / 100)
            scrollbar = required(self.report_text.verticalScrollBar(), "report scrollbar")
            fraction = scrollbar.value() / max(1, scrollbar.maximum())
            self._apply_report_typography(font)
            scrollbar.setValue(round(fraction * scrollbar.maximum()))
        else:
            self._fit_width_active = False
            self._figure_zoom_percent = percent
            self.graphics_view.setTransform(QTransform.fromScale(percent / 100, percent / 100))

    def _show_report(self, checked):
        self.content_stack.setCurrentWidget(self.report_text if checked else self.figure_page)
        self.zoom_control.setEnabled(True)
        self.fit_width_action.setEnabled(not checked)
        self._update_zoom_control(self._report_zoom_percent if checked else self._figure_zoom_percent)

    def _update_zoom_control(self, percent):
        self.zoom_control.blockSignals(True)
        self.zoom_control.setValue(percent)
        self.zoom_control.blockSignals(False)

    def _report_blocks(self):
        deferred = []
        calculation = []
        for section in sorted(self.results.sections, key=lambda section: section.order):
            if section.kind != "text":
                continue
            if section.semantic_id == "text:references" or section.source_key == "Weights":
                deferred.append(section)
                continue
            calculation.extend(table for table in section.tables if table.title.startswith("Calculation scale"))
            yield _report_section_block(section)
        if self.results.details:
            yield "model-configuration", "Model configuration", (self.results.details,), ()
        if calculation:
            yield "calculation-details", "Calculation details", (), tuple(calculation)
        for section in deferred:
            yield section.semantic_id, "Study weights" if section.source_key == "Weights" else section.title, section.paragraphs if section.tables else (section.value,), section.tables

    def _plain_text_report(self):
        blocks = [self.results.identity]
        for _anchor, heading, paragraphs, tables in self._report_blocks():
            blocks.append(_report_heading(heading))
            blocks.extend(paragraph for paragraph in paragraphs if paragraph.startswith("Pooled "))
            for index, table in enumerate(tables):
                caption = _report_heading(table.title) + "\n" if table.title != heading and not (index == 0 and table.title.endswith("Model Results")) else ""
                blocks.append(caption + "\n".join(
                    "\t".join(row) for row in (table.headers, *table.rows)))
            blocks.extend(paragraph for paragraph in paragraphs if not paragraph.startswith("Pooled "))
        return "\n\n".join(block for block in blocks if block) + "\n"

    def _copy_report(self):
        required(QApplication.clipboard(), "system clipboard").setText(self._plain_text_report())
        self.statusbar.showMessage("Report copied")

    def _export_report(self):
        path, _filter = QFileDialog.getSaveFileName(self, "Export analysis report", self._export_name("report", "txt"), "Text report (*.txt)")
        if path:
            Path(path).write_text(self._plain_text_report(), encoding="utf-8")
            self.statusbar.showMessage(f"Saved report: {Path(path).resolve()}")

    def _export_name(self, title, extension):
        context = (self.results.identity or "Analysis results").split("\n")[0]
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", context + " — " + title)
        return name.strip(" .")[:160] + "." + extension

    def _selected_plot(self):
        item = self.nav_tree.currentItem()
        if item is None:
            return None
        plot_item = self._nav_items_to_sections.get(id(item))
        artifact = self._nav_plot_artifacts.get(id(item))
        if artifact is not None:
            return artifact, plot_item
        return None

    def _export_selected_plot(self):
        selected = self._selected_plot()
        if selected is not None:
            artifact, _item = selected
            self.save_image_as(artifact, None if artifact.params_path else QPixmap(artifact.image_path), format=self.export_format_control.currentData())

    def _change_analysis_settings(self):
        if self._change_settings is None:
            return
        choice = None
        selected = self._selected_plot()
        artifact = selected[0] if selected is not None else self._nav_plot_artifacts.get(id(getattr(self, "_last_plot_item", None)))
        if artifact is not None and artifact.capability.regenerator == "forest" and artifact.params_path is not None:
            params = self.plot_service.load_params(artifact.params_path)
            if params is not None:
                choice = params.get("fp_axis_scale")
                if isinstance(choice, (list, tuple)):
                    choice = choice[0] if choice else None
        self._change_settings(str(choice) if choice is not None else None)

    def _edit_selected_plot(self):
        selected = self._selected_plot()
        if selected is not None:
            self.edit_plot(*selected)

    def add_result_sections(self):
        # Ordering and plot capabilities come from the immutable result
        # contract.  The title is used only when painting display text.
        for section in sorted(self.results.sections, key=lambda item: item.order):
            if section.kind == "image":
                self.add_image_section(section.source_key, section.title, section.value)

    def add_image_section(self, title, display_title, image):
        params_path = None
        if self.params_paths is not None and title in self.params_paths:
            params_path = self.params_paths[title]

        artifact = self.create_plot_artifact(title, image, params_path=params_path)
        if not artifact.can_display():
            return

        qt_item = self.add_title(display_title)
        img_shape, pos, plot_item = self.create_plot_item(artifact, self.position())

        self.items_to_coords[id(qt_item)] = pos
        self._nav_items_to_sections[id(qt_item)] = plot_item
        self._nav_plot_artifacts[id(qt_item)] = artifact

    def create_plot_artifact(self, title, image_path, params_path=None):
        return PlotArtifact(
            title,
            image_path,
            self.plot_capabilities[title],
            params_path=params_path,
            display_path=self.display_images.get(title),
        )

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

        scaled_width, scaled_height = self._fit_size_to_viewport(
            item_width,
            item_height,
            max_scale=MAX_VECTOR_PLOT_SCALE,
        )
        if item_width <= 0:
            return scaled_width, scaled_height

        target_scale = float(scaled_width) / float(item_width)
        if abs(target_scale - svg_item.scale()) >= 0.001:
            svg_item.setScale(target_scale)
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
        return qt_item

    def item_clicked(self, item, column):
        if id(item) in getattr(self, "_report_nav_anchors", {}):
            anchor = self._report_nav_anchors[id(item)]
            if anchor is None:
                self._show_tables()
            else:
                self.report_action.setChecked(True)
                self._show_report(True)
                self.report_text.scrollToAnchor(anchor)
                if not anchor:
                    required(self.report_text.verticalScrollBar(), "report scrollbar").setValue(0)
            self.export_plot_action.setEnabled(False)
            self.edit_plot_action.setEnabled(False)
            return
        self._scroll_to_section(item)
        if getattr(self, "_fit_width_active", False):
            self._fit_width()
        if hasattr(self, "report_action"):
            selected = self._selected_plot()
            if selected is not None:
                self._last_plot_item = item
            # Tables also unchecks the action; a no-op value change cannot select the page.
            self.report_action.blockSignals(True)
            self.report_action.setChecked(selected is None)
            self.report_action.blockSignals(False)
            self._show_report(selected is None)
            self.export_plot_action.setEnabled(selected is not None)
            self.edit_plot_action.setEnabled(selected is not None and selected[0].capability.editable)
            self._update_export_formats(selected, item)

    def _update_export_formats(self, selected, item):
        self.export_format_control.blockSignals(True)
        self.export_format_control.clear()
        if selected is not None:
            for export_format in selected[0].export_formats():
                self.export_format_control.addItem(export_format.extension.upper(), export_format.extension)
            preferred = self.export_format_control.findData(load_plot_export_format())
            if preferred >= 0:
                self.export_format_control.setCurrentIndex(preferred)
        else:
            for section in self.results.sections:
                if section.title == item.text(0):
                    self.report_text.scrollToAnchor(section.semantic_id)
        self.export_format_control.blockSignals(False)

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
                if getattr(self, "_fit_width_active", False):
                    self._apply_fit_width()
            finally:
                self._viewport_width_override = None

    def eventFilter(  # ty: ignore[invalid-method-override] -- PyQt6 generated-form multiple inheritance
        self, watched: QObject | None, event: QEvent | None
    ) -> bool:
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
            source = item.source_pixmap
            if source.isNull():
                continue
            logical_width, logical_height = _pixmap_device_independent_size(source)
            scaled_width, _scaled_height = self._fit_size_to_viewport(
                logical_width, logical_height
            )
            item.setPixmap(source)
            item.setScale(float(scaled_width) / float(logical_width))

    def _relayout_sections(self):
        """Place every result item from its current measured size and stored order."""
        next_y = float(self.add_offset)
        for item in self._layout_items:
            item.setPos(self.x_coord, next_y)
            next_y += item.sceneBoundingRect().height()
            if not isinstance(item, QGraphicsTextItem):
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
        self.deleteLater()

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

    def _make_context_menu(self, artifact, plot_item):
        plot_img = QImage(artifact.image_path)

        def _graphics_item_context_menu(event):
            def add_save_as_menu_action(menu, export_format):
                action = QAction("Export %s…" % export_format.label, self)
                guidance = (
                    PLOT_EXPORT_GUIDANCE[export_format.extension]
                    if artifact.params_path
                    else "Save the original raster image at its native resolution."
                )
                action.setStatusTip(guidance)
                action.setToolTip(guidance)

                def save_action(_checked=False, selected_format=export_format):
                    self.save_image_as(
                        artifact,
                        unscaled_image=(
                            plot_img
                            if selected_format.qt_format is not None
                            and not artifact.params_path
                            else None
                        ),
                        format=selected_format.extension,
                    )

                action.triggered.connect(
                    app_error_handler.safe_slot(save_action, parent=self)
                )
                menu.addAction(action)

            context_menu = QMenu(self)
            if artifact.capability.editable:
                if plot_capabilities.option_groups(artifact.plot_kind):
                    action = QAction("Edit plot…", self)
                    action.setStatusTip(
                        "Edit plot appearance and regenerate the result before closing."
                    )
                    action.setToolTip(
                        "Edit plot appearance and regenerate the result before closing."
                    )
                    action.setWhatsThis("Edit plot appearance and regenerate the result before closing.")
                    action.triggered.connect(
                        app_error_handler.safe_slot(
                            lambda _checked=False: self.edit_plot(artifact, plot_item),
                            parent=self,
                        )
                    )
                    context_menu.addAction(action)
            for export_format in artifact.export_formats():
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

    def _edit_sroc_plot(self, artifact, plot_item):
        plot_params = self.plot_service.load_params(artifact.params_path)
        if plot_params is None:
            return
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
        updated_params = dialog.plot_params()
        outpath = updated_params.get("fp_outpath") or artifact.image_path
        try:
            self.plot_service.apply_edits(
                regenerator="sroc",
                params_path=artifact.params_path,
                updated_params=updated_params,
                output_path=outpath,
            )
        except Exception as error:
            dialog.mark_commit_failed(error)
            raise
        self._refresh_plot_item(plot_item, artifact, outpath)
        dialog.mark_commit_succeeded()

    def _edit_funnel_plot(self, artifact, plot_item):
        plot_params = self.plot_service.load_params(artifact.params_path)
        if plot_params is None:
            return
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
        updated_params = dialog.plot_params()
        outpath = updated_params.get("funnel.outpath") or artifact.image_path
        if str(outpath).lower().endswith(".svgz"):
            raise ValueError(
                "SVGZ output is not supported when editing funnel plots; use SVG instead."
            )
        try:
            self.plot_service.apply_edits(
                regenerator="funnel",
                params_path=artifact.params_path,
                updated_params=updated_params,
                output_path=outpath,
            )
        except Exception:
            dialog.mark_commit_failed()
            raise
        self._refresh_plot_item(plot_item, artifact, outpath)
        dialog.mark_commit_succeeded()

    def _edit_forest_plot(self, artifact, plot_item):
        plot_params = self.plot_service.load_params(artifact.params_path)
        if plot_params is None:
            return

        dialog = EditPlotDialog(plot_params, artifact.image_path, parent=self)
        dialog.applied.connect(
            app_error_handler.safe_slot(
                lambda: self._apply_forest_plot_edits(dialog, artifact, plot_item),
                parent=self,
            )
        )
        dialog.exec()

    def edit_regression_plot(self, artifact, plot_item):
        plot_params = self.plot_service.load_params(artifact.params_path)
        if plot_params is None:
            return

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
        updated_params = dialog.plot_params()
        outpath = updated_params["bp_outpath"] or artifact.image_path
        try:
            self.plot_service.apply_edits(
                regenerator="regression",
                params_path=artifact.params_path,
                updated_params=updated_params,
                output_path=outpath,
            )
        except Exception as error:
            dialog.mark_commit_failed(error)
            raise
        self._refresh_plot_item(plot_item, artifact, outpath)
        dialog.mark_commit_succeeded()

    def _apply_forest_plot_edits(self, dialog, artifact, plot_item):
        updated_params = dialog.plot_params()
        outpath = updated_params["fp_outpath"] or artifact.image_path
        try:
            self.plot_service.apply_edits(
                regenerator="forest",
                params_path=artifact.params_path,
                updated_params=updated_params,
                output_path=outpath,
            )
        except Exception as error:
            dialog.mark_commit_failed(error)
            raise

        parent = self.parent()
        if self._source_sheet is not None and parent is not None and self._source_sheet in parent.model.dataset.sheets:
            self._source_sheet.settings["favours_labels"] = [updated_params.get("fp_favours_left", ""), updated_params.get("fp_favours_right", "")]
            parent.data_dirtied()
        self._refresh_plot_item(plot_item, artifact, outpath)
        dialog.mark_commit_succeeded()

    def _refresh_plot_item(self, plot_item, artifact, outpath):

        if plot_item is not None:
            refreshed_artifact = PlotArtifact(
                artifact.title,
                outpath,
                artifact.capability,
                params_path=artifact.params_path,
                display_path=(
                    outpath
                    if artifact.display_image_path == artifact.image_path
                    else artifact.display_image_path
                ),
            )
            if (
                isinstance(plot_item, _svg_item_class())
                and refreshed_artifact.has_vector_display()
            ):
                renderer = _opaque_svg_renderer(refreshed_artifact.display_path(), self)
                if renderer.isValid():
                    plot_item.setSharedRenderer(renderer)
                    self._schedule_viewport_refit()
                    self.scene.update()
            elif isinstance(plot_item, ResponsivePixmapItem):
                source_pixmap = QPixmap(outpath)
                if not source_pixmap.isNull():
                    plot_item.replace_source(source_pixmap)
                    self._schedule_viewport_refit()

    def save_image_as(self, artifact, unscaled_image=None, format=None):
        if not isinstance(artifact, PlotArtifact):
            artifact = self.create_plot_artifact("", artifact, params_path=None)

        if format not in PLOT_EXPORT_FORMATS_BY_EXTENSION:
            valid_formats = ", ".join(PLOT_EXPORT_FORMATS_BY_EXTENSION.keys())
            raise Exception("Invalid format, needs to be one of: %s!" % valid_formats)

        export_format = PLOT_EXPORT_FORMATS_BY_EXTENSION[format]
        allow_svgz = artifact.capability.regenerator != "funnel"

        if not unscaled_image:
            regenerator = artifact.capability.regenerator
            default_path = {
                "forest": "forest_plot",
                "regression": "regression",
                "funnel": "small_study_effects_funnel",
                "sroc": "sroc",
            }[regenerator]
            default_path = self._export_name(default_path, export_format.extension)

            # where to save the graphic?
            file_path, _selected_filter = QFileDialog.getSaveFileName(
                self,
                "Save Plot As",
                default_path,
            )

            # now we re-generate it, unless they canceled, of course
            if file_path != "":
                file_path = _path_with_export_extension(
                    file_path, export_format, allow_svgz=allow_svgz
                )
                self.plot_service.export(
                    regenerator=regenerator,
                    params_path=artifact.params_path,
                    output_path=file_path,
                )
        else:
            default_path = self._export_name(artifact.title, "png")
            file_path, _selected_filter = QFileDialog.getSaveFileName(
                self,
                "Save Plot As",
                default_path,
            )
            if file_path != "":
                file_path = _path_with_export_extension(
                    file_path, export_format, allow_svgz=allow_svgz
                )
                if not unscaled_image.save(file_path, export_format.qt_format):
                    raise OSError(f"Could not save plot: {file_path}")
        if file_path:
            self.statusbar.showMessage(f"Saved {export_format.extension.upper()} plot: {Path(file_path).resolve()}")

    def position(self):
        return QPointF(float(self.x_coord), float(self.y_coord))

    def _viewport_width(self) -> int:
        viewport = self.graphics_view.viewport()
        if viewport is None:
            raise RuntimeError("Results graphics view has no viewport")
        return viewport.width()


def _numeric_cell(cell: str) -> bool:
    return bool(re.match(r"^\s*(?:[<>]\s*)?[+−-]?(?:\d|\.\d)", cell))


def _reference_html(text: str) -> str:
    entries = re.split(r"(?:^|\n)\s*\d+\.\s+", text.strip())
    return "<ol>" + "".join("<li><p>" + escape(entry.strip()).replace("\n", " ") + "</p></li>"
                             for entry in entries if entry.strip()) + "</ol>"


def _report_heading(title):
    title = re.sub(r"\s*-\s*Model Results", " — model results", title)
    title = re.sub(r"\s+-\s*", " — ", title)
    return title.replace("Model Results", "Model results")


def _report_table_html(table, section_heading: str, suppress_title=False) -> str:
    headers, rows = list(table.headers), [list(row) for row in table.rows]
    _report_heterogeneity_columns(headers, rows)
    _report_interval_columns(headers, rows)
    numeric = [all(not row[index] or _numeric_cell(row[index]) or row[index].startswith("[") for row in rows)
               for index in range(len(headers))]
    align = ["right" if value else "left" for value in numeric]
    body = [] if suppress_title or table.title == section_heading else [f"<h3>{escape(_report_heading(table.title))}</h3>"]
    body.append("<table cellpadding='7' cellspacing='0'>")
    body.append("<tr>" + "".join(f"<th align='{align[index]}'>{escape(header)}</th>" for index, header in enumerate(headers)) + "</tr>")
    body.extend("<tr>" + "".join(f"<td align='{align[index]}'>{escape(cell)}</td>" for index, cell in enumerate(row)) + "</tr>" for row in rows)
    body.append("</table>")
    return "".join(body)


def _normalize_results(results: AnalysisResult) -> AnalysisResult:
    if "Inference Method" in results.texts:
        inference = results.texts["Inference Method"]
        details = results.details
        if inference not in details:
            details += ("\n" if details else "") + "Inference: " + inference
        results = replace(results, details=details,
                          texts=MappingProxyType({key: value for key, value in results.texts.items() if key != "Inference Method"}),
                          sections=tuple(section for section in results.sections if section.source_key != "Inference Method"))
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

    if not normalized["texts"] and not normalized["images"]:
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

    return parse_analysis_result(normalized)


def _report_heterogeneity_columns(headers, rows):
    for index in range(len(headers) - 1, -1, -1):
        header = headers[index]
        if header.startswith("Q(df="):
            df = header.removeprefix("Q(df=").removesuffix(")")
            headers[index:index + 1] = ["Q", "df"]
            for row in rows:
                row[index:index + 1] = [row[index], df]
        elif header in {"p-value", "Het. p-value"}:
            headers[index] = "P"


def _report_interval_columns(headers, rows):
    for index, header in enumerate(headers):
        if header.startswith("Lower bound (") and index + 1 < len(headers) and headers[index + 1].startswith("Upper bound ("):
            level = header.removeprefix("Lower bound (").removesuffix(")")
            start = index - 1 if index > 0 and headers[index - 1] == "Estimate" else index
            headers[start:index + 2] = [f"Estimate [{level}]" if start < index else level]
            for row in rows:
                interval = f"[{row[index]}, {row[index + 1]}]"
                row[start:index + 2] = [f"{row[start]} {interval}" if start < index else interval]
            break


def _report_section_block(section):
    tables = tuple(table for table in section.tables if not table.title.startswith("Calculation scale"))
    difference = next((table for table in tables if table.title.endswith("Test of subgroup differences")), None)
    if difference is not None:
        ordered = [table for table in tables if table is not difference]
        before = next((index for index, table in enumerate(ordered) if table.title.endswith("Prediction interval")), len(ordered))
        ordered.insert(before, difference)
        tables = tuple(ordered)
    paragraphs = section.paragraphs if section.tables else (section.value,)
    heading = section.title
    if tables and section.title.endswith("Summary"):
        heading = tables[0].title if section.title == "Summary" else section.title.removesuffix("Summary") + "results"
    return section.semantic_id, heading, paragraphs, tables


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
