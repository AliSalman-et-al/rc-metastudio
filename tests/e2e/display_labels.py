"""Inspect attached menus and real dialog/result surfaces across dataset families."""
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from PyQt6 import QtCore, QtWidgets

FORBIDDEN = re.compile(r'\b(?:TX|Tx|tx)(?:\s*Mean)?\b|\[default\]|\b(?:rm\.method|inference\.method|conf\.level|fp_\w+|bp_\w+|intrcpt|tsens|tfpr|pval)\b')
METRICS = {'OR','RR','RD','AS','YUQ','YUY','PR','PLN','PLO','PAS','PFT','MD','SMD','Sens','Spec','DOR','PLR','NLR','HR','IRR','TX Mean'}


def check_label(text, surface, user_names=()):
    text = str(text).replace('&', '').strip()
    for name in user_names:
        text = text.replace(name, '')
    assert not FORBIDDEN.search(text), (surface, text)
    assert text not in METRICS, ('metric needs a readable name', surface, text)
    return dict(surface=surface, text=text) if text else None


def plot_label_inventory(paths, user_names=()):
    inventory = []
    for path in sorted(set(paths)):
        if Path(path).suffix != '.svg' or not Path(path).is_file():
            continue
        for node in ET.parse(path).iter('{http://www.w3.org/2000/svg}text'):
            item = check_label(''.join(node.itertext()), str(path), user_names)
            if item is not None:
                inventory.append(item)
    return inventory


def visible_label_inventory(widget, user_names=()):
    inventory = []
    def check(text, surface):
        item = check_label(text, surface, user_names)
        if item is not None:
            inventory.append(item)
    for child in [widget, *widget.findChildren(QtWidgets.QWidget)]:
        if not child.isVisible():
            continue
        if isinstance(child, (QtWidgets.QLabel, QtWidgets.QAbstractButton, QtWidgets.QGroupBox)):
            check(child.title() if isinstance(child, QtWidgets.QGroupBox) else child.text(), child.objectName())
        check(child.toolTip(), child.objectName() + ':tooltip')
        if isinstance(child, QtWidgets.QComboBox):
            for index in range(child.count()):
                check(child.itemText(index), child.objectName() + ':choice')
        if isinstance(child, (QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit)):
            check(child.toPlainText(), child.objectName())
    return inventory


def run(app, window, record):
    from analysis_matrix import DATA_TYPES, run as matrix
    from advanced_workflows import modal
    from tests.e2e.audit_round3 import analyze_existing
    from rc_metastudio.binary_data_dialog import BinaryDataDialog
    from rc_metastudio.continuous_data_dialog import ContinuousDataDialog
    from rc_metastudio.diagnostic_data_dialog import DiagnosticDataDialog
    from rc_metastudio.ratio_data_dialog import RatioDataDialog

    root = Path(__file__).resolve().parents[2]
    inventory = []

    def check(text, surface):
        text = str(text).replace('&', '').strip()
        # These are investigator text, never built-in vocabulary to rename.
        for name in window.model.current_groups:
            if name not in {'Group', 'Intervention', 'Control'}:
                text = text.replace(name, '')
        assert not FORBIDDEN.search(text), (surface, text)
        assert text not in METRICS, ('metric needs a readable name', surface, text)
        if text:
            inventory.append(dict(surface=surface, text=text))

    def inspect(widget):
        names = [name for name in window.model.current_groups if name not in {'Group', 'Intervention', 'Control'}]
        inventory.extend(visible_label_inventory(widget, names))

    def observe(action, *widgets, **observations):
        for widget in widgets:
            inspect(widget)
        record(action, *widgets, **observations)

    def menus(menu, path='Menu'):
        for action in menu.actions():
            if action.isSeparator():
                continue
            check(action.text(), path)
            check(action.toolTip(), path + ':tooltip')
            if action.menu() is not None:
                menus(action.menu(), path + '/' + action.text())

    for family in (*DATA_TYPES, 'hr', 'irr'):
        window.workspace.mark_saved()
        if family in DATA_TYPES:
            matrix(app, window, 'analysis-data-' + family, observe)
        else:
            sample = 'Pignon2000-HR' if family == 'hr' else 'NielWeise2008-IRR'
            assert window.open(str(root / 'sample_projects' / (sample + '.rcms')), raise_on_error=True)
            view = analyze_existing(app, window, 'standard', 'time_to_event.random' if family == 'hr' else 'event_rates.random', observe)
            view.close()
        menus(window.menuBar())
        if family in {'onearm-mean', 'reg-coef', 'generic-effect', 'twoarm-mean', 'twoarm-smd'}:
            menu = window.oneArmMetricMenu
            menu.popup(window.mapToGlobal(QtCore.QPoint(100, 100)))
            app.processEvents()
            record('display-metric-popup', menu, family=family,
                   capture_surface='desktop-composite', labels=[action.text() for action in menu.actions()])
            menu.hide()
        kind = (BinaryDataDialog if window.model.get_current_outcome_type() == 'binary' else
                DiagnosticDataDialog if window.model.is_diagnostic() else
                RatioDataDialog if family in {'hr','irr'} else ContinuousDataDialog)
        def calculator(dialog):
            inspect(dialog)
            record('display-label-calculator', dialog, family=family)
            dialog.reject()
        modal(app, kind, calculator, lambda: window.tableView.row_header_clicked(0))
        record('display-label-attached-menus', window, family=family, labels=list(inventory))
        inventory.clear()
