"""Project the workspace fields into CSV and workbook import order."""

from collections.abc import Sequence
from dataclasses import dataclass

from rc_metastudio.analysis.catalog import LEGACY_MEAN_METRIC_NAMES
from rc_metastudio.workspace.columns import STUDY_COLUMN, YEAR_COLUMN, SheetColumns, sheet_columns

IDENTITY_COLUMNS = (0, 1)
YEAR_IMPORT_COLUMN = YEAR_COLUMN - STUDY_COLUMN


@dataclass(frozen=True, slots=True)
class ImportFieldPlan:
    columns: SheetColumns
    required_headers: tuple[str, ...]
    header_aliases: dict[str, str]
    optional_headers: dict[str, str]
    sections: tuple[int, ...]
    raw_columns: tuple[int, ...]
    count_columns: frozenset[int]
    positional_width: int | None

    @classmethod
    def for_sheet(
        cls, data_type: int, subtype: str | None, arms: Sequence[str], metric: str | None,
        *, single_arm: bool,
    ) -> "ImportFieldPlan":
        columns = sheet_columns(data_type, subtype)
        optional = {
            section: (field.label, field.import_default)
            for section, field in zip(columns.effect_sections, columns.effects, strict=True)
            if field.label is not None and field.import_default is not None
        }
        required = tuple(section for section in range(STUDY_COLUMN, columns.first_covariate) if section not in optional)
        headers = tuple(columns.label(section, arms, metric) for section in required)
        legacy = tuple(columns.label(section, ("Tx A", "Tx B"), metric, legacy=True) for section in required)
        physical_raw = tuple(zip(columns.raw_sections, columns.raw, strict=True))
        return cls(
            columns, headers, _aliases(headers, legacy), dict(optional.values()),
            (*required, *optional),
            tuple(required.index(section) for section, raw in physical_raw if not single_arm or raw.arm_index != 1),
            frozenset(required.index(section) for section, raw in physical_raw if raw.field.count),
            columns.first_effect - STUDY_COLUMN if physical_raw else None,
        )

    @property
    def effect_columns(self) -> range:
        start = self.columns.first_effect - STUDY_COLUMN
        return range(start, len(self.required_headers))


def _aliases(headers: tuple[str, ...], legacy: tuple[str, ...]) -> dict[str, str]:
    aliases = {header.casefold(): header for header in headers}
    aliases["study"] = headers[0]
    for old, current in zip(legacy, headers, strict=True):
        old = old.casefold()
        aliases[old] = current
        if old == "mean":
            aliases.update({name.casefold(): current for name in LEGACY_MEAN_METRIC_NAMES})
        words = old.replace("#evts", "events").replace("#total", "total")
        aliases[words] = current
        for value in (old, words):
            aliases[value.replace("tx a", "txa").replace("tx b", "txb")] = current
            if value.startswith("tx a "):
                aliases.setdefault("tx " + value[5:], current)
    return aliases
