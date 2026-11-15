"""Small, semantic Qt control policies shared across canonical forms.

Top-level geometry belongs to :mod:`adaptive_window`; form hierarchy and
overflow belong to canonical ``.ui`` resources.  This module deliberately has
no root-fitting, coordinate inference, or descendant-repair surface.
"""

from PyQt6.QtCore import QEvent, QObject, QSize, Qt, QTimer
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor, QKeyEvent
from PyQt6.QtWidgets import QApplication, QAbstractScrollArea, QAbstractSpinBox, QComboBox, QCommonStyle, QHeaderView, QMenu, QProxyStyle, QSizePolicy, QStyle, QStyleOptionToolButton, QStylePainter, QToolButton, QStyleOption, QWidget


class _ScrollSettingsFilter(QObject):
    """Route form scrolling past settings; arrows and popup selection still edit."""

    def __init__(self, scroll_area: QAbstractScrollArea):
        super().__init__(scroll_area)
        self.viewport = scroll_area.viewport()

    def eventFilter(
        self, watched: QObject | None, event: QEvent | None
    ) -> bool:
        if event is not None and event.type() == QEvent.Type.Wheel:
            QApplication.sendEvent(self.viewport, event)
            return True
        return super().eventFilter(watched, event)


def protect_scroll_settings(scroll_area: QAbstractScrollArea) -> QObject:
    policy = _ScrollSettingsFilter(scroll_area)
    for control in (*scroll_area.findChildren(QComboBox), *scroll_area.findChildren(QAbstractSpinBox)):
        control.installEventFilter(policy)
    return policy


PRIMARY_ACTION_ICON_EXTENT = 24
PRIMARY_ACTION_CONTROL_HEIGHT = 36
TOOLBAR_ICON_EXTENT = 28
TOOLBAR_CONTROL_EXTENT = 36
COMPACT_ANALYSIS_ICON_EXTENT = 18
STANDARD_ANALYSIS_ICON_EXTENT = 28


def configure_analysis_menu(menu):
    """Use the compact analysis master at its intended 18-pixel size."""
    menu.setProperty("rcmsCompactAnalysisIcons", True)


class DisclosureButton(QToolButton):
    """Native disclosure styling follows palette changes, including checked state."""

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setAutoRaise(True)
        self.setCheckable(True)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setArrowType(Qt.ArrowType.RightArrow)
        self.toggled.connect(lambda checked: self.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow))

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event is not None and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.click()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event) -> None:
        painter = QStylePainter(self)
        option = QStyleOptionToolButton()
        self.initStyleOption(option)
        option.state &= ~QStyle.StateFlag.State_On
        painter.drawComplexControl(QStyle.ComplexControl.CC_ToolButton, option)


def configure_analysis_action_icon(action, icon_name):
    """Attach optically tuned menu and toolbar masters to one QAction."""
    icon = QIcon()
    icon.addFile(
        ":/icons/analyses/compact/{}.svg".format(icon_name),
        QSize(COMPACT_ANALYSIS_ICON_EXTENT, COMPACT_ANALYSIS_ICON_EXTENT),
    )
    icon.addFile(
        ":/icons/analyses/{}.svg".format(icon_name),
        QSize(STANDARD_ANALYSIS_ICON_EXTENT, STANDARD_ANALYSIS_ICON_EXTENT),
    )
    action.setIcon(icon)


def configure_primary_action_buttons(buttons):
    """Give text-and-icon workflow actions an optically useful icon size."""
    for button in buttons:
        # layout-audit: allow=semantic-icon-control; reason=primary workflow actions use a surface-specific optical icon size
        button.setIconSize(
            QSize(PRIMARY_ACTION_ICON_EXTENT, PRIMARY_ACTION_ICON_EXTENT)
        )
        # layout-audit: allow=semantic-icon-control; reason=primary workflow actions need a dependable desktop click target
        button.setMinimumHeight(PRIMARY_ACTION_CONTROL_HEIGHT)


def configure_main_toolbar(toolbar):
    """Separate toolbar artwork scale from its interactive hit target."""
    # layout-audit: allow=semantic-icon-control; reason=the main toolbar uses its documented optical icon size
    toolbar.setIconSize(QSize(TOOLBAR_ICON_EXTENT, TOOLBAR_ICON_EXTENT))
    for button in toolbar.findChildren(QToolButton):
        action = button.defaultAction()
        if action is None:
            continue
        action.setToolTip(action.toolTip() or action.text().replace("&", ""))
        button.setAccessibleName(action.text().replace("&", ""))
        button.setAccessibleDescription(action.toolTip())
        button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        if action.objectName() in {"action_new_dataset", "action_open", "action_import_csv", "action_save", "action_go"}:
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        # layout-audit: allow=semantic-icon-control; reason=toolbar actions need consistent cross-platform click targets
        button.setMinimumSize(QSize(TOOLBAR_CONTROL_EXTENT, TOOLBAR_CONTROL_EXTENT))


