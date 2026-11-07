"""Validate the historical before bundle without creating captures or installing R."""
import json
from pathlib import Path
import re
import sys


def preflight(here):
    receipt_path = here / 'raw/reviewer-groups-before.json'
    receipt = json.loads(receipt_path.read_text())
    if receipt['exit_code'] != 0:
        raise ValueError('Before receipt did not pass')
    log = (here / 'raw' / receipt['log']).read_text()
    match = re.search(r'^Evidence: (.+)$', log, re.M)
    if not match:
        raise ValueError('Before log has no Evidence path')
    directory = Path(match[1])
    manifest = json.loads((directory / 'manifest.json').read_text())
    if not manifest['passed'] or not manifest['native_requested']:
        raise ValueError('Before evidence must be a passed native run')
    steps = [json.loads(line) for line in (directory / 'steps.jsonl').read_text().splitlines()]
    captures = [directory / name for step in steps for name in step.get('captures', [])]
    if not captures or any(not path.is_file() for path in captures):
        raise ValueError('Before captures are missing')
    return directory


if __name__ == '__main__':
    preflight(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent)
    print('Historical before bundle preflight passed')
