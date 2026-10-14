"""Round-three report and sequential figure contracts through real Qt and R."""

import json
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET


def check_report(app, view, work, record):
    from rc_metastudio import results_window

    assert view.report_text.toPlainText().startswith("Model configuration\n")
    view.copy_report_action.trigger()
    copied = app.clipboard().text()
    assert copied.startswith(view.results.identity + "\n"), copied
    for section in view.results.sections:
        for table in section.tables:
            assert "\t".join(table.headers) in copied, (table.title, copied)
            for row in table.rows:
                assert "\t".join(row) in copied, (table.title, row, copied)
    output = work / "round3-report.txt"
    with patch.object(results_window.QFileDialog, "getSaveFileName", return_value=(str(output), "Text report (*.txt)")):
        view.export_report_action.trigger()
    assert output.read_text(encoding="utf-8") == copied
    view.report_action.setChecked(True)
    app.processEvents()
    record("round3-report-copy-export", view, identity=view.results.identity,
           text=copied, tables=[dict(title=t.title, headers=t.headers, rows=t.rows)
                               for s in view.results.sections for t in s.tables])


def check_sequential(view, workflow, record):
    from rc_metastudio import r_bridge

    tables = [t for s in view.results.sections for t in s.tables if t.title == "Model Results"]
    for index, (title, path) in enumerate(view.results.display_images.items()):
        params = view.params_paths[title]
        r_bridge.load_in_r(str(params) + ".plotdata")
        data = json.loads(str(r_bridge.ro.r('jsonlite::toJSON(list(slab=plot.data$slab, labels=rcmetar.metafor.effect.labels(plot.data), has_overall=plot.data$has_overall, estimates=plot.data$effect_display$estimate), auto_unbox=TRUE, digits=16)')[0]))
        svg = ET.parse(path)
        nodes = [("".join(node.itertext()), float(node.attrib.get("y", 0)))
                 for node in svg.iter("{http://www.w3.org/2000/svg}text")]
        table = tables[index]
        assert len(table.rows) == len(data["slab"]), (title, table, data)
        assert table.headers[0] == ("Study added (k)" if workflow == "cumulative" else "Study omitted"), table
        for row, name, effect in zip(table.rows, data["slab"], data["labels"], strict=True):
            label_y = [y for text, y in nodes if text == name]
            effect_y = [y for text, y in nodes if text == effect]
            assert label_y and any(abs(a-b) < .01 for a in label_y for b in effect_y), (title, name, effect, nodes)
            assert row[0] == name, (title, row, name)
            assert row[1] == effect, (title, row, effect)
        if workflow == "leave-one-out":
            assert isinstance(data.get("has_overall"), bool), data
            assert (data["slab"][0] == "All studies") == data["has_overall"], data
        record("round3-sequential-rows", view, title=title, workflow=workflow,
               rows=table.rows, figure=data, plots={title: path})


def run(app, window, work, record):
    from analysis_matrix import DATA_TYPES, run as matrix
    from rc_metastudio.analysis_dataset import Covariate

    def prepare(target):
        studies = target.model.get_studies(only_if_included=True)
        target.model.dataset.add_covariate(Covariate("Group", "factor"),
                                          {s.name: "A" if i % 2 else "B" for i, s in enumerate(studies)})
        target.model.reset_model()
        target.enable_menu_options_that_require_dataset()

    for name in DATA_TYPES:
        for workflow in ("cumulative", "leave-one-out", "subgroup"):
            window.workspace.mark_saved()
            view = matrix(app, window, "analysis-data-" + name, record,
                          keep_results=True, workflow_override=workflow,
                          parameters={"digits": 6}, prepare=prepare if workflow == "subgroup" else None)
            check_report(app, view, work, record)
            if workflow != "subgroup":
                check_sequential(view, workflow, record)
            else:
                tables = [t for s in view.results.sections for t in s.tables]
                assert any("k" in t.headers for t in tables), tables
                assert any("Q" in t.headers and "df" in t.headers and "I²" in t.headers for t in tables), tables
            view.close()
            app.processEvents()
