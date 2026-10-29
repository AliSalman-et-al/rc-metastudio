------------------------- MODULE ProjectSave -------------------------
EXTENDS TLC
CONSTANT Mutation
VARIABLES phase, disk, validated, installed
vars == <<phase, disk, validated, installed>>
Init == /\ phase = "Input" /\ disk = "Previous" /\ validated = FALSE /\ installed = FALSE
Prepare == /\ phase = "Input" /\ phase' = "Temporary"
           /\ UNCHANGED <<disk, validated, installed>>
Write == /\ phase = "Temporary" /\ phase' = "Written"
         /\ UNCHANGED <<disk, validated, installed>>
Flush == /\ phase = "Written" /\ phase' = "Flushed"
         /\ UNCHANGED <<disk, validated, installed>>
Sync == /\ phase = "Flushed" /\ phase' = "Synced"
        /\ UNCHANGED <<disk, validated, installed>>
Validate == /\ phase = "Synced" /\ phase' = "Validated" /\ validated' = TRUE
            /\ UNCHANGED <<disk, installed>>
Replace == /\ (phase = "Validated" \/ (Mutation = "skip-validation" /\ phase = "Synced"))
           /\ phase' = "Installed" /\ disk' = "New" /\ installed' = TRUE
           /\ UNCHANGED validated
FailBeforeReplace == /\ phase \in {"Input", "Temporary", "Written", "Flushed", "Synced", "Validated"}
                     /\ phase' = "Failed"
                     /\ disk' = IF Mutation = "truncate" /\ phase = "Validated" THEN "Corrupt" ELSE disk
                     /\ UNCHANGED <<validated, installed>>
ConfirmDurability == /\ phase = "Installed" /\ phase' = "Saved"
                     /\ UNCHANGED <<disk, validated, installed>>
DurabilityFailure == /\ phase = "Installed"
                     /\ phase' = IF Mutation = "misclassify" THEN "Failed" ELSE "Uncertain"
                     /\ UNCHANGED <<disk, validated, installed>>
Done == /\ phase \in {"Failed", "Saved", "Uncertain"} /\ UNCHANGED vars
Next == Prepare \/ Write \/ Flush \/ Sync \/ Validate \/ Replace \/ FailBeforeReplace
        \/ ConfirmDurability \/ DurabilityFailure \/ Done
PreservePrevious == ~installed => disk = "Previous"
InstallOnlyValidated == installed => validated
ReportInstalled == phase = "Failed" => ~installed
=====================================================================
