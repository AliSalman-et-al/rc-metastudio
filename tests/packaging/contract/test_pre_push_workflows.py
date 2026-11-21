"""Every Windows source CI job needs an executable local gate step."""

import yaml

from scripts.verify import REPO_ROOT, pre_push_steps


def test_every_windows_latest_job_runs_in_pre_push():
    local_steps = pre_push_steps()
    missing = []
    for workflow in sorted((REPO_ROOT / ".github/workflows").iterdir()):
        if workflow.suffix not in {".yml", ".yaml"}:
            continue
        for name, job in yaml.safe_load(workflow.read_text(encoding="utf-8")).get("jobs", {}).items():
            runner = job.get("runs-on")
            matrix = job.get("strategy", {}).get("matrix", {})
            if "windows-latest" in str(runner) or (
                "${{" in str(runner) and "windows-latest" in str(matrix)
            ):
                if f"{workflow.stem}/{name}" not in local_steps:
                    missing.append(f"{workflow.name}: {name}")
    assert not missing, f"Windows jobs missing from pre-push: {missing}"
