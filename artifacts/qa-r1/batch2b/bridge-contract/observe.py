"""Print measurements from the real bridge driver without changing its assertions."""
import os
import subprocess
import sys
import tempfile

from tests.r_stack.test_inprocess_rpy2_backend import _DRIVER

resize_assert = 'assert shrunken_width < initial_plot_width'
resize_probe = '''print("PLOT_RESIZE", {"window_initial": initial_window_width, "window_shrunken": result_window.width(), "plot_initial": initial_plot_width, "plot_shrunken": shrunken_width, "viewport": result_window.graphics_view.viewport().width(), "item_scale": plot_item.scale(), "font_size": plot_item.renderer().property("minimum_text_size")}, flush=True)
'''
driver = _DRIVER.replace(resize_assert, resize_probe + resize_assert)
restore_size = 'result_window.resize(initial_window_width, result_window.height())'
auto_probe = '''print("AUTOMATIC_FLOOR", {"label_pt": label_pt, "scroll_max": result_window.graphics_view.horizontalScrollBar().maximum(), "viewport": viewport.width()}, flush=True)
'''
if 'label_pt = ' in driver:
    driver = driver.replace(restore_size, auto_probe + restore_size)
with tempfile.TemporaryDirectory() as directory:
    env = dict(os.environ, RCMS_R_TEST_SETTINGS_DIR=directory, RCMS_REQUIRE_IN_PROCESS_RPY2='1')
    result = subprocess.run([sys.executable, '-c', driver], env=env, text=True, capture_output=True)
    print(result.stdout)
    print(result.stderr)
    sys.exit(result.returncode)
