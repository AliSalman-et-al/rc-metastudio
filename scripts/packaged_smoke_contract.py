# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared evidence contract for packaged desktop smoke runs."""

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


def valid_sha256(value: object) -> bool:
    return (
        isinstance(value, str) and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def valid_sha256_map(value: object) -> bool:
    return isinstance(value, dict) and bool(value) and all(
        isinstance(label, str) and bool(label) and valid_sha256(digest)
        for label, digest in value.items()
    )


def sample_hashes(value: object) -> dict[str, str] | None:
    if not isinstance(value, dict) or value.get("passed") is not True:
        return None
    if not valid_sha256(value.get("manifest_sha256")):
        return None
    records = value.get("projects")
    if not isinstance(records, list) or not records:
        return None
    projects: dict[str, str] = {}
    for record in records:
        if not isinstance(record, dict):
            return None
        project = record.get("project")
        digest = record.get("sha256")
        if (
            not isinstance(project, str) or not project.endswith(".rcms") or project in projects
            or not isinstance(digest, str) or not valid_sha256(digest)
            or not valid_sha256(record.get("semantic_sha256"))
            or record.get("opened_in_packaged_application") is not True
        ):
            return None
        projects[project] = digest
    return projects


def locale_variants(value: object) -> tuple[dict, dict] | None:
    if not isinstance(value, list) or len(value) != 2:
        return None
    en, de = value
    if not isinstance(en, dict) or not isinstance(de, dict):
        return None
    if not (
        en.get("locale") == "en_US" and de.get("locale") == "de_DE"
        and "." in str(en.get("input")) and "," in str(de.get("input"))
        and en.get("canonical_value") == de.get("canonical_value")
        and all(
            en.get(field) == de.get(field) and valid_sha256(en.get(field))
            for field in ("normalized_summary_sha256", "raw_summary_sha256")
        )
        and en.get("svg_sha256") == de.get("svg_sha256")
        and valid_sha256_map(en.get("svg_sha256"))
    ):
        return None
    return en, de


if __name__ == "__main__":
    print("\n".join(SURFACE_SCALES))
