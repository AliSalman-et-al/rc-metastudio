Merge origin/master (bf975092) into PR #544 without rewriting history.
The sole verify_analysis_authorities call is inside args.desktop_shard is None.
Non-desktop --skip-desktop executes it; --desktop-shard 1/2/3 do not.
The desktop job checkout retains fetch-depth: 0.

Local commands from the repository root:
source artifacts/statistical-mutants/env.sh
bash artifacts/statistical-mutants/typing-command.sh
python -m pytest tests/python/fast/test_rcmetar_r_manifest_validation.py -q

Strict Ty target: win32. Result: all checks passed.
Manifest tests: 16 passed, 1 skipped (see retained transcript).
