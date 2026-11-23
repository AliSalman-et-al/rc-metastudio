# 0014. Preserve native window and editor contracts

## Context

Qt can defer layout and destruction across event-loop turns. Its reported
widget size and visibility can change after a controller has composed the
window. The workspace and calculators also maintain draft state while nested
dialogs and worker calls run.

## Decision

Keep the adaptive dialog's measured minimum and preferred widths separate
and owned by the application. Native QDialog can replace its minimum with
a narrower style hint in a show-time adjustSize pass. Restore the measured
contract on the next turn and let a single refit settle the geometry. Preserve
explicit widget minimums when layout hints omit them. Include native frame
decorations in screen fits. An explicit geometry provider owns the geometry
while the cached screen owns signal connections. Establish the maximized
startup state before showing a window. Reapplying it on Show can leave Cocoa
with a visible Qt widget and an unexposed native window.

Size analysis setup against the selected tab's layout. Qt's tab size hint
includes hidden pages, including those with an Ignored size policy. Allow
controls to fit the viewport while preserving the primary method selector's
readable preferred size. Disclosing Advanced options can grow the dialog
without changing its placement.

Results pages scroll within the available pane so their content cannot push
navigation off-screen. Establish a usable splitter width on creation, then
apply stored proportions after the first native layout. Flush lazy splitter
geometry before a queued refit. Compute overflow against the full viewport
before reserving scrollbar space to avoid oscillation. Stop rendering before
a nested modal loop can deliver deferred deletion. A TSA replacement keeps
the existing navigation entry and changes its scene item and export artifact
together.

Keep wizard draft inputs on Back because Qt otherwise resets registered
fields. In binary back-calculation, a nested choice shares the calculator's
transaction. Cancel leaves the table and its copied model untouched.
Continuous back-calculation may probe both metric-specific assumptions to
determine availability, and commits the selected one after user acceptance.
Use SE to reconstruct a missing SD since an already populated SE cell can
itself be derived. An unchanged diagnostic edit may emit no cellChanged
signal. A rejected edit that restores valid data keeps OK available.
