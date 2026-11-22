"""Load saved R data so desktop checks can compare values with public R APIs."""

from tests.e2e import r_oracle

from pathlib import Path



def load_serialized_object(path: str | Path) -> None:
    r_oracle.load(path)


def load_saved_analysis(prefix: str, *, include_plot_data: bool = False) -> None:
    for suffix in ("data", "params", "res"):
        load_serialized_object(f"{prefix}.{suffix}")
    plot_data = Path(f"{prefix}.plotdata")
    if include_plot_data and plot_data.is_file():
        load_serialized_object(plot_data)
