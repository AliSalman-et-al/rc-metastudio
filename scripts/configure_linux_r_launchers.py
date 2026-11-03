from pathlib import Path
import sys

home = Path(sys.argv[1]).resolve()
launcher = home / "bin" / "R"
text = launcher.read_text(encoding="utf-8")
marker = "R_HOME_DIR=\"/opt/R/4.6.1/lib/R\""
if marker not in text:
    raise SystemExit("unexpected Posit R launcher; cannot make it relocatable")
tail = text[text.index("usage=\"") :]
header = '''#!/bin/bash
# Relocatable wrapper for the private R runtime.
r_script_dir=${0%/*}
R_HOME_DIR="$(CDPATH= cd -- "$r_script_dir/.." && pwd)"
if test -n "${R_HOME}" && test "${R_HOME}" != "${R_HOME_DIR}"; then
  echo "WARNING: ignoring environment value of R_HOME" >&2
fi
R_HOME="${R_HOME_DIR}"
export R_HOME
R_SHARE_DIR="${R_HOME}/share"
export R_SHARE_DIR
R_INCLUDE_DIR="${R_HOME}/include"
export R_INCLUDE_DIR
R_DOC_DIR="${R_HOME}/doc"
export R_DOC_DIR

'''
launcher.write_text(header + tail, encoding="utf-8")
launcher.chmod(0o755)

rscript = home / "bin" / "Rscript"
# Keep upstream's option parser: R itself does not implement Rscript argv rules.
rscript.rename(home / "bin" / "Rscript.real")
rscript.write_text('''#!/bin/sh
r_script_dir=${0%/*}
RHOME="$(CDPATH= cd -- "$r_script_dir/.." && pwd)"
export RHOME
exec "$RHOME/bin/Rscript.real" "$@"
''', encoding="utf-8")
rscript.chmod(0o755)
