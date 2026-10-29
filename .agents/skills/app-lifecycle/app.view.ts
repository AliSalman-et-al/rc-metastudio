export const title = "RC MetaStudio - projects and workspace";
export const state = (v) => ({Workspace: "Workspace", Prompt: "Unsaved changes prompt", Authorized: "Project action allowed", Wizard: "New dataset or CSV wizard", Opening: "Open project", Saving: "Save project", SavingBeforeAction: "Save before replacing or closing", Closed: "Main window closed"})[v.main];
export const step = (action, from, to) => action === "Continue"
  ? ({New: "you start a new dataset", Import: "you import CSV or Excel data", Open: "you open a project", Close: "you close the main window"})[from.intent]
  : ({
  Request: "you request New, Open, Import or Close", Discard: "you discard changes",
  Cancel: "you cancel or the operation fails", SaveFirst: "you choose Save",
  Save: "you save or Save As", SaveInstalled: "the file is installed, possibly with a durability warning",
  Continue: "you continue the selected project action", Create: "you finish creating or importing",
  Open: "the validated project opens", Edit: "you edit, calculate, change selection, undo or redo",
  Setup: "you choose an analysis or change result settings", Run: "you run the selected method",
  AnalysisFailed: "you cancel settings or analysis or display fails", AnalysisSucceeded: "results open",
  EditPlot: "you edit a supported figure", ReturnToResults: "you finish, cancel or recover from failure",
  Export: "you export a report, table or figure", CloseResults: "you close results", Done: "the main window stays closed",
})[action] ?? action;
