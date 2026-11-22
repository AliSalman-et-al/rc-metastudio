"""Save raw fits in an instrumented desktop drive for independent R checks."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
from shutil import copyfile
from unittest.mock import patch
from uuid import uuid4

from rc_metastudio import r_worker
from tests.e2e import r_oracle


@contextmanager
def instrument_worker(work: Path):
    directory = work / "fit-observations"
    directory.mkdir()
    os.environ["RCMS_TEST_FIT_DIRECTORY"] = str(directory)
    program, source = r_worker._runtime_paths()
    script = directory / "worker.R"
    hook = '''
        invisible(trace(".rcmetar.result.payload", where=asNamespace("RCMetaR"), print=FALSE,
            tracer=quote({
                path <- Sys.getenv("RCMS_TEST_FIT_DIRECTORY")
                if (file.exists(file.path(path, "record"))) {
                    saveRDS(result, tempfile("fit-", tmpdir=path, fileext=".rds"))
                }
            })))
'''
    text = source.read_text(encoding="utf-8")
    anchor = 'library("RCMetaR", lib.loc=dirname(path))'
    assert anchor in text
    script.write_text(text.replace(anchor, anchor + hook, 1), encoding="utf-8")
    with patch.object(r_worker, "_runtime_paths", return_value=(program, script)):
        yield


class FitObservation:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.before = set(directory.glob("fit-*.rds"))

    def path(self) -> Path:
        fit, = set(self.directory.glob("fit-*.rds")) - self.before
        return fit

    def evaluate(self, expression: str):
        path = json.dumps(self.path().as_posix(), ensure_ascii=False)
        return r_oracle.evaluate(f"local({{result <- readRDS({path}); {expression}}})")

    def save(self, path: Path) -> None:
        copyfile(self.path(), path)


@contextmanager
def observe_fit():
    directory = Path(os.environ["RCMS_TEST_FIT_DIRECTORY"])
    marker = directory / "record"
    observation = FitObservation(directory)
    marker.touch(exist_ok=False)
    try:
        yield observation
        observation.path()
    finally:
        marker.unlink()
