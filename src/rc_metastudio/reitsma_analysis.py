# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Frozen count inputs and the single joint Reitsma execution path."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
import math
import re
from types import MappingProxyType
from typing import Literal, Protocol, TypeAlias, TypeGuard, cast
from uuid import uuid4

from rc_metastudio.analysis_results import AnalysisResult, ResultSection, parse_analysis_result


REITSMA_METHOD = "diagnostic.reitsma"
JOINT_MEASURE = "Sensitivity and specificity"
JOINT_MEASURES = ("Sensitivity", "Specificity")
CORRECTION_POLICIES = frozenset(
    {
        "Studies with any zero cell",
        "All studies if any zero exists",
        "None",
    }
)

_SNAPSHOT_FIELDS = {
    "version",
    "data_type",
    "method",
    "measures",
    "input_source",
    "outcome",
    "time_point",
    "groups",
    "studies",
}
_STUDY_FIELDS = {"id", "name", "tp", "fn", "fp", "tn"}
_REQUEST_FIELDS = {"version", "data_type", "workflow", "method", "metric", "params"}
_REQUEST_PARAMETER_FIELDS = {
    "estimator",
    "conf.level",
    "adjust",
    "correction.policy",
    "digits",
    "create.plot",
}
_R_SYMBOL = re.compile(r"^[A-Za-z][A-Za-z0-9_.]*$")


def _is_string_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping) and all(isinstance(key, str) for key in value)


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Reitsma {label} must be non-empty text")
    return value


def _required_int(value: object, label: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"Reitsma {label} must be an integer of at least {minimum}")
    return value


def _optional_count(value: object, label: str) -> int | None:
    if value is None:
        return None
    return _required_int(value, label)


def _required_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Reitsma {label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Reitsma {label} must be finite")
    return number


def _validate_snapshot_version(version: int) -> None:
    if type(version) is not int or version != 1:
        raise ValueError(f"unsupported Reitsma input snapshot version: {version}")


def _validate_snapshot_groups(groups: tuple[str]) -> None:
    if (
        not isinstance(groups, tuple)
        or len(groups) != 1
        or any(not isinstance(group, str) or not group.strip() for group in groups)
    ):
        raise ValueError("Reitsma input requires one selected study group")


def _validate_snapshot_studies(studies: tuple[ReitsmaStudyInput, ...]) -> None:
    if not isinstance(studies, tuple) or any(
        not isinstance(study, ReitsmaStudyInput) for study in studies
    ):
        raise ValueError("Reitsma studies must be an immutable tuple")
    if len({study.id for study in studies}) != len(studies):
        raise ValueError("Reitsma input contains duplicate study identities")


def _snapshot_mapping(value: object) -> Mapping[str, object]:
    if not _is_string_mapping(value) or set(value) != _SNAPSHOT_FIELDS:
        raise ValueError("Reitsma input snapshot has unknown or missing fields")
    return value


def _validate_snapshot_mapping_identity(value: Mapping[str, object]) -> None:
    if value["version"] != 1 or type(value["version"]) is not int:
        raise ValueError("Reitsma snapshot must identify count-based joint analysis")
    if value["data_type"] != "diagnostic" or value["method"] != REITSMA_METHOD:
        raise ValueError("Reitsma snapshot must identify count-based joint analysis")
    if value["measures"] != list(JOINT_MEASURES) or value["input_source"] != "counts":
        raise ValueError("Reitsma snapshot must identify count-based joint analysis")


def _snapshot_groups_from_mapping(value: object) -> tuple[str]:
    if (
        not isinstance(value, (tuple, list))
        or len(value) != 1
        or any(not isinstance(group, str) for group in value)
    ):
        raise ValueError("Reitsma input snapshot groups are invalid")
    return cast(tuple[str], tuple(value))


def _snapshot_studies_from_mapping(value: object) -> tuple[ReitsmaStudyInput, ...]:
    if not isinstance(value, (tuple, list)):
        raise ValueError("Reitsma input snapshot studies must be a list")
    return tuple(_study_from_mapping(study) for study in value)


@dataclass(frozen=True, slots=True)
class ReitsmaStudyInput:
    """One included study's raw 2x2 diagnostic counts."""

    id: int
    name: str
    tp: int | None
    fn: int | None
    fp: int | None
    tn: int | None

    def __post_init__(self) -> None:
        _required_int(self.id, "study id")
        _required_text(self.name, "study name")
        for field in ("tp", "fn", "fp", "tn"):
            value = getattr(self, field)
            if value is not None:
                _required_int(value, f"{field.upper()} count")

    def to_mapping(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "tp": self.tp,
            "fn": self.fn,
            "fp": self.fp,
            "tn": self.tn,
        }


@dataclass(frozen=True, slots=True)
class ReitsmaInputSnapshot:
    """Joint sensitivity/specificity input, independent of any one metric."""

    version: int
    outcome: str
    time_point: str
    groups: tuple[str]
    studies: tuple[ReitsmaStudyInput, ...]

    def __post_init__(self) -> None:
        _validate_snapshot_version(self.version)
        _required_text(self.outcome, "outcome")
        _required_text(self.time_point, "time point")
        _validate_snapshot_groups(self.groups)
        _validate_snapshot_studies(self.studies)

    @property
    def method(self) -> str:
        return REITSMA_METHOD

    @property
    def measures(self) -> tuple[str, str]:
        return JOINT_MEASURES

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "data_type": "diagnostic",
            "method": REITSMA_METHOD,
            "measures": list(JOINT_MEASURES),
            "input_source": "counts",
            "outcome": self.outcome,
            "time_point": self.time_point,
            "groups": list(self.groups),
            "studies": [study.to_mapping() for study in self.studies],
        }

    @classmethod
    def from_mapping(cls, value: object) -> ReitsmaInputSnapshot:
        mapping = _snapshot_mapping(value)
        _validate_snapshot_mapping_identity(mapping)
        return cls(
            version=1,
            outcome=_required_text(mapping["outcome"], "outcome"),
            time_point=_required_text(mapping["time_point"], "time point"),
            groups=_snapshot_groups_from_mapping(mapping["groups"]),
            studies=_snapshot_studies_from_mapping(mapping["studies"]),
        )


