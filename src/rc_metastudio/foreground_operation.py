"""Keep foreground desktop commands exclusive during nested event loops."""

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar


_active = ContextVar("foreground_operation_active", default=False)


class OperationCancelled(RuntimeError):
    """The user cancelled an operation before it published its output."""


def is_active() -> bool:
    return _active.get()


@contextmanager
def foreground_operation() -> Generator[None]:
    token = _active.set(True)
    try:
        yield
    finally:
        _active.reset(token)
