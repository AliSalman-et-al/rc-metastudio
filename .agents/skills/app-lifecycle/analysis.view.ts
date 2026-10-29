import { step } from "./app.view.ts";
export { step };
export const title = "RC MetaStudio - analyses, results and exports";
export const state = (v) => ({None: "No active result", Setup: "Analysis settings", Running: "R analysis", Results: "Report, tables and figures", Editor: "Plot editor", Export: "Report, table or figure export"})[v.result];
