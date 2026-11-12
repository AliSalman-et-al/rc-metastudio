#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Audit ownership contracts for top-level Qt Designer forms."""

import ast
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


# Each canonical form has one owner that registers its window role. Specialized
# subclasses inherit that contract. Wizard pages likewise inherit it from
# MainWizard and are intentionally absent here.
TOP_LEVEL_FORM_INVENTORY = {
    "about_legal.ui": (("about_legal_dialog.py", "AboutLegalDialog", "TRANSACTIONAL"),),
    "binary_data_dialog.ui": (
        ("binary_data_dialog.py", "BinaryDataDialog", "TRANSACTIONAL"),
    ),
    "covariate_type_dialog.ui": (
        ("covariate_type_dialog.py", "CovariateTypeDialog", "TRANSACTIONAL"),
    ),
    "edit_name_dialog.ui": (
        ("edit_name_dialogs.py", "EditGroupNameDialog", "TRANSACTIONAL"),
        ("edit_name_dialogs.py", "EditCovariateNameDialog", "TRANSACTIONAL"),
    ),
    "binary_back_calculation_dialog.ui": (
        ("binary_data_dialog.py", "BinaryBackCalculationDialog", "TRANSACTIONAL"),
    ),
    "confidence_level_dialog.ui": (
        ("confidence_level_dialog.py", "ConfidenceLevelDialog", "CONFIDENCE_LEVEL"),
    ),
    "continuous_back_calculation_dialog.ui": (
        (
            "continuous_data_dialog.py",
            "ContinuousBackCalculationDialog",
            "TRANSACTIONAL",
        ),
    ),
    "continuous_data_dialog.ui": (
        ("continuous_data_dialog.py", "ContinuousDataDialog", "TRANSACTIONAL"),
    ),
    "publication_bias_dialog.ui": (
        ("small_study_effects_dialog.py", "PublicationBiasDialog", "TRANSACTIONAL"),
    ),
    "subgroup_analysis_dialog.ui": (
        ("subgroup_analysis_dialog.py", "SubgroupAnalysisDialog", "TRANSACTIONAL"),
    ),
    "diagnostic_data_dialog.ui": (
        ("diagnostic_data_dialog.py", "DiagnosticDataDialog", "TRANSACTIONAL"),
    ),
    "diagnostic_metrics_dialog.ui": (
        ("diagnostic_metrics_dialog.py", "DiagnosticMetricsDialog", "TRANSACTIONAL"),
    ),
    "edit_plot_dialog.ui": (
        ("plot_editor_dialog.py", "EditPlotDialog", "TRANSACTIONAL"),
    ),
    "funnel_plot_editor_dialog.ui": (
        ("funnel_plot_editor_dialog.py", "FunnelPlotEditorDialog", "TRANSACTIONAL"),
    ),
    "analysis_setup_dialog.ui": (
        ("analysis_setup_dialog.py", "AnalysisSetupDialog", "TRANSACTIONAL"),
    ),
    "main_window.ui": (("main_window.py", "MainWindow", "MAIN"),),
    "new_covariate_dialog.ui": (
        ("add_new_dialogs.py", "AddCovariateDialog", "TRANSACTIONAL"),
    ),
    "new_study_dialog.ui": (("add_new_dialogs.py", "AddStudyDialog", "TRANSACTIONAL"),),
    "results_window.ui": (("results_window.py", "ResultsWindow", "RESULTS"),),
    "progress_dialog.ui": (
        ("progress_dialog.py", "AnalysisProgressDialog", "TRANSIENT"),
    ),
}

TOP_LEVEL_CLASSES = {"QDialog", "QMainWindow"}


@dataclass(frozen=True)
class OwnershipFinding:
    """An ownership finding before conversion to the main audit's Finding type."""

    path: Path
    detail: str


