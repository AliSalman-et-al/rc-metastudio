"""Run the complete desktop matrix, optionally including current-source R proof."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.verify_rcms import SCENARIOS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full",
        action="store_true",
        help="Also run current-source R-stack and independent authority comparisons",
    )
    args = parser.parse_args()
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    evidence = ROOT / "artifacts/verification/rcms" / (run_id + "-complete")
    evidence.mkdir(parents=True)
    print(f"Complete-run evidence: {evidence}", flush=True)
    commands = []
    if args.full:
        r_home = Path(os.environ["RCMS_R_HOME"])
        rscript = r_home / "bin" / ("Rscript.exe" if os.name == "nt" else "Rscript")
        commands.extend(
            [
                [
                    sys.executable,
                    "scripts/verify.py",
                    "r-stack",
                    "--rscript",
                    str(rscript),
                ],
                [
                    str(rscript),
                    ".agents/skills/verify-rcms/scripts/analysis_authorities.R",
                    str(evidence / "authorities.json"),
                ],
            ]
        )
    # The full R-stack lane already exercises every desktop scenario via pytest.
    # Keep doctor here; repeating the whole registry doubles the expensive work.
    scenarios = ("doctor",) if args.full else SCENARIOS
    commands.extend(
        [sys.executable, "scripts/verify_rcms.py", scenario] for scenario in scenarios
    )
    rows = []
    status_before = subprocess.check_output(
        ["git", "status", "--short"], cwd=ROOT, text=True
    ).strip()
    env = os.environ.copy()
    if env.get("RCMS_R_LIBS"):
        env["R_LIBS"] = env["RCMS_R_LIBS"]
    try:
        for index, command in enumerate(commands):
            print("Running " + " ".join(command), flush=True)
            with (evidence / f"{index:02d}.log").open("wb") as output:
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=env,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
            log = evidence / f"{index:02d}.log"
            rows.append(
                {
                    "command": command,
                    "exit_code": result.returncode,
                    "log": log.name,
                    "evidence": [
                        line.removeprefix("Evidence: ").strip()
                        for line in log.read_text(
                            encoding="utf-8", errors="replace"
                        ).splitlines()
                        if line.startswith("Evidence: ")
                    ],
                }
            )
            if result.returncode:
                print(f"Failed; inspect {evidence / rows[-1]['log']}", flush=True)
                return 1
        return 0
    finally:
        (evidence / "summary.json").write_text(
            json.dumps(
                {
                    "head": subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                    ).strip(),
                    "full_requested": args.full,
                    "passed": len(rows) == len(commands)
                    and all(row["exit_code"] == 0 for row in rows),
                    "commands": rows,
                    "worktree_status_before": status_before,
                    "worktree_status_after": subprocess.check_output(
                        ["git", "status", "--short"], cwd=ROOT, text=True
                    ).strip(),
                    "files_sha256": {
                        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in evidence.iterdir()
                        if path.is_file()
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    raise SystemExit(main())
