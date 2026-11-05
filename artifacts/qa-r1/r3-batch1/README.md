# Round-three batch-one evidence

Base ffa8c4aa. No R or numerical oracle files changed.

Environment: source /home/ali/.t3/qa-env/ENV.sh, then export PYTHONPATH=$PWD/src:$PWD and RCMS_QT6_BUILD_ROOT=$PWD/build/qt6-verification. Forms generated with python scripts/build_qt6.py generate --build-root $RCMS_QT6_BUILD_ROOT.

Strict typing: python -c 'from scripts.verify import run_typing; from pathlib import Path; run_typing(Path("build/qt6-verification"))'. Full invocation and win32 target retained in proof/typing-win32.log.

Targeted command: python scripts/verify_rcms.py amino. proof/ retains runtime, transcript, inputs/source manifest, steps and selected captures. It proves Return advances, two-decimal report retains 0.004 to 1.44, and the three-decimal fitted fields match the unchanged numeric contract. R rendering uses the configured warm package, unchanged by this Python-only patch.

Native: RCMS_QA_APP_SRC=$PWD RCMS_QA_BUILD_ROOT=$PWD/build/qt6-verification /home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session r3batch1 start --dark --large-font. Open Analysis, capture menu; Escape, Ctrl+N, capture tiles; click Proportions, Return, capture next page. Owned sessions stopped. A light default-font tile capture is also retained.

Before evidence is the supplied reports and their screenshots in /home/ali/.t3/qa-round3/{A,B,I}. No newly captured before matrix. Native after coverage is incomplete: grid, mapping, About, covariate, Analysis focus, plot editor and manuscript still need light/dark/default/large-font captures. The light capture lacks window-manager chrome and must not be treated as full native-window proof.

Notes deferred: storage supports notes, but the workspace editing service has no note target/undo command. A direct row mutation in a context-menu callback would bypass the existing transaction and history model. No unsafe edit shortcut added.

Presentation: the report re-rounding now preserves the existing R formatter’s nonzero value when rounding would produce zero. Amino two-decimal Giamarellou lower limit changes 0.00 -> 0.004; fitted values do not change. No R golden text or numerical references updated. Python manuscript/report presentation changes are outside the R golden reference files; CI must confirm the unchanged R authority/golden gates.

Final local qualification: python scripts/verify.py pre-push passed; full transcript in proof/pre-push.log. Final source E2E also passed in artifacts/verification/rcms/20261105T012714Z-c4b3f98f-amino.