def _is_exact_window_registration(node: ast.AST, expected_role: str) -> bool:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    if (
        node.func.attr != "register_adaptive_window"
        or not isinstance(node.func.value, ast.Name)
        or node.func.value.id != "adaptive_window"
        or not node.args
        or not isinstance(node.args[0], ast.Name)
        or node.args[0].id != "self"
    ):
        return False
    role_node = (
        node.args[1]
        if len(node.args) >= 2
        else next(
            (keyword.value for keyword in node.keywords if keyword.arg == "role"),
            None,
        )
    )
    return (
        isinstance(role_node, ast.Attribute)
        and role_node.attr == expected_role
        and isinstance(role_node.value, ast.Attribute)
        and role_node.value.attr == "WindowRole"
        and isinstance(role_node.value.value, ast.Name)
        and role_node.value.value.id == "adaptive_window"
    )


def _registered_in(statements: list[ast.stmt], role: str, *, annotated: bool) -> bool:
    for statement in statements:
        if isinstance(statement, (ast.Return, ast.Raise)):
            break
        kinds = (ast.Expr, ast.Assign, ast.AnnAssign) if annotated else (ast.Expr, ast.Assign)
        if isinstance(statement, kinds) and statement.value is not None and _is_exact_window_registration(statement.value, role):
            return True
    return False


def _calls_configure(statement: ast.stmt) -> bool:
    if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
        return False
    func = statement.value.func
    return (isinstance(func, ast.Attribute) and func.attr == "_configure_window"
            and isinstance(func.value, ast.Name) and func.value.id == "self")


def _class_registers(target: ast.ClassDef | None, role: str) -> bool:
    if target is None:
        return False
    # Match the first definition, as the original scan did.
    initializer = next((node for node in target.body if isinstance(node, ast.FunctionDef) and node.name == "__init__"), None)
    configure = next((node for node in target.body if isinstance(node, ast.FunctionDef) and node.name == "_configure_window"), None)
    if initializer is None:
        return False
    for statement in initializer.body:
        if configure is not None and _calls_configure(statement) and _registered_in(configure.body, role, annotated=False):
            return True
        if isinstance(statement, (ast.Return, ast.Raise)):
            break
        if _registered_in([statement], role, annotated=True):
            return True
    return False


def _parse_source(source: Path) -> ast.Module | None:
    try:
        return ast.parse(source.read_text(encoding="utf-8")) if source.exists() else None
    except SyntaxError:
        return None


def _audit_registrations(source_dir: Path) -> list[OwnershipFinding]:
    findings: list[OwnershipFinding] = []
    parsed_sources: dict[Path, ast.Module | None] = {}
    for form_name, registrations in TOP_LEVEL_FORM_INVENTORY.items():
        for source_name, class_name, role in registrations:
            source = source_dir / source_name
            if source not in parsed_sources:
                parsed_sources[source] = _parse_source(source)
            tree = parsed_sources[source]
            target = next((node for node in (tree.body if tree is not None else ())
                           if isinstance(node, ast.ClassDef) and node.name == class_name), None)
            if not _class_registers(target, role):
                findings.append(OwnershipFinding(source, f"{class_name} for {form_name} does not explicitly register {role}"))
    return findings


def audit_top_level_form_ownership(
    forms_dir: Path, source_dir: Path
) -> tuple[OwnershipFinding, ...]:
    findings: list[OwnershipFinding] = []
    actual_top_levels: set[str] = set()
    for path in forms_dir.glob("*.ui"):
        try:
            top = ET.parse(path).getroot().find("widget")
        except ET.ParseError:
            continue
        if top is not None and top.get("class") in TOP_LEVEL_CLASSES:
            actual_top_levels.add(path.name)

    expected = set(TOP_LEVEL_FORM_INVENTORY)
    for missing in sorted(actual_top_levels - expected):
        findings.append(OwnershipFinding(forms_dir / missing, "top-level form has no authoritative inventory entry"))
    for stale in sorted(expected - actual_top_levels):
        findings.append(OwnershipFinding(forms_dir / stale, "inventory entry is not a canonical top-level form"))

    findings.extend(_audit_registrations(source_dir))
    return tuple(findings)
