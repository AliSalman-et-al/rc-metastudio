# UnsavedActions

TLC reached 13 states and 17 steps. The chart draws 10 states and 11 arrows.
The chart does not draw 6 steps that stay in one chart state.

## AuthorizeOnlyWithConsent breaks
The shortest path has 4 steps:
0. Action requested with unsaved work
1. ask what to do with unsaved work: Await save, discard or cancel decision
2. you choose to save: Try saving the current project
3. you cancel the save picker: Save picker cancelled
4. decide whether to continue: Action incorrectly allowed without saving

## Rules that hold
NoDeadlock
