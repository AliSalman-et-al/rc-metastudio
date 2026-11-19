import json
import re
import shutil
from xml.etree import ElementTree as ET
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.e2e.desktop_scenarios import SCENARIOS, Scenario


def run(driver, app, window, scenario):
    from PyQt6 import QtWidgets
    from advanced_workflows import click, modal
    from analysis_matrix import run as run_analysis
    from rc_metastudio import r_bridge
    from rc_metastudio.plot_editor_dialog import EditPlotDialog
    from tests.e2e.analysis_presentation_workflows import analyze_existing
    from tests.e2e.plot_observations import load_serialized_object
    from tests.python.gui.qt_test_support import metric_action

    ns = "{http://www.w3.org/2000/svg}"
    receipts = []

    def proof(view, metric, style, digits):
        view.fit_width_action.trigger()
        app.processEvents()
        artifact, _ = view._selected_plot()
        load_serialized_object(artifact.params_path + ".plotdata")
        values = json.loads(str(r_bridge.r_iterable_to_list(r_bridge.ro.r("""
            jsonlite::toJSON(local({
                b <- plot.data
                plan <- RCMetaR:::rcmetar.forest.layout.preflight(b)
                e <- RCMetaR:::rcmetar.forest.axis.effect(b, RCMetaR:::rcmetar.forest.journal.effect.intervals(b))
                pooled <- vapply(c(b$res$ci.lb, b$res$ci.ub),
                                 function(value) RCMetaR:::rcmetar.forest.axis.values(b, value), numeric(1))
                list(limits=plan$x$alim, ticks=plan$x$at,
                     study_extents=range(c(e$ci.lb, e$ci.ub), finite=TRUE), pooled=pooled)
            }), digits=16)
        """))[0]))
        values.update(metric=metric, style=style, digits=digits)
        lo, hi = values["limits"]
        for x in (*values["study_extents"], *values["pooled"]):
            if metric in ("PR", "PLN", "PLO", "PAS", "PFT"):
                x = min(1, max(0, x))
            assert lo <= x <= hi, values
        assert len([tick for tick in values["ticks"] if lo <= tick <= hi]) >= 2, values
        if metric in ("PR", "PLN", "PLO", "PAS", "PFT"):
            assert 0 <= lo < hi <= 1, values
        if metric in ("RD", "RR", "AS", "MD", "SMD", "Mean"):
            assert lo <= 0 <= hi, values
        if metric == "RD":
            assert hi - lo < .5, values
        receipts.append(values)
        name = f"{metric}-{style}-{digits}"
        nodes = list(ET.parse(artifact.display_path()).iter(ns + "text"))
        labels = ["".join(node.itertext()) for node in nodes]
        if metric in ("RR", "RD") and style == "bmj":
            assert "Favours BCG vaccine" in labels and "Favours Control" in labels, labels
            estimate = rf"[−]?[0-9,]+\.\d{{{digits}}}"
            columns = [label for label in labels if re.fullmatch(r"−?[0-9,.]+ \(.+ to .+\)", label)]
            prediction = next(label for label in labels if "% prediction interval: " in label)
            assert re.search(rf"\({estimate} to {estimate}\)$", prediction), prediction
            assert len(columns) >= 13
            assert all(re.fullmatch(rf"{estimate} \({estimate} to {estimate}\)", label) for label in columns), columns
            assert not any(re.search(rf"−0\.0{{{digits}}}\b", label) for label in labels), labels
        driver.record_step(name, view, axis=values, plots={name: artifact.display_path()})
        return artifact

    owned = driver.WORK / "BCG.rcms"
    shutil.copyfile(ROOT / "sample_projects/BCG.rcms", owned)
    assert window.open(str(owned), raise_on_error=True)
    for metric, style, digits in (("RR", "bmj", 2), ("RD", "bmj", 2), ("RD", "bmj", 4),
                                  ("RD", "default", 2), ("RD", "revman", 2), ("AS", "bmj", 2)):
        metric_action(window.menuMetric, metric).trigger()
        view = analyze_existing(app, window, "standard", "binary.random", driver.record_step,
                                parameters={"digits": digits, "rm.method": "DL", "fp_style": style})
        proof(view, metric, style, digits)
        if metric == "RR":
            def edit(dialog):
                dialog.favours_left.setText("Favours the longer intervention vaccine name")
                dialog.favours_right.setText("Favours the longer comparison control name")
                click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
            modal(app, EditPlotDialog, edit, view.edit_plot_action.trigger)
            app.processEvents()
            artifact, _ = view._selected_plot()
            labels = ["".join(node.itertext()) for node in ET.parse(artifact.display_path()).iter(ns + "text")]
            assert "Favours the longer intervention vaccine name" not in labels
            assert "Favours the longer comparison control name" not in labels
            driver.record_step("RR-bmj-long-directions", view, plots={"long-directions": artifact.display_path()})
            view.close()
            app.processEvents()
            window.workspace.mark_saved()
            assert window.open(str(owned), raise_on_error=True)
        else:
            if (metric, style, digits) == ("RD", "default", 2):
                def bounds(dialog):
                    dialog.plot_lb_le.setText("-0.1")
                    dialog.plot_ub_le.setText("0.05")
                    click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
                modal(app, EditPlotDialog, bounds, view.edit_plot_action.trigger)
                artifact, _ = view._selected_plot()
                load_serialized_object(artifact.params_path + ".plotdata")
                limits = r_bridge.r_iterable_to_list(r_bridge.ro.r("RCMetaR:::rcmetar.forest.layout.preflight(plot.data)$x$alim"))
                assert limits == [-0.1, 0.05], limits
                driver.record_step("RD-explicit-bounds", view, limits=limits, plots={"RD-explicit": artifact.display_path()})
            view.close()
            app.processEvents()
            if (metric, style, digits) == ("RD", "default", 2):
                window.workspace.mark_saved()
                assert window.open(str(owned), raise_on_error=True)
        window.workspace.mark_saved()

    for family, metric in (("twoarm-mean", "MD"), ("twoarm-smd", "SMD"), ("onearm-mean", "Mean"),
                           *(("onearm-proportion", m) for m in ("PR", "PLN", "PLO", "PAS", "PFT"))):
        def prepare(target):
            metric_action(target.menuMetric, metric).trigger()
            app.processEvents()
        view = run_analysis(app, window, "analysis-data-" + family, driver.record_step, keep_results=True,
                            parameters={"digits": 2, "fp_style": "bmj"}, prepare=prepare)
        proof(view, metric, "bmj", 2)
        view.close()
        app.processEvents()
        window.workspace.mark_saved()
    (driver.WORK / "axis-measurements.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")


SCENARIOS["output-polish-r3"] = Scenario(run, 320, qualifies=False)
if len(sys.argv) > 1 and sys.argv[1] == "desktop":
    sys.argv = [str(ROOT / "tests/e2e/desktop_driver.py"), *sys.argv[2:]]
    runpy.run_path(sys.argv[0], run_name="__main__")
else:
    from scripts import verify_rcms
    desktop_command = verify_rcms._desktop_command
    def command(scenario, work):
        original = desktop_command(scenario, work)
        original[-3:-2] = [str(Path(__file__).resolve()), "desktop"]
        return original
    verify_rcms._desktop_command = command
    sys.argv = [__file__, "output-polish-r3", "--native"]
    raise SystemExit(verify_rcms.main())
