"""Run the real desktop driver with an explicit app font; keep helper evidence."""
import sys
from scripts import verify_rcms
point_size = int(sys.argv.pop())
original_command = verify_rcms._desktop_command

def desktop_command(scenario, work):
    command = original_command(scenario, work)
    driver = str(verify_rcms.ROOT / 'tests/e2e/desktop_driver.py')
    index = command.index(driver)
    bootstrap = (
        'import sys,runpy; from PyQt6.QtWidgets import QApplication; '
        'app=QApplication([]); font=app.font(); '
        f'font.setPointSize({point_size}); app.setFont(font); '
        f'sys.argv[0]={driver!r}; runpy.run_path({driver!r},run_name="__main__")'
    )
    return command[:index] + ['-c', bootstrap] + command[index+1:]

verify_rcms._desktop_command = desktop_command
raise SystemExit(verify_rcms.main())
