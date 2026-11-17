"""Command entry point for RC MetaStudio."""

from __future__ import annotations

import os
from pathlib import Path


def main() -> int:
    from rc_metastudio.qt6_ui import prepare_generated_ui_imports

    prepare_generated_ui_imports()
    from rc_metastudio import app_error_handler, launch, qt6_resources

    qt6_resources.ensure_application_resources()
    app_error_handler.install_global_exception_handler()
    arguments = launch.resolve_startup_argv()
    pid_path = launch.startup_argument_value(arguments, "--automation-pid-file") or os.environ.get(
        "RCMS_AUTOMATION_PID_FILE"
    )
    if pid_path:
        Path(pid_path).write_text(f"{os.getpid()}\n", encoding="utf-8")

    command = arguments[1] if len(arguments) > 1 else ""
    if command.startswith("--automation-") and command != "--automation-startup-project-smoke":
        from rc_metastudio import automation

        return automation.dispatch(arguments)
    return launch.start(arguments) or 0


if __name__ == "__main__":
    raise SystemExit(main())
