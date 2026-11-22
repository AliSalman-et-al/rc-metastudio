# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared packaged smoke identities, trace markers, and display scales."""

SURFACE_SCALES = ("1.25", "1.50", "1.75")
BARZA_SAMPLE = "Binary - Aminoglycoside dosing, Barza 1996.rcms"
BCG_SAMPLE = "Binary - BCG vaccine and tuberculosis, Colditz 1994.rcms"
EXPECTED_SUMMARY_SHA256_BY_SAMPLE = {
    BARZA_SAMPLE: "eee9974e5edd6f39dbbff0a177c6da3a737a458d74245b4f78365b386ec689b9",
    BCG_SAMPLE: "bfec74e1538844afe5b79042292a2bf3f823ed596dee4a6da0aa7689b09f28e9",
}
POST_CLOSE = "packaged-workflow:post-close"
STARTUP_PROJECT_PASSED = "startup-project:normal-entry-point-passed"


def process_exit_marker(result: int) -> str:
    return f"packaged-workflow:process-exit:{result}"


WORKFLOW_MARKERS = (
    "packaged-runtime-probe:passed",
    *(f"packaged-surface:scale-{scale}-passed" for scale in SURFACE_SCALES),
    "packaged-workflow:project-exercise:complete",
    "packaged-workflow:evidence-written",
    POST_CLOSE,
)
ATOMIC_COMPLETION_MARKERS = (*WORKFLOW_MARKERS, process_exit_marker(0))
ASSEMBLED_COMPLETION_MARKERS = (*WORKFLOW_MARKERS, STARTUP_PROJECT_PASSED, process_exit_marker(0))


if __name__ == "__main__":
    print("\n".join(SURFACE_SCALES))