def _study_from_mapping(value: object) -> ReitsmaStudyInput:
    if not _is_string_mapping(value) or set(value) != _STUDY_FIELDS:
        raise ValueError("Reitsma study has unknown or missing fields")
    return ReitsmaStudyInput(
        id=_required_int(value["id"], "study id"),
        name=_required_text(value["name"], "study name"),
        tp=_optional_count(value["tp"], "TP count"),
        fn=_optional_count(value["fn"], "FN count"),
        fp=_optional_count(value["fp"], "FP count"),
        tn=_optional_count(value["tn"], "TN count"),
    )


class ReitsmaModel(Protocol):
    current_outcome_name: str | None

    def get_current_follow_up_name(self) -> str | None: ...

    def get_current_groups(self) -> Sequence[object]: ...

    def get_studies(self, only_if_included: bool = True) -> Sequence[object]: ...

    def get_current_raw_data(
        self, only_if_included: bool = True, only_these_studies: Sequence[int] | None = None
    ) -> Sequence[Sequence[object]]: ...


def freeze_reitsma_input(model: ReitsmaModel) -> ReitsmaInputSnapshot:
    """Copy the included rows and their current diagnostic context."""
    outcome, time_point, groups = _selected_reitsma_context(model)
    included = tuple(model.get_studies(only_if_included=True))
    study_ids = [
        _required_int(_study_attr(study, "id"), "study id") for study in included
    ]
    raw_rows = model.get_current_raw_data(
        only_if_included=True,
        only_these_studies=study_ids,
    )
    if len(raw_rows) != len(included):
        raise ValueError("Reitsma count rows do not match the included studies")
    studies = tuple(
        _study_input_from_raw_row(study, study_id, row)
        for study, study_id, row in zip(included, study_ids, raw_rows, strict=True)
    )
    return ReitsmaInputSnapshot(
        version=1,
        outcome=outcome,
        time_point=time_point,
        groups=groups,
        studies=studies,
    )


