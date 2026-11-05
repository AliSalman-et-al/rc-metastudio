# Startup copy follow-up to PR #566

During startup the primary project status is now `Starting… · Untitled dataset`; the temporary status message is exactly `Starting R…`. Once real R is usable, the primary status becomes `Ready to create or open a dataset · Untitled dataset`. Startup failure sets both statuses to `R failed to start` rather than leaving the primary status starting or ready.

The existing E2E startup assertions check the exact concise temporary message and primary status before the real R timer runs, and the Ready primary status after R is usable. Disabled controls and the wait cursor assertions remain.

Environment: `source /home/ali/.t3/qa-env/ENV.sh && export PYTHONPATH=$PWD/src:$PWD`.
Strict win32 typing command/transcript: typing.log. Targeted real Qt/R E2E: `python scripts/verify_rcms.py doctor`; e2e-manifest/runtime/stdout retained here. The doctor executes the common desktop-driver startup assertions with real R.

Real-display captures: `RCMS_QA_APP_SRC=$PWD /home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session b2b-copy start --dark` (then `shot dark-start.png`, `shot dark-ready.png`, `stop`); repeated with `--large-font` for light-large-start/ready.png. Screenshots were captured while R actually initialized, without a mocked or delayed R loader. Session stopped after each capture. Before images are ../after-dark-start.png and ../after-light-large-start.png from the original implementation; this directory supersedes their startup copy.

Required pre-push command: `python scripts/verify.py pre-push`, transcript pre-push.log. Statistics and excluded surfaces remain unchanged; no broad analysis rerun is claimed for this copy-only follow-up. The original native analysis proof remains in the parent directory.
