"""Full device, caption and arm identity checks for actual forest SVGs."""
import re
import math
from xml.etree import ElementTree as ET
from tests.python.gui.qt_test_support import required


def check_headers(source, names):
    tree = ET.parse(source)
    device_left, _, device_width, _ = map(float, tree.getroot().attrib['viewBox'].split())
    texts = list(tree.iter('{http://www.w3.org/2000/svg}text'))
    first = min(float(n.attrib['y']) for n in texts if ''.join(n.itertext()).startswith('Fixture 1'))
    caption_nodes = set()
    for group in tree.iter('{http://www.w3.org/2000/svg}g'):
        lines = list(group.findall('{http://www.w3.org/2000/svg}text'))
        for index, node in enumerate(lines):
            if 'Comparison:' not in ''.join(node.itertext()):
                continue
            caption_nodes.add(node)
            previous = node
            size = float(required(re.search(r'font-size:\s*([\d.]+)px', node.attrib['style']))[1])
            for continuation in lines[index + 1:]:
                gap = float(continuation.attrib['y']) - float(previous.attrib['y'])
                if (continuation.attrib['style'] != node.attrib['style']
                        or continuation.attrib['x'] != node.attrib['x']
                        or not 0 < gap <= 1.5 * size):
                    break
                caption_nodes.add(continuation)
                previous = continuation
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
        assert box[0] >= device_left and box[2] <= device_left + device_width, ('header outside device horizontally', source, text, box)
        assert box[1] >= 4, ('header outside device top', source, text, box)
        for line in tree.iter('{http://www.w3.org/2000/svg}line'):
            a,b,c,d = (float(line.attrib[key]) for key in ('x1','y1','x2','y2'))
            if abs(b-d) < .02 and abs(a-c) > 20 and min(a,c) < box[2] and max(a,c) > box[0]:
                assert not box[1] < b < box[3], ('header rule crosses text', source, text, box, (a,b,c,d))
        measurements.append(dict(text=text, box=box, caption=node in caption_nodes))
    captions = [m for m in measurements if m['caption']]
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


def check_direction_text(texts, directions, expected):
    ordered = sorted(directions, key=lambda node: (float(node.attrib['x']), node.attrib.get('text-anchor') != 'end'))
    observed = tuple(''.join(node.itertext()) for node in ordered)
    assert observed == expected, ('direction text changed', observed, expected)
    if len(ordered) == 2:
        assert ordered[0].attrib.get('text-anchor') == 'end', ('left direction anchor', observed)
        assert ordered[1].attrib.get('text-anchor', 'start') == 'start', ('right direction anchor', observed)
        gap = float(ordered[1].attrib['x']) - float(ordered[0].attrib['x'])
        size = float(required(re.search(r'font-size:\s*([\d.]+)', ordered[0].attrib['style']))[1])
        assert 0 < gap < 2 * size, ('direction null gutter', gap, size)


def check_direction_ink_gap(source, directions, width, height):
    """Check painted glyphs: Qt trims outer whitespace that SVG boxes retain."""
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QColor, QImage, QPainter
    from PyQt6.QtSvg import QSvgRenderer
    size = float(required(re.search(r'font-size:\s*([\d.]+)', directions[0].attrib['style']))[1])
    baseline = float(directions[0].attrib['y'])
    null = sum(float(node.attrib['x']) for node in directions) / 2
    # Resolve tiny fitted text without allocating a full high-resolution page.
    scale = max(4, math.ceil(16 / size))
    top = baseline - size * .8
    left_edge = null - size * 2
    image = QImage(math.ceil(size * 4 * scale) + 1, math.ceil(size * 1.1 * scale) + 1, QImage.Format.Format_RGB32)
    image.fill(QColor('white'))
    painter = QPainter(image)
    painter.scale(scale, scale)
    painter.translate(-left_edge, -top)
    QSvgRenderer(str(source)).render(painter, QRectF(0, 0, width, height))
    painter.end()
    center = round((null - left_edge) * scale)
    ink = [column for column in range(image.width())
           if any(image.pixelColor(column, row).lightness() < 100 for row in range(image.height()))]
    left = max(column for column in ink if column < center)
    right = min(column for column in ink if column >= center)
    gap = (right - left - 1) / scale
    assert gap >= size * .25, ('direction glyphs run together', source, gap, size)
    return gap


