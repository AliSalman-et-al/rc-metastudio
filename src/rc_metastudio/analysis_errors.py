# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain errors raised while executing analyses."""


class DiagnosticExecutionError(RuntimeError):
    """A diagnostic R execution failed and may be retried per metric."""


class PrimaryDiagnosticFitError(DiagnosticExecutionError):
    """The requested Reitsma fit failed during statistical execution."""

    def __init__(self, metric: str, workflow: str, detail: str):
        self.metric = metric
        self.method = "diagnostic.reitsma"
        self.workflow = workflow
        self.detail = detail
        super().__init__(detail)
