"""Seeded real-archive round trips; override RCMS_ROUND_TRIP_CASES/SEED to explore."""
import copy
import json
import os
from pathlib import Path
import random
import time

from rc_metastudio.project_adapter import dataset_to_project, project_to_dataset
from rc_metastudio.project_format import (
    ProjectFormatError, _validate, is_empty_entry_row, load_project, save_project,
)

from rc_metastudio.project_domain import ProjectSemanticError, validate_project_semantics

ROOT = Path(__file__).resolve().parents[3]
TEXT = ["", " ", 'é漢字🙂\n\t"quoted"', "x" * 1024]
KINDS = [
    ("binary", 0, [None, "proportion", "proportions"], ["OR", "RD", "RR", "AS", "YUQ", "YUY", "PR", "PLN", "PLO", "PAS", "PFT"]),
    ("continuous", 1, [None, "mean", "means", "smd", "reg_coef", "generic_effect"], ["MD", "SMD", "Mean"]),
    ("diagnostic", 2, [None], ["Sens", "Spec", "PLR", "NLR", "DOR"]),
    ("time_to_event", 5, [None, "hazard_ratio"], ["HR"]),
    ("event_rates", 6, [None, "incidence_rate_ratio"], ["IRR"]),
]


def generate(rng, index, samples):
    if samples and index % 7 == 0:
        document = rng.choice(samples)
        project, state = copy.deepcopy((document.project, document.state))
        project["sheets"] = project["sheets"][:rng.randint(1, 3)]
        state["current_sheet_id"] = rng.choice([None] + [s["id"] for s in project["sheets"]])
        project["title"] = rng.choice(TEXT)
        for sheet in project["sheets"]:
            sheet["rows"] = [r for r in sheet["rows"] if not is_empty_entry_row(r)][:rng.randint(1, 4)]
            for row in sheet["rows"]:
                row["notes"] = rng.choice(TEXT)
                row["year"] = rng.choice([None, -2147483648, 0, 2147483647])
        return project, state
    sheets = []
    for s in range(rng.randint(1, 3)):
        family, dtype, subtypes, metrics = KINDS[(index + s) % len(KINDS)]
        arms = [dict(id=f"a{a}", name=f"Arm {a} {rng.choice(TEXT)}") for a in range(1 if dtype == 2 else rng.randint(2, 4))]
        rows = []
        for r in range(rng.randint(1, 4)):
            raw = {}
            for arm in arms:
                if rng.randrange(3) == 0:
                    continue
                n = rng.randint(1, 10000)
                values = {0: [rng.randint(0, n), n], 1: [n, rng.uniform(-100, 100), rng.random() * 10],
                          2: [rng.randint(0, n) for _ in range(4)], 5: [], 6: [rng.randint(0, n), rng.random() * 100 + 1]}[dtype]
                raw[arm["id"]] = ["" if rng.randrange(5) == 0 else v for v in values]
            pair = [a["id"] for a in arms[:2]]
            metric = rng.choice(metrics)
            comparison = pair[:1] if metric in {"PR", "PLN", "PLO", "PAS", "PFT", "Mean"} or dtype == 2 else pair
            ratio = []
            if dtype in (5, 6):
                ratio = [dict(arms=pair, input=dict(estimate=2., lower=1., upper=3., se=.2,
                         scale="ratio", confidence=95., source=rng.choice(["", "raw", "reported"]), unit="person-years"))]
            rows.append(dict(id=f"r{r}", label=f"Study {r} {rng.choice(TEXT)}",
                year=rng.choice([None, -2147483648, 0, 2026, 2147483647]),
                sample_size=rng.choice([None, 1, 1000000]), include=bool(rng.randrange(2)),
                manually_excluded=bool(rng.randrange(2)), notes=rng.choice(TEXT),
                covariates=rng.choice([{}, {"c": "", "f": ""}, {"c": None, "f": None}, {"c": 3.5, "f": rng.choice(TEXT)}]),
                raw_data=raw, entered_effects=[dict(metric=metric, arms=comparison,
                values=dict(est=0., lower=-1., upper=1., SE=.2, display_est=2., display_lower=1., display_upper=3., display_se=.3))],
                ratio_inputs=ratio))
        sheets.append(dict(id=f"s{s}", name=f"Sheet {s} {rng.choice(TEXT)}", family=family,
            data_type=dtype, sub_type=rng.choice(subtypes), arms=arms,
            covariates=[dict(id="c", name="Age", data_type=1), dict(id="f", name="Category", data_type=4)],
            settings=dict(arms=[a["id"] for a in arms], metric=rng.choice(metrics), extra={"text": rng.choice(TEXT)}), rows=rows))
    return dict(schema_version=3, title=rng.choice(TEXT), notes=rng.choice(TEXT), sheets=sheets), dict(
        schema_version=3, current_sheet_id=rng.choice([None] + [s["id"] for s in sheets]))


