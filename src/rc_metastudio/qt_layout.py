"""Small, semantic Qt control policies shared across canonical forms.

Top-level geometry belongs to :mod:`adaptive_window`; form hierarchy and
overflow belong to canonical ``.ui`` resources.  This module deliberately has
no root-fitting, coordinate inference, or descendant-repair surface.
"""

from PyQt6.QtCore import QEvent, QObject, QSize, Qt
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor
from PyQt6.QtWidgets import QApplication, QAbstractScrollArea, QAbstractSpinBox, QComboBox, QHeaderView, QProxyStyle, QSizePolicy, QStyle, QToolButton, QStyleOption, QWidget


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


class _MenuIconProxyStyle(QProxyStyle):
    """Override only the small-icon metric for one menu surface."""

    def __init__(self, icon_extent, parent=None):
        super(_MenuIconProxyStyle, self).__init__()
        self._icon_extent = icon_extent
        self.setParent(parent)

    def pixelMetric(self, metric, option=None, widget=None):
        if metric == QStyle.PixelMetric.PM_SmallIconSize:
            return self._icon_extent
        return super(_MenuIconProxyStyle, self).pixelMetric(metric, option, widget)


def configure_analysis_menu(menu):
    """Use the compact analysis master at its intended 18-pixel size."""
    icon_style = _MenuIconProxyStyle(COMPACT_ANALYSIS_ICON_EXTENT, menu)
    menu.setStyle(icon_style)
    menu._rcms_icon_style = icon_style


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
    app.setProperty("rcms_controls_configured", True)


def configure_heading(label, scale=1.15):
    font = QFont(label.font())
    font.setBold(True)
    font.setPointSizeF(max(10, font.pointSizeF()) * scale)
    label.setFont(font)


def style_inline_error(label):
    """Use a contrasting error foreground against the current window palette."""
    dark = label.palette().color(QPalette.ColorRole.Window).lightness() < 128
    label.setStyleSheet("color: " + ("#ff9ca8" if dark else "#b00020") + ";")
