# ProjectSave

TLC reached 11 states and 18 steps. The chart draws 10 states and 14 arrows.
The chart does not draw 4 steps that stay in one chart state.

## ReportInstalled breaks
The shortest path has 7 steps:
0. Validate input
1. prepare a sibling temporary file: Temporary file created
2. write the project archive: Archive written
3. flush buffered data: File flushed
4. synchronize the file: File synchronized
5. reopen and validate the archive: Temporary archive validated
6. atomically replace the destination: New project installed
7. directory open, sync or close fails: Installed but reported failed

## Rules that hold
PreservePrevious, InstallOnlyValidated, NoDeadlock