def configure_context_label(label):
    """Keep wrapped context readable without stretching it into spare space."""
    label.setWordWrap(True)
    policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
    policy.setHeightForWidth(True)
    label.setSizePolicy(policy)


def configure_spreadsheet_table_view(table_view):
    """Give a Workspace table an expanding viewport and user-owned columns."""
    if table_view is None:
        return

    table_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    header = table_view.horizontalHeader()
    header.setStretchLastSection(False)
    header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)


class _ControlStyle(QProxyStyle):
    def drawControl(self, element, option, painter, widget=None):
        if element == QStyle.ControlElement.CE_ToolButtonLabel and isinstance(widget, DisclosureButton):
            # Windows' native label painter can ignore a custom palette.
            QCommonStyle.drawControl(self, element, option, painter, widget)
        else:
            super().drawControl(element, option, painter, widget)

    def pixelMetric(self, metric, option=None, widget=None):
        if metric == QStyle.PixelMetric.PM_SmallIconSize and isinstance(widget, QMenu) and widget.property("rcmsCompactAnalysisIcons"):
            return COMPACT_ANALYSIS_ICON_EXTENT
        return super().pixelMetric(metric, option, widget)

    def sizeFromContents(self, type: QStyle.ContentsType, option: QStyleOption | None, size: QSize, widget: QWidget | None = None) -> QSize:
        result = super().sizeFromContents(type, option, size, widget)
        if type in {QStyle.ContentsType.CT_PushButton, QStyle.ContentsType.CT_ToolButton} and widget is not None:
            result.setHeight(max(result.height(), widget.fontMetrics().height() + 12))
        return result

    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QStyle.StyleHint.SH_DialogButtonBox_ButtonsHaveIcons:
            return 0
        return super().styleHint(hint, option, widget, returnData)


def configure_application_controls(app):
    if app.property("rcms_controls_configured"):
        return
    palette = app.palette()
    role = QPalette.ColorRole
    if palette.color(role.Window).lightness() < 128:
        for text_role in (role.WindowText, role.Text, role.ButtonText):
            palette.setColor(QPalette.ColorGroup.Disabled, text_role, QColor("#999999"))
        palette.setColor(QPalette.ColorGroup.Disabled, role.Button, palette.color(role.Window))
        for border_role in (role.Mid, role.Dark, role.Light):
            palette.setColor(border_role, QColor("#999999"))
        app.setPalette(palette)
    font = app.font()
    app.setStyle(_ControlStyle(app.style().objectName()))
    # Style polish installs class-specific system fonts unless the app font is reapplied.
    app.setFont(font)
    app._rcms_error_palette = _InlineErrorPaletteFilter(app)
    app.setProperty("rcms_controls_configured", True)


def configure_heading(label, scale=1.15):
    font = QFont(label.font())
    font.setBold(True)
    font.setPointSizeF(max(10, font.pointSizeF()) * scale)
    label.setFont(font)


def _set_error_palette(label):
    palette = label.palette()
    dark = palette.color(label.backgroundRole()).lightness() < 128
    color = QColor("#ff9ca8" if dark else "#b00020")
    roles = (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text)
    if any(palette.color(role) != color for role in roles):
        error_palette = QPalette()
        for role in roles:
            error_palette.setColor(role, color)
        label.setPalette(error_palette)


class _InlineErrorPaletteFilter(QObject):
    """Explicit foregrounds need an application hook after palette propagation."""

    def __init__(self, app):
        super().__init__(app)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.refresh)
        app.installEventFilter(self)

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:
        if event is not None and event.type() in (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange):
            self.timer.start(0)
        elif event is not None and event.type() == QEvent.Type.Paint and isinstance(watched, QWidget) and watched.property("rcmsInlineError"):
            # Wizard pages can finish resolving their surface palette at paint time.
            _set_error_palette(watched)
        return False

    def refresh(self):
        for widget in QApplication.allWidgets():
            if widget.property("rcmsInlineError"):
                _set_error_palette(widget)


def style_inline_error(label):
    """Use the error foreground on the label's actual themed surface."""
    label.setProperty("rcmsInlineError", True)
    _set_error_palette(label)


def clear_inline_error(label):
    if label.property("rcmsInlineError"):
        label.setProperty("rcmsInlineError", False)
        label.setPalette(QPalette())
