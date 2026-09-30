"""Small validated renderer records for GUI tests."""


def forest_render_state(figure_key, variant="standard"):
    state = {
        "version": 1,
        "renderer": "rcmetar_forest_v1",
        "figure_key": figure_key,
        "data_type": "binary",
        "style": "default",
        "variant": variant,
        "single_study": False,
        "studies": {
            "yi": [0.2, -0.1],
            "vi": [0.01, 0.04],
            "ci_lb": [0.004, -0.492],
            "ci_ub": [0.396, 0.292],
            "labels": ["Trial A, 2020", "Trial B, 2021"],
        },
        "summary": {
            "b": 0.1,
            "ci_lb": -0.12,
            "ci_ub": 0.32,
            "QE": 1.5,
            "k": 2,
            "p": 1,
            "QEp": 0.2,
            "I2": 0.0,
            "tau2": 0.0,
            "method": "REML",
            "zval": 1.0,
            "pval": 0.3,
        },
        "weights": [0.7, 0.3],
        "ilab": {"matrix": [[], []], "columns": [], "headers": [], "groups": []},
        "sample_sizes": None,
        "params": {
            "measure": "OR",
            "conf.level": 95,
            "digits": 2,
            "rm.method": "REML",
            "fp_style": "default",
            "fp_xlabel": "Original effect",
            "fp_col1_str": "Study",
        },
        "plot_range": [-1.0, 1.0],
        "effect_display": {
            "y_disp": [0.2, -0.1],
            "lb_disp": [0.004, -0.492],
            "ub_disp": [0.396, 0.292],
        },
    }
    if variant == "subgroup":
        state["single_study"] = True
        state["weights"] = None
        state["subgroups"] = {
            "names": ["Early", "Late"],
            "results": [
                {"b": 0.15, "ci_lb": -0.1, "ci_ub": 0.4, "QE": 0.2, "k": 1, "p": 1},
                {"b": -0.05, "ci_lb": -0.3, "ci_ub": 0.2, "QE": 0.1, "k": 1, "p": 1},
            ],
            "overall": dict(state["summary"]),
            "study_rows": [2.0, 1.0],
            "header_rows": [3.0, 0.0],
            "polygon_rows": [1.5, -0.5],
            "overall_row": -1.5,
            "difference_test": {"QM": 0.4, "df": 1, "QMp": 0.5},
            "ylim": [-3.0, 5.5],
        }
    elif variant != "standard":
        state["single_study"] = True
    return state


def regression_render_state(figure_key):
    return {
        "version": 1,
        "renderer": "rcmetar_regression_v1",
        "figure_key": figure_key,
        "geometry": {
            "moderator": "age",
            "measure": "MD",
            "point_x": [1.0],
            "point_y": [0.2],
            "point_size": [1.0],
            "labels": ["Study A"],
            "line_x": [1.0, 2.0],
            "line_y": [0.2, 0.3],
            "ci_lb": [0.1, 0.2],
            "ci_ub": [0.3, 0.4],
            "pi_lb": None,
            "pi_ub": None,
            "confidence_level": 95.0,
        },
        "appearance": {
            "bp_style": "default",
            "bp_accent_color": "#2f5597",
            "bp_point_size_multiplier": 1.0,
            "bp_xlabel": "Age",
            "bp_plot_lb": "[default]",
            "bp_plot_ub": "[default]",
            "bp_xticks": "[default]",
            "bp_yticks": "[default]",
            "bp_show_regression_line": True,
            "bp_show_confidence_band": True,
            "bp_show_prediction_interval": False,
            "bp_show_legend": False,
        },
    }


def saved_plot_fixture(figure_key, state):
    """Return a record-shaped frozen source and a revision-tracking commit."""
    record = {
        "presentation": {"figures": {figure_key: {}}},
        "results": {"plot_render_state": {figure_key: state}},
    }
    commits = []

    def commit(
        committed_key,
        image_data,
        image_media_type,
        display_data,
        display_media_type,
        presentation_update,
    ):
        assert committed_key == figure_key
        record["presentation"]["figures"][figure_key].update(presentation_update)
        commits.append(
            (
                committed_key,
                image_data,
                image_media_type,
                display_data,
                display_media_type,
                dict(presentation_update),
            )
        )
        return "after-render-%d" % len(commits)

    return (
        record,
        {"record_id": "saved-plot-fixture", "revision": "before-render"},
        commit,
        commits,
    )
