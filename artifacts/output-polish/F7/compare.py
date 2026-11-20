from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

here = Path(__file__).resolve().parent
inputs = [("metafor reference (RD)", "metafor-bmj.png"),
          ("RC MetaStudio (RD)", "rd-paper.png"), ("RC MetaStudio (RR)", "rr-paper.png")]
figures = []
for name, file in inputs:
    with Image.open(here / file) as source:
        figures.append((name, ImageOps.contain(source.convert("RGB"), (780, 980))))
canvas = Image.new("RGB", (2400, max(figure.height for _, figure in figures) + 58), "white")
draw = ImageDraw.Draw(canvas)
for i, (name, figure) in enumerate(figures):
    left = 800 * i + 10
    draw.text((left, 10), name, fill="black", font_size=22)
    canvas.paste(figure, (left, 48))
canvas.save(here / "BMJ-comparison.png")
