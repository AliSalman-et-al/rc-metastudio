"""Exercise analysis cardinality and plot ownership with production Qt/R."""

import hashlib
import json
from pathlib import Path

from PyQt6 import QtCore


def run(app, window, scenario, record):
    if scenario == "project-request-cardinality":
        request_cardinality(app, window, record)
    else:
        plot_ownership(app, window, record)


def request_cardinality(app, window, record):
    from advanced_workflows import ROOT
    from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
    from rc_metastudio.analysis_adapter import execute_analysis_requests

    for family, metric, sample in (
        ("time_to_event", "HR", "Pignon2000-HR.rcms"),
        ("event_rates", "IRR", "NielWeise2008-IRR.rcms"),
    ):
        assert window.open(str(ROOT / "sample_projects" / sample), raise_on_error=True)
        window.action_go.trigger()
        app.processEvents()
        dialog = next(w for w in app.topLevelWidgets()
                      if isinstance(w, AnalysisSetupDialog) and w.isVisible())
        method = family + ".fixed"
        dialog.method_cbo_box.setCurrentText(next(label for label, key
                                                in dialog.available_method_d.items() if key == method))
        app.processEvents()
        request, = dialog.analysis_requests()
        assert request.data_type == family and request.metric == metric
        record("analysis-request-configured", dialog, request=request.to_mapping())
        dialog.reject()
        before = window.workspace.document
        try:
            execute_analysis_requests(window.model, (request, request))
        except ValueError as error:
            assert "exactly one request" in str(error), str(error)
            record("extra-analysis-requests-rejected", window, family=family,
                   requests=[request.to_mapping(), request.to_mapping()], error=str(error))
        else:
            raise AssertionError("Extra analysis request silently ignored: " + family)
        assert window.workspace.document == before
        result = execute_analysis_requests(window.model, (request,))
        assert result.sections and result.images
        record("single-analysis-request-executed", window, family=family,
               texts=dict(result.texts), plots=dict(result.display_images))


def plot_ownership(app, window, record):
    from analysis_matrix import run as matrix
    from rc_metastudio import r_bridge
    from rc_metastudio.plot_service import PlotServiceError

    def artifact(view):
        return next(view.create_plot_artifact(title, path,
                    params_path=view.results.image_params_paths.get(title))
                    for title, path in view.results.images.items()
                    if view.results.plot_capabilities[title].regenerator == "forest")

    def semantics(selected):
        r_bridge.load_in_r(selected.params_path + ".plotdata")
        return json.loads(str(r_bridge.execute_r_string(
            'jsonlite::toJSON(list(studies=plot.data$slab, '
            'estimate=as.numeric(plot.data$res$b), yi=as.numeric(plot.data$res$yi)), '
            'auto_unbox=FALSE, digits=16)')[0]))

    first = matrix(app, window, "analysis-binary.fixed.inv.var", record, keep_results=True)
    first_plot = artifact(first)
    expected = semantics(first_plot)
    params = first.plot_service.load_params(first_plot.params_path)
    assert params is not None
    params.pop("resolved.defaults", None)
    first.hide()

    def prepare(other):
        model = other.model
        assert model.setData(model.index(0, model.NAME), "Other analysis study")
        index = model.index(0, model.INCLUDE_STUDY)
        assert model.setData(index, QtCore.Qt.CheckState.Unchecked,
                             QtCore.Qt.ItemDataRole.CheckStateRole)

    second = matrix(app, window, "analysis-binary.fixed.inv.var", record,
                    keep_results=True, prepare=prepare)
    window.workspace.mark_saved()
    second_plot = artifact(second)
    assert semantics(second_plot) != expected
    second_files = [Path(second_plot.params_path + suffix)
                    for suffix in (".params", ".plotdata", ".data", ".res")]
    second_hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in second_files}
    # A caller may inspect another result after loading this editor's parameters.
    # Apply must use its own persisted inputs, regardless of the last R load.
    assert second.plot_service.load_params(second_plot.params_path) is not None
    first.show()
    params["plot_caption"] = "First analysis after another result was loaded"
    record("plot-ownership-before-apply", first, expected=expected,
           other=semantics(second_plot), other_hashes=second_hashes)
    first.plot_service.apply_edits(regenerator="forest", params_path=first_plot.params_path,
                                   updated_params=params, output_path=first_plot.image_path)
    actual = semantics(first_plot)
    assert actual == expected, ("Another analysis replaced the plot's studies/results", expected, actual)
    assert {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in second_files} == second_hashes
    record("plot-ownership-preserved", first, expected=expected, actual=actual,
           plots={first_plot.title: first_plot.display_path()})
    protected = [Path(first_plot.params_path + suffix)
                 for suffix in (".params", ".plotdata", ".data", ".res")]
    protected.append(Path(first_plot.image_path))
    for suffix in (".data", ".params", ".res"):
        source = Path(first_plot.params_path + suffix)
        hidden = source.with_suffix(source.suffix + ".missing")
        original = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
        source.rename(hidden)
        try:
            try:
                first.plot_service.apply_edits(regenerator="forest", params_path=first_plot.params_path,
                                               updated_params=params, output_path=first_plot.image_path)
            except PlotServiceError:
                pass
            else:
                raise AssertionError("Missing plot input accepted: " + suffix)
        finally:
            hidden.rename(source)
        assert {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected} == original
        record("missing-plot-input-preserved-artifacts", first, missing=suffix, hashes=original)
    first.close()
    second.close()
    window.workspace.mark_saved()
