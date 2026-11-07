import json
from pathlib import Path
import sys
import os
import subprocess
from xml.etree import ElementTree as ET
from tests.e2e.header_geometry import check_forest_footer
# The shared geometry observer uses assertions; run it without optimization too.
if sys.flags.optimize:
    environment = dict(os.environ)
    environment.pop("PYTHONOPTIMIZE", None)
    raise SystemExit(subprocess.run([sys.executable, __file__, *sys.argv[1:]], env=environment, check=False).returncode)
output = Path(sys.argv[1])
results = {}
for path in sorted(output.glob('*.svg')):
    if '.display.' in path.name:
        continue
    rows = check_forest_footer(path)
    nodes = [n for n in ET.parse(path).iter('{http://www.w3.org/2000/svg}text') if ''.join(n.itertext()).startswith('Favours')]
    if len(nodes) != 2:
        raise ValueError(f"{path}: expected two footer labels")
    if nodes[0].attrib['y'] != nodes[1].attrib['y']:
        raise ValueError(f"{path}: footer labels are not aligned")
    results[path.name] = rows
if len(results) != 6:
    raise ValueError(f"expected six SVG results, got {len(results)}")
(output / 'geometry.json').write_text(json.dumps(results, indent=2))
print('FOOTER METRICS PASSED', len(results))
