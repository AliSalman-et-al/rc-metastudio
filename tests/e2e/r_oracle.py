"""Run independent public-R checks in the desktop drive's owned scratch directory."""

import json
import os
from pathlib import Path
import subprocess

from rc_metastudio.settings import analysis_scratch


def evaluate(expression: str):
    directory = analysis_scratch().root / "oracle"
    directory.mkdir(parents=True, exist_ok=True)
    source = directory / "expression.R"
    source.write_text(expression, encoding="utf-8")
    executable = Path(os.environ["R_HOME"]) / "bin" / ("Rscript.exe" if os.name == "nt" else "Rscript")
    driver = directory / "oracle.R"
    driver.write_text("""
        suppressPackageStartupMessages(library(RCMetaR))
        if (file.exists("session.RData")) load("session.RData", envir=.GlobalEnv)
        local({
            evaluated <- withVisible(eval(parse("expression.R", encoding="UTF-8"), envir=.GlobalEnv))
            value <- if (evaluated$visible) evaluated$value else NULL
            if (inherits(value, "json")) value <- as.character(value)
            jsonlite::write_json(value, "result.json", digits=I(17), null="null", auto_unbox=FALSE)
        })
        save(list=ls(.GlobalEnv, all.names=TRUE), file="session.RData", envir=.GlobalEnv)
    """, encoding="utf-8")
    process = subprocess.run([str(executable), "--vanilla", str(driver)], cwd=directory,
                             capture_output=True, timeout=60)
    if process.returncode:
        (directory / "stderr.log").write_bytes(process.stderr)
        process.check_returncode()
    return json.loads((directory / "result.json").read_text(encoding="utf-8"))


def load(path: str | Path) -> None:
    evaluate(f"load({json.dumps(Path(path).resolve().as_posix(), ensure_ascii=False)})")


def assign(name: str, value: str) -> None:
    evaluate(f"assign({json.dumps(name)}, {json.dumps(value, ensure_ascii=False)}, envir=.GlobalEnv)")


def apply(expression: str, *args):
    arguments = json.dumps(json.dumps(args, ensure_ascii=False), ensure_ascii=False)
    return evaluate(f"do.call(({expression}), jsonlite::fromJSON({arguments}, simplifyVector=FALSE))")


def evaluate_result_vector(expression: str):
    """Retain the dimensions and statistical metadata used by the result decoder."""
    from rc_metastudio.r_worker import _decode_number

    encoded = evaluate(f"""local({{
        scalar <- function(value) {{
            if (is.numeric(value) && is.infinite(value))
                return(list("$num"=if (value > 0) "+Inf" else "-Inf"))
            if (is.na(value)) return(NULL)
            unname(value)
        }}
        vector <- RCMetaR:::.rcmetar.worker.result.vector({{{expression}}}, scalar)
        jsonlite::toJSON(vector, auto_unbox=TRUE, digits=I(17), null="null")
    }})""")
    return json.loads(encoded[0], object_hook=_decode_number)