def _selected_reitsma_context(
    model: ReitsmaModel,
) -> tuple[str, str, tuple[str]]:
    return (
        _selected_outcome(model),
        _selected_time_point(model),
        _selected_group(model),
    )


def _selected_outcome(model: ReitsmaModel) -> str:
    outcome = getattr(model, "current_outcome_name", None)
    if not isinstance(outcome, str) or not outcome.strip():
        raise ValueError("select an outcome before running a Reitsma analysis")
    return outcome


def _selected_time_point(model: ReitsmaModel) -> str:
    time_point = model.get_current_follow_up_name()
    if not isinstance(time_point, str) or not time_point.strip():
        raise ValueError("select a time point before running a Reitsma analysis")
    return time_point


def _selected_group(model: ReitsmaModel) -> tuple[str]:
    groups = model.get_current_groups()
    if len(groups) != 1 or any(not isinstance(group, str) or not group.strip() for group in groups):
        raise ValueError("select one study group before running a Reitsma analysis")
    return cast(tuple[str], tuple(groups))


def _study_input_from_raw_row(
    study: object, study_id: int, row: Sequence[object]
) -> ReitsmaStudyInput:
    values = list(row)
    values.extend([None] * max(0, 4 - len(values)))
    if len(values) != 4:
        raise ValueError("Reitsma study data must contain TP, FN, FP, and TN")
    study_name = _required_text(_study_attr(study, "name"), "study name")
    return ReitsmaStudyInput(
        id=study_id,
        name=study_name,
        tp=_parse_count(values[0], "TP", study_name),
        fn=_parse_count(values[1], "FN", study_name),
        fp=_parse_count(values[2], "FP", study_name),
        tn=_parse_count(values[3], "TN", study_name),
    )


def _study_attr(study: object, attribute: str) -> object:
    try:
        return getattr(study, attribute)
    except AttributeError as error:
        raise ValueError(f"Reitsma study is missing {attribute}") from error


def _parse_count(value: object, label: str, study: str) -> int | None:
    if value is None or value == "":
        return None
    number = _count_number(value, label, study)
    if not math.isfinite(number) or number < 0 or number % 1 != 0:
        raise ValueError(f"{study}: {label} count must be a non-negative whole number")
    return int(number)


def _count_number(value: object, label: str, study: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{study}: {label} count must be a whole number")
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(f"{study}: {label} count must be a whole number") from error


@dataclass(frozen=True, slots=True)
class ReitsmaRequest:
    """Effective parameters for the pinned joint count model."""

    version: int = 1
    estimator: Literal["REML", "ML"] = "REML"
    confidence_level: float = 95.0
    correction_factor: float = 0.5
    correction_policy: str = "All studies if any zero exists"
    digits: int = 2
    create_plot: bool = True

    def __post_init__(self) -> None:
        _validate_request_version(self.version)
        _validate_estimator(self.estimator)
        _validate_confidence_level(self.confidence_level)
        _validate_correction_factor(self.correction_factor)
        _validate_correction_policy(self.correction_policy)
        _validate_display_options(self.digits, self.create_plot)

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "data_type": "diagnostic",
            "workflow": "standard",
            "method": REITSMA_METHOD,
            "metric": JOINT_MEASURE,
            "params": {
                "estimator": self.estimator,
                "conf.level": self.confidence_level,
                "adjust": self.correction_factor,
                "correction.policy": self.correction_policy,
                "digits": self.digits,
                "create.plot": self.create_plot,
            },
        }

    @classmethod
    def from_mapping(cls, value: object) -> ReitsmaRequest:
        mapping = _request_mapping(value)
        _validate_request_mapping_identity(mapping)
        params = _request_parameters(mapping["params"])
        estimator = _request_estimator(params["estimator"])
        policy = _request_policy(params["correction.policy"])
        create_plot = _request_plot_option(params["create.plot"])
        digits = _required_int(params["digits"], "display digits", minimum=0)
        return cls(
            version=1,
            estimator=estimator,
            confidence_level=_required_number(params["conf.level"], "confidence level"),
            correction_factor=_required_number(params["adjust"], "correction factor"),
            correction_policy=policy,
            digits=digits,
            create_plot=create_plot,
        )


