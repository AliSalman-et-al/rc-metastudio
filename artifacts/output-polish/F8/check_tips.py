from pathlib import Path
import sys
from xml.etree import ElementTree as ET


svg = "{http://www.w3.org/2000/svg}"
directory = Path(sys.argv[1])
for preset in ("Default", "RevMan", "BMJ"):
    drawing = ET.parse(directory / f"clipped-{preset}.svg")
    def vertices(shape):
        return [tuple(map(float, value.split(","))) for value in shape.attrib["points"].split()]
    polygons = [vertices(shape) for shape in drawing.iter(svg + "polygon")
                if "fill: #" in shape.get("style", "")]
    summary = next(points for points in reversed(polygons) if len(points) == 6)
    tip = min(summary)
    same_edge = [point for point in summary if point[0] == tip[0]]
    assert same_edge == [tip], (preset, summary)
    bases = sorted(point[1] for point in summary if point[0] == summary[1][0])
    assert len(bases) == 2 and bases[0] < tip[1] < bases[1], (preset, summary)
    study_marks = polygons + [vertices(shape) for shape in drawing.iter(svg + "polyline")]
    study_clips = [points for points in study_marks if len(points) == 3 and abs(min(points)[0] - tip[0]) < 0.1]
    assert study_clips, (preset, summary)
    print(preset, "pooled tip at", tip, "matches the left edge of", len(study_clips), "study tips")
