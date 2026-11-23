"""Own the directories that hold analysis results."""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


@dataclass(frozen=True, slots=True)
class AnalysisScratch:
    root: Path
    caller_owned: bool

    def ensure(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root

    def prepare_launch(self) -> None:
        self.ensure()
        if self.caller_owned:
            return
        for item in self.root.iterdir():
            try:
                if item.is_file():
                    item.unlink()
            except OSError:
                continue

    @contextmanager
    def result_directory(self) -> Generator[Path]:
        directory = TemporaryDirectory(prefix="worker-result-", dir=self.ensure(), delete=False,
                                       ignore_cleanup_errors=True)
        try:
            yield Path(directory.name).resolve()
        except BaseException:
            directory.cleanup()
            raise
