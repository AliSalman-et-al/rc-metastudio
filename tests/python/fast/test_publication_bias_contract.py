import pytest

from rc_metastudio import r_bridge
from rc_metastudio.publication_bias import (
    EligibilityReport,
    FunnelKind,
    FunnelPlotSpec,
    LabelPolicy,
    SmallStudyEffectsRequest,
    TrimAndFillEstimator,
    TrimAndFillModel,
)


@pytest.mark.parametrize("version", [None, True, 1.0, 2, "1"])
def test_python_r_boundary_requires_exact_small_study_request_version(version):
    request = {"data.type": "continuous", "metric": "MD"}
    if version is not None:
        request["version"] = version

    with pytest.raises(ValueError, match="unsupported small-study effects request version"):
        r_bridge.run_small_study_effects(object(), request)


@pytest.mark.parametrize("version", [True, 1.0, 2, "1"])
def test_small_study_request_rejects_non_exact_versions(version):
    with pytest.raises(ValueError, match="unsupported small-study effects request version"):
        SmallStudyEffectsRequest(
            data_type="continuous", metric="MD", version=version
        )


def test_eligibility_parser_rejects_incomplete_wire_entries():
    with pytest.raises(ValueError, match="eligibility method is missing fields"):
        EligibilityReport.from_mapping(
            {
                "data.type": "continuous",
                "metric": "MD",
                "usable.studies": 4,
                "raw.data.available": False,
                "standard.error.range": [0.1, 0.4],
                "package.versions": {"meta": "8.5-0"},
                "warnings": [],
                "methods": [{"method": "classical-egger"}],
            }
        )


def test_eligibility_parser_normalizes_scalarized_single_method_mapping():
    report = EligibilityReport.from_mapping(
        {
            "data.type": "diagnostic",
            "metric": "DOR",
            "usable.studies": 4,
            "raw.data.available": True,
            "standard.error.range": [0.1, 0.4],
            "package.versions": {"meta": "8.5-0"},
            "warnings": "one warning",
            "methods": {
                "method": "deeks",
                "available": True,
                "reason": "",
                "usable.studies": 4,
                "required.inputs": [],
                "warnings": "one method warning",
                "role": "primary",
            },
        }
    )
    assert len(report.methods) == 1
    assert report.methods[0].method == "deeks"
    assert report.warnings == ("one warning",)
    assert report.methods[0].warnings == ("one method warning",)


def test_contour_levels_are_only_valid_for_contour_specs():
    with pytest.raises(ValueError, match="contour levels apply only"):
        FunnelPlotSpec(FunnelKind.ORDINARY, contour_levels=(90.0,))


def test_create_applies_custom_contour_levels_only_to_contour_specs():
    request = SmallStudyEffectsRequest.create(
        data_type="continuous",
        metric="MD",
        selected_funnels=(FunnelKind.ORDINARY, FunnelKind.CONTOUR),
        contour_levels=(85.0, 95.0),
    )
    assert request.plot_specs[0].contour_levels == ()
    assert request.plot_specs[1].contour_levels == (85.0, 95.0)
    assert request.to_mapping()["funnel.contour.levels"] == ["", "85,95"]


def test_contour_plot_spec_serializes_presentation_controls_without_options_bag():
    request = SmallStudyEffectsRequest.create(
        data_type="continuous",
        metric="MD",
        selected_funnels=(FunnelKind.ORDINARY, FunnelKind.CONTOUR),
        label_policy=LabelPolicy.ALL,
        sampling_confidence_level=90,
        include_tau2=True,
        point_size=1.5,
        reference_line_visible=False,
        pooled_overlay_visible=False,
    )
    wire = request.to_mapping()
    assert wire["funnels"] == ["ordinary", "contour"]
    assert wire["funnel.label.policy"] == ["all", "all"]
    assert wire["funnel.sampling.conf.level"] == [90.0, 90.0]
    assert wire["funnel.sampling.region.visible"] == [True, True]
    assert "funnel.show.sampling.region" not in wire
    assert wire["funnel.include.tau2"] == [True, True]
    assert wire["funnel.point.size"] == [1.5, 1.5]
    assert wire["funnel.reference.visible"] == [False, False]
    assert wire["funnel.pooled.overlay.visible"] == [False, False]
    assert wire["funnel.style"] == ["default", "default"]
    assert wire["funnel.point.symbol"] == [19, 19]
    assert "options" not in wire


def test_trimfill_request_serializes_estimator_model_side_and_extrapolation():
    request = SmallStudyEffectsRequest.create(
        data_type="continuous",
        metric="MD",
        trim_and_fill=True,
        trim_and_fill_estimator=TrimAndFillEstimator.R0,
        trim_and_fill_side="right",
        trim_and_fill_model=TrimAndFillModel.COMMON,
        extrapolation=True,
    )
    wire = request.to_mapping()
    assert wire["trim.and.fill"] is True
    assert wire["trim.and.fill.estimator"] == "R0"
    assert wire["trim.and.fill.side"] == "right"
    assert wire["trim.and.fill.model"] == "common"
    assert wire["extrapolation"] is True


def test_request_rejects_unknown_asymmetry_method():
    with pytest.raises(ValueError, match="unsupported small-study effects test"):
        SmallStudyEffectsRequest.create(
            data_type="binary", metric="OR", selected_tests=("not-a-test",)
        )
