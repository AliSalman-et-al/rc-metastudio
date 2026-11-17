"""Load saved R data so desktop checks can compare values with public R APIs."""

from pathlib import Path

from rc_metastudio import r_bridge


def load_serialized_object(path: str | Path) -> None:
    r_bridge.execute_r_function("load", str(path))


def load_saved_analysis(prefix: str, *, include_plot_data: bool = False) -> None:
    for suffix in ("data", "params", "res"):
        load_serialized_object(f"{prefix}.{suffix}")
    plot_data = Path(f"{prefix}.plotdata")
    if include_plot_data and plot_data.is_file():
        load_serialized_object(plot_data)
