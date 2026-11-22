"""The main window's starting surface, using the ordinary project actions."""

from pathlib import Path
from datetime import datetime
from PyQt6 import QtCore, QtGui, QtWidgets

from rc_metastudio import app_error_handler, qt_layout
from rc_metastudio.qt_object_guard import required


class _RecentPathLabel(QtWidgets.QLabel):
    def __init__(self, path, parent):
        super().__init__(path, parent)
        self.setToolTip(path)
        self.setAccessibleName(path)
        self.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        muted = QtWidgets.QGraphicsOpacityEffect(self)
        muted.setOpacity(0.8)
        self.setGraphicsEffect(muted)
        self.setMinimumWidth(0)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Preferred)

    def resizeEvent(self, a0: QtGui.QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        self.setText(self.fontMetrics().elidedText(self.toolTip(), QtCore.Qt.TextElideMode.ElideMiddle, self.contentsRect().width()))


class StartPage(QtWidgets.QScrollArea):
    def __init__(self, create_action, import_action, open_action, parent=None, *, sample_menu: QtWidgets.QMenu | None = None):
        super().__init__(parent)
        self.sample_menu = sample_menu
        self.setObjectName('start_page')
        self.setAccessibleName('Start a project')
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        page = QtWidgets.QWidget(self)
        outer = QtWidgets.QHBoxLayout(page)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.addStretch()
        content = QtWidgets.QWidget(page)
        content.setMaximumWidth(1000)
        layout = QtWidgets.QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        title = QtWidgets.QLabel('RC MetaStudio', content)
        qt_layout.configure_heading(title, 1.8)
        layout.addWidget(title)
        intro = QtWidgets.QLabel('Bring your study data together. Analyze, inspect, and export your results.', content)
        qt_layout.configure_context_label(intro)
        layout.addWidget(intro)
        actions = QtWidgets.QHBoxLayout()
        actions.setSpacing(16)
        buttons = []
        for action, caption, description in (
            (create_action, 'New project…', 'Start with your first outcome and effect measure, then enter study data.'),
            (import_action, 'Import data…', 'Import Excel, CSV, or RevMan (.rm5) files and review them before adding an outcome.'),
            (open_action, 'Open project…', 'Continue working with a saved .rcms project.'),
        ):
            card = QtWidgets.QGroupBox(content)
            card.setFlat(True)
            card_layout = QtWidgets.QVBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)
            card_layout.setSpacing(12)
            button = QtWidgets.QToolButton(card)
            button.setDefaultAction(action)
            button.setText(caption)
            action.changed.connect(lambda b=button, text=caption: b.setText(text))
            button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            qt_layout.configure_primary_action_buttons((button,))
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
            buttons.append(button)
            card_layout.addWidget(button, 0, QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
            label = QtWidgets.QLabel(description, card)
            qt_layout.configure_context_label(label)
            label_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
            label_policy.setHeightForWidth(True)
            label.setSizePolicy(label_policy)
            card_layout.addWidget(label)
            card_layout.addStretch()
            policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
            policy.setHeightForWidth(True)
            card.setSizePolicy(policy)
            actions.addWidget(card, 1)
        self.create_button, self.import_button, self.open_button = buttons
        height = max(button.sizeHint().height() for button in buttons)
        for button in buttons:
            button.setFixedHeight(height)
        layout.addLayout(actions, 0)
        heading = QtWidgets.QLabel('Recent projects', content)
        qt_layout.configure_heading(heading)
        layout.addWidget(heading)
        self.recent_projects = QtWidgets.QWidget(content)
        self.recent_layout = QtWidgets.QGridLayout(self.recent_projects)
        self.recent_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_layout.setHorizontalSpacing(16)
        self.recent_layout.setVerticalSpacing(8)
        self.recent_layout.setColumnStretch(1, 1)
        layout.addWidget(self.recent_projects)
        layout.addStretch()
        outer.addWidget(content, 1, QtCore.Qt.AlignmentFlag.AlignTop)
        outer.addStretch()
        self.setWidget(page)

    def changeEvent(self, event: QtCore.QEvent | None) -> None:
        super().changeEvent(event)
        if event is not None and event.type() in (QtCore.QEvent.Type.PaletteChange, QtCore.QEvent.Type.ApplicationPaletteChange):
            button = self.findChild(QtWidgets.QPushButton, 'empty_recent_sample')
            if button is not None:
                button.setStyleSheet('QPushButton { color: ' + qt_layout.readable_link_color(self.palette()).name() + '; text-decoration: underline; }')

    def set_recent_projects(self, paths, open_project, locate_project=None, remove_project=None):
        while self.recent_layout.count():
            item = required(self.recent_layout.takeAt(0), "recent project row")
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        if not paths:
            self.recent_layout.addWidget(QtWidgets.QLabel('Projects you open or save will appear here.', self.recent_projects))
            if self.sample_menu is not None and self.sample_menu.isEnabled():
                sample_button = QtWidgets.QPushButton("Open a sample project", self.recent_projects)
                sample_button.setFlat(True)
                sample_button.setObjectName("empty_recent_sample")
                sample_button.setStyleSheet('QPushButton { color: ' + qt_layout.readable_link_color(self.palette()).name() + '; text-decoration: underline; }')
                sample_button.setMenu(self.sample_menu)
                self.recent_layout.addWidget(sample_button, 1, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        for index, path in enumerate(reversed(paths)):
            self._add_recent_project(index, path, open_project, locate_project, remove_project)

    def _add_recent_project(self, index, path, open_project, locate_project, remove_project):
        exists = Path(path).is_file()
        button = QtWidgets.QPushButton(Path(path).name, self.recent_projects)
        button.setEnabled(exists)
        button.setToolTip(str(path) if exists else 'Missing file: ' + str(path))
        button.clicked.connect(app_error_handler.safe_slot(lambda _checked=False, path=path: open_project(path), parent=self))
        self.recent_layout.addWidget(button, index, 0)
        self.recent_layout.addWidget(_RecentPathLabel(str(path), self.recent_projects), index, 1)
        if exists:
            try:
                timestamp = datetime.fromtimestamp(Path(path).stat().st_mtime)
                modified = f'{timestamp.day} {timestamp:%b %Y}'
            except OSError:
                modified = ''
            date_label = QtWidgets.QLabel('Modified ' + modified if modified else '', self.recent_projects)
            date_label.setForegroundRole(QtGui.QPalette.ColorRole.PlaceholderText)
            self.recent_layout.addWidget(date_label, index, 2)
        if not exists:
            self.recent_layout.addWidget(QtWidgets.QLabel('Missing file', self.recent_projects), index, 2)
            for column, (caption, callback) in enumerate((("Locate…", locate_project), ("Remove from list", remove_project)), 3):
                if callback is None:
                    continue
                action = QtWidgets.QPushButton(caption, self.recent_projects)
                action.setAccessibleName(caption + " " + Path(path).name)
                action.clicked.connect(app_error_handler.safe_slot(lambda _checked=False, path=path, callback=callback: callback(path), parent=self))
                self.recent_layout.addWidget(action, index, column)
