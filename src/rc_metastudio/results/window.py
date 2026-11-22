# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render and export meta-analysis results."""

import textwrap
import math
import csv
import io
import re
from html import escape
from pathlib import Path
from rc_metastudio.results.svg_rendering import svg_bytes_for_qt
from rc_metastudio.results.formatting import numeric_cell as _numeric_cell, numeric_columns, report_cell
from rc_metastudio import qt_layout
from collections import Counter, namedtuple
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable
from PyQt6.QtCore import (
    QByteArray,
    QEvent,
    QObject,
    QPointF,
    QRectF,
    QSettings,
    QTimer,
    QSignalBlocker,
    Qt,
)
from PyQt6.QtGui import (
    QAction,
    QCloseEvent,
    QFont,
    QFontMetrics,
    QKeySequence,
    QIcon,
    QImage,
    QPainter,
    QPen,
    QPalette,
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
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QTreeWidgetItem,
    QToolButton,
    QComboBox,
    QLabel,
    QSpinBox,
    QTextBrowser,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QAbstractItemView,
)
import os
from rc_metastudio import adaptive_window, app_error_handler
from rc_metastudio.results import plot_capabilities
from rc_metastudio.results.contract import (
    AnalysisResult,
    ResultSection,
    normalize_analysis_result,
)
from rc_metastudio.results.funnel_editor import FunnelPlotEditorDialog
from rc_metastudio.results.plot_capabilities import PlotCapability
from rc_metastudio.results.plot_editor import EditPlotDialog
from rc_metastudio.results.export_files import compose_export, staged_output
from rc_metastudio.results.plot_service import PlotService
from rc_metastudio.qt_geometry import logical_extent_to_physical_pixels
from rc_metastudio.qt_object_guard import required
from rc_metastudio.settings import (
    DEFAULT_RESULTS_SPLITTER_PROPORTIONS,
    restore_results_window_state,
    save_results_window_state,
)

if TYPE_CHECKING:
    from rc_metastudio.results.report import ManuscriptReport
    from ui_results_window import Ui_ResultsWindow
else:
    from rc_metastudio.ui_results_window import Ui_ResultsWindow

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
        self.display_image_path = str(display_path or self.image_path)

    @property
    def plot_kind(self):
        return self.capability.plot_kind

    @classmethod
    def from_section(cls, section: ResultSection):
        if section.capability is None:
            raise ValueError("Result section has no plot capability")
        return cls(section.source_key, section.value, section.capability,
                   params_path=section.plot_data, display_path=section.display_image)

    def display_path(self):
        if os.path.exists(self.display_image_path):
            return self.display_image_path
        return self.image_path

    def has_vector_display(self):
        return self.display_path().lower().endswith((".svg", ".svgz"))

    def export_formats(self):
        if self.params_path:
            return PLOT_EXPORT_FORMATS
        return (PLOT_EXPORT_FORMATS_BY_EXTENSION["png"],)


@dataclass
class _PlotEntry:
    artifact: PlotArtifact
    navigation_item: QTreeWidgetItem
    scene_item: QGraphicsItem | None = None


_PLOT_ID_ROLE = Qt.ItemDataRole.UserRole
_REPORT_ANCHOR_ROLE = Qt.ItemDataRole.UserRole + 1
_SENSITIVITY_SECTION = "trial-sequential.sensitivity"


class ResponsivePixmapItem(QGraphicsPixmapItem):
    def __init__(self, source_pixmap):
        super(ResponsivePixmapItem, self).__init__()
        self.source_pixmap = QPixmap(source_pixmap)
        self.source_path = None
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
    svg = svg_bytes_for_qt(path)
    root = re.search(rb"<svg\b[^>]*>", svg, flags=re.IGNORECASE)
    if root is None:
        return svg
    white_canvas = b'<rect width="100%" height="100%" fill="#ffffff"/>'
    return svg[: root.end()] + white_canvas + svg[root.end() :]


