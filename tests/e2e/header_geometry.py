"""Full device, caption and arm identity checks for actual forest SVGs."""
import re
from xml.etree import ElementTree as ET
from tests.python.gui.test_types import required


def check_headers(source, names):
    tree = ET.parse(source)
    texts = list(tree.iter('{http://www.w3.org/2000/svg}text'))
    first = min(float(n.attrib['y']) for n in texts if ''.join(n.itertext()).startswith('Fixture 1'))
    measurements = []
    for node in texts:
        x, y = float(node.attrib['x']), float(node.attrib['y'])
        if y >= first - 5:
            continue
        size = float(required(re.search(r'font-size:\s*([\d.]+)px', node.attrib['style']))[1])
        width = float(node.attrib.get('textLength', '0').removesuffix('px'))
        anchor = node.attrib.get('text-anchor')
        left = x-width if anchor == 'end' else x-width/2 if anchor == 'middle' else x
        box = (left, y-size*.8, left+width, y+size*.2)
        text = ''.join(node.itertext())
        assert box[1] >= 4, ('header outside device top', source, text, box)
        for line in tree.iter('{http://www.w3.org/2000/svg}line'):
            a,b,c,d = (float(line.attrib[key]) for key in ('x1','y1','x2','y2'))
            if abs(b-d) < .02 and abs(a-c) > 20 and min(a,c) < box[2] and max(a,c) > box[0]:
                assert not box[1] < b < box[3], ('header rule crosses text', source, text, box, (a,b,c,d))
        measurements.append(dict(text=text, box=box))
    captions = [m for m in measurements if 'Follow-up:' in m['text'] or 'Outcome:' in m['text'] or 'Comparison:' in m['text']]
    assert captions, ('caption missing', source)
    caption_bottom = max(m['box'][3] for m in captions)
    headings = [m for m in measurements if m not in captions]
    assert headings, source
    for heading in headings:
        assert heading['box'][1] - caption_bottom >= 6, ('header/caption clearance', source, heading, caption_bottom)
    # Match contiguous wrapped lines in the heading block, excluding the caption:
    # the caption also contains the full name and must not mask truncation.
    for name in names:
        words = name.split()
        candidates = [m for m in headings if m['text'].split() and m['text'].split()[0] == words[0]]
        assert candidates, ('arm header missing', source, name, headings)
        found = False
        for start in candidates:
            center = (start['box'][0] + start['box'][2]) / 2
            column = sorted((m for m in headings if abs((m['box'][0]+m['box'][2])/2-center) < 2 and m['box'][1] >= start['box'][1] - 1), key=lambda m:m['box'][1])
            observed = ' '.join(m['text'] for m in column).split()
            found |= observed[:len(words)] == words
        assert found, ('arm header lost words', source, name, candidates)
    return measurements
