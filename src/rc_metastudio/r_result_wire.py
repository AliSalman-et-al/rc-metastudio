"""R result vectors transported as values and display metadata."""

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
import math


class ResultVector:
    def __init__(self, values: list[object], kind: str, attributes: dict[str, object]):
        self.values = values
        self.kind = kind
        self.attributes = attributes

    @property
    def names(self):
        return self.attributes.get("names")

    def __iter__(self) -> Iterator[object]:
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)

    def __getitem__(self, index: int):
        return self.values[index]

    def named_fields(self) -> dict[str, object]:
        names = require_result_vector(self.names)
        if names.kind != "character" or len(names) != len(self.values):
            raise ValueError("worker result field names do not match its values")
        fields: dict[str, object] = {}
        for name, value in zip(names, self.values, strict=True):
            if not isinstance(name, str) or not name or name in fields:
                raise ValueError("worker result field names must be nonempty and unique")
            fields[name] = value
        return fields


def require_result_vector(value: object) -> ResultVector:
    if not isinstance(value, ResultVector):
        raise ValueError("expected a worker result vector")
    return value


def result_vector(value: dict[str, object]) -> object:
    kind = value.get("$vector")
    if kind is None:
        return value
    fields = value.get("values")
    attrs = value.get("attributes")
    if attrs == []:
        attrs = {}
    if not isinstance(kind, str) or not isinstance(fields, list) or not isinstance(attrs, dict):
        raise ValueError("invalid result vector")
    if kind == "double":
        fields = [float(item) if isinstance(item, (int, float)) else item for item in fields]
    return ResultVector(fields, kind, attrs)


@dataclass(frozen=True, slots=True)
class RegressionCoefficient:
    term: str
    estimate: float | None
    lower: float | None
    upper: float | None
    se: float | None
    statistic: float | None
    p: float | None


@dataclass(frozen=True, slots=True)
class RegressionOutput:
    scale: str
    level: float
    inference: str
    coefficients: tuple[RegressionCoefficient, ...]
    residual: tuple[tuple[str, float | None], ...]


def _result_text(field: object) -> str:
    value, = require_result_vector(field)
    if not isinstance(value, str):
        raise ValueError("expected a worker result string")
    return value


def _result_number(field: object) -> float | None:
    if field is None:
        return None
    value, = require_result_vector(field)
    if value is None:
        return None
    if not isinstance(value, (float, int)) or isinstance(value, bool):
        raise ValueError("expected a worker result number")
    return float(value)


def _regression_coefficient(field: object) -> RegressionCoefficient:
    values = require_result_vector(field).named_fields()
    return RegressionCoefficient(
        _result_text(values["term"]), _result_number(values["estimate"]),
        _result_number(values["lower"]), _result_number(values["upper"]),
        _result_number(values["se"]), _result_number(values["statistic"]),
        _result_number(values["p"]),
    )


def regression_output(value: object) -> RegressionOutput | None:
    if value is None:
        return None
    fields = require_result_vector(value).named_fields()
    level = _result_number(fields["level"])
    if level is None:
        raise ValueError("missing confidence level in worker regression output")
    coefficients = require_result_vector(fields["coefficients"])
    residual = require_result_vector(fields["residual"])
    residual_fields = residual.named_fields() if residual else {}
    return RegressionOutput(
        _result_text(fields["scale"]), level, _result_text(fields["inference"]),
        tuple(_regression_coefficient(field) for field in coefficients),
        tuple((key, _result_number(residual_fields[key])) for key in ("q", "p", "tau2") if key in residual_fields),
    )


def _r_is_null(value):
    return value is None


def named_r_list_to_dict(named_r_list):
    keys = named_r_list.names
    if _r_is_null(keys):
        raise ValueError("R list has no names")
    return dict(zip(keys, r_iterable_to_list(named_r_list)))


def r_object_to_python(data):
    if _r_is_null(data):
        return None

    if isinstance(data, Mapping):
        return data
    if _r_dims(data):
        return [_r_na_to_none(value) for value in list(data)]
    if _has_r_names(data):
        return {
            key: r_object_to_python(value)
            for key, value in named_r_list_to_dict(data).items()
        }
    if _is_r_iterable(data):
        return [r_object_to_python(value) for value in r_iterable_to_list(data)]
    return _r_na_to_none(data)


def r_iterable_to_list(r_iterable):
    return [
        _r_singleton_to_scalar(value)
        if _is_r_iterable(value) and len(value) == 1
        else value
        for value in r_iterable
    ]


def _r_singleton_to_scalar(singleton):
    if len(singleton) != 1:
        raise ValueError("expected an R sequence with one element")
    return _r_na_to_none(singleton[0])


def _r_na_to_none(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _is_r_iterable(value, exclude_strings=True):
    if exclude_strings and isinstance(value, str):
        return False
    try:
        iter(value)
    except TypeError:
        return False
    return True


def _has_r_names(value):
    return isinstance(value, ResultVector) and not _r_dims(value) and value.names is not None


def _r_mapping_or_empty(r_object):
    """Convert named R metadata to a mapping, including empty vectors."""
    if _r_is_null(r_object):
        return {}
    try:
        if len(r_object) == 0:
            return {}
    except TypeError:
        pass
    converted = r_object_to_python(r_object)
    return converted if isinstance(converted, Mapping) else {}


def _is_r_string_vector(value):
    return isinstance(value, ResultVector) and value.kind == "character"


def _r_attribute(value, name):
    return value.attributes.get(name) if isinstance(value, ResultVector) else None


def _r_dims(value):
    dimensions = _r_attribute(value, "dim")
    return [int(dimension) for dimension in dimensions] if dimensions is not None else []


def _r_dimnames(value):
    dimensions = _r_attribute(value, "dimnames")
    if dimensions is None:
        return []
    return [None if names is None else [str(name) for name in names] for names in dimensions]


def _r_names_or_none(r_object):
    if _r_dims(r_object):
        return None
    names = getattr(r_object, "names", None)
    if names is None or _r_is_null(names):
        return None
    names = [str(name) for name in list(names)]
    if not names or any(name == "" for name in names):
        return None
    return names
