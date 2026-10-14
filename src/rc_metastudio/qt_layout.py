"""Small, semantic Qt control policies shared across canonical forms.

Top-level geometry belongs to :mod:`adaptive_window`; form hierarchy and
overflow belong to canonical ``.ui`` resources.  This module deliberately has
no root-fitting, coordinate inference, or descendant-repair surface.
"""

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import QHeaderView, QProxyStyle, QSizePolicy, QStyle, QToolButton, QStyleOption, QWidget


OUTCOME_NAVIGATION_ICON_EXTENT = 24
OUTCOME_NAVIGATION_CONTROL_EXTENT = 32
ICON_ONLY_ACTION_ICON_EXTENT = 24
ICON_ONLY_ACTION_CONTROL_EXTENT = 32
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


def configure_navigation_tool_buttons(buttons):
    """Give outcome-navigation controls a coherent cross-platform scale."""
    for button in buttons:
        # layout-audit: allow=semantic-icon-control; reason=outcome navigation uses a surface-specific optical icon size
        button.setIconSize(
            QSize(OUTCOME_NAVIGATION_ICON_EXTENT, OUTCOME_NAVIGATION_ICON_EXTENT)
        )
        # layout-audit: allow=semantic-icon-control; reason=outcome navigation requires a reliable compact click target
        button.setMinimumSize(
            QSize(OUTCOME_NAVIGATION_CONTROL_EXTENT, OUTCOME_NAVIGATION_CONTROL_EXTENT)
        )
        button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)


def configure_structure_action_buttons(buttons, icon_name):
    """Give structural changes visible names and dependable targets."""
    for button, target in buttons:
        button.setIcon(QIcon(":/icons/actions/{}.svg".format(icon_name)))
        button.setText(icon_name.title())
        button.setAccessibleName(f"{icon_name.title()} {target}")
        button.setToolTip(f"{icon_name.title()} {target}")
        # layout-audit: allow=semantic-icon-control; reason=dataset action icons use a surface-specific optical size beside their text
        button.setIconSize(
            QSize(ICON_ONLY_ACTION_ICON_EXTENT, ICON_ONLY_ACTION_ICON_EXTENT)
        )
        # layout-audit: allow=semantic-icon-control; reason=dataset actions need a reliable click target that fits the visible label
        button.setMinimumHeight(ICON_ONLY_ACTION_CONTROL_EXTENT)
        button.setMinimumWidth(button.sizeHint().width())


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


def configure_compact_table(table, stretch_columns=False, fill_available_width=False):
    """Fit a compact Transactional table once; native scrolling owns overflow."""
    if table is None:
        return

    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    # layout-audit: allow=compact-table-overflow; reason=compact table keeps rows visible and owns excess overflow
    table.setMinimumWidth(0)
    header = table.horizontalHeader()
    header.setStretchLastSection(False)

    if stretch_columns:
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    else:
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.resizeColumnsToContents()
        header.setStretchLastSection(fill_available_width)

    table.resizeRowsToContents()
    header_height = 0 if header.isHidden() else header.sizeHint().height()
    table_height = (
        header_height
        + sum(table.rowHeight(row) for row in range(table.rowCount()))
        + 2 * table.frameWidth()
    )
    # layout-audit: allow=compact-table-overflow; reason=compact table keeps rows visible and owns excess overflow
    table.setMinimumHeight(table_height)
    # layout-audit: allow=compact-table-overflow; reason=compact table keeps rows visible and owns excess overflow
    table.setMaximumHeight(table_height)


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
    app.setStyle(_ControlStyle(app.style().objectName()))
    app.setProperty("rcms_controls_configured", True)


def configure_heading(label, scale=1.15):
    font = QFont(label.font())
    font.setBold(True)
    font.setPointSizeF(max(10, font.pointSizeF()) * scale)
    label.setFont(font)