def difference(expected, actual, path="project"):
    if isinstance(expected, dict) and isinstance(actual, dict):
        if expected.keys() != actual.keys():
            return f"{path}: fields changed from {list(expected)} to {list(actual)}"
        for key in expected:
            found = difference(expected[key], actual[key], f"{path} / {key}")
            if found:
                return found
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return f"{path}: length changed from {len(expected)} to {len(actual)}"
        for i, (left, right) in enumerate(zip(expected, actual)):
            found = difference(left, right, f"{path} / item {i}")
            if found:
                return found
    elif expected != actual:
        return f"{path}: expected {expected!r}, got {actual!r}"
    return None


def check(path, project, state):
    try:
        save_project(path, project, state)
        loaded = load_project(path)
    except ProjectFormatError as exc:
        return f"accepted input could not be saved/reopened: {exc}"
    return difference(project, dataset_to_project(project_to_dataset(loaded.project))) or difference(state, loaded.state, "state")


def shrink(path, project, state):
    """Greedily delete list items and optional object fields, retaining valid failures."""
    project, state = copy.deepcopy((project, state))

    def visit(value):
        if isinstance(value, dict):
            for key in list(value):
                old = value.pop(key)
                try:
                    _validate(3, "project.json", project)
                    validate_project_semantics(project, state)
                    keep = bool(check(path, project, state))
                except (ProjectFormatError, KeyError, TypeError, ValueError):
                    keep = False
                if not keep:
                    value[key] = old
                    visit(old)
        elif isinstance(value, list):
            i = 0
            while i < len(value):
                old = value.pop(i)
                try:
                    _validate(3, "project.json", project)
                    validate_project_semantics(project, state)
                    keep = bool(check(path, project, state))
                except (ProjectFormatError, KeyError, TypeError, ValueError):
                    keep = False
                if not keep:
                    value.insert(i, old)
                    visit(old)
                    i += 1
    visit(project)
    return project, state


def test_project_round_trip_property(tmp_path):
    seed = int(os.environ.get("RCMS_ROUND_TRIP_SEED", "20261104"))
    count = int(os.environ.get("RCMS_ROUND_TRIP_CASES", "20"))
    assert count > 0
    rng = random.Random(seed)
    samples = [load_project(p) for p in sorted((ROOT / "sample_projects").glob("*.rcms"))]
    rejected = 0
    started = time.monotonic()
    path = tmp_path / "generated.rcms"
    for index in range(count):
        project, state = generate(rng, index, samples)
        try:
            _validate(3, "project.json", project)
            _validate(3, "state.json", state)
            validate_project_semantics(project, state)
        except (ProjectFormatError, ProjectSemanticError):
            rejected += 1
            continue
        failure = check(path, project, state)
        if failure:
            minimal, minimal_state = shrink(path, project, state)
            raise AssertionError(f"seed={seed} case={index}\n{check(path, minimal, minimal_state)}\n"
                                 f"Greedy minimal counterexample:\n{json.dumps([minimal, minimal_state], ensure_ascii=False, indent=2)}")
    print(f"seed={seed} candidates={count} rejected={rejected} ({rejected/count:.2%}) seconds={time.monotonic()-started:.3f}")
    assert rejected / count <= .2, "Fix generator: more than 20% of candidates rejected"
