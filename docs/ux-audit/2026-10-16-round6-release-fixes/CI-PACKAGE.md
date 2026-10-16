# Windows package qualification: report and style observations

At source/test head 035ebd3, run 38828597592 / job 116742050548 completed all
packaged project, edit, analysis, locale, save/reopen, scaled-surface and normal
entry-point processes with exit zero. Final evidence inspection failed. Original
job log and diagnostics ZIP remain under raw/lexer/package-035ebd3*.

The approved c62df31 source and its separately installed RCMetaR were exercised
through the ordinary AnalysisSetupDialog with default parameters, for amino and
BCG. Current 035ebd3 source was exercised identically. **Every report string
matches exactly**, including references, weights and the full numerical summary.
The actual Windows amino report differs only by the platform's `t²` spelling of
`τ²`. The release intentionally changed the heterogeneity columns to Q / df /
p-value / I² / tau²; its package hash constants still describe the old report.

The existing normalizer handled only tau² before Q in the old header. The new
case must recognize the exact reordered heterogeneity header, preserving every
number and all unrelated tau text. The frozen package presentation identities
are derived from the approved c62df31 reports, after that glyph canonicalization:

| Sample | Old package presentation identity | Approved release identity |
| --- | --- | --- |
| amino.rcms | d37d0aa920c9ae2397b1c44d3fbe9f91d5d89b61fad43ced991148f2e51245d0 | 61ea84ba73eab657282ceabdf3ee1f29ab0ed55a1be574023017bc490d279ab5 |
| BCG.rcms | 2cb1cb0b867b7280a8843f633a9a040f7810d4c9e0ab91ff6333d8110fc41933 | b47d4f5347252350c0c6a5507221a41c3a65bbbedacfe34e0dd164c5f75c93cb |

The normalizer's numerical sensitivity, frozen numerical contracts, golden ZIP,
tolerances, source defaults and report production stay unchanged. Exact snapshots
and their provenance are retained in CI-PACKAGE-IDENTITIES.json. This is a package
presentation identity correction to the already approved release, not a new
numerical oracle or a golden refresh.

The surface observer also reads the unnamed `_ControlStyle` proxy's objectName.
The real proxy delegates to a named native base style (Fusion locally; Windows
style in the actual package). Observe QProxyStyle.baseStyle().objectName() rather
than emitting an empty proxy name. Keep the inspector's nonempty active style,
qwindows platform, plugin, locale, DPR, cleanup and output requirements intact.
No product style or UI behavior needs changing. Empty top-level accessibility
labels are observed but are not a failed gate; this repair does not change that
contract.

Before implementation, package-style-before exits 1 on the real Qt observation;
package-identity-before exits 1 after establishing exact approved-vs-Windows text
apart from the single tau glyph. Both raw command receipts/transcripts remain.
The isolated failure list precedes repair in raw/lexer/PACKAGE-DIAGNOSIS.md.
Actual final-head Windows package CI, including exact-archive reinspection, remains
required even after local source-hook/inspector checks pass.


Post-fix replays pass: the identical native-style assertion, both canonical report
identities, unchanged actual Windows workflow record, and ordinary source surface
hooks at all three scales. Strict goldens and 415 exact fields pass again; the
source/packaging sweep passes 891 tests with 16 existing skips. The extended
comparator case failed before the normalizer change. The failed original package
record is preserved; actual final-head Windows package qualification is separate.
