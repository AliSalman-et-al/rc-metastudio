# Fable UI/UX refinement

The aim is a coherent, polished and easy-to-use research application, with the
existing features exposed clearly. Fable's screenshot review is input to this
work, not proof that every suspected defect exists. Larger interaction changes
need a concrete proposal before implementation.

## Proof obligations before changes

- A real failed analysis must leave its error and Method controls readable.
  Revealing error details may grow the dialog within the owning screen; it must
  not cover or cut off Advanced. Retain collapsed and expanded captures.
- Switching continuous calculator input modes must size visible content to the
  available screen and start pre/post inputs at the first arm. Capture before
  the driver scrolls, then prove both arms remain reachable on smaller screens.
- About must keep the wordmark readable without a white panel in dark mode,
  including a live theme change. Retain both themes.
- An executed Reitsma result must preserve the proper name in its title.
  Continuity-correction prose must use sentence-ready policy descriptions and
  retain the actual correction meaning.
- HR/IRR editable source values must retain their full accepted precision.
  Do not round source fields merely to make them shorter. Existing precision,
  save/reopen and public-reference comparisons remain authoritative.
- Report table layout must retain every row and quantity. Verify suspected
  regression omissions and alignment against executed objects before changing
  them. Check editable Word and rendered paper, not XML alone.

Use real Qt/R E2E observations and retained before/after evidence. Run strict
Windows typing before GUI qualification. Stop editing executable inputs before
the final matrix. Interrupted earlier matrices do not qualify v0.5.5.

## First concrete corrections

The native `ui-fable-polish` drive reproduced About's white panel, both pre/post
arm visibility failures, clipped Method controls with collapsed/expanded errors,
and the Reitsma title/correction wording. Failed evidence is retained at
`artifacts/verification/rcms/20261115T163307Z-b3e7eb35-ui-fable-polish/`.

The corrected drive passed at
`artifacts/verification/rcms/20261115T163524Z-24505332-ui-fable-polish/`:
pre/post opens at scroll position zero with both tables visible; error disclosure
grows within the screen; About renders a transparent monochrome wordmark on dark
backgrounds; executed titles retain Reitsma and policy text fits a sentence.
Strict win32 typing preceded each run. The installed test-owned RCMetaR library
was rebuilt at 0.5.5. These are Windows native source checks, not release-package
or other-platform qualification.

The existing dialog behavior suite passed 88 checks after updating its obsolete
assumption that an explicit pre/post mode change must retain summary-mode height.
Edits after the mode change still preserve settled geometry. Both transcripts
are retained under `artifacts/verification/ui-fable-2026-11-15/`.

HR/IRR source-field precision remains unchanged: the proposed six-significant-
digit rounding would lose original scientific input. The pre/post screenshot's
intentional scroll did not prove an initial defect, but a fresh native run did
confirm that mode changes were not requesting a content refit.
