from collections import Counter, defaultdict
from pathlib import Path
import re
import xml.etree.ElementTree as ET

source = Path(__file__).resolve().with_name('continuous-default.display.svg')
root = ET.parse(source).getroot()
texts = defaultdict(list)
for node in root.iter('{http://www.w3.org/2000/svg}text'):
    size = re.search(r'font-size:\s*([\d.]+)px', node.get('style', ''))
    if size:
        texts[float(size[1])].append(''.join(node.itertext()))
for size, labels in sorted(texts.items()):
    print(size, 'px:', len(labels), 'elements; examples:', labels[:5])
body = Counter({size: len(labels) for size, labels in texts.items()}).most_common(1)[0][0]
assert any('Carroll' in label for label in texts[body])
print('Study label/body size:', body, 'px')
print('Annotation/body floor inflation:', body/min(texts))
