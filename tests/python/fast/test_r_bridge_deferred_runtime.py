import subprocess
import sys


def test_importing_application_r_bridge_does_not_initialize_rpy2():
    script = (
        "import sys\n"
        "import rc_metastudio.analysis_adapter\n"
        "import rc_metastudio.r_bridge\n"
        "assert 'rpy2.robjects' not in sys.modules\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
