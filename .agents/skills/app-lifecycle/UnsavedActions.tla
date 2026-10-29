------------------------ MODULE UnsavedActions ------------------------
EXTENDS TLC
CONSTANT Mutation
VARIABLES phase, initiallyDirty, choice, saveResult, authorized
vars == <<phase, initiallyDirty, choice, saveResult, authorized>>
Init == /\ phase = "Requested" /\ initiallyDirty \in BOOLEAN
        /\ choice = "None" /\ saveResult = "None" /\ authorized = FALSE
CheckClean == /\ phase = "Requested" /\ ~initiallyDirty
              /\ phase' = "Allowed" /\ authorized' = TRUE
              /\ UNCHANGED <<initiallyDirty, choice, saveResult>>
Prompt == /\ phase = "Requested" /\ initiallyDirty /\ phase' = "Prompt"
          /\ UNCHANGED <<initiallyDirty, choice, saveResult, authorized>>
Cancel == /\ phase = "Prompt" /\ phase' = "Aborted" /\ choice' = "Cancel"
          /\ UNCHANGED <<initiallyDirty, saveResult, authorized>>
Discard == /\ phase = "Prompt" /\ phase' = "Allowed" /\ choice' = "Discard"
           /\ authorized' = TRUE /\ UNCHANGED <<initiallyDirty, saveResult>>
ChooseSave == /\ phase = "Prompt" /\ phase' = "Saving" /\ choice' = "Save"
              /\ UNCHANGED <<initiallyDirty, saveResult, authorized>>
SaveReturns == /\ phase = "Saving" /\ phase' = "Decide"
               /\ saveResult' \in {"Cancelled", "Failed", "Installed"}
               /\ UNCHANGED <<initiallyDirty, choice, authorized>>
Decide == /\ phase = "Decide"
          /\ authorized' = (saveResult = "Installed" \/
                            (Mutation = "allow-cancelled-save" /\ saveResult = "Cancelled"))
          /\ phase' = IF authorized' THEN "Allowed" ELSE "Aborted"
          /\ UNCHANGED <<initiallyDirty, choice, saveResult>>
Done == /\ phase \in {"Allowed", "Aborted"} /\ UNCHANGED vars
Next == CheckClean \/ Prompt \/ Cancel \/ Discard \/ ChooseSave \/ SaveReturns \/ Decide \/ Done
AuthorizeOnlyWithConsent == authorized =>
    (~initiallyDirty \/ choice = "Discard" \/ (choice = "Save" /\ saveResult = "Installed"))
======================================================================
