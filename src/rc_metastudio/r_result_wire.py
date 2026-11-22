"""R result vectors transported as values and display metadata."""

from collections.abc import Iterator


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

    def rx2(self, name: str):
        return next((value for key, value in zip(self.names, self.values) if key == name), None)


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