def _opaque_svg_renderer(path, parent):
    svg = _svg_bytes_with_white_background(path)
    renderer = _svg_renderer_class()(QByteArray(svg), parent)
    font_sizes = [float(size) * (96 / 72 if unit == b"pt" else 1)
                  for size, unit in re.findall(rb"font-size:\s*([\d.]+)(px|pt)", svg)]
    # R repeats the body size for study labels and data cells. Small fitted
    # annotations (for example Favours labels) must not set the body-text floor.
    body_size = Counter(font_sizes).most_common(1)
    renderer.setProperty("body_text_size", body_size[0][0] if body_size else 0)
    return renderer


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
        change_settings: Callable[[dict[str, object], QWidget], None] | None = None,
        manuscript: "ManuscriptReport | None" = None,
        *,
        source_sheet_name: str | None = None,
        plot_overrides: dict[str, dict[str, object]] | None = None,
        save_plot_override: Callable[[str, dict[str, object]], None] | None = None,
    ):

        super(ResultsWindow, self).__init__(parent)
        self._plot_overrides = dict(plot_overrides or {})
        self._plot_defaults: dict[str, dict[str, object]] = {}
        self._save_plot_override = save_plot_override
        self._explicit_fit_width = False
        self._svg_plot_items = []
        self._raster_plot_items = []
        self._refitting_svg_plots = False
        self._refitting_viewport_items = False
        self._viewport_refit_pending = False
        self._closing = False
        self._viewport_refit_timer = QTimer(self)
        self._viewport_refit_timer.setSingleShot(True)
        self._viewport_refit_timer.timeout.connect(self._run_scheduled_viewport_refit)
        self._viewport_width_override = None
        self._first_show_refit_pending = True
        self._restored_splitter_proportions: tuple[float, ...] | None = None
        self._splitter_user_sized = False
        self._layout_items = []
        self._plots: dict[str, _PlotEntry] = {}
        self._last_plot_item: QTreeWidgetItem | None = None
        self.setupUi(self)
        self.nav_tree.setAccessibleName("Result sections")
        self.nav_tree.setAccessibleDescription(
            "Navigate between analysis result sections and plots."
        )
        self.graphics_view.setAccessibleName("Analysis figures")
        self.graphics_view.setAccessibleDescription(
            "View analysis summaries, references, and generated plots."
        )
        viewport = self.graphics_view.viewport()
        if viewport is None:
            raise RuntimeError("Results graphics view has no viewport")
        self._graphics_viewport = viewport
        viewport.installEventFilter(self)
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.RESULTS
        )
        restored_state = restore_results_window_state(self)
        self._restored_splitter_proportions = restored_state.splitter_proportions
        self.add_offset = 5
        self.borders = []
        self.plot_service = plot_service or PlotService()
        self._change_settings = change_settings
        self._prepared_manuscript = manuscript

        self.nav_tree.itemClicked.connect(
            app_error_handler.safe_slot(self.item_clicked, parent=self)
        )
        self.results_nav_splitter.splitterMoved.connect(
            app_error_handler.safe_slot(
                self._splitter_moved, parent=self
            )
        )

        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.setAccessibleName("Result sections")
        self.nav_tree.setAccessibleDescription("Choose a figure, the text report, data tables, or model configuration.")
        self.graphics_view.setAccessibleName("Analysis figures")
        self.graphics_view.setAccessibleDescription("Scrollable figures. Use the results toolbar to edit, zoom, or export the selected figure.")
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
        # Every content page scrolls. Its minimum size hint must not push the
        # fixed navigation outside a narrow screen when the splitter moves.
        self.content_stack.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding
        )
        self.results_nav_splitter.setChildrenCollapsible(False)
        self.results_nav_splitter.setStretchFactor(0, 0)
        self.results_nav_splitter.setStretchFactor(1, 5)
        self.x_coord = 5.0
        self.y_coord = 5.0

        self._splitter_restore_pending = True

        self.scene = QGraphicsScene(self)

        self._load_result(results)
        self._wrapped_text_items = []
        self.add_result_sections()
        self._relayout_sections()

        self.graphics_view.setScene(self.scene)
        self.graphics_view.ensureVisible(QRectF(0, 0, 0, 0))
        # Establish a starting width; the first visible refit applies saved
        # proportions again after the native window receives its final geometry.
        self._apply_restored_splitter_proportions()
        self._setup_report_controls(source_sheet_name)
        for entry in self._plots.values():
            if entry.scene_item is not None:
                self._restore_plot_override(entry.artifact, entry.scene_item)

    def _load_result(self, results: AnalysisResult) -> None:
        self.results = results = normalize_analysis_result(results)
        self.params_paths = results.image_params_paths
        self.texts = results.texts

    def replace_trial_sequential_result(self, results: AnalysisResult, manuscript: "ManuscriptReport") -> None:
        # TSA has one figure. Keep its navigation item and replace its scene
        # item and export artifact together so they always refer to the same run.
        section, = (section for section in results.sections if section.kind == "image")
        artifact = PlotArtifact.from_section(section)
        entry = self._plots[section.semantic_id]
        _, _, plot = self.create_plot_item(artifact, self.position())
        previous = entry.scene_item
        if previous is not None:
            self._layout_items.remove(previous)
            if previous in self._svg_plot_items:
                self._svg_plot_items.remove(previous)
            if previous in self._raster_plot_items:
                self._raster_plot_items.remove(previous)
            self.scene.removeItem(previous)
        entry.scene_item = plot
        entry.artifact = artifact
        self._load_result(results)
        self._plot_defaults.pop(artifact.title, None)
        self._restore_plot_override(artifact, plot)
        self.manuscript = manuscript
        self._refresh_manuscript_theme()
        self._load_report_tables()
        self._update_sensitivity_navigation()
        self._relayout_sections()
        self._schedule_viewport_refit()
        self.raise_()

    def _setup_report_controls(self, source_sheet_name: str | None):
        self._setup_identity(source_sheet_name)
        self._setup_manuscript_page()
        self._setup_result_tables()
        self._report_nav = QTreeWidgetItem(self.nav_tree, ["Text report"])
        self._report_nav.setToolTip(0, "Read the formatted analysis report")
        self._report_nav.setData(0, _REPORT_ANCHOR_ROLE, "")
        self._tables_nav = QTreeWidgetItem(self.nav_tree, ["Data tables"])
        self._tables_nav.setToolTip(0, "Inspect, copy, or export result tables.")
        self._tables_nav.setDisabled(not self._report_tables)
        self._setup_results_actions()
        sections = []
        if self.manuscript.methods:
            sections.append(('Methods', 'methods'))
        if self.manuscript.results:
            sections.append(('Results', 'results'))
        if self._report_tables:
            sections.append(('Report tables', 'report-tables'))
        if any(section.source_key == 'References' for section in self.manuscript.sections):
            sections.append(('References', 'references'))
        if self.results.details:
            sections.append(('Model configuration', 'model-configuration'))
        for title, anchor in sections:
            child = QTreeWidgetItem(self._report_nav, [title])
            child.setData(0, _REPORT_ANCHOR_ROLE, anchor)
        if self.results.analysis_method == "trial-sequential":
            self._sensitivity_nav = QTreeWidgetItem(["Sensitivity"])
            self._sensitivity_nav.setToolTip(0, "View trial sequential sensitivity analyses across alternative anticipated effects.")
            self._report_nav.insertChild(3, self._sensitivity_nav)
            self._sensitivity_nav.setData(0, _REPORT_ANCHOR_ROLE, "section-" + _SENSITIVITY_SECTION)
            self._update_sensitivity_navigation()
        self._report_nav.setExpanded(True)
        self.nav_tree.currentItemChanged.connect(lambda item, _previous: self.item_clicked(item, 0) if item is not None else None)
        self.nav_tree.setMinimumWidth(min(self.nav_tree.sizeHintForColumn(0) + 12, self.fontMetrics().height() * 12))
        required(self.nav_tree.header(), "Results navigation header").setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.nav_tree.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.nav_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_tree.setRootIsDecorated(True)
        self._refresh_navigation_palette()
        navigation = []
        for index in range(self.nav_tree.topLevelItemCount()):
            item = required(self.nav_tree.topLevelItem(index), 'result navigation item')
            if item is self._report_nav:
                action = self.report_action
            elif item is self._tables_nav:
                action = self.tables_action
            else:
                action = QAction(item.text(0), self)
                action.triggered.connect(lambda checked=False, item=item: self.nav_tree.setCurrentItem(item))
            if index < 9:
                action.setShortcuts([*action.shortcuts(), QKeySequence(f'Ctrl+{index + 1}')])
            action.setEnabled(not item.isDisabled())
            self.addAction(action)
            navigation.append(action)
        self.view_menu.addActions(navigation)
        self.view_menu.addSeparator()
        self.view_menu.addActions((self.fit_page_action, self.fit_width_action, *self.zoom_actions))
        self._show_initial_result()

    def _update_sensitivity_navigation(self) -> None:
        self._sensitivity_nav.setHidden(not any(
            section.semantic_id == _SENSITIVITY_SECTION for section in self.manuscript.primary_sections
        ))

    def _refresh_navigation_palette(self):
        palette = QPalette(QApplication.palette())
        highlight = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight)
        text = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText)
        self.nav_tree.setStyleSheet(f'QTreeWidget::item:selected {{ background-color: {highlight.name()}; color: {text.name()}; }}')
        for role in (QPalette.ColorRole.Highlight, QPalette.ColorRole.HighlightedText):
            palette.setColor(QPalette.ColorGroup.Inactive, role, palette.color(QPalette.ColorGroup.Active, role))
        self.nav_tree.setPalette(palette)

    def _show_initial_result(self):
        self._fit_width_active = True
        first_plot = next((entry for entry in self._plots.values() if entry.scene_item is not None), None)
        if first_plot is not None:
            self.nav_tree.setCurrentItem(first_plot.navigation_item)
        clinical = any(section.semantic_id.startswith("diagnostic.reitsma.summary")
                       for section in self.results.sections)
        self.report_action.setChecked(clinical or first_plot is None)
        self._show_report(self.report_action.isChecked())
        if self.report_action.isChecked():
            self._activate_report(True)
        self._set_restored_splitter_sizes()
        if not self.report_action.isChecked():
            self._apply_fit_width()

    def _identity_facts(self, workflow, context, rest, description, separator):
        details = [workflow] if context and workflow != 'Meta-analysis' else []
        model_info = dict(self.results.manuscript_model_info)
        study_count = model_info.get('Studies included', model_info.get('Studies (k)'))
        models, confidence = self._identity_model_details(self.results.details)
        study_count = _identity_context_facts(rest, details, confidence, study_count)
        if separator:
            details.append(description if description.startswith('Entered effect estimate') else description.rpartition(' · ')[2])
        details.extend(model + (f' ({estimator})' if estimator else '')
                       for model, estimator in dict.fromkeys(models))
        details.extend(line for line in self.results.details.splitlines() if line.startswith('Moderators: '))
        details.extend(dict.fromkeys(confidence))
        if study_count:
            details = [detail for detail in details if detail != study_count + ' eligible']
            suffix = ' included' if any(detail.endswith(' eligible') for detail in details) else (' study' if study_count == '1' else ' studies')
            details.append(study_count + suffix)
        details = list(dict.fromkeys(details))
        return details

    def _setup_identity(self, source_name: str | None):
        identity = self.results.identity or "Analysis results"
        workflow, _, context = identity.partition(" — ")
        first, *rest = context.splitlines() if context else identity.splitlines()
        name, separator, description = first.partition(" · ")
        if source_name and (first == source_name or first.startswith(source_name + ' · ')):
            name = source_name
            separator = ' · ' if first != source_name else ''
            description = first[len(source_name):].removeprefix(' · ')
        details = self._identity_facts(workflow, context, rest, description, separator)
        self.setWindowTitle(self._result_window_title(identity, details))
        title_font = QFont(self.font())
        title_font.setPointSizeF(title_font.pointSizeF() * 1.35)
        title_font.setWeight(QFont.Weight.DemiBold)
        self.result_identity.setFont(title_font)
        self.result_identity.setText(name[:1].upper() + name[1:])
        items = [f'<span style="white-space:nowrap">{escape(detail)}</span>'
                 if len(detail) <= 48 and not detail.startswith('Moderators: ') else escape(detail)
                 for detail in details]
        self.result_facts.setForegroundRole(QPalette.ColorRole.PlaceholderText)
        self._refresh_header_palette()
        self.result_facts.setText('&nbsp;&nbsp;·&nbsp; '.join(items))
        self.result_facts.setAccessibleDescription(' · '.join(details))
        self.result_identity.setToolTip(identity + '\n' + self.results.details)
        self.result_facts.setToolTip(self.result_identity.toolTip())
        self.result_identity.setContentsMargins(12, round(self.fontMetrics().height() * .25), 0, 0)
        self.result_facts.setContentsMargins(12, 0, 0, round(self.fontMetrics().height() * .5))
        self.results_body_layout.setSpacing(round(self.fontMetrics().height() * .5))
        margin = round(self.fontMetrics().height() * .75)
        self.verticalLayout.setContentsMargins(margin, margin, margin, margin)
        self.verticalLayout.setSpacing(round(self.fontMetrics().height() * .5))
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

    def _result_window_title(self, identity: str, details: list[str]) -> str:
        models, levels = self._identity_model_details(self.results.details)
        title_facts = [model + (f" ({estimator})" if estimator else "") for model, estimator in models]
        title_facts.extend(detail for detail in details if detail.startswith("Pooled display: "))
        title_facts.extend(levels or [detail for detail in details if detail.endswith("% CI")])
        return " · ".join((identity.splitlines()[0], *dict.fromkeys(title_facts)))

    def _refresh_header_palette(self):
        palette = QPalette(self.palette())
        secondary = palette.color(QPalette.ColorRole.WindowText)
        secondary.setAlpha(160)
        palette.setColor(QPalette.ColorRole.PlaceholderText, secondary)
        self.result_facts.setPalette(palette)

    @staticmethod
    def _identity_model_details(details):
        models = []
        confidence = []
        for line in details.splitlines():
            if line.startswith('Model: '):
                models.append((line.removeprefix('Model: '), ''))
            elif line.startswith('Estimator: ') and models:
                model, estimator = models[-1]
                value = re.sub(r'^.* \(([A-Z]+)\)$', r'\1', line.removeprefix('Estimator: '))
                models[-1] = (model, estimator + ', ' + value if estimator else value)
            elif line.startswith('Confidence level: '):
                confidence.append(line.removeprefix('Confidence level: ') + ' CI')
        return models, confidence

    def _setup_manuscript_page(self):
        from rc_metastudio.results.report import ManuscriptReport
        self.manuscript = self._prepared_manuscript if self._prepared_manuscript is not None else ManuscriptReport.from_result(self.results)
        self.manuscript_page = QWidget(self.content_stack)
        layout = QVBoxLayout(self.manuscript_page)
        self.manuscript_text = QTextBrowser(self.manuscript_page)
        self._manuscript_base_font = QFont(self.font())
        self._manuscript_base_font.setPointSizeF(max(11.0, self.font().pointSizeF()))
        self._manuscript_zoom_percent = 100
        self._figure_zoom_percent = 100
        self.manuscript_text.setFont(self._manuscript_base_font)
        self.manuscript_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.manuscript_text.setAccessibleName("Text report")
        manuscript_document = required(self.manuscript_text.document(), "manuscript document")
        option = manuscript_document.defaultTextOption()
        option.setWrapMode(QTextOption.WrapMode.WordWrap)
        manuscript_document.setDefaultTextOption(option)
        self._refresh_manuscript_theme()
        layout.addWidget(self.manuscript_text)
        self.content_stack.addWidget(self.manuscript_page)

    def _refresh_manuscript_theme(self):
        scrollbar = required(self.manuscript_text.verticalScrollBar(), "manuscript scrollbar")
        position = scrollbar.value()
        color = self.manuscript_text.palette().color(self.manuscript_text.foregroundRole()).name()
        self.manuscript_text.setHtml((self.manuscript.html(heading=False) + self.manuscript.html(supplementary=True))
                                     .replace('solid black', 'solid ' + color))
        scrollbar.setValue(position)

    def _refresh_theme(self):
        self._refresh_header_palette()
        self._refresh_navigation_palette()
        for item in self._wrapped_text_items:
            item.setDefaultTextColor(self.palette().color(self.foregroundRole()))
        self._refresh_manuscript_theme()
        if hasattr(self, "result_table"):
            header = required(self.result_table.horizontalHeader(), "result table header")
            header.setStyleSheet("QHeaderView::section { border: 0; border-bottom: 1px solid palette(mid); padding: 0 0.5em; }")
        for item in (*self._svg_plot_items, *self._raster_plot_items):
            for child in item.childItems():
                if isinstance(child, QGraphicsRectItem):
                    pen = QPen(self.palette().color(QPalette.ColorRole.Mid))
                    pen.setCosmetic(True)
                    child.setPen(pen)

    def changeEvent(self, event: QEvent | None) -> None:
        super().changeEvent(event)
        if event is not None and event.type() in (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange) and hasattr(self, "manuscript_text"):
            self._refresh_navigation_palette()
            QTimer.singleShot(0, self._refresh_theme)

    def _setup_result_tables(self):
        self.tables_page = QWidget(self.content_stack)
        layout = QVBoxLayout(self.tables_page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self.table_selector = QComboBox(self.tables_page)
        self.table_selector.setAccessibleName("Result table")
        self.table_selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.table_selector.setMinimumWidth(0)
        self.table_header_layout = QHBoxLayout()
        self.table_header_layout.addWidget(self.table_selector)
        self.table_header_layout.addStretch()
        layout.addLayout(self.table_header_layout)
        self.result_table = QTableWidget(self.tables_page)
        self.result_table.setTabKeyNavigation(False)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setShowGrid(False)
        self.result_table.setWordWrap(False)
        header = required(self.result_table.horizontalHeader(), "result table column header")
        header.setStyleSheet("QHeaderView::section { border: 0; border-bottom: 1px solid palette(mid); padding: 0 0.5em; }")
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        header.setStretchLastSection(False)
        header.setResizeContentsPrecision(-1)
        self._sizing_result_table = False
        for widget in (self.result_table, self.result_table.viewport(), header):
            required(widget, "table sizing surface").installEventFilter(self)
        self.result_table.setFont(self._manuscript_base_font)
        self.result_table.setAccessibleDescription("Read-only result cells with column headers. Ctrl+C copies selected cells, or the entire table when no cells are selected. Tab moves to the next control.")
        required(self.result_table.verticalHeader(), "result table row header").hide()
        layout.addWidget(self.result_table)
        self.table_note = QLabel(self.tables_page)
        qt_layout.configure_context_label(self.table_note)
        layout.addWidget(self.table_note)
        self.copy_table_action = QAction("Copy table", self)
        self.copy_table_action.triggered.connect(self._copy_table)
        copy_shortcut = QAction(self.result_table)
        copy_shortcut.setShortcut("Ctrl+C")
        copy_shortcut.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        copy_shortcut.triggered.connect(self._copy_table)
        self.result_table.addAction(copy_shortcut)
        self.export_table_action = QAction("Export formatted CSV…", self)
        self.export_table_action.triggered.connect(app_error_handler.safe_slot(self._export_table, parent=self))
        self.export_values_action = QAction("Export values CSV…", self)
        self.export_values_action.triggered.connect(app_error_handler.safe_slot(self._export_values, parent=self))
        for action in (self.export_table_action, self.export_values_action):
            action.setIcon(QIcon(':/icons/actions/export.svg'))
            button = QToolButton(self.tables_page)
            button.setDefaultAction(action)
            button.setAutoRaise(True)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            self.table_header_layout.addWidget(button)
        layout.addStretch()
        self.table_selector.currentIndexChanged.connect(self._select_result_table)
        self.content_stack.addWidget(self.tables_page)
        self._load_report_tables()

    def _load_report_tables(self) -> None:
        index = self.table_selector.currentIndex()
        self._report_tables = []
        self._report_table_notes = []
        with QSignalBlocker(self.table_selector):
            self.table_selector.clear()
            for section in self.manuscript.sections:
                for table in section.tables:
                    self._report_tables.append(table)
                    self._report_table_notes.append(
                        " ".join(section.paragraphs) if section.semantic_id.startswith("trial-sequential.") else "")
                    title = table.title if table.title == section.title or section.title.endswith(("Summary", "summary")) else section.title + " — " + table.title
                    self.table_selector.addItem(_report_heading(title))
            self.table_selector.setCurrentIndex(max(0, min(index, len(self._report_tables) - 1)))
        self._select_result_table(self.table_selector.currentIndex())

    def _select_result_table(self, index):
        if not 0 <= index < len(self._report_tables):
            return
        table = self._report_tables[index]
        note = self._report_table_notes[index]
        self.table_note.setText(note)
        self.table_note.setVisible(bool(note))
        self.export_values_action.setEnabled(bool(table.quantities))
        self.export_values_action.setStatusTip('Export unrounded values with their scales and confidence levels' if table.quantities else 'Only formatted values are available for this table.')
        self.export_values_action.setToolTip(self.export_values_action.statusTip())
        self.result_table.clear()
        self.result_table.setColumnCount(len(table.headers))
        self.result_table.setRowCount(len(table.rows))
        self.result_table.setHorizontalHeaderLabels([
            "\n".join(textwrap.wrap(label, width=16, break_long_words=False, break_on_hyphens=False))
            for label in table.headers
        ])
        self.result_table.setAccessibleName(_report_heading(table.title))
        for row_index, row in enumerate(table.rows):
            for column_index, cell in enumerate(row):
                item = QTableWidgetItem(cell)
                if _numeric_cell(cell):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.result_table.setItem(row_index, column_index, item)
        header_font = QFont(self.result_table.font())
        header_font.setBold(True)
        required(self.result_table.horizontalHeader(), "result table header").setFont(header_font)
        numeric = numeric_columns(table.rows) or (False,) * len(table.headers)
        for column_index in range(len(table.headers)):
            alignment = Qt.AlignmentFlag.AlignRight if numeric[column_index] else Qt.AlignmentFlag.AlignLeft
            required(self.result_table.horizontalHeaderItem(column_index), "result column header").setTextAlignment(alignment | Qt.AlignmentFlag.AlignVCenter)
        self._size_result_table_columns()

    def _size_result_table_columns(self):
        table = self.result_table
        count = table.columnCount()
        if self._sizing_result_table or not count:
            return
        headers = [table.horizontalHeaderItem(column) for column in range(count)]
        if any(item is None for item in headers):
            return
        self._sizing_result_table = True
        try:
            header = required(table.horizontalHeader(), "result table column header")
            metrics = header.fontMetrics()
            minimums = []
            for column, item in enumerate(headers):
                minimum = self._result_column_minimum(column, item, header, metrics)
                minimums.append(minimum)
            for column, minimum in enumerate(minimums):
                table.setColumnWidth(column, minimum + 16)
            table.setMaximumWidth(sum(table.columnWidth(column) for column in range(count)) + 2 * table.frameWidth()
                                  + required(table.verticalScrollBar(), "table vertical scrollbar").sizeHint().width())
            table.resizeRowsToContents()
            scrollbar_height = (required(table.horizontalScrollBar(), "table scrollbar").sizeHint().height()
                                if sum(table.columnWidth(column) for column in range(count)) > required(table.viewport(), "table viewport").width() else 0)
            table.setMaximumHeight(header.sizeHint().height()
                                   + sum(table.rowHeight(row) for row in range(table.rowCount()))
                                   + 2 * table.frameWidth() + scrollbar_height)
        finally:
            self._sizing_result_table = False

    def _result_column_minimum(self, column, item, header, metrics):
        table = self.result_table
        minimum = max(
            header.minimumSectionSize(),
            max((metrics.horizontalAdvance(line) for line in required(item, "table header").text().splitlines()), default=0) + 8,
            table.sizeHintForColumn(column),
        )
        for row in range(table.rowCount()):
            cell = table.item(row, column)
            if cell is None:
                continue
            font = cell.data(Qt.ItemDataRole.FontRole)
            cell_metrics = QFontMetrics(font) if font is not None else table.fontMetrics()
            minimum = max(minimum, max((cell_metrics.horizontalAdvance(line)
                                       for line in cell.text().splitlines()), default=0) + 8)
        return minimum

    def _table_rows(self, selected=False):
        table = self._report_tables[self.table_selector.currentIndex()]
        headers, rows = table.headers, table.rows
        indexes = self.result_table.selectedIndexes() if selected else []
        if indexes:
            top, bottom = min(item.row() for item in indexes), max(item.row() for item in indexes)
            left, right = min(item.column() for item in indexes), max(item.column() for item in indexes)
            headers = ()
            rows = tuple(row[left:right + 1] for row in table.rows[top:bottom + 1])
        return headers, rows

    def _table_payload(self, delimiter, selected=False):
        headers, rows = self._table_rows(selected)
        stream = io.StringIO(newline="")
        csv.writer(stream, delimiter=delimiter, lineterminator="\n").writerows([headers, *rows] if headers else rows)
        return stream.getvalue()

    def _copy_table(self):
        from PyQt6.QtCore import QMimeData
        from rc_metastudio.results.formatting import table_html
        headers, rows = self._table_rows(selected=True)
        mime = QMimeData()
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        if headers:
            writer.writerow(headers)
        writer.writerows([report_cell(cell) if _numeric_cell(cell) else cell for cell in row]
                         for row in rows)
        mime.setText(stream.getvalue())
        mime.setHtml(table_html(headers, rows))
        required(QApplication.clipboard(), "system clipboard").setMimeData(mime)
        scope = "Table" if headers else "Cell" if len(rows) == 1 and len(rows[0]) == 1 else "Selection"
        self.statusbar.showMessage(f"{scope} copied", 4000)

    def _export_table(self):
        table = self._report_tables[self.table_selector.currentIndex()]
        path, _filter = QFileDialog.getSaveFileName(self, "Export result table", self._export_name(table.title, "csv"), "CSV table (*.csv)")
        if path:
            with staged_output(path) as temporary, temporary.open("w", encoding="utf-8-sig", newline="") as stream:
                stream.write(self._table_payload(","))
            QSettings().setValue("export/last_directory", str(Path(path).resolve().parent))
            self.statusbar.showMessage(f"Saved table: {Path(path).resolve()}", 4000)

    def _export_values(self):
        table = self._report_tables[self.table_selector.currentIndex()]
        if not table.quantities:
            return
        path, _filter = QFileDialog.getSaveFileName(self, 'Export numeric result values', self._export_name(table.title + '-values', 'csv'), 'CSV values (*.csv)')
        if not path:
            return
        with staged_output(path) as temporary, temporary.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.writer(stream, lineterminator='\n')
            writer.writerow(('Table', 'Row', 'Column', 'Quantity', 'Value', 'Scale', 'Level', 'Display'))
            for row, numbers in zip(table.rows, table.quantities):
                identity = ' / '.join(cell for header, cell, qs in zip(table.headers, row, numbers)
                                      if not qs and cell not in ('', '—', 'NA', 'Not estimable') and header != 'SE scale')
                for header, cell, quantities in zip(table.headers, row, numbers):
                    for q in quantities:
                        writer.writerow((table.title, identity, header, q.role, '' if q.value is None else repr(q.value),
                                         q.scale, '' if q.level is None else f'{q.level:g}', cell))
        QSettings().setValue("export/last_directory", str(Path(path).resolve().parent))
        self.statusbar.showMessage(f'Saved values: {Path(path).resolve()}', 4000)

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
        self.nav_tree.setCurrentItem(self._tables_nav)
        self.nav_tree.blockSignals(False)
        self.result_table.setFocus()

    def _activate_report(self, checked):
        item = self._report_nav if checked else self._last_plot_item
        if item is not None:
            self.nav_tree.setCurrentItem(item)

    def _setup_results_actions(self):
        toolbar = required(self.addToolBar("Results actions"), "results toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.report_action = QAction("Text report", self)
        self.report_action.setCheckable(True)
        self.report_action.setShortcuts([QKeySequence("Ctrl+T"), QKeySequence("Ctrl+M")])
        self.report_action.toggled.connect(self._show_report)
        self.report_action.triggered.connect(self._activate_report)
        self.tables_action = QAction("Data tables", self)
        self.tables_action.setShortcut("Ctrl+Shift+T")
        self.tables_action.setEnabled(bool(self._report_tables))
        self.tables_action.triggered.connect(self._show_tables)
        self.edit_menu = required(self.menubar.addMenu("&Edit"), "Edit menu")
        for section in ("methods", "results"):
            action = required(self.edit_menu.addAction("Copy " + section + " section"), "copy section action")
            action.triggered.connect(lambda checked=False, section=section: self._copy_section(
                section.capitalize(), getattr(self.manuscript, section)
            ))
            action.setEnabled(bool(getattr(self.manuscript, section)))
        self.edit_menu.addAction(self.copy_table_action)
        self.content_stack.currentChanged.connect(lambda: self.copy_table_action.setEnabled(self.content_stack.currentWidget() is self.tables_page))
        self.copy_table_action.setEnabled(False)
        self.export_report_action = QAction("Export report…", self)
        self.export_report_action.setIcon(QIcon(':/icons/actions/export.svg'))
        self.export_report_action.setShortcut("Ctrl+Shift+S")
        self.export_report_action.setToolTip('Export the text report, tables, and figures to PDF or Word (DOCX).')
        self.export_report_action.triggered.connect(app_error_handler.safe_slot(self._export_report, parent=self))
        toolbar.addAction(self.export_report_action)
        self.export_plot_action = QAction("Export plot…", self)
        self.export_plot_action.setIcon(QIcon(':/icons/actions/export.svg'))
        self.export_plot_action.setToolTip("Select a plot to export (Ctrl+Shift+E)")
        self.export_plot_action.setShortcut("Ctrl+Shift+E")
        self.export_plot_action.setEnabled(False)
        self.export_plot_action.triggered.connect(app_error_handler.safe_slot(self._export_selected_plot, parent=self))
        toolbar.addAction(self.export_plot_action)
        toolbar.addSeparator()
        self.edit_plot_action = QAction("Edit plot…", self)
        self.edit_plot_action.setIcon(QIcon(':/icons/actions/edit-plot.svg'))
        self.edit_plot_action.setShortcut('Ctrl+E')
        self.edit_plot_action.setToolTip('Select a plot to edit (Ctrl+E)')
        self.edit_plot_action.setEnabled(False)
        self.edit_plot_action.triggered.connect(app_error_handler.safe_slot(self._edit_selected_plot, parent=self))
        toolbar.addAction(self.edit_plot_action)
        self.change_settings_action = QAction("Change settings…", self)
        self.change_settings_action.setIcon(QIcon(':/icons/actions/settings.svg'))
        self.change_settings_action.setShortcut('Ctrl+Shift+R')
        self.change_settings_action.setEnabled(self._change_settings is not None)
        self.change_settings_action.setToolTip("Rerun this analysis with its original dataset and changed settings (Ctrl+Shift+R)." if self._change_settings else "This analysis cannot be rerun from here.")
        if self._change_settings is not None:
            self.change_settings_action.triggered.connect(app_error_handler.safe_slot(self._change_analysis_settings, parent=self))
        toolbar.addAction(self.change_settings_action)
        toolbar.addSeparator()
        zoom_widget = QWidget(toolbar)
        zoom_layout = QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.addWidget(QLabel("Zoom", zoom_widget))
        self.zoom_control = QSpinBox(self)
        self.zoom_control.setAccessibleName("Result zoom")
        self.zoom_control.setRange(10, 400)
        self.zoom_control.setSingleStep(25)
        self.zoom_control.setSuffix("%")
        self.zoom_control.setValue(100)
        self.zoom_control.valueChanged.connect(self._set_zoom)
        zoom_layout.addWidget(self.zoom_control)
        toolbar.addWidget(zoom_widget)
        self.fit_page_action = QAction(QIcon(':/icons/actions/fit-page.svg'), 'Fit page', self)
        self.fit_page_action.setShortcut('Ctrl+0')
        self.fit_page_action.setToolTip('Fit the plot while keeping text readable (Ctrl+0)')
        self.fit_page_action.triggered.connect(self._fit_page)
        toolbar.addAction(self.fit_page_action)
        self.fit_width_action = QAction("Fit width", self)
        self.fit_width_action.setIcon(QIcon(':/icons/actions/fit-width.svg'))
        self.fit_width_action.setShortcut('Ctrl+Shift+0')
        self.fit_width_action.setToolTip('Fill the available plot width (Ctrl+Shift+0)')
        self.fit_width_action.triggered.connect(self._fit_width)
        toolbar.addAction(self.fit_width_action)
        self.fit_width_action.changed.connect(lambda: self.fit_page_action.setEnabled(self.fit_width_action.isEnabled()))
        self.zoom_actions = []
        for text, shortcut, delta in (('Zoom in', 'Ctrl+=', 25), ('Zoom out', 'Ctrl+-', -25)):
            action = QAction(text, self)
            action.setShortcut(shortcut)
            action.triggered.connect(lambda checked=False, delta=delta: self.zoom_control.setValue(self.zoom_control.value() + delta) if self.zoom_control.isEnabled() else None)
            self.addAction(action)
            self.zoom_actions.append(action)
        qt_layout.configure_main_toolbar(toolbar)
        for action in (self.fit_page_action, self.fit_width_action):
            button = toolbar.widgetForAction(action)
            if isinstance(button, QToolButton):
                button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        for button in toolbar.findChildren(QToolButton):
            action = button.defaultAction()
            if action is not None:
                button.setAccessibleName(action.text())
                button.setAccessibleDescription(action.toolTip() or action.text())
                button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                # Keep command labels readable; Qt moves whole controls into
                # toolbar overflow when the window cannot fit them.
                button.setMinimumWidth(button.sizeHint().width())
        self.setTabOrder(self.nav_tree, self.graphics_view)
        self.setTabOrder(self.table_selector, self.result_table)
        self.setTabOrder(self.result_table, self.nav_tree)
        file_menu = required(self.menubar.addMenu("&File"), "File menu")
        self.menubar.insertMenu(self.edit_menu.menuAction(), file_menu)
        file_menu.addActions((self.export_report_action, self.export_plot_action))
        file_menu.addSeparator()
        close_action = required(file_menu.addAction("Close"), "Close action")
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close)
        self.view_menu = required(self.menubar.addMenu("&View"), "View menu")
        analysis_menu = required(self.menubar.addMenu("&Analysis"), "Analysis menu")
        analysis_menu.addActions((self.edit_plot_action, self.change_settings_action))

    def _fit_page(self):
        if self.content_stack.currentWidget() is not self.figure_page:
            return
        self._explicit_fit_width = False
        self._fit_width_active = True
        self._apply_fit_width()

    def _fit_width(self):
        if self.content_stack.currentWidget() is not self.figure_page:
            return
        self._explicit_fit_width = True
        self._fit_width_active = True
        self._apply_fit_width()

    def _apply_fit_width(self):
        self.graphics_view.resetTransform()
        self._refit_viewport_items()
        selected = self._selected_plot()
        self._figure_zoom_percent = round((selected[1].scale() if selected else 1) * 100)
        if self.content_stack.currentWidget() is self.figure_page:
            self._update_zoom_control(self._figure_zoom_percent)
        self._scroll_to_section(self.nav_tree.currentItem())

    def _scroll_to_section(self, item):
        required(self.graphics_view.horizontalScrollBar(), "horizontal scrollbar").setValue(0)
        entry = self._plot_entry(item)
        if entry is not None and entry.scene_item is not None:
            index = self._layout_items.index(entry.scene_item)
            heading = self._layout_items[max(0, index - 1)]
            required(self.graphics_view.verticalScrollBar(), "figure scrollbar").setValue(round(heading.sceneBoundingRect().top() * self.graphics_view.transform().m22()))

    def _set_zoom(self, percent):
        page = self.content_stack.currentWidget()
        if page is self.manuscript_page:
            self._manuscript_zoom_percent = percent
            font = QFont(self._manuscript_base_font)
            font.setPointSizeF(font.pointSizeF() * percent / 100)
            self.manuscript_text.setFont(font)
        elif page is self.figure_page:
            self._fit_width_active = False
            self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self._figure_zoom_percent = percent
            self._refit_svg_plot_items()
            self._refit_raster_plot_items()
            self.graphics_view.setTransform(QTransform.fromScale(percent / 100, percent / 100))
            self._relayout_sections()
            required(self.graphics_view.horizontalScrollBar(), "horizontal scrollbar").setValue(0)

    def _show_report(self, checked):
        if checked:
            self.export_plot_action.setEnabled(False)
            self.edit_plot_action.setEnabled(False)
        item = self.nav_tree.currentItem()
        if checked and item is not self._tables_nav and (
            item is None or item.data(0, _REPORT_ANCHOR_ROLE) is None
        ):
            with QSignalBlocker(self.nav_tree):
                self.nav_tree.setCurrentItem(self._report_nav)
        self.content_stack.setCurrentWidget(self.manuscript_page if checked else self.figure_page)
        self.zoom_control.setEnabled(True)
        self.fit_width_action.setEnabled(not checked)
        self._update_zoom_control(self._manuscript_zoom_percent if checked else self._figure_zoom_percent)

    def _update_zoom_control(self, percent):
        self.zoom_control.blockSignals(True)
        self.zoom_control.setValue(percent)
        self.zoom_control.blockSignals(False)

    def _copy_section(self, name, text):
        required(QApplication.clipboard(), "clipboard").setText(text)
        self.statusbar.showMessage(name + " copied", 4000)

    def _export_report(self):
        from rc_metastudio.results.report import write_docx, write_pdf
        path, selected = QFileDialog.getSaveFileName(self, "Export report", self._export_name("report", "pdf"), "PDF (*.pdf);;Word document (*.docx)")
        if path:
            extension = "docx" if "docx" in selected else "pdf"
            destination = str(Path(path).with_suffix("." + extension))
            if not self._confirm_export_destination(path, destination):
                return
            path = destination
            report = self.manuscript
            (write_docx if extension == "docx" else write_pdf)(report, path)
            QSettings().setValue("export/last_directory", str(Path(path).resolve().parent))
            self.statusbar.showMessage(f"Saved report: {Path(path).resolve()}", 4000)

    def _confirm_export_destination(self, selected, destination):
        # The save dialog confirmed the entered name, before suffix normalization.
        if selected != destination and Path(destination).exists():
            return QMessageBox.question(
                self, "Replace existing file?",
                f"This file already exists:\n{destination}\n\nReplace it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            ) == QMessageBox.StandardButton.Yes
        return True

    def _export_name(self, title, extension):
        context = (self.results.identity or "Analysis results").split("\n")[0]
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", context + " — " + title)
        directory = Path(str(QSettings().value("export/last_directory", "")))
        return str(directory / (name.strip(" .")[:160] + "." + extension))

    def _plot_entry(self, item: QTreeWidgetItem | None) -> _PlotEntry | None:
        if item is None:
            return None
        entry = self._plots.get(item.data(0, _PLOT_ID_ROLE))
        return entry if entry is not None and entry.scene_item is not None else None

    def _selected_plot(self):
        entry = self._plot_entry(self.nav_tree.currentItem())
        if entry is None or entry.scene_item is None:
            return None
        return entry.artifact, entry.scene_item

    def _export_selected_plot(self):
        selected = self._selected_plot()
        if selected is not None:
            artifact, _item = selected
            self.save_image_as(artifact, None if artifact.params_path else QPixmap(artifact.image_path), format=None)

    def _change_analysis_settings(self):
        if self._change_settings is None:
            return
        plot_parameters = {}
        entry = self._plot_entry(self.nav_tree.currentItem()) or self._plot_entry(self._last_plot_item)
        artifact = entry.artifact if entry is not None else None
        if artifact is not None and artifact.capability.regenerator == "forest" and artifact.params_path is not None:
            params = self.plot_service.load_params(artifact.params_path)
            if params is not None:
                plot_parameters = params
        self._change_settings(plot_parameters, self)

    def _edit_selected_plot(self):
        selected = self._selected_plot()
        if selected is not None:
            self.edit_plot(*selected)

    def add_result_sections(self):
        for section in sorted(self.results.sections, key=lambda item: item.order):
            if section.kind == "image":
                self.add_image_section(section)

    def add_image_section(self, section: ResultSection):
        artifact = PlotArtifact.from_section(section)
        qt_item = self.add_title("Meta-regression bubble plot" if section.source_key == "Regression Plot" else section.title)
        qt_item.setData(0, _PLOT_ID_ROLE, section.semantic_id)
        entry = _PlotEntry(artifact, qt_item)
        self._plots[section.semantic_id] = entry
        try:
            _, _, plot_item = self.create_plot_item(artifact, self.position())
        except Exception as error:
            app_error_handler.log_exception(type(error), error, error.__traceback__)
            self.add_title("Could not load plot. Text results are still available.")
            return

        entry.scene_item = plot_item

    def plot_artifact(self, source_key):
        section = next(
            section for section in self.results.sections
            if section.kind == "image" and section.source_key == source_key
        )
        return PlotArtifact.from_section(section)

    def generate_pixmap(self, image):
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
        renderer = svg_item.renderer()
        text_size = renderer.property("body_text_size")
        text_pixels = text_size * item_width / renderer.viewBoxF().width() if text_size else 0
        target_scale = self._automatic_plot_scale(svg_item, target_scale, item_height, text_pixels)
        scaled_width, scaled_height = item_width * target_scale, item_height * target_scale
        if target_scale != svg_item.scale():
            svg_item.setScale(target_scale)
        return scaled_width, scaled_height

    def _automatic_plot_scale(self, item, target_scale, height, body_pixels):
        if self._explicit_fit_width:
            return target_scale
        kind = item.data(0)
        if kind != 'trial_sequential':
            target_scale = min(target_scale, 1.0)
        if kind and not str(kind).endswith('forest'):
            index = self._layout_items.index(item) if item in self._layout_items else len(self._layout_items)
            heading = self._layout_items[index - 1] if index else None
            heading_height = heading.boundingRect().height() if isinstance(heading, QGraphicsTextItem) else 0
            available = self.graphics_view.maximumViewportSize().height() - heading_height - SECTION_SPACING - 2 * padding
            target_scale = min(target_scale, max(1, available) / height)
        if body_pixels:
            target_scale = max(target_scale, math.nextafter(12 / body_pixels, math.inf))
        return target_scale

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
        text.setDefaultTextColor(self.palette().color(self.foregroundRole()))
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
        if item is self._tables_nav:
            self._show_tables()
            return
        anchor = item.data(0, _REPORT_ANCHOR_ROLE)
        if anchor is not None:
            self.report_action.setChecked(True)
            self._show_report(True)
            self.manuscript_text.scrollToAnchor(anchor)
            if not anchor:
                required(self.manuscript_text.verticalScrollBar(), "report scrollbar").setValue(0)
            self.export_plot_action.setEnabled(False)
            self.edit_plot_action.setEnabled(False)
            return
        self._scroll_to_section(item)
        if getattr(self, "_fit_width_active", False):
            self._apply_fit_width()
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
        if self._refitting_viewport_items:
            return
        self._refitting_viewport_items = True
        previous_width = self._viewport_width_override
        horizontal = required(self.graphics_view.horizontalScrollBar(), "figure horizontal scrollbar")
        vertical = required(self.graphics_view.verticalScrollBar(), "figure vertical scrollbar")
        full_width = self.graphics_view.maximumViewportSize().width()
        full_height = self.graphics_view.maximumViewportSize().height()
        if self.graphics_view.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOn:
            full_width += vertical.sizeHint().width()
        if self.graphics_view.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOn:
            full_height += horizontal.sizeHint().height()
        try:
            if self._fit_width_active:
                self._viewport_width_override = full_width
            self._update_wrapped_text_widths()
            self._refit_svg_plot_items()
            self._refit_raster_plot_items()
            self._relayout_sections()
            if self._fit_width_active:
                # Decide from the full viewport, then reserve any required bars.
                # Reconsidering vertical overflow after narrowing can oscillate.
                needs_horizontal = self.scene.width() > full_width
                available_height = full_height - (horizontal.sizeHint().height() if needs_horizontal else 0)
                needs_vertical = self.scene.height() > available_height
                if needs_vertical:
                    self._viewport_width_override = full_width - vertical.sizeHint().width()
                    self._update_wrapped_text_widths()
                    self._refit_svg_plot_items()
                    self._refit_raster_plot_items()
                    self._relayout_sections()
                    needs_horizontal = self.scene.width() > self._viewport_width_override
                self.graphics_view.setHorizontalScrollBarPolicy(
                    Qt.ScrollBarPolicy.ScrollBarAlwaysOn if needs_horizontal else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
                )
                self.graphics_view.setVerticalScrollBarPolicy(
                    Qt.ScrollBarPolicy.ScrollBarAlwaysOn if needs_vertical else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
                )
        finally:
            self._viewport_width_override = previous_width
            self._refitting_viewport_items = False

    def _schedule_viewport_refit(self):
        if self._closing or self._viewport_refit_pending:
            return
        self._viewport_refit_pending = True
        self._viewport_refit_timer.start(0)

    def _splitter_moved(self, _position, _index):
        self._splitter_user_sized = True
        self._schedule_viewport_refit()

    def _run_scheduled_viewport_refit(self):
        self._viewport_refit_pending = False
        if not self._closing and self.isVisible():
            if self._first_show_refit_pending:
                self._first_show_refit_pending = False
                self._set_restored_splitter_sizes()
                self._viewport_width_override = self._layout_viewport_width()
            try:
                if getattr(self, "_fit_width_active", False):
                    self._apply_fit_width()
                else:
                    self._refit_viewport_items()
            finally:
                self._viewport_width_override = None

    def eventFilter(
        self, watched: QObject | None, event: QEvent | None
    ) -> bool:
        if (
            event is not None
            and event.type() == QEvent.Type.Resize
            and watched is self._graphics_viewport
            and not self._refitting_viewport_items
        ):
            if self.isVisible() and not self._refitting_svg_plots:
                self._viewport_refit_timer.stop()
                self._run_scheduled_viewport_refit()
            else:
                self._schedule_viewport_refit()
        table = getattr(self, "result_table", None)
        if table is not None and event is not None and event.type() in (
            QEvent.Type.Resize, QEvent.Type.FontChange, QEvent.Type.StyleChange,
        ) and watched in (table, table.viewport(), table.horizontalHeader()):
            self._size_result_table_columns()
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

                if self._fit_width_active:
                    self._fit_vector_plot_to_viewport(item)
                else:
                    item.setScale(1)
        finally:
            self._refitting_svg_plots = False

    def _refit_raster_plot_items(self):
        for item in self._raster_plot_items:
            source = QPixmap(item.source_path) if item.source_path else item.source_pixmap
            if source.isNull():
                continue
            logical_width, logical_height = _pixmap_device_independent_size(source)
            scaled_width, _scaled_height = self._fit_size_to_viewport(
                logical_width, logical_height
            )
            item.setPixmap(source)
            scale = self._automatic_plot_scale(item, float(scaled_width) / float(logical_width), logical_height, 0)
            item.setScale(scale if self._fit_width_active else 1)

    def _relayout_sections(self):
        """Place every result item from its current measured size and stored order."""
        next_y = float(self.add_offset)
        for item in self._layout_items:
            if isinstance(item, QGraphicsTextItem):
                item.setScale(1 / self.graphics_view.transform().m22())
            item.setPos(self.x_coord, next_y)
            next_y = math.ceil(item.sceneBoundingRect().bottom())
            if not isinstance(item, QGraphicsTextItem):
                next_y += SECTION_SPACING

        self.y_coord = next_y

        scene_bounds = self.scene.itemsBoundingRect()
        # layout-audit: allow=intrinsic-ratio; reason=scene follows its intrinsic-ratio visual artifact
        self.scene.setSceneRect(
            0,
            0,
            max(self._layout_viewport_width(), scene_bounds.right() + padding),
            max(1, scene_bounds.bottom() + padding),
        )

    def showEvent(
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
        proportions = self._restored_splitter_proportions
        if proportions is not None:
            sizes = [max(1, int(splitter_extent * value)) for value in proportions]
        else:
            em = self.fontMetrics().height()
            max_navigation = int(splitter_extent * DEFAULT_RESULTS_SPLITTER_PROPORTIONS[0])
            navigation = min(max(self.nav_tree.sizeHintForColumn(0) + 2 * em, 12 * em), max_navigation)
            sizes = [navigation, splitter_extent - navigation]
        self.results_nav_splitter.setSizes(sizes)

    def resizeEvent(
        self, event: QResizeEvent | None
    ) -> None:
        super(ResultsWindow, self).resizeEvent(event)
        if self._restored_splitter_proportions is not None and not self._splitter_user_sized:
            self._first_show_refit_pending = True
        self._schedule_viewport_refit()

    def closeEvent(
        self, event: QCloseEvent | None
    ) -> None:
        sizes = self.results_nav_splitter.sizes() if self._splitter_user_sized else None
        save_results_window_state(self, sizes)
        super(ResultsWindow, self).closeEvent(event)
        if event is not None and not event.isAccepted():
            return
        # A later modal loop may deliver deferred deletion. Stop rendering while
        # the window, viewport and scene are still alive, before that boundary.
        self._closing = True
        self._viewport_refit_timer.stop()
        self._viewport_refit_pending = False
        self._graphics_viewport.removeEventFilter(self)
        self.graphics_view.setScene(None)
        self.deleteLater()

    def create_pixmap_item(self, pixmap, position, artifact):
        item = ResponsivePixmapItem(QPixmap(artifact.image_path))
        item.setData(0, artifact.plot_kind)
        item.source_path = artifact.image_path
        item.setPixmap(pixmap)
        item.setToolTip(
            'Right-click the plot and choose Export plot…, or press Ctrl+Shift+E.'
        )

        self.y_coord += item.boundingRect().size().height() + SECTION_SPACING
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
        self._outline_plot_paper(item)
        self._raster_plot_items.append(item)
        self._layout_items.append(item)
        item.setPos(position)

        item.contextMenuEvent = self._make_context_menu(artifact, item)

        return (item.boundingRect().size(), position, item)

    def _outline_plot_paper(self, item):
        outline = QGraphicsRectItem(item.boundingRect().adjusted(.5, .5, -.5, -.5), item)
        pen = QPen(self.palette().color(QPalette.ColorRole.Mid))
        pen.setCosmetic(True)
        outline.setPen(pen)
        outline.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def create_plot_item(self, artifact, position):
        if artifact.has_vector_display():
            svg_item = self.create_svg_item(artifact, position)
            if svg_item is not None:
                return svg_item

        pixmap = self.generate_pixmap(artifact.image_path)
        if pixmap.isNull():
            raise ValueError("Plot image could not be decoded")
        return self.create_pixmap_item(pixmap, position, artifact)

    def create_svg_item(self, artifact, position):
        renderer = _opaque_svg_renderer(artifact.display_path(), self)
        if not renderer.isValid():
            return None
        item = _svg_item_class()()
        item.setData(0, artifact.plot_kind)
        item.setSharedRenderer(renderer)

        item.setToolTip(
            'Right-click the plot and choose Export plot…, or press Ctrl+Shift+E.'
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
        self._outline_plot_paper(item)
        self._svg_plot_items.append(item)
        self._layout_items.append(item)
        item.setPos(position)
        item.contextMenuEvent = self._make_context_menu(artifact, item)

        return (item.boundingRect().size(), position, item)

    def _make_context_menu(self, artifact, plot_item):
        def _graphics_item_context_menu(event):
            context_menu = QMenu(self)
            if artifact.capability.editable:
                if plot_capabilities.option_groups(artifact.plot_kind):
                    action = QAction("Edit plot…", self)
                    action.setStatusTip(
                        "Edit this figure's appearance."
                    )
                    action.setToolTip(
                        "Edit this figure's appearance."
                    )
                    action.setWhatsThis("Edit this figure's appearance.")
                    action.triggered.connect(
                        app_error_handler.safe_slot(
                            lambda _checked=False: self.edit_plot(artifact, plot_item),
                            parent=self,
                        )
                    )
                    context_menu.addAction(action)
            export_action = required(context_menu.addAction("Export plot…"), "plot export action")
            export_action.triggered.connect(app_error_handler.safe_slot(lambda: self.save_image_as(artifact), parent=self))

            app_error_handler.popup_context_menu(
                context_menu, event.screenPos(), parent=self, event=event
            )

        return _graphics_item_context_menu

    def edit_plot(self, artifact, plot_item):
        regenerator = artifact.capability.regenerator
        if regenerator == "none":
            return
        plot_params = self.plot_service.load_params(artifact.params_path)
        if plot_params is None:
            return
        defaults = self._plot_defaults.setdefault(artifact.title, plot_params)

        def commit(parameters: dict[str, object]) -> None:
            self._apply_plot_edits(parameters, artifact, plot_item)

        if regenerator == "funnel":
            dialog = FunnelPlotEditorDialog(
                plot_params, artifact.image_path, parent=self, plot_type=artifact.plot_kind,
                on_commit=commit, default_params=defaults,
            )
        else:
            dialog = EditPlotDialog(
                plot_params, artifact.image_path, parent=self, plot_type=artifact.plot_kind,
                on_commit=commit, default_params=defaults,
            )
            if regenerator == "forest":
                reopen = self._change_settings
                dialog.sequence_rerun.setEnabled(reopen is not None)
                if reopen is not None:
                    dialog.rerun_requested.connect(lambda: reopen(dialog.plot_params(), self))

        dialog.exec()

    def _restore_plot_override(self, artifact, plot_item):
        params = self._plot_overrides.get(artifact.title)
        if params and artifact.params_path:
            defaults = self.plot_service.load_params(artifact.params_path)
            if defaults is not None:
                self._plot_defaults[artifact.title] = defaults
                self._apply_plot_edits(params, artifact, plot_item, persist=False)

    def _apply_plot_edits(self, updated_params, artifact, plot_item, *, persist=True):
        regenerator = artifact.capability.regenerator
        output_parameter = {
            "forest": "fp_outpath", "regression": "bp_outpath",
            "sroc": "fp_outpath", "funnel": "funnel.outpath", "trial_sequential": "fp_outpath",
        }[regenerator]
        outpath = updated_params.get(output_parameter) or artifact.image_path
        self.plot_service.apply_edits(
            regenerator=regenerator, params_path=artifact.params_path,
            updated_params=updated_params, output_path=outpath,
        )

        if persist and self._save_plot_override is not None:
            exclusions = {"fp_outpath", "fp_display_path", "bp_outpath", "bp_display_path",
                          "funnel.outpath", "funnel.kind", "funnel.index", "funnel.center"}
            overrides = {name: value for name, value in updated_params.items()
                         if name not in exclusions and (name in {"plot_caption", "tsa_x_axis"}
                             or name.startswith(("fp_", "bp_", "funnel.")))}
            self._plot_overrides[artifact.title] = overrides
            self._save_plot_override(artifact.title, overrides)
        self._refresh_plot_item(plot_item, artifact, outpath)

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
                    plot_item.source_path = outpath
                    self._schedule_viewport_refit()

    def _plot_export_options(self, artifact, unscaled_image):
        from rc_metastudio.results.plot_export import PlotExportDialog
        from rc_metastudio.results.plot_service import svg_view_box_size
        text_per_inch = (0.0, 0.0)
        forest_geometry = None
        native_dpi = 96
        if artifact.has_vector_display():
            view_width, view_height = svg_view_box_size(artifact.display_path())
            width = view_width / 72
            ratio = view_width / view_height
            if artifact.params_path and artifact.capability.plot_kind in {
                "forest", "cumulative_forest", "leave_one_out_forest", "subgroup_forest",
            }:
                from functools import partial
                from rc_metastudio import r_bridge
                forest_geometry = partial(r_bridge.forest_export_dimensions, artifact.params_path)
            elif artifact.params_path:
                from tempfile import TemporaryDirectory
                from rc_metastudio.results.plot_service import svg_text_points_per_inch

                with TemporaryDirectory(prefix="rcms-export-size-") as directory:
                    untitled = Path(directory) / "untitled.svg"
                    self.plot_service.export(regenerator=artifact.capability.regenerator,
                                             params_path=artifact.params_path, output_path=str(untitled),
                                             include_title=False, outline_text=False)
                    text_per_inch = (
                        svg_text_points_per_inch(untitled, 1 / ratio),
                        svg_text_points_per_inch(artifact.display_path(), 1 / ratio),
                    )
        else:
            source = QImage(artifact.display_path())
            if source.isNull():
                raise ValueError("Could not read the plot image.")
            native_dpi = round(source.dotsPerMeterX() * .0254)
            width = source.width() / max(1, source.dotsPerMeterX() * .0254)
            ratio = source.width() / source.height()
        dialog = PlotExportDialog(
            artifact.export_formats(), width, width / ratio, self,
            resizable=bool(artifact.params_path), text_per_inch=text_per_inch,
            forest_geometry=forest_geometry,
            native_dpi=native_dpi,
        )
        if not dialog.exec():
            return
        format = dialog.format_control.currentData()
        dimensions = dialog.dimensions()
        if not artifact.params_path:
            unscaled_image = QImage(artifact.image_path)

        return format, dimensions, unscaled_image, dialog.include_title.isChecked(), dialog.forest_dimensions

    def save_image_as(self, artifact, unscaled_image=None, format=None):
        dimensions = None
        forest_dimensions = None
        include_title = True
        if format is None:
            options = self._plot_export_options(artifact, unscaled_image)
            if options is None:
                return
            format, dimensions, unscaled_image, include_title, forest_dimensions = options

        if format not in PLOT_EXPORT_FORMATS_BY_EXTENSION:
            valid_formats = ", ".join(PLOT_EXPORT_FORMATS_BY_EXTENSION.keys())
            raise Exception("Unsupported export format. Choose one of: %s." % valid_formats)

        export_format = PLOT_EXPORT_FORMATS_BY_EXTENSION[format]
        allow_svgz = artifact.capability.regenerator != "funnel"
        suffixes = PLOT_EXPORT_EXTENSION_ALIASES[export_format.extension]
        patterns = " ".join("*" + suffix for suffix in suffixes if allow_svgz or suffix != ".svgz")
        name_filter = f"{export_format.label} ({patterns})"

        regenerator = artifact.capability.regenerator
        if unscaled_image:
            default_path = self._export_name(artifact.title, "png")
        else:
            default_path = {
                "forest": "forest_plot",
                "regression": "regression",
                "funnel": "small_study_effects_funnel",
                "sroc": "sroc",
                "trial_sequential": "trial_sequential_analysis",
            }[regenerator]
            default_path = self._export_name(default_path, export_format.extension)

        file_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export plot",
            default_path,
            name_filter,
        )
        if not file_path:
            return
        destination = _path_with_export_extension(
            file_path, export_format, allow_svgz=allow_svgz
        )
        if not self._confirm_export_destination(file_path, destination):
            return
        if unscaled_image:
            image = unscaled_image.toImage() if isinstance(unscaled_image, QPixmap) else unscaled_image
            with staged_output(destination) as temporary:
                def write() -> None:
                    if not image.save(str(temporary), export_format.qt_format):
                        raise OSError(f"Could not save plot: {destination}")
                compose_export(write)
        elif dimensions is not None:
            width, height, dpi = dimensions
            self.plot_service.export_sized(regenerator=regenerator, params_path=artifact.params_path,
                                           output_path=destination, width=width, height=height, dpi=dpi,
                                           include_title=include_title, geometry=forest_dimensions)
        else:
            self.plot_service.export(
                regenerator=regenerator,
                params_path=artifact.params_path,
                output_path=destination,
            )
        QSettings().setValue("export/last_directory", str(Path(destination).resolve().parent))
        self.statusbar.showMessage(f"Saved {export_format.extension.upper()} plot: {Path(destination).resolve()}", 4000)

    def position(self):
        return QPointF(float(self.x_coord), float(self.y_coord))


def _report_heading(title):
    title = re.sub(r"\s*[-—]\s*model results\b", " — model results", title, flags=re.I)
    title = re.sub(r"\s+-\s*", " — ", title)
    return title.replace("Model Results", "Model results")


def _identity_context_facts(rest, details, confidence, study_count):
    for line in rest:
        for fact in line.split(' · '):
            if fact.startswith('k = '):
                study_count = fact.removeprefix('k = ')
            elif fact.endswith('% CI'):
                confidence.append(fact)
            elif fact.startswith('Comparison: '):
                comparison = fact.removeprefix('Comparison: ')
                details.append(comparison.replace(' / ', ' vs ', 1) if comparison.count(' / ') == 1 else fact)
            elif fact:
                if fact.startswith('Primary test: '):
                    method = fact.removeprefix('Primary test: ')
                    fact = re.sub(r'^Deeks(?=\s|$)', 'Deeks test', method)
                details.append(fact)
    return study_count
