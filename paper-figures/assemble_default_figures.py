"""Assemble vector figures at 1:1 and render them at 300 dpi."""
from contextlib import ExitStack
from pathlib import Path
import os
import sys

import pymupdf

OUT = Path(os.environ["RCMS_PAPER_OUTPUT"])
PANELS = Path(os.environ.get("RCMS_PAPER_PANELS", OUT))
GUTTER = 6 * 72 / 25.4
LEFT_MARGIN = 4 * 72 / 25.4
LABEL_SIZE_PT = 28
LABEL_BAND = LABEL_SIZE_PT + 14
LABEL_BASELINE = LABEL_SIZE_PT + 3
LABEL_FONT = "hebo"
FIGURES = {
    "figure-2-forest": ("figure-2a-forest-default", "figure-2b-forest-bmj", "figure-2c-forest-revman"),
    "figure-3-pairwise": ("figure-3a-regression", "figure-3b-contour-funnel"),
    "figure-4-diagnostic-sequential": ("figure-4a-sroc", "figure-4b-tsa"),
}


def main():
    font = pymupdf.Font(LABEL_FONT)
    for name in sys.argv[1:] or ("figure-3-pairwise", "figure-4-diagnostic-sequential"):
        stems = FIGURES[name]
        target = OUT / f"{name}.pdf"
        with ExitStack() as stack:
            panels = [stack.enter_context(pymupdf.open(PANELS / f"{stem}.pdf")) for stem in stems]
            for panel in panels:
                assert len(panel) == 1 and not panel[0].get_image_info(), panel.name
            width = LEFT_MARGIN + max(panel[0].rect.width for panel in panels)
            height = sum(panel[0].rect.height + LABEL_BAND for panel in panels) + GUTTER * (len(panels) - 1)
            output = stack.enter_context(pymupdf.open())
            page = output.new_page(width=width, height=height)
            y = 0
            for label, panel in zip("ABC", panels):
                rect = panel[0].rect
                bearing = font.glyph_bbox(ord(label)).x0 * LABEL_SIZE_PT
                page.insert_text((LEFT_MARGIN - bearing, y + LABEL_BASELINE), label,
                                 fontname=LABEL_FONT, fontsize=LABEL_SIZE_PT)
                top = y + LABEL_BAND
                page.show_pdf_page(rect + (LEFT_MARGIN, top, LEFT_MARGIN, top), panel, 0)
                y += rect.height + LABEL_BAND + GUTTER
            output.save(target, deflate=True, garbage=4)
        with pymupdf.open(target) as output:
            output[0].get_pixmap(dpi=300, alpha=False).save(target.with_suffix(".png"))


if __name__ == "__main__":
    main()

