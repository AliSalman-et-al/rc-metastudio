import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
from tests.e2e.header_geometry import check_forest_footer
output = Path(sys.argv[1])
results = {}
for path in sorted(output.glob('*.svg')):
    if '.display.' in path.name:
        continue
    rows = check_forest_footer(path)
    nodes = [n for n in ET.parse(path).iter('{http://www.w3.org/2000/svg}text') if ''.join(n.itertext()).startswith('Favours')]
    assert len(nodes) == 2, path
    assert nodes[0].attrib['y'] == nodes[1].attrib['y'], (path, [n.attrib['y'] for n in nodes])
    results[path.name] = rows
assert len(results) == 6, results
(output / 'geometry.json').write_text(json.dumps(results, indent=2))
print('FOOTER METRICS PASSED', len(results))
