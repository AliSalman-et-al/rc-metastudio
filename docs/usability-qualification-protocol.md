# Observed usability qualification for 0.5.0

Issue [#498](https://github.com/AliSalman-et-al/rc-metastudio/issues/498) requires observed sessions with researchers new to RC MetaStudio and experienced meta-analysts. Automated tests and agent-operated probes do not count as participant sessions.

Use the exact release-candidate package on a supported desktop. Record its archive SHA-256, application/backend versions, operating system version, display size and scaling, input device, and any assistive technology used. Do not record private study data; use the packaged sample project or a public fixture. Give each participant the task, then observe without demonstrating the path first. Record the actions taken, the visible result, any incorrect scientific interpretation, errors, recovery attempts, and whether help was needed. Keep the participant's own words separate from the observer's interpretation.

## Tasks

| Participant | Task | Observe |
| --- | --- | --- |
| Researcher new to RC MetaStudio | Import the provided CSV, map study columns, resolve a flagged row, run a standard analysis, identify the pooled effect and excluded studies, save the project, reopen it, and export a figure. | Whether the task is completed correctly, where labels or error messages cause confusion, whether the saved result and exported figure are found without prompting, and whether numerical meaning is understood. |
| Experienced meta-analyst | Open a provided project, inspect eligibility, exclude a study, run a sequential analysis and a supported subgroup or meta-regression, compare the result with the supplied reference, edit a figure's appearance, save/reopen, and export the retained figure. | Whether method and measure choices are understood, whether study order and exclusions remain visible, whether unavailable methods are interpreted correctly, and whether numerical results and figure edits survive the intended workflow. |

Exercise keyboard-only navigation and the platform assistive-technology path with the same package. Capture the control names, focus order, announced status/errors, and any task blocked by missing access. Include a narrow-window/high-scaling pass and recovery from one invalid input or interrupted analysis. Use the package's own evidence output for worker completion and saved-result identity; compare numerical values against a pinned authority fixture rather than estimating them from a screenshot.

The release record should link to each session's dated observations and package hash, list all blockers and their disposition, and identify the exact retest after a fix. If a participant group, platform, or task has not been observed, mark that part of #498 outstanding. Do not promote the release on the strength of a simulated session.
