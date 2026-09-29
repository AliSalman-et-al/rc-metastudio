"""Check the R list boundary in an isolated embedded-R process."""

import os
import textwrap

from ._r_driver_support import REPO_ROOT, run_python_driver


_DRIVER = textwrap.dedent(
    r"""
    import os
    import sys

    sys.path.insert(0, __REPO_ROOT__ + os.sep + "src")
    try:
        from rc_metastudio.r_bridge import ro, parse_out_results
        r_result = ro.r('''
            local({
                cell <- function(x) list(status="available", value=x, reason=NULL)
                estimate <- function(x) list(
                    estimate=cell(x), lower=cell(x - .1), upper=cell(x + .1)
                )
                list(binary_numerics=list(
                    version=1L, metric="OR", calculation_scale="log",
                    display_scale="ratio", weight_scale="percent",
                    calculation_null_value=0, display_null_value=1,
                    pooled=list(
                        calculation=estimate(-.5), display=estimate(exp(-.5)),
                        study_count=cell(1), p_value=cell(.23)
                    ),
                    studies=unname(list(list(
                        order=0L, label="Study A",
                        treatment_events=cell(2), treatment_total=cell(20),
                        control_events=cell(3), control_total=cell(20),
                        weight=cell(100),
                        p_value=list(status="not_available", value=NULL,
                                     reason="No per-study p-values."),
                        calculation=estimate(-.5), display=estimate(exp(-.5))
                    )))
                ))
            })
        ''')
    except (ImportError, RuntimeError) as exc:
        print("SKIP %s: %s" % (type(exc).__name__, exc))
        sys.exit(42)

    result = parse_out_results(r_result)
    assert result.binary_numerics is not None
    assert result.binary_numerics.studies[0].label == "Study A"
    assert result.binary_numerics.pooled.study_count.value == 1
    assert result.binary_numerics.studies[0].weight.value == 100
    assert result.binary_numerics.studies[0].p_value.status == "not_available"
    assert "binary_numerics" not in result.texts
    print("OK")
    """
).replace("__REPO_ROOT__", repr(REPO_ROOT))


def test_binary_numerics_bridge_preserves_a_single_study_sequence():
    env = dict(os.environ)
    env["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    run_python_driver(_DRIVER, env=env)
