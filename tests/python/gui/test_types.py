# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Small typing helpers for Qt test seams.

Qt's generated stubs correctly model nullable lookups, while these tests
usually establish the widgets before using them.  Keeping the assertion in a
single helper makes that invariant explicit without weakening Ty globally.
QTest's stubs incorrectly declare its static functions as instance methods;
these casts describe their actual QWidget overload signatures.
"""

from collections.abc import Callable
from typing import TypeVar, cast

from PyQt6 import QtCore, QtTest
from PyQt6.QtWidgets import QWidget

T = TypeVar("T")


def required(value: T | None, name: str = "value") -> T:
    """Return a required value, failing the test setup when it is missing."""

    assert value is not None, f"Expected {name} to exist"
    return value


def key_click(
    widget: QWidget,
    key: QtCore.Qt.Key,
    modifiers: QtCore.Qt.KeyboardModifier = QtCore.Qt.KeyboardModifier.NoModifier,
) -> None:
    """Invoke Qt's overloaded keyClick API through its runtime signature."""

    cast(Callable[..., None], QtTest.QTest.keyClick)(widget, key, modifiers)


def key_clicks(widget: QWidget, sequence: str) -> None:
    """Invoke Qt's overloaded keyClicks API through its runtime signature."""

    cast(Callable[..., None], QtTest.QTest.keyClicks)(widget, sequence)


def mouse_click(
    widget: QWidget,
    button: QtCore.Qt.MouseButton,
    pos: QtCore.QPoint | None = None,
) -> None:
    """Invoke Qt's overloaded mouseClick API through its runtime signature."""

    cast(Callable[..., None], QtTest.QTest.mouseClick)(
        widget, button, pos=QtCore.QPoint() if pos is None else pos
    )


def wait(milliseconds: int) -> None:
    """Wait through Qt's generated test API."""

    cast(Callable[[int], None], QtTest.QTest.qWait)(milliseconds)


def mouse_release(
    widget: QWidget, button: QtCore.Qt.MouseButton, pos: QtCore.QPoint
) -> None:
    """Invoke Qt's overloaded mouseRelease API through its runtime signature."""

    cast(Callable[[QWidget, QtCore.Qt.MouseButton, QtCore.Qt.KeyboardModifier, QtCore.QPoint, int], None], QtTest.QTest.mouseRelease)(
        widget, button, QtCore.Qt.KeyboardModifier.NoModifier, pos, -1
    )


def mouse_press(widget: QWidget, button: QtCore.Qt.MouseButton, pos: QtCore.QPoint) -> None:
    """Press through the runtime QWidget overload."""
    cast(Callable[[QWidget, QtCore.Qt.MouseButton, QtCore.Qt.KeyboardModifier, QtCore.QPoint, int], None], QtTest.QTest.mousePress)(
        widget, button, QtCore.Qt.KeyboardModifier.NoModifier, pos, -1
    )


def mouse_move(widget: QWidget, pos: QtCore.QPoint, delay: int = -1) -> None:
    """Move through the runtime QWidget overload."""
    cast(Callable[[QWidget, QtCore.QPoint, int], None], QtTest.QTest.mouseMove)(widget, pos, delay)
