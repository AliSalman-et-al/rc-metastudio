"""Open a genuine legacy metric archive through the ordinary desktop path."""

import copy
import hashlib
import json
from pathlib import Path
import zipfile


def reopen_legacy_mean_project(app, window, record):
    canonical_path = Path(window.workspace.path)
    with zipfile.ZipFile(canonical_path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    canonical = json.loads(members["project.json"])
    legacy = copy.deepcopy(canonical)
    for sheet in legacy["sheets"]:
        if sheet["settings"].get("metric") == "Mean":
            sheet["settings"]["metric"] = "TX Mean"
        for row in sheet["rows"]:
            for entry in row["entered_effects"]:
                if entry["metric"] == "Mean":
                    entry["metric"] = "TX Mean"
    members["project.json"] = json.dumps(legacy).encode("utf-8")
    manifest = json.loads(members["manifest.json"])
    manifest["members"]["project.json"] = {
        "size": len(members["project.json"]),
        "sha256": hashlib.sha256(members["project.json"]).hexdigest(),
    }
    members["manifest.json"] = json.dumps(manifest).encode("utf-8")
    legacy_path = canonical_path.with_name("mean-legacy-input.rcms")
    with zipfile.ZipFile(legacy_path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    assert window.open(str(legacy_path), raise_on_error=True)
    assert window.model.current_effect == "Mean"
    from rc_metastudio.project.adapter import dataset_to_project
    assert dataset_to_project(window.model.dataset) == canonical
    record("legacy-mean-reopened", window, metric=window.model.current_effect,
           exports={"legacy_input": str(legacy_path), "canonical_input": str(canonical_path)})
    assert window.save(destination=canonical_path.with_name("mean-migrated.rcms"))
    assert window.open(window.workspace.path, raise_on_error=True)
    assert dataset_to_project(window.model.dataset) == canonical
    app.processEvents()
    record("legacy-mean-resaved", window, metric=window.model.current_effect,
           exports={"canonical_project": str(window.workspace.path)})


def open_mean_sample(app, window, record, root, work):
    """Prove sample measurements and archive round trips before real analysis."""
    from rc_metastudio.project.adapter import dataset_to_project

    source = root / "sample_projects/Single-arm mean - Handgrip strength in young adults, Abe 2025.rcms"
    retained = root / "sample_projects/sources/abe2025.json"
    rows = json.loads(retained.read_text(encoding="utf-8"))["rows"]
    measurements = [[row["n"], row["mean"], row["sd"]] for row in rows]
    assert window.open(str(source), raise_on_error=True)
    assert window.model.current_effect == "Mean"
    sheet = window.model.current_sheet
    arm = "Young adult volunteers"
    assert sheet.arms[0].name == arm
    assert [(row.label, row.year) for row in sheet.rows] == [(row["study"], row["year"]) for row in rows]
    assert [row.analysis_unit.get_raw_data_for_arm(arm) for row in sheet.rows] == measurements
    before = dataset_to_project(window.model.dataset)
    from PyQt6 import QtWidgets
    from advanced_workflows import click, modal
    from rc_metastudio.calculators.continuous_dialog import ContinuousDataDialog

    def inspect_calculator(dialog):
        assert dialog.arm_names == [arm]
        assert dialog.simple_table.isRowHidden(1)
        values = []
        for column in range(3):
            item = dialog.simple_table.item(0, column)
            assert item is not None
            values.append(float(item.text()))
        assert values == measurements[0]
        record("mean-sample-calculator", dialog, measurements=values)
        click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel))

    modal(app, ContinuousDataDialog, inspect_calculator, lambda: window.tableView.row_header_clicked(0))
    assert dataset_to_project(window.model.dataset) == before
    assert window.save(destination=work / "mean-sample-resaved.rcms")
    assert window.open(window.workspace.path, raise_on_error=True)
    assert dataset_to_project(window.model.dataset) == before
    record("mean-sample-reopened", window, exports={"input": str(source), "saved": str(window.workspace.path)})
    return retained, sum(row["n"] for row in rows)


def compare_mean_sample_analysis(view, record, retained):
    """Compare displayed pooling with independent public metafor inputs."""
    from rc_metastudio import r_bridge
    from rc_metastudio.r_call_serialization import r_transaction
    from tests.analysis_regression.golden.support.golden_analysis import parsed_numeric_sections

    with r_transaction():
        expected = r_bridge.ro.r('''function(path) {
            rows <- jsonlite::fromJSON(path)$rows
            fit <- metafor::rma(measure="MN", mi=mean, sdi=sd, ni=n, data=rows, method="DL")
            c(estimate=as.numeric(fit$b), lower_bound=fit$ci.lb, upper_bound=fit$ci.ub)
        }''')(str(retained))
        reference = dict(zip(expected.names, map(float, expected)))
    summary = parsed_numeric_sections(view.results)["Summary"]
    for field, value in reference.items():
        assert abs(summary[field] - value) <= .00051, (field, summary, reference)
    record("mean-sample-public-authority", view, observed=summary, expected=reference,
           exports={"retained_source": str(retained)})
