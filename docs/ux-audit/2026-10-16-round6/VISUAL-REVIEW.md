# Native visual inspection

The original sixty images in SCREENSHOTS.json were viewed in eight inspection
montages (`raw/inspect-0.png` through `raw/inspect-7.png`). These were inspection
aids; the contact sheet retains original PNGs and their helper provenance.

The first curation exposed two misleading frames: the mean submenu had closed
when its parent window was raised, and the bubble editor obscured the figure.
The drivers now capture the actual open popup and actual result figure. The
replacement metric-label, visible-legend, tiny-SD and wrapped-header after-images
were also opened individually at full size.

- The tiny SD is visible as `1e-05`; the native helper proves the stored number
  after Accept, Save and reopen rather than relying on the screenshot.
- The open one-arm submenu says `Mean`, without the internal TX prefix.
- Dense subgroup caps fit inside the study rows. The retained SVG check measures
  caps against matched horizontal intervals in the display and export.
- Wrapped BMJ arm headings have clear rules and superheadings. Three actual name
  pairs are measured across all styles, including unequal wrapping.
- Diagnostic six-digit output uses readable fitted-scale headings. Two-digit
  sequential/subgroup SEs have a separate observable formatting assertion.
- The visible bubble legend contains the displayed regression component; hidden
  confidence/prediction components have no entries.
- The native forest pairs show natural, evenly spaced proportion and diagnostic
  axes in each style; ratio ticks retain logarithmic spacing and natural labels.
  Coordinate checks prove this independently of appearance.

Native transformed-proportion export inspection additionally caught a BMJ footer
collision after adding the natural zero tick. The physical device-width fix
passed the unchanged geometry check for four measures, three styles and four
export formats. A failed full attempt interrupted while this was corrected is
retained and is not qualification.

These observations establish the exercised Linux Qt surfaces. They do not
establish screen-reader behaviour, other operating systems, native OS pickers,
every data/parameter combination or every raster pixel.
