# UI/UX rewrite design decisions

Design interview completed and shared understanding confirmed on September 29, 2026. The [UI/UX audit and rewrite blueprint](ui-ux-audit-rewrite-plan-2026-09-29.md), amended by the decisions below, is the agreed implementation specification. These decisions take precedence where they differ from the blueprint; the preserved source document records audit observations, not verified facts about the current checkout.

## Agreed scope

- Implement the complete blueprint incrementally, with all agreed workflows fully working in the final outcome. Incremental releases do not reduce the final scope.
- Preserve existing supported analytical workflows throughout delivery.
- Design defaults for researchers who understand meta-analysis but are new to RCMS. Show scientific choices explicitly and keep advanced settings available.
- Preserve saved analyses as self-contained records, as specified in ADR 0014.
- Qualify Windows, macOS, and Ubuntu, as specified in ADR 0015.
- Hardware coverage is Windows x64, Apple silicon macOS, and Ubuntu x64. Intel macOS and ARM Ubuntu are outside this release scope.
- Automatically retain completed runs, including partial results, in the open project. Mark the project unsaved and persist through normal Save; allow explicit deletion and never silently replace an earlier run.
- Save unfinished analysis drafts with the project. Unsaved draft changes participate in the same Save / Discard / Keep editing decision as dataset changes.
- Include step-level failure isolation for cumulative and leave-one-out analyses, with numerical verification. Preserve the selected estimator, retain failed steps with reasons, and label incomplete results; statistical defaults remain unchanged.
- Optimize the end-user experience for clear analysis context, recovery without lost work, and discoverable actions. Validate the resulting interactions rather than treating visual polish alone as success.
- Permit data editing, draft configuration, and inspection of previous results during execution. Each run uses frozen inputs and identifies when relevant working data have subsequently changed.
- Allow one active analysis initially, without an analysis queue. Keep the active run and Stop action discoverable.
- Closing a project during execution offers Keep project open or Stop analysis and close. Stop first, then resolve unsaved changes through the normal save prompt; preserve the draft and prior results, and do not leave invisible work running.
- Recover unsaved data and drafts from a separate local recovery snapshot without overwriting the saved project. Offer recovery with a timestamp and preview; intentional Discard must invalidate the discarded recovery state.
- Never silently exclude studies with missing required analysis inputs. Identify affected studies and reasons, allow correction or explicit acceptance of exclusions where the method permits them, and preserve the choice in the analysis record.
- Require a visible ordering choice for new cumulative analyses. Offer year ordering, display the actual sequence, and resolve ties and missing years explicitly. Preserve existing order for migrated analyses; display sorting never changes analytical order.
- Save available generated figures with numerical results so projects remain viewable on another computer without R. Distinguish viewing/exporting a stored figure from regeneration, which requires a compatible statistical engine.
- Save presentation settings separately from the immutable scientific record. Changing plot colors, labels, or dimensions does not create a new analysis execution, refit the model, or alter numerical results.
- Adopt the blueprint's Data / Results workspace, retained analysis editor, and restrained native desktop appearance. Keep analysis context and primary actions visible, use native numerical tables, and provide family-specific reading orders. Validate keyboard use, small screens, and error recovery alongside visual design.

## Platform versions and acceptance

- Retain Windows 10 version 1809 as the Windows minimum and macOS 14 as the macOS minimum. Qualify Ubuntu 24.04 and 26.04 LTS on x64.
- Implement the blueprint's family-specific results, import improvements, accessibility requirements, and verification requirements, subject to the amendments above.
- Completion requires numerical parity, working end-to-end journeys, safe persistence and recovery, and native evidence from actual packaged applications on the declared platforms. CI runner selection alone does not establish platform support.
- Unavailable verification remains explicitly outstanding; it cannot be reported as passed.
- Resolve routine layout and implementation choices autonomously. Return changes to scientific behavior or agreed scope to the user.

## Status

The design interview is complete. Implementation and acceptance verification remain outstanding; this record does not certify either. Before implementation, verify source findings against the current checkout and use the existing release-oracle and statistical-authority ADRs.
