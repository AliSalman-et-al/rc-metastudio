"""The main window's starting surface, using the ordinary project actions."""

from pathlib import Path
from PyQt6 import QtCore, QtWidgets

from rc_metastudio import app_error_handler, qt_layout
from rc_metastudio.runtime_types import required


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
        for attribute, action, caption, description in (
            ('create_button', create_action, 'Create dataset…', 'Choose an outcome and effect measure, then enter study data.'),
            ('import_button', import_action, 'Import CSV…', 'Map your spreadsheet columns and preview the data before importing.'),
            ('open_button', open_action, 'Open project…', 'Continue working with a saved .rcms project.'),
        ):
            card = QtWidgets.QGroupBox(content)
            card_layout = QtWidgets.QVBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)
            card_layout.setSpacing(12)
            button = QtWidgets.QToolButton(card)
            button.setDefaultAction(action)
            button.setText(caption)
            button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            qt_layout.configure_primary_action_buttons((button,))
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
            setattr(self, attribute, button)
            card_layout.addWidget(button)
            label = QtWidgets.QLabel(description, card)
            qt_layout.configure_context_label(label)
            card_layout.addWidget(label)
            card.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Maximum)
            actions.addWidget(card, 1)
        layout.addLayout(actions)
        heading = QtWidgets.QLabel('Recent projects', content)
        qt_layout.configure_heading(heading)
        layout.addWidget(heading)
        self.recent_projects = QtWidgets.QWidget(content)
        self.recent_layout = QtWidgets.QVBoxLayout(self.recent_projects)
        self.recent_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_layout.setSpacing(12)
        layout.addWidget(self.recent_projects)
        heading = QtWidgets.QLabel('From data to results', content)
        qt_layout.configure_heading(heading)
        layout.addWidget(heading)
        orientation = QtWidgets.QLabel(
            '1. Prepare your studies — enter counts, means or reported effects; use row calculators when needed.\n\n'
            '2. Run an analysis — choose the model and inspect estimates, heterogeneity and uncertainty.\n\n'
            '3. Finish your output — edit the figure, compare settings, and export a figure, report or table.', content)
        qt_layout.configure_context_label(orientation)
        layout.addWidget(orientation)
        layout.addStretch()
        outer.addWidget(content, 1)
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
        for path in reversed(paths):
            row = QtWidgets.QWidget(self.recent_projects)
            layout = QtWidgets.QVBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)
            exists = Path(path).is_file()
            button = QtWidgets.QPushButton(Path(path).name + ('' if exists else ' — Missing file'), row)
            button.setEnabled(exists)
            button.setToolTip(str(path) if exists else 'Missing file: ' + str(path))
            button.clicked.connect(app_error_handler.safe_slot(lambda _checked=False, path=path: open_project(path), parent=self))
            layout.addWidget(button, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
            if not exists:
                recovery = QtWidgets.QHBoxLayout()
                for caption, callback in (("Locate…", locate_project), ("Remove from list", remove_project)):
                    if callback is None:
                        continue
                    action = QtWidgets.QPushButton(caption, row)
                    action.setAccessibleName(caption + " " + Path(path).name)
                    action.clicked.connect(app_error_handler.safe_slot(lambda _checked=False, path=path, callback=callback: callback(path), parent=self))
                    recovery.addWidget(action)
                recovery.addStretch()
                layout.addLayout(recovery)
            label = QtWidgets.QLabel(str(path), row)
            label.setTextFormat(QtCore.Qt.TextFormat.PlainText)
            label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            qt_layout.configure_context_label(label)
            layout.addWidget(label)
            self.recent_layout.addWidget(row)
