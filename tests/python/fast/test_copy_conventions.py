import ast
import json
import re
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "src/rc_metastudio"
TEXT_SETTERS = {
    "setAccessibleDescription", "setAccessibleName", "setPlaceholderText",
    "setStatusTip", "setText", "setToolTip", "setWhatsThis", "setWindowTitle",
}
TEXT_FIRST_ARGUMENT = {
    "QCheckBox", "QGroupBox", "QLabel", "QPushButton", "QRadioButton", "QToolButton",
    "addAction", "addItem", "addMenu", "CellRejection", "ValueError", "RuntimeError",
}
TEXT_RETURN_FILES = {
    "report.py", "tabular.py", "r_bridge.py", "trial_sequential.py",
    "identity.py", "method_labels.py", "name_validation.py", "editing.py",
}
MESSAGE_KINDS = {"critical", "information", "question", "warning"}
R_UI_LITERAL = re.compile(
    r"""(?:\b(?:stop|warning|paste0?|return)\(\s*|["']?(?:description|pretty\.name)["']?\s*=\s*)"""
    r"""(["'])((?:\\.|(?!\1)[^\\])*)\1"""
)
R_DISPLAY_FILES = {"forest_style_bmj.R", "plot_text.R", "results_display.R", "trial_sequential_plot.R"}
R_STRING_OR_COMMENT = re.compile(r"""(?P<comment>#[^\n]*)|(["'])((?:\\.|(?!\2)[^\\])*)\2""")
SHARED_IMPORT_WORDING = re.compile(
    r"\b(?:Import(?:ing)? CSV(?: (?:data|file))?[.…]?$|(?:Select|Choose) (?:a |the )?CSV column\b|"
    r"(?:The )?CSV file (?:is|has|must|does|could)\b)", re.I,
)
SHARED_IMPORT_SOURCES = {"main_wizard.py", "main_window.py", "csv_import_page.ui", "importing/tabular.py"}
RULES = {
    "straight quotes": re.compile("[‘’“”]"),
    "outcome and effect measure": re.compile(r"\b(?:sheets?|metrics?)\b", re.I),
    "US spelling": re.compile(
        r"\b(?:favours?|favouring|penalis(?:e|ed|es|ing)|cancell(?:ed|ing)|"
        r"colours?|labelled|modelling|centring|(?:standard|normal|organ)is(?:e|ed|es|ing))\b",
        re.I,
    ),
    "P value": re.compile(r"\b[pP]-values?\b|\bp\s*[=<≤>≥]\s*\d|\bp values?\b"),
    "correction of a repeated direction label": re.compile(r"\bfavoring Favors\b"),
    "multiplication sign in count tables": re.compile(r"\b2x2\b|\brows x \S+ columns\b"),
    "sentence case for statistical labels": re.compile(
        r"\b(?:Trial Sequential Analysis|Diagnostic Odds Ratio|Maximum Likelihood|Random-Effects method|"
        r"Meta-Regression|Positive Likelihood Ratio|Negative Likelihood Ratio)\b"
    ),
    "retired display terms": re.compile(r"\b(?:Non-estimable|Display digits|Original CI|between-studies)\b", re.I),
    "ellipsis in actions": re.compile(r"\.\.\.$"),
    "en dash in author pairs": re.compile(
        r"\b(?:Mantel-Haenszel|DerSimonian-Laird|Freeman-Tukey|Knapp-Hartung|Paule-Mandel)\b"
    ),
}


def _literals(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        yield node.lineno, node.value
    elif isinstance(node, (ast.JoinedStr, ast.List, ast.Tuple)):
        for item in node.values if isinstance(node, ast.JoinedStr) else node.elts:
            yield from _literals(item)
    elif isinstance(node, ast.IfExp):
        yield from _literals(node.body)
        yield from _literals(node.orelse)
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        yield from _literals(node.left)
        yield from _literals(node.right)


def _python_copy(path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Return) and path.name in TEXT_RETURN_FILES:
            values = (node.value,)
        elif isinstance(node, ast.Dict) and path.name == "method_labels.py":
            values = node.values
        elif isinstance(node, ast.Call):
            target = node.func
            name = target.attr if isinstance(target, ast.Attribute) else target.id if isinstance(target, ast.Name) else ""
            owner = target.value if isinstance(target, ast.Attribute) else None
            if isinstance(owner, ast.Name) and owner.id == "QMessageBox" and name in MESSAGE_KINDS:
                values = node.args[1:3]
                if values and isinstance(title := values[0], ast.Constant):
                    assert title.value not in ("Warning", "Error", "Notice"), (path, title.lineno, title.value)
            elif name == "QAction":
                values = node.args[:2]
            elif name in TEXT_FIRST_ARGUMENT or (name == "append" and path.name in TEXT_RETURN_FILES):
                values = node.args[:1]
            elif name in TEXT_SETTERS | {"addRow", "addTab", "QTreeWidgetItem", "setHorizontalHeaderLabels"}:
                values = node.args[-1:]
            else:
                continue
        else:
            continue
        for value in values:
            yield from _literals(value)


def _visible_copy():
    for path in sorted((PACKAGE / "forms").glob("*.ui")):
        for element in ElementTree.parse(path).iter("string"):
            if element.get("notr") != "true" and element.text:
                yield path.name, element.text
    for path in sorted(PACKAGE.rglob("*.py")):
        for line, value in _python_copy(path):
            yield f"{path.relative_to(PACKAGE).as_posix()}:{line}", value
    manifest = ROOT / "sample_projects/manifest.json"
    for project in json.loads(manifest.read_text(encoding="utf-8"))["projects"]:
        for key in ("scientific_name", "description"):
            yield manifest.name, project[key]
    for path in sorted((ROOT / "r/RCMetaR/R").glob("*.R")):
        source = path.read_text(encoding="utf-8")
        matches = R_STRING_OR_COMMENT.finditer(source)
        if path.name in R_DISPLAY_FILES:
            for match in matches:
                if not match["comment"]:
                    yield f"{path.name}:{source.count(chr(10), 0, match.start()) + 1}", match[3]
        else:
            for match in R_UI_LITERAL.finditer(source):
                yield f"{path.name}:{source.count(chr(10), 0, match.start()) + 1}", match[2]


def test_user_facing_copy_conventions():
    failures = []
    for location, value in _visible_copy():
        if location.partition(":")[0] in SHARED_IMPORT_SOURCES and SHARED_IMPORT_WORDING.search(value):
            failures.append(f"{location}: file or spreadsheet in shared import instructions: {value!r}")
        for rule, pattern in RULES.items():
            if pattern.search(value):
                failures.append(f"{location}: {rule}: {value!r}")
    assert not failures, "\n" + "\n".join(failures)
