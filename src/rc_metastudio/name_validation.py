from rc_metastudio import input_text


ENTITY_LABELS = {
    "study": "Study",
    "group": "Arm",
    "outcome": "Outcome",
    "covariate": "Covariate",
}


def normalize_name(value):
    return input_text.to_native_text(value).strip()


def required_message(entity):
    return "%s names cannot be empty." % ENTITY_LABELS[entity]


def duplicate_message(entity, name):
    article = "An" if entity[0].lower() in "aeiou" else "A"
    return "%s %s named \"%s\" already exists. Choose another name." % (
        article,
        entity,
        name,
    )


def validate_required_name(entity, value):
    name = normalize_name(value)
    if name == "":
        raise ValueError(required_message(entity))
    return name


def validate_unique_name(entity, value, existing_names):
    name = validate_required_name(entity, value)
    if name in existing_names:
        raise ValueError(duplicate_message(entity, name))
    return name


def study_identity(name: object, year: int | None) -> tuple[str, int]:
    return normalize_name(name), year or 0


def study_conflict(identity: tuple[str, int], row_number: int) -> str:
    name, year = identity
    display = f"'{name}' ({year})" if year else f"'{name}' with no year"
    return f"Study {display} already exists in row {row_number}."
