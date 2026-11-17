# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared packaged smoke trace and the display scales emitted for native builders."""

SURFACE_SCALES = ("1.25", "1.50", "1.75")
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
