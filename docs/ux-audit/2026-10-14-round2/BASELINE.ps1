. ./docs/ux-audit/2026-10-14-round2/ENV.ps1
New-Item -ItemType Directory -Force -Path $round2Library | Out-Null
Get-ChildItem -LiteralPath build/verification/review-r-library -Directory |
    Copy-Item -Destination $round2Library -Recurse -Force
uv run python docs/ux-audit/2026-10-14-round2/run.py before-doctor uv run python scripts/verify_rcms.py doctor
uv run python docs/ux-audit/2026-10-14-round2/run.py before-authorities "$env:RCMS_R_HOME/bin/Rscript.exe" .agents/skills/verify-rcms/scripts/analysis_authorities.R docs/ux-audit/2026-10-14-round2/before-authorities-results.json
uv run python docs/ux-audit/2026-10-14-round2/run.py before-golden uv run python scripts/verify_golden_compatibility.py --output build/qt6-verification/golden-compatibility-round2-before
uv run python docs/ux-audit/2026-10-14-round2/run.py before-r-tests uv run python -m pytest tests/r_stack -q -ra
