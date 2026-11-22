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
R_UI_LITERAL = re.compile(
    r"""(?:\b(?:stop|warning)\(\s*|["'](?:description|pretty\.name)["']\s*=\s*)"""
    r"""(["'])((?:\\.|(?!\1)[^\\])*)\1"""
)
RULES = {
    "straight quotes": re.compile("[‘’“”]"),
    "outcome and effect measure": re.compile(r"\b(?:sheets?|metrics?)\b", re.I),
    "US spelling": re.compile(
        r"\b(?:favours?|favouring|penalis(?:e|ed|es|ing)|cancell(?:ed|ing)|"
        r"colours?|labelled|modelling|centring|(?:standard|normal|organ)is(?:e|ed|es|ing))\b",
        re.I,
    ),
    "P value": re.compile(r"\b[pP]-values?\b|\bp\s*[=<≤>≥]\s*\d|\bp values?\b"),
    "file or spreadsheet in import instructions": re.compile(r"\bCSV\b"),
}


def _visible_copy():
    for path in sorted((PACKAGE / "forms").glob("*.ui")):
        for element in ElementTree.parse(path).iter("string"):
            if element.get("notr") != "true" and element.text:
                yield path.name, element.text
    for path in sorted(PACKAGE.rglob("*.py")):
        for call in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
                continue
            if call.func.attr not in TEXT_SETTERS or not call.args:
                continue
            value = call.args[-1]
            fragments = value.values if isinstance(value, ast.JoinedStr) else (value,)
            for fragment in fragments:
                if isinstance(fragment, ast.Constant) and isinstance(fragment.value, str):
                    yield f"{path.relative_to(PACKAGE)}:{fragment.lineno}", fragment.value
    manifest = ROOT / "sample_projects/manifest.json"
    for project in json.loads(manifest.read_text(encoding="utf-8"))["projects"]:
        for key in ("scientific_name", "description"):
            yield manifest.name, project[key]
    for path in sorted((ROOT / "r/RCMetaR/R").glob("*.R")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.lstrip().startswith("#"):
                for match in R_UI_LITERAL.finditer(line):
                    yield f"{path.name}:{line_number}", match[2]


def test_user_facing_copy_conventions():
    failures = []
    for location, value in _visible_copy():
        for rule, pattern in RULES.items():
            if rule.startswith("file ") and not re.search(r"\bimport\b", value, re.I):
                continue
            if pattern.search(value):
                failures.append(f"{location}: {rule}: {value!r}")
    assert not failures, "\n" + "\n".join(failures)
