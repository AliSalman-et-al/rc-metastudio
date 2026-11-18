import csv
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent / "tsa-phase4"
sys.path.insert(0, str(PRIOR))
from review import CASES, STYLES, legend_fits, manifest, sheet, steps


def main():
    proof = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "qualification")
    screenshots = []
    plots = {}
    artwork = {}
    for scale in (100, 150):
        for case, scenario in CASES.items():
            run = proof / f"native{scale}" / scenario
            manifest(run)
            runtime = json.loads((run / "runtime.json").read_text(encoding="utf-8"))
            assert runtime["platform_plugin"] == "windows", runtime
            recorded = steps(run)
            for style in STYLES:
                name = f"{case}-{style}"
                action = f"tsa-{name}"
                record, = (step for step in recorded if step["action"] == action)
                observed = record["dpi_scale"]
                assert abs(observed - scale / 100) < .01, (name, scale, observed)
                capture, = run.glob(f"*-0-{action}.png")
                screen = run / "workflow" / f"{name}-viewport.png"
                saved = run / "workflow" / f"{name}.svg"
                legend_fits(saved)
                if scale == 100:
                    artwork[name] = saved.read_bytes()
                else:
                    assert artwork[name] == saved.read_bytes(), (scale, name)
                with Image.open(screen) as image:
                    plots[scale, case, style] = image.convert("RGB")
                screenshots.append((case, style, scale, observed, capture.relative_to(ROOT).as_posix(),
                                    screen.relative_to(ROOT).as_posix()))

    with (ROOT / "screenshots.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(("case", "style", "scale_percent", "observed_dpr", "window", "plot_crop"))
        writer.writerows(screenshots)
    for style in STYLES:
        sheet(ROOT / f"native-{style}.png", [
            (f"{case} at {scale}%", plots[scale, case, style])
            for case in CASES for scale in (100, 150)
        ], 2)
        # Replace the TSA image in the original four-plot family sheet.
        with Image.open(PRIOR / f"contact-{style}.png") as original:
            page = original.convert("RGB")
        width, height = page.width // 2, page.height // 2
        page.paste("white", (0, 25, width, height))
        plot = ImageOps.contain(plots[100, "bcg", style], (width - 20, height - 34))
        page.paste(plot, ((width - plot.width) // 2, 25))
        page.save(ROOT / f"contact-{style}.png")
    print(f"Verified manifests, DPI and SVG bounds for {len(screenshots)} native captures; "
          "SVGs match across scales in all 15 case/style pairs.")


if __name__ == "__main__":
    main()