def _validate_request_version(version: int) -> None:
    if type(version) is not int or version != 1:
        raise ValueError("unsupported Reitsma request version")


def _validate_estimator(estimator: object) -> None:
    if not isinstance(estimator, str) or estimator not in {"REML", "ML"}:
        raise ValueError("Reitsma estimator must be REML or ML")


def _validate_confidence_level(value: object) -> None:
    confidence = _required_number(value, "confidence level")
    if not 0 < confidence < 100:
        raise ValueError("Reitsma confidence level must be between 0 and 100")


def _validate_correction_factor(value: object) -> None:
    correction = _required_number(value, "correction factor")
    if correction < 0:
        raise ValueError("Reitsma correction factor must be non-negative")


def _validate_correction_policy(policy: object) -> None:
    if not isinstance(policy, str) or policy not in CORRECTION_POLICIES:
        raise ValueError("Reitsma correction policy is unsupported")


def _validate_display_options(digits: int, create_plot: bool) -> None:
    if type(digits) is not int or not 0 <= digits <= 15:
        raise ValueError("Reitsma display digits must be between 0 and 15")
    if type(create_plot) is not bool:
        raise ValueError("Reitsma create_plot must be boolean")


def _request_mapping(value: object) -> Mapping[str, object]:
    if not _is_string_mapping(value) or set(value) != _REQUEST_FIELDS:
        raise ValueError("Reitsma request has unknown or missing fields")
    return value


def _validate_request_mapping_identity(value: Mapping[str, object]) -> None:
    if type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("request must remain one standard joint Reitsma analysis")
    if value["data_type"] != "diagnostic" or value["workflow"] != "standard":
        raise ValueError("request must remain one standard joint Reitsma analysis")
    if value["method"] != REITSMA_METHOD or value["metric"] != JOINT_MEASURE:
        raise ValueError("request must remain one standard joint Reitsma analysis")


def _request_parameters(value: object) -> Mapping[str, object]:
    if not _is_string_mapping(value) or set(value) != _REQUEST_PARAMETER_FIELDS:
        raise ValueError("request must remain one standard joint Reitsma analysis")
    return value


def _request_estimator(value: object) -> Literal["REML", "ML"]:
    _validate_estimator(value)
    return cast(Literal["REML", "ML"], value)


