# Cancel-path focus correction

Merged origin/master (#546) before local qualification. Strict repository-wide Ty
(target win32, on Linux) passed before and after the edit; commands are in typing logs.
Both requested scenarios passed before and after the edit on Linux offscreen Qt/R.
The reported Windows entered-binary QMessageBox failure was not reproduced here;
that scenario runs in a separate process through advanced_workflows.calculators,
not the baseline calculator function changed by this PR.

The edit restores accept-only focus/event processing. Cancel records the same text
metrics and contents rectangle without changing focus. The +6pt application-font
reopen/Cancel pass and the combined width/height assertion are unchanged.

After correction: calculator-mode-entered-binary and calculator-binary exit 0;
large-font and clipped mutants each exit 1; each restoration exits 0. Exact commands,
measured scenario steps, runtime identities and manifests are retained alongside.

Earlier dispatched mutation CI runs both completed with Required Windows Desktop
E2E (2/3) and Qt6 Integration Verification Gate failing at the fit assertion:
- https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/41771909029
  Windows large font: text 212x22, contents 212x14.
- https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/41771917139
  Windows default font: text 131x14, contents 40x22.

Retained failed job log: windows-job.log. No existing assertion was weakened.
Native Windows reproduction remains unverified locally.
