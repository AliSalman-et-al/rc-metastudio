import json
from pathlib import Path
from scripts import inspect_windows_deployment as inspector

root = Path("/home/ali/.t3/qa-round3/E/package-run41956137300")
for relative in (
    "dist/RCMetaStudio/qualification",
    "work/archive-qualification/RCMetaStudio-0.5.1-windows-x64/qualification",
):
    directory = root / relative
    smoke = json.loads((directory / "packaged-smoke.json").read_text())
    workflow = smoke["workflows"]
    print(relative)
    print("pinned summary:", workflow["normalized_summary_sha256"] == inspector.EXPECTED_SUMMARY_SHA256)
    print("scales:", [inspector._windows_scale_valid(scale) for scale in smoke["scales"]])
    print("log markers:", inspector._windows_log_markers_valid((directory / "packaged-smoke.log").read_text()))
    print("locale identity:", inspector._valid_locale_variants(workflow["locale_variants"]))
    for variant in workflow["locale_variants"]:
        print(variant["locale"], variant["raw_summary_sha256"], variant["svg_sha256"])
    try:
        inspector._validate_windows_smoke(smoke, (directory / "packaged-smoke.log").read_text())
        print("PASS")
    except inspector.DeploymentInspectionError as error:
        print("FAIL:", error)