def _request_policy(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Reitsma correction policy must be text")
    return value


def _request_plot_option(value: object) -> bool:
    if type(value) is not bool:
        raise ValueError("Reitsma create.plot must be boolean")
    return value


class _GlobalEnvironment(Protocol):
    def __getitem__(self, key: str) -> object: ...

    def __setitem__(self, key: str, value: object) -> None: ...


class ReitsmaBridge(Protocol):
    ro: object

    def _r_numeric_vector(self, values: Sequence[object]) -> object: ...

    def _r_character_vector(self, values: Sequence[str]) -> object: ...

    def execute_r_function(self, name: str, *args: object, **kwargs: object) -> object: ...

    def run_versioned_analysis_request(
        self, request: Mapping[str, object], res_name: str, data_name: str
    ) -> AnalysisResult: ...


def create_reitsma_r_data(
    snapshot: ReitsmaInputSnapshot, bridge: ReitsmaBridge
) -> object:
    """Build the RCMetaR DiagnosticData object from counts without deriving effects."""
    studies = snapshot.studies
    return bridge.execute_r_function(
        "rcmetar.create.diagnostic.data",
        TP=bridge._r_numeric_vector([study.tp for study in studies]),
        FN=bridge._r_numeric_vector([study.fn for study in studies]),
        TN=bridge._r_numeric_vector([study.tn for study in studies]),
        FP=bridge._r_numeric_vector([study.fp for study in studies]),
        **{
            "study.names": bridge._r_character_vector(
                [study.name for study in studies]
            )
        },
    )


@dataclass(frozen=True, slots=True)
class ReitsmaStudyEligibilityIssue:
    study_id: int
    study_name: str
    reason: str
    fields: tuple[str, ...] = ()

    def to_mapping(self) -> dict[str, object]:
        return {
            "study_id": self.study_id,
            "study_name": self.study_name,
            "reason": self.reason,
            "fields": list(self.fields),
        }


class ReitsmaEligibilityError(ValueError):
    """RCMetaR rejected the count input at its implementation boundary."""

    def __init__(
        self,
        reason: str,
        study_issues: Sequence[ReitsmaStudyEligibilityIssue] = (),
    ) -> None:
        self.reason = reason
        self.study_issues = tuple(study_issues)
        detail = f"Reitsma bivariate model is not eligible: {reason}"
        if self.study_issues:
            detail += "\n" + "\n".join(
                f"- {issue.study_name}: {issue.reason}"
                for issue in self.study_issues
            )
        super().__init__(detail)


class ReitsmaAnalysisError(RuntimeError):
    """RCMetaR failed to run the explicit joint Reitsma request."""


def _clean_authority_error(error: BaseException) -> str:
    message = str(error).strip()
    if message.startswith("Error: "):
        message = message[7:].strip()
    return message or error.__class__.__name__


def _validate_authority_counts(
    snapshot: ReitsmaInputSnapshot, data: object, bridge: ReitsmaBridge
) -> None:
    missing = _missing_count_issues(snapshot)
    if missing:
        raise ReitsmaEligibilityError(
            "complete TP/FN/FP/TN counts are required for every included study",
            missing,
        )
    validator = bridge.execute_r_function(
        "getFromNamespace", "rcmetar.reitsma.validate.counts", "RCMetaR"
    )
    call = getattr(validator, "__call__", None)
    if not callable(call):
        raise TypeError("RCMetaR Reitsma count validator is not callable")

    try:
        call(data)
    except Exception as error:
        reason = _clean_authority_error(error)
        issues = _missing_count_issues(snapshot)
        if not issues and "positive diseased and non-diseased denominators" in reason:
            issues = _authority_row_issues(snapshot, validator, bridge)
        raise ReitsmaEligibilityError(reason, issues) from error


def _missing_count_issues(
    snapshot: ReitsmaInputSnapshot,
) -> tuple[ReitsmaStudyEligibilityIssue, ...]:
    issues = []
    for study in snapshot.studies:
        missing = tuple(
            label
            for label, value in (
                ("TP", study.tp),
                ("FN", study.fn),
                ("FP", study.fp),
                ("TN", study.tn),
            )
            if value is None
        )
        if missing:
            issues.append(
                ReitsmaStudyEligibilityIssue(
                    study.id,
                    study.name,
                    "missing required count(s): " + ", ".join(missing),
                    missing,
                )
            )
    return tuple(issues)


def _authority_row_issues(
    snapshot: ReitsmaInputSnapshot, validator: object, bridge: ReitsmaBridge
) -> tuple[ReitsmaStudyEligibilityIssue, ...]:
    call = getattr(validator, "__call__", None)
    if not callable(call):
        return ()
    issues: list[ReitsmaStudyEligibilityIssue] = []
    for study in snapshot.studies:
        row_data = create_reitsma_r_data(
            replace(snapshot, studies=(study,)), bridge
        )
        try:
            call(row_data, **{"min.studies": 1})
        except Exception as error:
            issues.append(
                ReitsmaStudyEligibilityIssue(
                    study.id, study.name, _clean_authority_error(error)
                )
            )
    return tuple(issues)


@dataclass(frozen=True, slots=True)
class ReitsmaReportSection:
    key: str
    title: str
    kind: Literal["text", "image"]
    status: Literal["available", "not_available"]
    value: str | None
    reason: str | None = None

    def __post_init__(self) -> None:
        _validate_report_section_identity(self.key, self.title)
        _validate_report_section_kind(self.kind)
        _validate_report_section_status(self.status)
        _validate_report_section_content(self.status, self.value, self.reason)

    def to_mapping(self) -> dict[str, object]:
        return {
            "key": self.key,
            "title": self.title,
            "kind": self.kind,
            "status": self.status,
            "value": self.value,
            "reason": self.reason,
        }


def _validate_report_section_identity(key: str, title: str) -> None:
    if not key or not title:
        raise ValueError("Reitsma report section needs a key and title")


def _validate_report_section_kind(kind: str) -> None:
    if kind not in {"text", "image"}:
        raise ValueError("Reitsma report section kind is invalid")


def _validate_report_section_status(status: str) -> None:
    if status not in {"available", "not_available"}:
        raise ValueError("Reitsma report section status is invalid")


def _validate_report_section_content(
    status: str, value: str | None, reason: str | None
) -> None:
    if status == "available" and (not isinstance(value, str) or not value):
        raise ValueError("available Reitsma report sections require a value")
    if status == "not_available" and (value is not None or not reason):
        raise ValueError("unavailable Reitsma report sections require a reason")


@dataclass(frozen=True, slots=True)
class ReitsmaReport:
    version: int
    method: str
    measures: tuple[str, str]
    sections: tuple[ReitsmaReportSection, ...]

    def __post_init__(self) -> None:
        if self.version != 1 or self.method != REITSMA_METHOD:
            raise ValueError("Reitsma report identity is invalid")
        if self.measures != JOINT_MEASURES:
            raise ValueError("Reitsma report must identify paired sensitivity and specificity")
        keys = [section.key for section in self.sections]
        if len(set(keys)) != len(keys):
            raise ValueError("Reitsma report section keys must be unique")

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "method": self.method,
            "measures": list(self.measures),
            "sections": [section.to_mapping() for section in self.sections],
        }


