# Windows path investigation — run 41956470804

The failing assertion checks WORK/meantime-export.png, not the in-app preview.
Downloaded shards 1 and 2 have identical dimensions in both theme variants:
- workflow/analysis/forest.png: 1943 × 3939, 30613908 bytes RGBA (29.20 MiB),
  decoded successfully by QImage.
- workflow/meantime-export.png: 9712 × 19694, 765072512 bytes RGBA (729.63 MiB).
  This is the intentional 600 dpi user export, never loaded into Qt by the app.

Writer trace:
The initial analysis renders forest.png through rcmetar.render.plot_file with
a display path, and rcmetar.plot.preview.size guards it.
The E2E later calls view.plot_service.export(regenerator="forest", ...,
output_path=WORK/meantime-export.png). PlotService.export loads plotdata and calls
generate_forest_plot(output_path). This different requested output path has no
display companion (rcmetar.plot.display_path_for_bundle); keep.display is FALSE,
so user export resolution correctly remains 600 dpi.

The failing test had Linux's exact (9712, 19679) export dimension hard-coded.
It now keeps exact dimensions, selecting Windows's (9712, 19694) platform fixture.
An added assertion decodes the actual preview and checks the 256 MiB reader
budget independently. No product rendering, reader limit or golden changes.
The full-resolution export scenarios receive the existing plot-export 240-second
allowance after an initial local 120-second timeout (retained in light.log).

Both downloaded preview PNGs were decoded successfully by Qt locally.

The Windows golden capture's amino PNG is byte-identical to the reviewed oracle:
09fd47608900a71230894cdbbf3272d96379f4325ba6518a828e54944e10f746
The CI golden report has no drift. See windows-files.log and ci-golden-report.json.

Local final light/default and dark/large-font real Qt/R drives both PASS with
the separate preview check and exact export dimensions; strict Ty PASS.
