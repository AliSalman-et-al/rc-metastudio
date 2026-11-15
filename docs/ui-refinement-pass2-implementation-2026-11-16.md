# Second UI refinement pass

Fable's directions are in `ui-refinement-pass2-fable-2026-11-16.md`. The first
implementation is commit `dbd42e1a`. Existing user decisions remain binding:
solid icons, plus/minus sequential-analysis symbols, upright numbers, original
coloured logo in both themes, far-right status-bar confidence control, native
palettes and producer precision.

## Acceptance selected before implementation

Extend the existing real Qt/R `ui-design-direction` workflow to prove that
Ctrl+M reaches Manuscript and Ctrl+1 returns to the first figure, inactive
navigation selection stays visible, editor fields share a column, wizard context
persists and Word headings/table spacing follow the same typography. Retain the
existing exact scientific values, clipboard, report-retention and export checks.
Run the transactional calculator geometry and keyboard checks at large, medium
and small screen sizes. Inspect the native whole-app tour in both themes.

## Implemented direction

- R1–R12: shared editor label columns; arm vocabulary; Add study form; visible
  inactive selection; small-study identity facts; common heading vocabulary;
  compact τ² label with explanatory tooltip; grouped Results menu and manuscript
  shortcut; Word font/spacing fixes; quiet RevMan table; IRR labels; shell menus.
- R13–R19: compact table frame; calculator section order; one import-preview
  frame; wizard context band; compact Home buttons; colour swatches alongside
  native buttons; moderator identity.
- R20 takes Fable's explicitly offered smaller alternative: keep the established
  format combo, add “as”, and explain DOCX on the report action.
- C1, C2, C4, C5: empty-sheet guidance, Results jump keys, recent-project modified
  dates, and small-study context without an extra box.
- C3 is limited to continuous summary cells whose existing supplied-value role
  explicitly identifies a computed value. No provenance is inferred from a
  number or column heading.

## Qualification and simplification

The first native direction run caught a shadowed `Pt` import in Word export;
it was fixed before the next run. Focused GUI checks: 201 passed. Native direction
workflow: `20261115T211309Z-487afb34-ui-design-direction`, passed. Native tour
and pre-push evidence retain their individual outcomes.

The pre-push code-health gate found accumulated changed-code complexity across
report parsing/formatting, SVG clipping and a few Qt presentation functions.
Before changing those functions, the failure cases to preserve are: malformed
quantity input must still fail; raw numeric quantities and display strings must
stay paired; subgroup test degrees of freedom must stay separate; report order,
labels and precision must remain identical; SVG intersections must preserve
caller clipping and empty rectangles; split figures must keep captions clear;
calculator modes and native keyboard/focus transitions must survive.

Existing fast contract tests, real R/public-reference/golden comparisons,
report-retention and split-figure E2E, calculator transaction E2E, and the native
tour cover these obligations. Simplify the production functions; do not change
code-health exceptions, statistical goldens or tolerances to obtain a pass.

The simplification in `d3170cd1` passed the complete pre-push lane: unchanged
code-health gate, 557 fast/contract checks (one platform skip), 401 GUI checks and
144 packaging contracts (two platform skips). The native tour
`20261115T212553Z-d5f03ac8-ui-crawl` passed 312 steps; its 492 artifact hashes
match. The R package checks, deterministic Reitsma visual checks and ten bridge
tests passed, but the full profile `20261115T212552Z-420c2cc7-complete` was
interrupted during desktop qualification to fix two visual findings. It must not
be reported as a completed full qualification.

The parent visual review found an empty column in the editor Axes grid and a
native Windows selection painter that ignored the inactive palette. The native
acceptance was strengthened before the corrections: selected-row paint failed
with 0 of 6750 pixels in the configured highlight colour. After a selection-only
native-palette style, 6463 of 6750 pixels matched. The axis fields now occupy
column 1 in a standard Axes group. `20261115T215440Z-710a24f4-ui-design-direction`
passes the selection-paint and extended field-alignment checks. The full tour now
checks these rendered states in both themes as well.

Fable's first final-review attempt failed at its provider with HTTP 502 before
returning a review. A new review is required; this failure is not an approval.