_REPORT_ORDER = (
    ("Clinical interpretation", "text"),
    ("Summary operating point", "text"),
    ("SROC", "image"),
    ("SROC AUC", "text"),
    ("Marginal prediction", "text"),
    ("Sampling-based summary ratios", "text"),
    ("Between-study heterogeneity", "text"),
    ("Diagnostic I-squared", "text"),
    ("Model information", "text"),
    ("References", "text"),
)


def _ordered_result(result: AnalysisResult) -> AnalysisResult:
    rank = {key: index for index, (key, _kind) in enumerate(_REPORT_ORDER)}
    sections = sorted(
        result.sections,
        key=lambda section: (rank.get(section.source_key, len(rank)), section.order),
    )
    ordered_sections = tuple(
        replace(section, order=index) for index, section in enumerate(sections)
    )
    text_order = {
        key: index
        for index, (key, kind) in enumerate(_REPORT_ORDER)
        if kind == "text"
    }
    image_order = {
        key: index
        for index, (key, kind) in enumerate(_REPORT_ORDER)
        if kind == "image"
    }
    texts = dict(
        sorted(
            result.texts.items(),
            key=lambda item: (text_order.get(item[0], len(text_order)), item[0]),
        )
    )
    images = dict(
        sorted(
            result.images.items(),
            key=lambda item: (image_order.get(item[0], len(image_order)), item[0]),
        )
    )
    return replace(
        result,
        sections=ordered_sections,
        texts=MappingProxyType(texts),
        images=MappingProxyType(images),
    )


def _report_from_result(
    result: AnalysisResult, request: ReitsmaRequest
) -> ReitsmaReport:
    sections: list[ReitsmaReportSection] = []
    for key, kind in _REPORT_ORDER:
        if kind == "text":
            value = result.texts.get(key)
        else:
            value = result.display_images.get(key) or result.images.get(key)
        if isinstance(value, str) and value:
            sections.append(
                ReitsmaReportSection(key, key, kind, "available", value)
            )
        else:
            reason = (
                "SROC rendering was disabled for this request."
                if key == "SROC" and not request.create_plot
                else f"RCMetaR did not return the {key} section."
            )
            sections.append(
                ReitsmaReportSection(
                    key, key, kind, "not_available", None, reason
                )
            )
    return ReitsmaReport(1, REITSMA_METHOD, JOINT_MEASURES, tuple(sections))


@dataclass(frozen=True, slots=True)
class ReitsmaAnalysisRun:
    input_snapshot: ReitsmaInputSnapshot
    request: ReitsmaRequest
    result: AnalysisResult
    report: ReitsmaReport


