# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Opaque identities for entities that can be renamed or reordered."""

from typing import NewType

ArmId = NewType("ArmId", str)
RowId = NewType("RowId", str)
SheetId = NewType("SheetId", str)
