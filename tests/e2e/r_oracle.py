"""Run independent public-R checks in the desktop drive's owned scratch directory."""

import json
import os
from pathlib import Path
import subprocess


def evaluate(expression: str):
    directory = Path(os.environ["RCMS_ANALYSIS_SCRATCH_DIR"]) / "oracle"
    directory.mkdir(parents=True, exist_ok=True)
    source = directory / "expression.R"
    source.write_text(expression, encoding="utf-8")
    executable = Path(os.environ["R_HOME"]) / "bin" / ("Rscript.exe" if os.name == "nt" else "Rscript")
    subprocess.run([str(executable), "--vanilla", "-e", """
        suppressPackageStartupMessages(library(RCMetaR))
        if (file.exists("session.RData")) load("session.RData", envir=.GlobalEnv)
        local({
            evaluated <- withVisible(eval(parse("expression.R", encoding="UTF-8"), envir=.GlobalEnv))
            value <- if (evaluated$visible) evaluated$value else NULL
            if (inherits(value, "json")) value <- as.character(value)
            if (is.atomic(value) && !is.null(names(value))) value <- as.list(value)
            jsonlite::write_json(value, "result.json", digits=I(17), null="null", auto_unbox=FALSE)
        })
        save(list=ls(.GlobalEnv, all.names=TRUE), file="session.RData", envir=.GlobalEnv)
    """], cwd=directory, check=True, capture_output=True, timeout=60)
    return json.loads((directory / "result.json").read_text(encoding="utf-8"))


def load(path: str | Path) -> None:
    evaluate(f"load({json.dumps(Path(path).resolve().as_posix(), ensure_ascii=False)})")


def assign(name: str, value: str) -> None:
    evaluate(f"assign({json.dumps(name)}, {json.dumps(value, ensure_ascii=False)}, envir=.GlobalEnv)")


def apply(expression: str, *args):
    arguments = json.dumps(json.dumps(args, ensure_ascii=False), ensure_ascii=False)
    return evaluate(f"do.call(({expression}), jsonlite::fromJSON({arguments}, simplifyVector=FALSE))")