def _validate_run_inputs(
    input_snapshot: ReitsmaInputSnapshot, request: ReitsmaRequest
) -> None:
    if not isinstance(input_snapshot, ReitsmaInputSnapshot):
        raise TypeError("Reitsma execution requires a frozen joint count snapshot")
    if not isinstance(request, ReitsmaRequest):
        raise TypeError("Reitsma execution requires a frozen joint model request")


def _register_reitsma_data(
    bridge: ReitsmaBridge, data: object
) -> tuple[_GlobalEnvironment, str, str]:
    suffix = uuid4().hex
    data_name = f"rcms_reitsma_data_{suffix}"
    result_name = f"rcms_reitsma_result_{suffix}"
    if not _R_SYMBOL.fullmatch(data_name) or not _R_SYMBOL.fullmatch(result_name):
        raise RuntimeError("generated Reitsma bridge symbols are invalid")
    environment = cast(_GlobalEnvironment, getattr(bridge.ro, "globalenv", None))
    if environment is None:
        raise RuntimeError("Reitsma backend has no R global environment")
    environment[data_name] = data
    return environment, data_name, result_name


def _authority_request_with_plot(
    request: ReitsmaRequest, plot_output_path: str | None
) -> dict[str, object]:
    authority_request = request.to_mapping()
    if plot_output_path is not None:
        if (
            not request.create_plot
            or not isinstance(plot_output_path, str)
            or not plot_output_path.strip()
        ):
            raise ValueError("Reitsma plot path requires an enabled SROC request")
        authority_params = cast(dict[str, object], authority_request["params"])
        authority_params["fp_outpath"] = plot_output_path
    return authority_request


def _cleanup_reitsma_values(
    bridge: ReitsmaBridge,
    environment: _GlobalEnvironment,
    data_name: str,
    result_name: str,
) -> None:
    try:
        bridge.execute_r_function(
            "rm",
            list=bridge._r_character_vector([data_name, result_name]),
            envir=environment,
        )
    except Exception:
        # Temporary names are unique per call; failed cleanup cannot replace
        # the analysis result or collide with another worker request.
        pass


def _execute_reitsma_request(
    bridge: ReitsmaBridge,
    request: ReitsmaRequest,
    plot_output_path: str | None,
    environment: _GlobalEnvironment,
    data_name: str,
    result_name: str,
) -> object:
    try:
        return bridge.run_versioned_analysis_request(
            _authority_request_with_plot(request, plot_output_path),
            res_name=result_name,
            data_name=data_name,
        )
    except Exception as error:
        raise ReitsmaAnalysisError(
            "RCMetaR Reitsma analysis failed: " + _clean_authority_error(error)
        ) from error
    finally:
        _cleanup_reitsma_values(bridge, environment, data_name, result_name)


def _parse_authority_result(raw_result: object) -> AnalysisResult:
    try:
        if isinstance(raw_result, AnalysisResult):
            return raw_result
        return parse_analysis_result(raw_result)
    except Exception as error:
        raise ReitsmaAnalysisError(
            "RCMetaR returned an invalid Reitsma analysis result: "
            + _clean_authority_error(error)
        ) from error


def run_reitsma_analysis(
    input_snapshot: ReitsmaInputSnapshot,
    request: ReitsmaRequest,
    bridge: ReitsmaBridge,
    *,
    plot_output_path: str | None = None,
) -> ReitsmaAnalysisRun:
    """Validate counts and run one explicit public RCMetaR Reitsma request."""
    _validate_run_inputs(input_snapshot, request)
    data = create_reitsma_r_data(input_snapshot, bridge)
    _validate_authority_counts(input_snapshot, data, bridge)
    environment, data_name, result_name = _register_reitsma_data(bridge, data)
    raw_result = _execute_reitsma_request(
        bridge,
        request,
        plot_output_path,
        environment,
        data_name,
        result_name,
    )
    result = _ordered_result(_parse_authority_result(raw_result))
    report = _report_from_result(result, request)
    return ReitsmaAnalysisRun(input_snapshot, request, result, report)
