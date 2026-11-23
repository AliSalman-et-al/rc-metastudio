"""Check three-operation histories through the workspace and real project archive."""

from itertools import product
from pathlib import Path
from typing import Literal

import pytest

from rc_metastudio.project.archive import load_project
from rc_metastudio.workspace.session import RuntimeProject, WorkspaceSession


Edit = Literal["commit", "nested-commit", "rollback", "nested-rollback"]
Action = Literal[Edit, "undo", "redo", "save"]
ACTIONS: tuple[Action, ...] = (
    "commit", "nested-commit", "rollback", "nested-rollback", "undo", "redo", "save",
)
Snapshot = tuple[str, str]
SOURCE = Path(__file__).resolve().parents[2] / "fixtures/desktop-projects/continuous.rcms"


class ProjectionFailed(RuntimeError):
    pass


def snapshot(runtime: RuntimeProject | None) -> Snapshot:
    assert runtime is not None
    return runtime.dataset.title, runtime.dataset.notes


def apply_edit(session: WorkspaceSession, action: Edit, marker: str) -> None:
    before = snapshot(session.runtime)
    restored: list[Snapshot] = []

    def install(runtime: RuntimeProject) -> None:
        restored.append(snapshot(runtime))

    def edit() -> None:
        with session.change(install):
            runtime = session.runtime
            assert runtime is not None
            runtime.dataset.title = marker
            if action == "rollback":
                raise ProjectionFailed
            if action in ("nested-commit", "nested-rollback"):
                with session.change(install):
                    runtime.dataset.notes = marker
                    if action == "nested-rollback":
                        raise ProjectionFailed

    if action in ("rollback", "nested-rollback"):
        with pytest.raises(ProjectionFailed):
            edit()
        assert snapshot(session.runtime) == before
        assert restored == [before]
    else:
        edit()
        assert not restored


@pytest.mark.parametrize("first", ACTIONS)
def test_workspace_history_model(tmp_path: Path, first: Action) -> None:
    source = load_project(SOURCE)
    for tail in product(ACTIONS, repeat=2):
        trace = (first, *tail)
        session = WorkspaceSession(source)
        live = saved = snapshot(session.runtime)
        history: list[Snapshot] = []
        redo: list[Snapshot] = []
        for step, action in enumerate(trace):
            marker = f"edit {step}"
            if action == "undo":
                assert session.undo() == bool(history), trace
                if history:
                    redo.append(live)
                    live = history.pop()
            elif action == "redo":
                assert session.redo() == bool(redo), trace
                if redo:
                    history.append(live)
                    live = redo.pop()
            elif action == "save":
                path = session.save(tmp_path / "workspace.rcms")
                reopened = WorkspaceSession()
                reopened.open(path)
                assert snapshot(reopened.runtime) == live, trace
                saved = live
            else:
                apply_edit(session, action, marker)
                if action in ("commit", "nested-commit"):
                    history.append(live)
                    redo.clear()
                    live = (marker, marker if action == "nested-commit" else live[1])
            assert snapshot(session.runtime) == live, trace
            assert session.is_dirty == (live != saved), trace
            assert session.can_undo == bool(history), trace
            assert session.can_redo == bool(redo), trace
