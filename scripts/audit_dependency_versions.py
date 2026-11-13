"""Report locked Python versions and installed R identities for upgrade review."""
from __future__ import annotations

import argparse
import json
import subprocess
import tomllib
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--rscript', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    project = tomllib.loads((root / 'pyproject.toml').read_text())
    lock = tomllib.loads((root / 'uv.lock').read_text())
    packages = [dict(name=item['name'], version=item['version']) for item in lock['package'] if item['name'] != project['project']['name']]
    manifest = json.loads((root / 'config/r-dependencies.json').read_text())
    report = dict(
        python_runtime=(root / '.python-version').read_text().strip(),
        python_requirement=project['project']['requires-python'],
        python_packages=packages,
        r_runtime=manifest['target_runtime'],
        r_snapshot=manifest['binary_package_policy']['snapshot'],
    )
    if args.rscript is not None:
        expression = 'write.table(installed.packages()[,c("Package","Version","LibPath")],row.names=FALSE,sep="\\t",quote=FALSE)'
        result = subprocess.run([str(args.rscript.resolve()), '-e', expression], capture_output=True, text=True, check=True)
        report['installed_r_packages_tsv'] = result.stdout
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
