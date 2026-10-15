# Native visual review

Actual inspection, not inferred from a passing assertion. Original captures remain unmodified; contact-sheet previews resize them for comparison and open full resolution on click. NATIVE.json and SCREENSHOTS.json bind provenance and hashes. This is implementation inspection, not the independent re-audit.

Inspected during implementation:

- All three native IRR context figures from native-freeze-audit-round3-irr-context: entered events, catheter-days, group headings, row labels, weight/interval columns, sensible log ticks and footer clearance. Earlier BMJ group-rule/header crossing was rejected and corrected using measured multiline headers.
- Native MD report (`native-bubble-exports`, step 52): negligible Dose estimate/Z display zero at six decimals, interval and genuinely nonzero intercept retained; aligned numerical columns and readable hierarchy.
- Native diagnostic BMJ specificity at three decimals (`native-qualified-final-audit-round3-presentation-diagnostic`, step 63): no None placeholder, header/body hierarchy readable, overall-test/axis tick separated. The prior native-freeze diagnostic attempt exposed the real collision and is rejected; the unchanged geometry assertion passed after applying the text scale once.
- Native six-decimal BMJ continuous figure (`native-freeze-audit-round3-presentation-twoarm-mean`, step 84): aligned raw counts/means/SD/weights/intervals, pooled label and totals clear, footer and round ticks clear. Final explicit-text scaling is qualified again in the final native queue.
- Native start page at QT_SCALE_FACTOR=2 initially clipped its wrapped import description despite passing the old assertions. Rejected native-scale-2; accepted native-scale-2-fixed after Preferred/height-for-width layout and stronger assertions. Intentional page scrolling is distinguished from clipped label content.
- Native desktop-root funnel editor (`native-root-funnel`, step 04): caption field visible, controls/action row clear. Earlier direct-window captures with underlying plot paint-through are rejected for aesthetic acceptance; this is a capture-method distinction, not a claimed opacity fix.
- Main/setup/results and binary/continuous/diagnostic calculator frames listed in NATIVE: deliberate keyboard path, focus indication, named controls and readable labels. Measured grid contrast is recorded with the actual palette; derived cells also use italic type.

The final contact-sheet pairs and final scale/long/precision captures are reviewed after curation; acceptance is appended below. No claim covers Orca/screen readers, actual Windows/macOS OS scaling, native picker behavior, every parameter combination, or exported files not separately inspected. Decoded export checks establish format/content routing; they do not establish every exported pixel's aesthetics.
