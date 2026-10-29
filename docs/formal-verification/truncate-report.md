# ProjectSave

TLC reached 11 states and 18 steps. The chart draws 11 states and 14 arrows.
The chart does not draw 4 steps that stay in one chart state.

## PreservePrevious breaks
The shortest path has 6 steps:
0. Validate input
1. prepare a sibling temporary file: Temporary file created
2. write the project archive: Archive written
3. flush buffered data: File flushed
4. synchronize the file: File synchronized
5. reopen and validate the archive: Temporary archive validated
6. an operation fails before replacement: Previous project destroyed

## Rules that hold
InstallOnlyValidated, ReportInstalled, NoDeadlock
