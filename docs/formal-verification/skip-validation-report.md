# ProjectSave

TLC reached 14 states and 23 steps. The chart draws 10 states and 15 arrows.
The chart does not draw 6 steps that stay in one chart state.

## InstallOnlyValidated breaks
The shortest path has 5 steps:
0. Validate input
1. prepare a sibling temporary file: Temporary file created
2. write the project archive: Archive written
3. flush buffered data: File flushed
4. synchronize the file: File synchronized
5. atomically replace the destination: New project installed

## Rules that hold
PreservePrevious, ReportInstalled, NoDeadlock
