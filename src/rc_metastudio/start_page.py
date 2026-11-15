"""The main window's starting surface, using the ordinary project actions."""

from pathlib import Path
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
    def __init__(self, create_action, import_action, open_action, parent=None):
        super().__init__(parent)
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
        intro = QtWidgets.QLabel('Bring your study data together. Analyze, inspect and export your results.', content)
        qt_layout.configure_context_label(intro)
        layout.addWidget(intro)
        actions = QtWidgets.QHBoxLayout()
        actions.setSpacing(16)
        buttons = []
        for action, caption, description in (
            (create_action, 'New project', 'Start with your first outcome and effect measure, then enter study data.'),
            (import_action, 'Import data', 'Import Excel, CSV, or RevMan (.rm5) files and review the data before importing.'),
            (open_action, 'Open project', 'Continue working with a saved .rcms project.'),
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
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
            buttons.append(button)
            card_layout.addWidget(button, 0, QtCore.Qt.AlignmentFlag.AlignTop)
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
            import_button = QtWidgets.QPushButton('Import data…', self.recent_projects)
            import_button.setFlat(True)
            import_button.setStyleSheet('QPushButton { color: palette(link); text-decoration: underline; }')
            import_button.clicked.connect(self.import_button.click)
            self.recent_layout.addWidget(import_button, 1, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        for index, path in enumerate(reversed(paths)):
            exists = Path(path).is_file()
            button = QtWidgets.QPushButton(Path(path).name, self.recent_projects)
            button.setEnabled(exists)
            button.setToolTip(str(path) if exists else 'Missing file: ' + str(path))
            button.clicked.connect(app_error_handler.safe_slot(lambda _checked=False, path=path: open_project(path), parent=self))
            self.recent_layout.addWidget(button, index, 0)
            self.recent_layout.addWidget(_RecentPathLabel(str(path), self.recent_projects), index, 1)
            if not exists:
                self.recent_layout.addWidget(QtWidgets.QLabel('Missing file', self.recent_projects), index, 2)
                for column, (caption, callback) in enumerate((("Locate…", locate_project), ("Remove from list", remove_project)), 3):
                    if callback is None:
                        continue
                    action = QtWidgets.QPushButton(caption, self.recent_projects)
                    action.setAccessibleName(caption + " " + Path(path).name)
                    action.clicked.connect(app_error_handler.safe_slot(lambda _checked=False, path=path, callback=callback: callback(path), parent=self))
                    self.recent_layout.addWidget(action, index, column)
