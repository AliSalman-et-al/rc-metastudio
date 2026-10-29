----------------------------- MODULE App -----------------------------
EXTENDS TLC
VARIABLES main, document, result, intent
vars == <<main, document, result, intent>>
Init == /\ main = "Workspace" /\ document = "Empty"
        /\ result = "None" /\ intent = "New"
Request == /\ main = "Workspace"
           /\ intent' \in {"New", "Open", "Import", "Close"}
           /\ main' = IF document = "Dirty" THEN "Prompt" ELSE "Authorized"
           /\ UNCHANGED <<document, result>>
Discard == /\ main = "Prompt" /\ main' = "Authorized"
           /\ UNCHANGED <<document, result, intent>>
Cancel == /\ main \in {"Prompt", "Wizard", "Opening", "Saving", "SavingBeforeAction"}
          /\ main' = "Workspace" /\ UNCHANGED <<document, result, intent>>
SaveFirst == /\ main = "Prompt" /\ main' = "SavingBeforeAction"
             /\ UNCHANGED <<document, result, intent>>
Save == /\ main = "Workspace" /\ document # "Empty"
        /\ main' = "Saving" /\ UNCHANGED <<document, result, intent>>
SaveInstalled == /\ main \in {"Saving", "SavingBeforeAction"}
                 /\ main' = IF main = "SavingBeforeAction" THEN "Authorized" ELSE "Workspace"
                 /\ document' = "Clean"
                 /\ UNCHANGED <<result, intent>>
Continue == /\ main = "Authorized"
            /\ main' = CASE intent \in {"New", "Import"} -> "Wizard"
                         [] intent = "Open" -> "Opening"
                         [] OTHER -> "Closed"
            /\ UNCHANGED <<document, result, intent>>
Create == /\ main = "Wizard" /\ main' = "Workspace" /\ document' = "Dirty"
          /\ UNCHANGED <<result, intent>>
Open == /\ main = "Opening" /\ main' = "Workspace" /\ document' = "Clean"
        /\ UNCHANGED <<result, intent>>
Edit == /\ main = "Workspace" /\ document # "Empty" /\ document' \in {"Clean", "Dirty"}
        /\ UNCHANGED <<main, result, intent>>
Setup == /\ main = "Workspace" /\ document # "Empty" /\ result \in {"None", "Results"}
         /\ result' = "Setup" /\ UNCHANGED <<main, document, intent>>
Run == /\ main # "Closed" /\ result = "Setup" /\ result' = "Running" /\ UNCHANGED <<main, document, intent>>
AnalysisFailed == /\ main # "Closed" /\ result \in {"Setup", "Running"} /\ result' = "None"
                  /\ UNCHANGED <<main, document, intent>>
AnalysisSucceeded == /\ main # "Closed" /\ result = "Running" /\ result' = "Results"
                     /\ UNCHANGED <<main, document, intent>>
EditPlot == /\ main # "Closed" /\ result = "Results" /\ result' = "Editor" /\ UNCHANGED <<main, document, intent>>
ReturnToResults == /\ main # "Closed" /\ result \in {"Editor", "Export"} /\ result' = "Results"
                   /\ UNCHANGED <<main, document, intent>>
Export == /\ main # "Closed" /\ result = "Results" /\ result' = "Export" /\ UNCHANGED <<main, document, intent>>
CloseResults == /\ main # "Closed" /\ result = "Results" /\ result' = "None" /\ UNCHANGED <<main, document, intent>>
Done == /\ main = "Closed" /\ UNCHANGED vars
Next == Request \/ Discard \/ Cancel \/ SaveFirst \/ Save \/ SaveInstalled \/ Continue
            \/ Create \/ Open \/ Edit \/ Setup \/ Run \/ AnalysisFailed \/ AnalysisSucceeded
            \/ EditPlot \/ ReturnToResults \/ Export \/ CloseResults \/ Done
=====================================================================