def check_forest_footer(source, expected_directions=None):
    """Measure rendered direction lines and the axis title, with each direction on one line."""
    texts = list(ET.parse(source).iter('{http://www.w3.org/2000/svg}text'))
    directions = [node for node in texts if ''.join(node.itertext()).startswith('Favours')]
    if expected_directions is not None:
        check_direction_text(texts, directions, expected_directions)
    if not directions:
        return []  # Single-arm and diagnostic plots have no treatment direction.
    assert len({node.attrib['y'] for node in directions}) == 1, ('direction baselines', source)
    measurements = []
    root = ET.parse(source).getroot()
    _, _, device_width, device_height = map(float, root.attrib['viewBox'].split())
    ink_gap = check_direction_ink_gap(source, directions, device_width, device_height) if len(directions) == 2 else None
    first = min(float(node.attrib['y']) for node in directions)
    for node in texts:
        text = ''.join(node.itertext())
        # Axis titles and direction lines follow ticks; numeric tick labels are
        # excluded, as are the footer's heterogeneity/test sentences to the left.
        y = float(node.attrib['y'])
        if y < first - 25 or not text.strip() or re.fullmatch(r'[-+\d.,%eE ]+', text):
            continue
        if any(term in text for term in ('Heterogeneity:', 'Test for overall', 'prediction interval:')):
            continue
        size = float(required(re.search(r'font-size:\s*([\d.]+)px', node.attrib['style']))[1])
        x = float(node.attrib['x'])
        width = float(node.attrib.get('textLength', '0').removesuffix('px'))
        anchor = node.attrib.get('text-anchor')
        left = x - width if anchor == 'end' else x - width / 2 if anchor == 'middle' else x
        measurements.append(dict(text=text, box=(left, y - size * .8, left + width, y + size * .2), direction_ink_gap=ink_gap if text.strip().startswith('Favours') else None))
    for measurement in measurements:
        left, top, right, bottom = measurement['box']
        assert 0 <= left < right <= device_width and 0 <= top < bottom <= device_height, ('forest footer outside device', source, measurement)
    for index, a in enumerate(measurements):
        for b in measurements[index + 1:]:
            overlap = (min(a['box'][2], b['box'][2]) - max(a['box'][0], b['box'][0]),
                       min(a['box'][3], b['box'][3]) - max(a['box'][1], b['box'][1]))
            assert overlap[0] <= 0 or overlap[1] <= 0, ('forest footer text overlaps', source, a, b, overlap)
    return measurements


def check_contour_colours(source):
    root = ET.parse(source).getroot()
    fills = {}
    for node in root.iter():
        style = node.attrib.get('style', '')
        match = re.search(r'fill:\s*(#[0-9A-Fa-f]{6})', style)
        if match and node.tag.rsplit('}', 1)[-1] in {'polygon', 'rect'}:
            fills.setdefault(node.tag.rsplit('}', 1)[-1], set()).add(match[1].lower())
    regions = fills.get('polygon', set()) - {'#ffffff'}
    keys = fills.get('rect', set()) - {'#ffffff'}
    assert len(regions) >= 3 and regions <= keys, (source, regions, keys)
    def luminance(colour):
        channels = [int(colour[i:i+2], 16) / 255 for i in (1, 3, 5)]
        return sum((c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4) * w
                   for c, w in zip(channels, (.2126, .7152, .0722)))
    points = {match[1].lower() for node in root.iter('{http://www.w3.org/2000/svg}circle')
              if (match := re.search(r'fill:\s*(#[0-9A-Fa-f]{6})', node.attrib.get('style', '')))}
    assert points, ('study point colours missing', source)
    ratios = {(point, band): (max(luminance(point), luminance(band)) + .05) /
              (min(luminance(point), luminance(band)) + .05)
              for point in points for band in regions}
    # The original blue/grey palette has 1.8:1 minimum contrast; the darkened
    # #666666 band falls below this and must not silently return.
    assert min(ratios.values()) >= 1.8, (source, ratios)
    return ratios


def check_sroc_legend_bounds(source):
    root = ET.parse(source).getroot()
    width = float(root.attrib['viewBox'].split()[2])
    nodes = [n for n in root.iter('{http://www.w3.org/2000/svg}text')
             if ''.join(n.itertext()) == 'Joint prediction region']
    assert nodes, source
    for node in nodes:
        x = float(node.attrib['x'])
        length = float(node.attrib['textLength'].removesuffix('px'))
        assert 0 <= x and x + length <= width, (source, x, length, width)
