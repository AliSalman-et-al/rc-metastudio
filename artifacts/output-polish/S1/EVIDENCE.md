# I² display precision

The BCG leave-one-out forest always uses one decimal in the I² column and footer. At requested digits 2, the all-studies row changes from 92.12% to 92.1%, and the Aaronson omission changes from 92.74% to 92.7%. At digits 4, the same column still uses one decimal, and the footer keeps four decimals for Q and τ².

- The digits 2 and 4 leave-one-out screenshots and SVGs are local evidence, regenerable with `uv run python artifacts/output-polish/S2/drive.py`.
- The BMJ RD footer changes from 95.66% to 95.7%. [Before](../S2/before/07-0-RD-bmj-2.png) and [after](../S2/after/07-0-RD-bmj-2.png)
- Factor meta-regression Results changes from 22.15% to 22.2% in Word. The four-digit regression likewise reports 22.2%. The DOCX, PDF and HTML exports are local evidence, regenerable with `uv run python artifacts/output-polish/S2/drive.py`. [Before Word](before/word-results.jpg), [after Word](after/word-results.jpg)

The [shared native drive](../S2/EVIDENCE.md) records the commands and runtime identity. For Word, open `factor-2.docx` from each run’s `workflow` directory at 100% zoom and scroll to Results.
