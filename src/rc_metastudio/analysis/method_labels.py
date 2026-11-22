import re


_KNOWN_METHOD_LABELS = {
    "binary.fixed.inv.var": "Fixed-effect inverse-variance",
    "binary.fixed.mh": "Fixed-effect Mantel–Haenszel",
    "binary.fixed.peto": "Fixed-effect Peto",
    "binary.random": "Random-effects",
    "time_to_event.fixed": "Fixed-effect inverse-variance",
    "time_to_event.random": "Random-effects",
    "continuous.fixed": "Fixed-effect inverse-variance",
    "continuous.random": "Random-effects",
    "diagnostic.fixed.inv.var": "Fixed-effect inverse-variance",
    "diagnostic.fixed.mh": "Fixed-effect Mantel–Haenszel",
    "diagnostic.fixed.peto": "Fixed-effect Peto",
    "diagnostic.random": "Random-effects",
    "diagnostic.reitsma": "Reitsma bivariate model",
    "meta.regression": "Meta-regression",
}

_RAW_METHOD_KEY_RE = re.compile(r"^[a-z]+(?:\.[a-z0-9]+)+$")
_TOKEN_LABELS = {
    "fixed": "fixed-effect",
    "random": "random-effects",
    "inv": "inverse",
    "var": "variance",
    "mh": "Mantel–Haenszel",
    "peto": "Peto",
    "ml": "maximum likelihood (ML)",
}

_KNOWN_PARAMETER_VALUE_LABELS = {
    # Keep estimator choices compact in constrained dialogs.  The raw codes
    # remain the backend values and are standard statistical abbreviations.
    ("estimator", "REML"): "REML",
    ("estimator", "ML"): "ML",
    ("rm.method", "HE"): "Hedges–Olkin",
    ("rm.method", "DL"): "DerSimonian–Laird",
    ("rm.method", "SJ"): "Sidik–Jonkman",
    ("rm.method", "ML"): "Maximum likelihood (ML)",
    ("rm.method", "REML"): "Restricted maximum likelihood (REML)",
    ("rm.method", "EB"): "Empirical Bayes",
    ("rm.method", "HS"): "Hunter–Schmidt",
    ("rm.method", "HSk"): "Hunter–Schmidt with small-sample correction",
    ("rm.method", "PM"): "Paule–Mandel",
    ("rm.method", "PMM"): "Median-unbiased Paule–Mandel",
    ("inference.method", "z"): "Normal approximation",
    ("inference.method", "t"): "Student's t-distribution",
    ("inference.method", "knha"): "Knapp–Hartung",
    ("inference.method", "adhoc"): "Modified Knapp–Hartung",
    ("to", "only0"): "Studies with any zero cell",
    ("to", "all"): "All studies",
    ("to", "if0all"): "All studies if any zero exists",
    ("to", "none"): "None",
    ("correction.policy", "Studies with any zero cell"): "Studies with any zero cell",
    ("correction.policy", "All studies if any zero exists"): "All studies if any zero exists",
    ("correction.policy", "None"): "None",
}

_KNOWN_PARAMETER_LABELS = {
    "rm.method": "τ² estimator",
    "estimator": "Estimator",
    "inference.method": "Inference method",
    "to": "Apply correction to",
    "correction.policy": "Apply correction to",
    "conf.level": "Confidence level",
    "digits": "Decimal places",
    "adjust": "Continuity correction",
    "drop00": "Exclude studies with no events in either arm",
}

_PARAMETER_DESCRIPTIONS = {
    'rm.method': 'Between-study variance (heterogeneity) estimator.',
    'estimator': 'REML: restricted maximum likelihood; ML: maximum likelihood.',
    'adjust': 'Value added to each cell of a 2×2 table that needs correction.',
    'conf.level': 'Confidence level for intervals.',
    'digits': 'Decimal places for estimates and intervals. P values show at least 3.',
    'inference.method': 'Method for tests and confidence intervals.',
    'drop00': 'Exclude studies with no events in either arm.',
}

_DIAGNOSTIC_METRIC_GROUP_LABELS = {
    "sens_spec": "Sensitivity and specificity",
    "lr_dor": "Likelihood ratios and diagnostic odds ratio",
}


def method_display_label(method_key_or_label):
    text = str(method_key_or_label)
    if text in _KNOWN_METHOD_LABELS:
        return _KNOWN_METHOD_LABELS[text]
    if not _RAW_METHOD_KEY_RE.match(text):
        return text
    label = " ".join(_TOKEN_LABELS.get(token, token) for token in text.split("."))
    return label[:1].upper() + label[1:]


def method_labels_by_id(methods_by_label: dict[str, str]) -> dict[str, str]:
    return {
        method: method_display_label(method) if method in _KNOWN_METHOD_LABELS else label
        for label, method in methods_by_label.items()
    }


def parameter_value_display_label(param_name, value, param_metadata=None):
    text = str(value)
    known = _KNOWN_PARAMETER_VALUE_LABELS.get((str(param_name), text))
    if known is not None:
        return known
    if param_metadata is not None:
        value_names = param_metadata.get("%s.names" % param_name)
        if value_names is not None and text in value_names:
            return str(value_names[text])
    return _KNOWN_PARAMETER_VALUE_LABELS.get((str(param_name), text), text)


def parameter_display_label(param_name, param_metadata=None):
    text = str(param_name)
    if text in _KNOWN_PARAMETER_LABELS:
        return _KNOWN_PARAMETER_LABELS[text]
    if param_metadata is not None:
        pretty_name = param_metadata.get("pretty.name")
        if pretty_name:
            pretty_name = str(pretty_name)
            if pretty_name != text:
                return pretty_name
    return _label_from_key(text)


def parameter_description(param_name, param_metadata=None):
    if str(param_name) in _PARAMETER_DESCRIPTIONS:
        return _PARAMETER_DESCRIPTIONS[str(param_name)]
    if param_metadata is not None:
        description = param_metadata.get("description")
        if description and str(description) != "None provided":
            return str(description)
    return "No description provided."


def diagnostic_metric_group_display_label(group_key):
    return _DIAGNOSTIC_METRIC_GROUP_LABELS.get(str(group_key), str(group_key))


def _label_from_key(key):
    label = " ".join(_TOKEN_LABELS.get(token.lower(), token) for token in re.split(r"[._]", str(key)))
    return label[:1].upper() + label[1:]
