"""Reported ratio inputs, kept independently of calculated study effects."""

from dataclasses import dataclass, replace
import math
from typing import Literal

RATIO_FIELDS = ("estimate", "lower", "upper", "se", "scale", "confidence", "source", "unit")
RATIO_HEADERS = ("Reported estimate", "Reported lower", "Reported upper", "SE of log effect", "Input scale (ratio/log)", "Source CI (%)", "Effect source (raw/reported)", "Person-time unit")


@dataclass
class RatioInput:
    estimate: float | None = None
    lower: float | None = None
    upper: float | None = None
    se: float | None = None
    scale: Literal["ratio", "log"] = "ratio"
    confidence: float = 95.0
    source: Literal["", "raw", "reported"] = ""
    unit: str = "person-years"

    def validate(self) -> None:
        if not math.isfinite(self.confidence) or not 0 < self.confidence < 100:
            raise ValueError("Source confidence must be between 0 and 100 percent.")
        if self.scale not in ("ratio", "log") or self.source not in ("", "raw", "reported"):
            raise ValueError("Input scale must be ratio or log; source must be raw or reported.")
        self._validate_reported_values()
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise ValueError("Declare a shared person-time unit for both groups.")

    def _validate_reported_values(self) -> None:
        for field in ("estimate", "lower", "upper", "se"):
            value = getattr(self, field)
            if value is not None and not math.isfinite(value):
                raise ValueError("Reported values must be finite.")
            if value is not None and (field == "se" or self.scale == "ratio") and value <= 0:
                raise ValueError("Ratios, ratio bounds, and standard errors must be positive.")
        values = [value for value in (self.lower, self.estimate, self.upper) if value is not None]
        if any(a >= b for a, b in zip(values, values[1:])):
            raise ValueError("The interval must satisfy lower < estimate < upper.")

    def selected_source(self, raw: list[object], *, metric: str) -> str:
        if metric == "HR":
            return "reported"
        has_raw = any(value not in (None, "") for value in raw)
        has_reported = any(value is not None for value in (self.estimate, self.lower, self.upper, self.se))
        if self.source:
            return self.source
        if has_raw and has_reported:
            raise ValueError("Select raw or reported as the effect source when both are supplied.")
        return "raw" if has_raw else "reported"

    def reversed(self) -> "RatioInput":
        def invert(value: float | None) -> float | None:
            if value is None:
                return None
            return -value if self.scale == "log" else 1 / value
        return replace(self, estimate=invert(self.estimate), lower=invert(self.upper), upper=invert(self.lower))

    def ready(self, raw: list[object], *, metric: str) -> bool:
        try:
            self.validate()
            if self.selected_source(raw, metric=metric) == "raw":
                return len(raw) == 4 and all(value not in (None, "") for value in raw)
            return self.estimate is not None and (
                (self.scale == "log" and self.se is not None)
                or (self.lower is not None and self.upper is not None)
            )
        except ValueError:
            return False
