# Trial Sequential Analysis: methods research

This note collects the statistical methods behind Trial Sequential Analysis
(TSA) for the planned RC MetaStudio TSA layer. In that layer, metafor fits each
cumulative step, gsDesign supplies Lan-DeMets boundaries, and only the
TSA-specific formulas are ours. Every formula below cites a primary source.
Anything that a primary source could not confirm is marked **UNVERIFIED**.

Research date: 2026-11-18.

## Sources and how they were read

| Key | Source | How it was read |
|---|---|---|
| CTU | Thorlund K, Engstrøm J, Wetterslev J, Brok J, Imberger G, Gluud C. *User manual for Trial Sequential Analysis (TSA)*. Copenhagen Trial Unit, 2017 (ships with TSA 0.9.5.10 Beta) | Full text extracted with `pdftotext`. Page numbers are the printed page numbers. The Greek symbols are lost in extraction, so formulas were rebuilt from the surrounding text and checked numerically where possible. TSA.jar and lib were **not** opened. |
| CTU-sample | `TSA 0.9.5.10 Beta/samples/High perioperative oxygen SSI.TSA` | A plain-text data file (inputs only, no outputs). |
| W2008 | Wetterslev J, Thorlund K, Brok J, Gluud C. *J Clin Epidemiol* 2008;61:64-75 | Abstract only (Europe PMC). |
| W2009 | Wetterslev J, Thorlund K, Brok J, Gluud C. Estimating required information size by quantifying diversity in random-effects model meta-analyses. *BMC Med Res Methodol* 2009;9:86 (PMC2809074) | Full text through a fetch tool. The equations are images, so equation numbers and the surrounding text were used. |
| W2017 | Wetterslev J, Jakobsen JC, Gluud C. Trial Sequential Analysis in systematic reviews with meta-analysis. *BMC Med Res Methodol* 2017;17:39 (PMC5397700) | Full text through a fetch tool, including the appendix formulas. |
| B2008 / B2009 | Brok J et al. *J Clin Epidemiol* 2008;61:763-9; *Int J Epidemiol* 2009;38:287-98 | Abstracts only. |
| T2009 | Thorlund K et al. *Int J Epidemiol* 2009;38:276-86 | Not retrieved. Cited only through CTU. |
| P&Y1997 | Pogue J, Yusuf S. *Control Clin Trials* 1997;18:580-93 | Abstract, plus CTU's summary (CTU p.30). |
| Hu2007 | Hu M, Cappelleri JC, Lan KKG. *Clin Trials* 2007;4:329-40 | Abstract (Europe PMC). |
| Lan2003 | Lan KKG, Hu M, Cappelleri JC. *Statistica Sinica* 2003;13:1135-45 | Index page only, because the full text is gated. Its formula details come from CTU §2.2.6. |
| Imb2016 | Imberger G, Thorlund K, Gluud C, Wetterslev J. *BMJ Open* 2016;6:e011890 (PMC4985805) | Full-text XML (Europe PMC). |
| K&W2014 | Kulinskaya E, Wood J. Trial sequential methods for meta-analysis. *Res Synth Methods* 2014;5:212-20 | Abstract fragments only. Its arguments are summarised through W2017 and the RTSA vignette. **Full text UNVERIFIED.** |
| CSC2017 | Cochrane Scientific Committee. *Review of approaches to cumulative meta-analyses*, July 2017 | Full PDF. |
| RTSA | RTSA, GitHub `AnneLyng/RTSA` commit `dc13c0b` (2024-08-07), and the CRAN 0.2.2 binary | R source, vignettes, and runs of the CRAN binary. |
| tsahr | tsahr 0.2.8.17 (CRAN binary) | README, help pages, and deparsed R functions. |
| gsDesign | gsDesign 3.11.0, help pages `sfLDOF`, `gsDesign`, `gsBound` | Installed help, plus numerical runs. |
| ldbounds | ldbounds 2.0.2 (an R port of the Reboussin et al. Lan-DeMets program that CTU cites, CTU p.44 ref 60) | Numerical comparison. |

All numerical checks used R 4.6.1 with a throwaway library. The scripts are in
[Appendix A](#appendix-a-reproduction-scripts).

---

## 1. Required information size (RIS) and the information axis

### 1.1 Binary outcomes (RR, RRR, OR, RD, Peto OR)

**Formula (CTU p.24, eq. (1)):**

```
IS_patients = 2 · (z_{1-α/2} + z_{1-β})² · 2σ² / δ²
            = 4 (z_{1-α/2} + z_{1-β})² · P̄(1-P̄) / (P_C - P_E)²
P_E = P_C (1 - RRR),   P̄ = (P_C + P_E)/2,   σ² = P̄(1-P̄),   δ = P_C - P_E
```

CTU states that using α/2 means the RIS assumes two-sided testing (CTU
p.24-25). W2017 gives the same form in its appendix: `SS = 4(Z_{1-α/2}+Z_β)²·v/θ²`
with `v = P(1-P)` and `P = (P_E+P_C)/2`. The diversity-adjusted RIS is
`RIS = [1/(1-D²)]·SS`.

**Numerical confirmation** (Appendix A, `chk1.R`). The formula reproduces the
CTU §5 values:

| CTU example | Inputs | Published | Reproduced |
|---|---|---|---|
| §5.2 smoking cessation (p.87-88) | P_C=14%, relative **increase** 20% (P_E=16.8%), α=5%, β=20%, no adjustment | 5218 | 5217.26 → 5217 |
| §5.3.1 CABG AF (p.90-91) | P_C=27.6%, RRR 20%, α=1%, β=10%, D²=49% | 7150 | 7150.48 |
| §5.3.1 CABG AF, low-bias RRR (p.91) | P_C=27.6%, RRR 36.9%, α=1%, β=10%, D²=49% | 1964 | 1962.43 (a D² of 49.04% gives 1964) |
| §5.5 isoniazid (p.96) | P_C=5%, RRR 25%, α=5%, β=20%, D²=20% | 10,508 | 10,507.69 |
| §5.4 CABG MI (p.95-96) | P_C=3.9%, RRR 33%, α=5%, β=20%, I²=0 | 5942 | **5971.5, rounded to 5972 in the CTU run-only probe.** RRR=1/3 gives 5841. The cause of the manual discrepancy remains unverified. |

RCMetaR rounds participant RIS half up. This matches the printed CABG AF
7150.48 → 7150 and the run-only CABG MI 5971.5 → 5972. The smoking cessation
example differs by one participant on the printed inputs.

**How each effect measure is handled:**

- **RR/RRR.** As above, in CTU and RTSA (`ris.R`: `pI <- exp(log(pC)+log(mc))`,
  `var_mc <- p*(1-p)`, `NF <- 2*(qnorm(1-alpha/side)+qnorm(1-beta))^2*2*var_mc/mc_nf^2`).
- **OR.**
  - CTU asks for two of the three fields "Relative risk reduction", "Incidence in
    Intervention Group" and "Incidence in Control Group" whatever the effect
    measure (CTU p.75). The RIS is therefore always built from P_C and P_E.
    Whether CTU converts an anticipated OR to P_E is **UNVERIFIED**; the manual
    describes only RRR or incidence input.
  - RTSA converts on the logit scale, `pI = invlogit(logit(pC)+log(OR))`, and then
    uses the same pooled-variance formula (`ris.R`).
- **RD.**
  - CTU uses the same P_C/P_E input. **UNVERIFIED** whether anything differs.
  - RTSA uses `var_mc = pC(1-pC)+p1(1-p1)` with the same `4·z²·var/δ²` multiplier.
    That is **twice** the standard two-arm total `2z²[p_C q_C + p_E q_E]/δ²`.
    For P_C=0.10, P_E=0.08, α=5% and β=20%, RTSA gives 12,841, the standard
    formula gives 6,421, and CTU's pooled-variance formula gives 6,429. This
    looks like an RTSA error. Do not use it as an oracle.
- **Peto OR.** CTU offers it as an effect measure (CTU §2.1.1 p.13, appendix 6.1
  p.101). The manual does not separate its RIS from the binary P_C/P_E input.
  RTSA does not support Peto OR.

### 1.2 Continuous outcomes: mean difference (MD)

**Formula (CTU p.24-25):** the same as eq. (1), with δ the anticipated
difference in means and σ² "the associated variance":
`IS = 4 (z_{1-α/2}+z_{1-β})² σ²/δ²`. W2017's appendix gives the
continuous-outcome sample size from the mean difference and SD; the fetched
text was garbled, so the exact appendix wording is **UNVERIFIED**.

**Where the variance comes from:**

- CTU's dialog takes "Mean difference" and "Variance" as inputs. "Low-bias
  Based" pools the low-risk-of-bias trials to estimate both. "Empirical" uses the
  pooled estimate of all trials, but only for the variance (CTU p.75).
- W2017 estimates the variance for future trials from "the weighted average of
  the pooled squared standard deviations from the fixed-effect model". Kulinskaya
  & Wood, as quoted by W2017, used "the simple unweighted average of the within
  trial variances".
- RTSA takes `sd_mc` (an SD). Its retrospective default, when `sd_mc` is
  missing, is `sd_mc = sqrt(sy$peR[6])` (or `sqrt(sy$peF[7])` when τ²=0),
  according to `RTSA.R`. That is the square root of the **variance of the
  pooled estimate**, which is a standard error rather than a participant-level
  SD. On the `eds` data this default gave RIS = 208 against an accrued N of
  1129. Do not copy this default.

### 1.3 Standardised mean difference (SMD)

- CTU: "The TSA program does not facilitate meta-analysis of SMDs. … This
  effect measure does not resonate well with most clinicians and is therefore
  prone to produce unrealistic information size requirements." (CTU §2.1.1, p.13)
- RTSA SOP vignette: "Please be aware that the TSA cannot be calculated with
  standardised mean differences (SMD)." It does not give a statistical reason.
- No primary source found here defines an SMD TSA or a default SMD effect. The
  SOP cites Norman 2003 (half an SD) and Tsujimoto 2022 (MIC in SD units "highly
  variable", no universal value) among its references for MIREDIF. That
  argues against any fixed default. **Conclusion:** CTU and RTSA do not support
  SMD TSA, and neither source supports a default SMD of 0.2.

### 1.4 Hazard ratio (HR)

Neither CTU nor RTSA supports HR. tsahr (citing Miladinovic 2013, *J Clin
Epidemiol* 66:654-9, not retrieved here) implements:

```
I_required   = (z_{1-α/2} + z_{1-β})² / (ln HR_target)²            (statistical information)
RIS_events   = I_required / (ψ(1-ψ))                                (Schoenfeld; ψ = allocation proportion)
DARIS_info   = I_required · 1/(1-D²);   DARIS_events = RIS_events · 1/(1-D²)
accrued info = Σ 1/SE_i²   (fixed-effect inverse variance, per study log-HR SE)
IF           = accrued info / DARIS_info
D²           = max(0, (v_R - v_F)/v_R), capped at 0.999
```

The source is tsahr `tsa_hr()` (deparsed). By default ψ is
`sum(N_treatment)/sum(N_total)`. With ψ=0.5 the events formula reduces to
Schoenfeld's `4(z+z)²/ln²HR`. tsahr warns that `target_HR = NA` (the observed
pooled HR) is circular.

### 1.5 Incidence rate ratio (IRR) and event rates

No TSA primary source found here covers IRR or rate outcomes (CTU, RTSA,
W2009, W2017 and tsahr do not). **UNVERIFIED / no source.**

### 1.6 Information axis and information fraction

| Axis | Required (CTU) | Accrued at step k (CTU) | Source |
|---|---|---|---|
| Participants | `IS_patients`, eq. (1) × AF | Cumulative randomised participants | CTU p.24, p.38, p.73 |
| Events | `IS_events = P_C·IS/2 + P_E·IS/2` | Cumulative events in both arms | CTU p.25 |
| Statistical information | `IS_stat = (z_{1-α/2}+z_{1-β})²/δ²` | "the reciprocal of the pooled variance", i.e. Σw (fixed) or Σw* (random) | CTU p.25-26 |

- IF = accrued ÷ required "(e.g., the accumulated number of patients divided by
  the required number of patients)" (CTU p.38).
- On the statistical-information axis CTU applies **no** separate heterogeneity
  factor. The random-effects information already includes τ², so the result is
  "only reliable to the extent the estimate of the between-trial variance is
  reliable" (CTU p.33).
- RTSA uses participants only: `timing <- subjects/RIS` with
  `subjects <- cumsum(nI+nC)`, after dropping double-zero trials (`RTSA.R`).
  With `power_adj=TRUE` (the default) RTSA also multiplies the RIS by the
  sequential-design inflation factor `root` (reported as `SMA_RIS`/`SMA_HARIS`).
  CTU does not do this. tsahr names this choice "RTSA's own
  inflated-sequential-design convention, not the no-inflation convention of the
  Copenhagen Trial Unit's TSA software" (help `tsa_hr`, Details).
- tsahr uses Σ1/SE² against `DARIS_info` (§1.4).

**Sources agree:** the binary RIS form, the participant-axis IF, and the
two-sided convention.

**Sources differ:**
- RD variance: RTSA doubles it (§1.1).
- RIS inflation by the sequential design: RTSA does it by default; CTU does not.
- Default MD variance: RTSA uses the pooled SE; CTU uses user, low-bias or
  empirical input.
- Axes: RTSA has participants only; CTU has three axes.

---

## 2. Heterogeneity adjustment: diversity D² and I²

**Definition (CTU p.26-28; W2009 §2.1-2.3, eqs 2.6, 2.8-2.11):**

```
IS_random = (v_R / v_F) · IS_fixed                         (CTU p.27; W2009 eq 2.6: N_R = A_RF·N_F)
AF = v_R/v_F = 1/(1-D²)                                    (CTU p.27-28)
D² = (v_R - v_F)/v_R = 1 - v_F/v_R                          (CTU p.28)
   = τ² / (τ² + σ²_D)                                       (W2009 eqs 2.10-2.11; RTSA required-sample-size vignette)
I² = τ² / (τ² + σ²_M)   (σ²_M = Higgins-Thompson "typical" within-study variance)
v_F = 1/Σw_i,  v_R = 1/Σw_i*,  w_i = 1/σ_i²,  w_i* = 1/(σ_i²+τ²)
```

- With equal trial weights AF = 1/(1-I²) (CTU p.27). Otherwise I²
  underestimates AF (CTU p.27). W2009 shows D² ≥ I² always, with equality "when
  and only when all the weights" are equal (W2009 §3.1, eq 3.12), and "D2 = 0 when
  and only when I2 = 0" (W2009 §3.2).
- **For any random-effects model**, "D² = (v_R − v_F)/v_R and AF = v_R/v_F"
  (CTU p.28). The estimator is the one behind the chosen model. The CTU
  Diversity tab shows I², D² and τ² for DL, SJ and BT, and DL and BT share τ²
  (CTU §4.6 p.86).
- **τ²=0 ⇒ v_R=v_F ⇒ D²=0, AF=1.** CTU: with the fixed-effect model "this
  adjustments factor is always equal to 1" (CTU p.74-75). RTSA: when τ²=0 it
  sets `fixed=TRUE` and RIS = NF (`RTSA.R`). tsahr caps D² at 0.999.
- **A priori D² for few trials.** "If we let H denote a conceptual estimate of
  D²… AF = 1/(1−H)", with H = 25%, 50% and 75% giving AF = 1.33, 2.00 and 4.00
  (CTU p.29). The manual recommends sensitivity analyses, for example a range of
  20-60% (CTU p.29). W2017: when observed D² = 0, "an expected heterogeneity
  may be used in a sensitivity analysis", for example 25%. The RTSA SOP suggests
  a predefined D² of 25-50% when the observed heterogeneity is 0%.
- **CTU's two options** (CTU p.74-75): "Model Variance Based", which uses
  v_R/v_F from the selected random-effects model, or "User Defined", an a priori
  percentage. Which one is the default is **UNVERIFIED**; the manual names no
  default.
- **W2009 worked examples (Table 2).** These check the adjustment step only;
  P_C is not given in the extracted table.

| Meta-analysis | k | I² % | D² % | RRR % | SS | HIS | DIS |
|---|---|---|---|---|---|---|---|
| Afshari 2007 | 20 | 0.0 | 0.0 | 10 | 3,317 | 3,317 | 3,317 |
| Al-Inany 2006 | 13 | 7.2 | 13.9 | 25 | 3,516 | 3,789 | 4,083 |
| Soll 1997 | 8 | 22.9 | 37.3 | 60 | 193 | 250 | 307 |
| Wetterslev & Juhl 2006 | 11 | 13.4 | 40.5 | 20 | 8,421 | 9,726 | 14,164 |
| Bury & Tudehope 2000 | 5 | 40.2 | 57.7 | 45 | 440 | 736 | 1,039 |
| Li 2007 | 23 | 61.9 | 89.9 | 10 | 31,094 | 81,466 | 306,276 |
| Meyhoff 2008 | 4 | 74.2 | 79.4 | 30 | 1,699 | 6,581 | 8,239 |

  HIS ≈ SS/(1−I²) and DIS ≈ SS/(1−D²) up to rounding of the percentages.

**Sources differ:**
- **RTSA's D²** is `1 - vw/vwR` with `vw = 1/Σ(1/σ²)` (IV, even when the
  fixed-effect pooling is MH) and `vwR` the **DL** variance. Under
  `re_method="DL_HKSJ"` (RTSA's default), `vwR` is overwritten by the HKSJ
  variance **before** D² is computed (`metaanalysis.R`, `synthesize`), so D²
  then reflects the HKSJ variance. On perioOxy, D² from DL is 0.633 (HARIS
  13,201) and from HKSJ about 0.691 (HARIS 15,688). The HKSJ variance can be
  below v_F, so D² could go negative. That is not CTU's definition.
- **RTSA's default `random_adj="tau2"`** is not a D²/I² factor. It uses a
  Kulinskaya-Wood style minimum-number-of-trials calculation (`minTrial()`,
  required-sample-size vignette):
  `τ² < K/((z_{1-α/2}+z_{1-β})²/θ² − 1/σ²_R)` and
  `RIS_new = 2σ²/(K/((z+z)²/θ² − 1/σ²_R) − τ²)`. To get the CTU behaviour, set
  `random_adj="D2"`.

---

## 3. Default anticipated effect and control event proportion

### 3.1 What the sources actually use or recommend

| Source | Anticipated effect | Control proportion |
|---|---|---|
| P&Y1997 (via CTU p.30) | Truly effective cardiovascular treatments gave RRR "10%, 15%, or – at best – 20%" | 10% mortality "may be realistic" for major vascular outcomes |
| CTU §2.2.1 (p.30-32) | Clinical experience or related areas, or a meta-analysis of **low-risk-of-bias** trials. Use **ranges**: "It is not possible to recommend one technique" | Clinical experience; ranges for sensitivity analysis |
| CTU §5 examples | 20% relative increase (p.87); 20% RRR and the low-bias RRR of 36.9% (p.90-91); 33% RRR (p.95); 25% RRR (p.96) | **Median** control proportion (p.88, 91, 95, 96) |
| W2008 abstract | Low-bias heterogeneity-adjusted IS, and an assumed 15% effect | – |
| B2008 abstract | 30% RRR, 15% RRR, and the low-bias-trial estimate | – |
| B2009 abstract | 25% RRR | – |
| Imb2016 | **10% RRR** or NNT 100. Also the RRR at the conventional 95% CI limit closest to null | "**unweighted mean** of the proportion of events in the control groups of all the included trials" |
| W2017 | "realistic and minimally important intervention effect", fixed in a peer-reviewed protocol. Post hoc: "apply the least likely intervention effect, i.e., the confidence limit of the summary estimate" closest to null | "the **pooled unweighted proportion** of outcomes in the control groups in the included trials" |
| RTSA (code) | No default. `mc` or `RRR` must be given | Retrospective default `pC = sum(eC)/sum(nC)` (pooled **crude** proportion of all trials) |
| RTSA SOP | Realistic RRR, ideally from low-risk-of-bias trials or systematic reviews | Large low-risk-of-bias trial or SR, else a large observational study, else the meta-analysis control groups |
| Continuous (CTU/W2017/RTSA SOP) | Minimal relevant difference (MIREDIF), or the low-bias pooled estimate | – |

**Explicit warnings against using the observed pooled effect:**

- CTU p.31: low-bias pooled estimates are "only reliable to the extent that
  this meta-analysis can be considered free of large random errors…, time-lag
  bias and publication bias". The manual also notes that sample size
  calculations "abound with examples… based on overly optimistic anticipated
  intervention effects" (p.31).
- W2017: parameters must be fixed in a protocol before the analysis, and
  "data-driven" choices are a recognised danger. W2017 offers the CI limit
  closest to null as a post hoc conservative alternative. (It does not ban the
  observed estimate outright.)
- tsahr: `target_HR = NA` "is circular… can make the TSA boundary collapse to
  the conventional boundary almost immediately" (README and help).
- RTSA vignette: "Using information from already conducted trials in the
  sample and trial size calculations are problematic in terms of introducing
  bias."

### 3.2 Verdict on the proposed defaults

| Proposed default | Supported? | What sources support instead |
|---|---|---|
| Ratio 0.8 (RRR 20%) | **Partly.** No source recommends a 20% RRR as a general default. It appears as one of several worked examples (CTU p.87, 90; RTSA examples use `mc=0.8`) and as P&Y's "at best" figure. W2017 mentions 20% only as an empirical power benchmark. | A protocol-specified realistic or minimally important effect, a low-bias-trial estimate, or a range. Published TSAs used 10%, 15%, 20%, 25%, 30% and 33%. Imb2016 used 10%. |
| RD = 20% of control risk | **No direct source.** It equals RRR 20% expressed on the RD scale with the same P_C. CTU builds the RD RIS from the same P_C/P_E inputs (UNVERIFIED in detail). | As for the ratio row. |
| SMD 0.2 | **Not supported.** CTU and RTSA exclude SMD TSA altogether (§1.3). | None. |
| MD = 0.2 × pooled SD | **Not supported.** No source proposes it. | MIREDIF (clinical), with the variance from user input, low-bias trials, or an empirical pooled variance (CTU p.75; W2017). |
| Control proportion = pooled control-arm proportion | **Supported, but the definitions differ.** CTU examples use the median; W2017 and Imb2016 use the unweighted mean of the trial control proportions; RTSA uses the crude pooled Σe_C/Σn_C. | Pick one definition explicitly and name it. |
| HR/IRR/OR defaults | None found. | tsahr requires `target_HR` and treats NA as circular. |

---

## 4. Monitoring boundaries

### 4.1 Spending functions

- **O'Brien-Fleming (Lan-DeMets).** CTU (p.40): `α(IF) = 2 − 2Φ(z_{α/2}/√IF)`.
  It was the only α-spending function in the CTU program (p.40) and the only
  β-spending function (p.52, p.74). RTSA has `esOF`, `esPoc`, `HSDC` and `rho`.
- **Pocock (Lan-DeMets).** `α(t) = α·ln(1+(e−1)t)` (gsDesign `sfLDPocock` help;
  RTSA `esPoc`). It is not in CTU.
- **gsDesign** (help `sfLDOF`): `f(t;α) = 2 − 2Φ(Φ⁻¹(1−α/2)/t^{ρ/2})` with ρ=1,
  applied to the **one-sided** α ("alpha: Type I error, always one-sided",
  help `gsDesign`).

**Two-sided convention.** For two-sided α=0.05, gsDesign spends
`2−2Φ(z_{1−0.0125}/√t)` per side, written `sfLDOF(0.025, t)`. Reading the CTU
formula literally, with α the total two-sided level and the spend halved per
side, gives `1−Φ(z_{0.975}/√t)` per side. That differs for t<1: at t=0.5 the
per-side spends are 0.00153 and 0.00279. The evidence favours the gsDesign
convention for CTU:

1. CTU computes boundaries "according to Reboussin et al." (p.44).
2. ldbounds, the R port of that program, matches gsDesign to about 3e-3 at every
   look tested.
3. RTSA, whose authors include CTU staff, calls `esOF(alpha/side, …)`, which
   equals gsDesign's convention. A commented-out function `alphas()` next to
   the "old TSA functions (translated from java)" uses
   `2*(1-pnorm(qnorm(1-alpha/side/2)/sqrt(t)))`, the same convention.

A direct check against CTU output is **UNVERIFIED**, because no published CTU
boundary values with full trial data were found.

**Numerical agreement** (timing 0.1, 0.25, 0.5, 0.75, 1; two-sided α=5%; `chk1.R`):

| Look | gsDesign `test.type=2, alpha=0.025, sfu=sfLDOF` | RTSA `boundaries(side=2, es_alpha="esOF")` | ldbounds `ldBounds(iuse=1, alpha=0.05, sides=2)` |
|---|---|---|---|
| 0.10 | 6.991341 | 20 (no stopping: increment < 1e-9) | 6.991341 |
| 0.25 | 4.332634 | 4.332620 | 4.329712 |
| 0.50 | 2.963131 | 2.963131 | 2.963111 |
| 0.75 | 2.359045 | 2.359045 | 2.359022 |
| 1.00 | 2.014091 | 2.014091 | 2.014059 |

- With `test.type=1, alpha=0.025` gsDesign gives the identical bounds, matching
  RTSA `side=1, alpha=0.025`.
- Pocock: gsDesign `sfLDPocock` and RTSA `esPoc` agree exactly
  (2.65511, 2.524755, 2.385919, 2.366389, 2.355153).
- `gsBound(I=t, trueneg=inc, falsepos=inc)`, with `inc = diff(c(0, sfLDOF(0.025, t)$spend))`,
  gives the same bounds for **any** t vector, including a last look below 1.
  A spending-function bound at look j depends only on t₁…t_j, so appending a
  synthetic t=1 look, as RTSA does, leaves the earlier bounds unchanged.

### 4.2 Timing of looks

- Each look is a cumulative meta-analysis step after a trial is added, at
  IF_j = accrued_j / RIS (CTU p.38). Users may uncheck earlier looks; "the last
  trial on the list should always be checked" (CTU p.76). The CTU examples assume
  a look after every trial (CTU §5.3 p.89). Trials published in the same year
  were ordered alphabetically by first author (CTU p.89; Imb2016).
- **Small increments.** CTU "automatically removes (un-checks) interim analyses
  that yield a relative increase in information less than 1%". The example is a
  40-patient trial against a RIS of 20,000, i.e. 0.2% of the RIS. Their data
  still enter the cumulative Z (CTU §4.4.4 p.80). CTU also says OBF boundaries
  are "relatively unaffected" by the number of earlier looks if looks are at least
  1% of the RIS apart (CTU p.42).
- RTSA does the same with `time_tf = 0.01` on IF increments. It also drops
  leading looks with IF < `inf_first_analysis = 0.05`, and sets the bound to
  ±20 (no stopping possible) when the incremental α spend is below 1e-9
  (`RTSA.R`, `RTSA_helperfunctions.R`).
- CTU figures describe the boundary as "truncated for the first 14 trials"
  (Fig 58) and "for the first 4 trials" (Fig 59) (CTU p.91-92). The exact CTU
  rule for not drawing or computing early boundaries is **UNVERIFIED**; it may
  be display-only.

### 4.3 Information fraction above 1 (RIS exceeded)

- CTU defines the spending function on 0-1 (p.39). In CTU Table 3 the adjusted
  CI is shown as "–" for every year after the RIS (1964) was surpassed (p.93).
  That implies that beyond the RIS CTU reports no sequential adjustment.
  The [run-only CABG settings probe](../../r/RCMetaR/tests/testthat/fixtures/tsa/README.md)
  confirmed that CTU TSA 0.9.5.10 Beta ended its monitoring curves at IF=1,
  while the cumulative Z-curve continued at the later participant counts.
- RTSA analysis path: looks with IF > 1 (or > `design_R`) are dropped from the
  boundary computation, a synthetic final look is placed at `design_R` (1 when
  `power_adj=FALSE`), and the Z-curve continues without boundaries (`RTSA.R`).
  RTSA's lower-level `alpha_boundary()` instead rescales the timing by max(IF)
  when IF>1. For timing (0.3, 0.7, 1.2) that gives 4.332634, 2.712771, 1.978458,
  identical to gsDesign with `timing = t/max(t)`. The alternative gsDesign
  `usTime = pmin(t,1)` gives 3.928573, 2.438742, 2.020316 (`chk2.R`). These are
  different conventions; choose one deliberately.
- tsahr follows RTSA: formal looks only while IF<1, plus one synthetic look at
  t=1, with no boundaries after DARIS (help `tsa_hr`, "Retrospective boundary
  timeline").

### 4.4 One- or two-sided

CTU supports two-sided (symmetric) and one-sided Upper/Lower tests. Upper tests
favour the experimental arm for harmful outcomes; the roles reverse for
beneficial outcomes (CTU p.70, 73-74). The RIS uses α/2, i.e. two-sided (p.24).

### 4.5 Futility (inner wedge) and β-spending

- CTU: non-superiority and non-inferiority boundaries form an "inner wedge"
  (p.23, 53). The β-spending function is OBF (p.52). The program offered only
  non-binding futility ("The original TSA software only included non-binding
  futility boundaries", RTSA futility vignette). CTU §2.2.7 describes the
  conditional-probability requirements but gives no closed formula.
- **CTU construction, as ported by RTSA** (`getInnerWedge`, under the comment
  "## old TSA functions (translated from java)"). This is RTSA's statement and
  cannot be checked against TSA.jar, because the licence forbids inspecting it.
  1. `c^β_k` are symmetric two-sided boundaries computed under H0 with OBF
     spending of total level β per tail:
     `β(t) = 2(1−Φ(z_{1−β/2}/√t))` (`betas_Obf`).
  2. `drift θ = c^α_final + c^β_K·√t_K`, where `c^α_final` is the efficacy
     boundary at the final look (IF=1), or `z_{1−α/side}` when IF>1.
  3. `futility_k = θ√t_k − c^β_k`, mirrored for the lower wedge.

  The wedge therefore meets the efficacy boundary at IF=1. The drift is **not**
  the design drift `z_{1−α/2}+z_{1−β}`: in the example below θ = 3.063 against
  2.802. Futility is ignored when computing α (non-binding).
- **gsDesign reconstruction of the CTU wedge.** Take
  `cβ = gsDesign(k, test.type=2, alpha=β, timing=t, sfu=sfLDOF)$upper$bound` and
  `θ = cα_K + cβ_K`; then `b_k = θ√t_k − cβ_k`. For t = (0.2, 0.4, 0.6, 0.8, 1),
  α=5% two-sided and β=20%:

| t | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|
| efficacy cα | 4.876885 | 3.357011 | 2.680280 | 2.289817 | 2.031032 |
| RTSA `getInnerWedge` (CTU port) | −1.268779 | 0.203516 | 1.004008 | 1.573865 | 2.031032 |
| gsDesign reconstruction | −1.267937 | 0.203944 | 1.004442 | 1.574178 | 2.031032 |
| gsDesign `test.type=4` (true non-binding β-spending) | −1.292147 | 0.169705 | 0.962505 | 1.526494 | 2.031032 |

  The port uses a coarse grid (h=0.05), which explains differences of about
  1e-3. **gsDesign `test.type=4` is a different method**: it spends β under H1
  with the design drift and inflates the maximum information (×1.155 here).
- RTSA `futility="non-binding"`, one-sided, matches gsDesign `test.type=4`
  exactly (lower −1.292147, 0.169704, 0.962505, 1.526493, 2.031032; inflation
  1.155004 in both). RTSA binding, one-sided, matches `test.type=3` to about
  1e-4. RTSA's two-sided non-binding futility differs slightly from
  `test.type=4` (0.184 vs 0.170 at t=0.4), because RTSA drops wedge points
  below 0 (`rm_bs`).

### 4.6 Re-spending when the RIS changes

When the RIS estimate changes (new D², P_C or effect), CTU and RTSA
retrospective analyses recompute every IF and every boundary from the current
RIS. W2017 acknowledges this "moving target" ("a moving target seems better than
having no target at all"). RTSA's prospective mode keeps the stored design.

### 4.7 Matching gsDesign calls

| TSA element | gsDesign call (verified above) |
|---|---|
| Two-sided OBF efficacy (CTU/RTSA convention) | `gsDesign(k, test.type=2, alpha=α/2, timing=t, sfu=sfLDOF)` with `t[k]=1`, or `gsBound(I=t, trueneg=inc, falsepos=inc)` with `inc` from `sfLDOF(α/2, t)` |
| One-sided OBF | `test.type=1, alpha=α` (or `gsBound` with `trueneg=rep(-20,k)`) |
| Pocock | `sfu=sfLDPocock` |
| CTU inner wedge | No direct call. Reconstruct from `gsDesign(test.type=2, alpha=β, sfu=sfLDOF)` bounds as in §4.5 |
| RTSA non-binding / binding futility (one-sided) | `test.type=4` / `test.type=3`, `sfl=sfLDOF` |
| RTSA inflation `root` | `max(gsDesign(...)$n.I)` with `n.fix=1` (1.018279 in both) |

---

## 5. TSA-adjusted confidence interval

**CTU (§2.2.5 p.44-47).** The repeated CI at look j is `θ̂_j ± c_j · se(θ̂_j)`,
where c_j is the α-spending boundary at that look. On the log scale for RR/OR,
exponentiated. Both models use the pooled estimate and SE of the chosen model.
The overall coverage is 1−α, and the result "easily generalises to one-sided
confidence intervals". The program reports it for the **last** look only (CTU
p.47, p.69). Its coverage "will correspond to the alpha level set for the chosen
alpha-spending function" (CTU p.69).

**RTSA (`inference.R`)** reports two intervals:

1. `TSAadjCI`, the same repeated CI: `exp(log(θ̂) ± c_k·sqrt(var))`, using the
   fixed (MH or IV) variance or the random-effects variance (`peR[6]`, which is
   the **HKSJ variance** under `DL_HKSJ`). There is no t quantile, and the
   boundary c_k comes from the normal-theory spending calculation.
2. `seq_inf`, a **stage-wise ordering** CI, median-unbiased estimate and p-value,
   computed only when a boundary is crossed or at the final analysis. It finds
   the drift `x` where the probability of a result "at least as extreme" in
   stage-wise order equals (1−conf)/2 (`sw_cilower`/`sw_ciupper` via
   `ma_power`), then rescales: `est = x · SE_stop · √(IF_stop·root)`. CTU has no
   equivalent.

**Sources agree:** the repeated CI is `θ̂ ± c_k·SE`.

**Sources differ:** RTSA adds the stage-wise CI; CTU reports only the last look;
RTSA's random-effects version uses the HKSJ SE with normal boundaries.

---

## 6. Law of the iterated logarithm (LIL)

**Formula (CTU §2.2.6 p.47, citing Lan2003 and Hu2007):**

```
Z*_j = Z_j / sqrt( λ · ln( ln(I_j) ) )
```

- `I_j` is the **cumulative statistical information** at look j (CTU p.47: "see
  section 2.2.1 under alternatives to accumulating number of patients"), i.e.
  1/Var(pooled estimate). It is not the number of trials or participants.
  Lan2003's own definition is **UNVERIFIED** (full text gated).
- Z* is compared with the **conventional single-test threshold**: "|Z*|≥1.96
  means statistical significance at two-sided α=5%" (CTU p.48). CTU shows
  penalised curves on a separate graph from α-spending boundaries, because
  "combining these two approaches in one graph is not meaningful" (CTU p.85).

**λ recommendations:**

| Source | Measure | One-sided α=0.01 (c=2.33) | α=0.025 (c=1.96) | α=0.05 (c=1.65) |
|---|---|---|---|---|
| CTU Table 2 (p.48), from Hu2007 | Risk difference | 3 | 1.5 | 1.5 |
| | Relative risk | 3.5 | 2 | 2 |
| | Odds ratio | 3.5 | 2 | 2 |
| Lan2003 (via CTU p.48) | Continuous (MD) | – | 2 (two-sided 5%) | – |

The Hu2007 abstract confirms: "With an adjustment factor of 2… controls the
overall type I error when odds ratio or relative risk is the parameter of
interest. For risk difference, the adjustment factor can be reduced to 1.5."
More inspections may need a larger λ, which "stabilizes after 25 inspections".

**When to use it, and its caveats (CTU p.48-49).** The λ values "pertain only
to the ranges… used in the simulations". The minimum control proportion simulated
was 0.05, and the simulations had no time-lag or publication bias. If τ² is
underestimated, Z* "will be artificially large". The recommended λ "constitute
the very minimum", and higher values are probably needed for sparse
meta-analyses. CSC2017 notes the LIL approach "does not require the
pre-specification of the maximum information".

**Unresolved by the sources (UNVERIFIED):**
- ln ln I is undefined or non-positive for I ≤ e, and how CTU handles small I
  is not stated.
- For MD, I has units of 1/(outcome unit)², so Z* depends on the measurement
  scale. This follows from the formula itself; no source discusses it.
- Peto OR, HR and SMD have no λ in any source.

---

## 7. Random-effects models, the cumulative Z, and zero events

**CTU (§2.1.3 p.16-19; §4.3.2-4.3.3 p.67-68; appendix 6.2.1 p.102):**

- **Models.** Fixed effect, DerSimonian-Laird (`τ²_DL = max(0,(Q−k+1)/(S₁−S₂/S₁))`),
  Sidik-Jonkman (`τ²_SJ = Σv_i(Y_i−θ̂₀)²/(k−1)` with `v_i = r_i+1`,
  `r_i = σ_i²/τ₀²`, `τ₀² = Σ(Y_i−ȳ)²/k`), and Biggerstaff-Tweedie (DL τ²
  distribution, averaged weights `w_i*(τ²) = E[w_i*(τ̂²_DL)]`, and an adjusted
  variance).
- The manual recommends sensitivity analysis across DL, SJ and BT (p.19).
- **Cumulative Z.** A Wald statistic, `Z = θ̂/sqrt(Var(θ̂))`, with
  `Var = 1/Σw*` under random effects and the normal reference (CTU p.16). W2017
  uses the MH-weighted RR with the DL random-effects model.
- **Zero events** (CTU §2.1.4 p.20-22, §4.3.3 p.68):
  - constant continuity correction (RevMan uses 0.5 per cell, entered as a
    "Value" sum of 1);
  - reciprocal of the opposite arm size ("treatment arm" correction);
  - empirical correction from the pooled OR of the non-zero trials
    (`CF_I = R/(R+θ̂)·C`, `CF_C = θ̂/(R+θ̂)·C` per Sweeting 2004; extraction
    garbled, so **verify against Sweeting 2004**);
  - an option to include double-zero trials.

  CTU-sample uses `zeroEventHandling Empirical`, `zeroEventValue 0.01` and
  `ignoreZeroEventsTrials true`.

**RTSA (`metaanalysis.R`, `RTSA.R`):**

- **Models.** Fixed effect (MH by default, or IV), `re_method = "DL"` or
  `"DL_HKSJ"` (the default).
- **HKSJ.** `vwR = Σw*(y−θ̂)²/((k−1)Σw*)` with no truncation at q=1. The
  statistic `zvalR = θ̂/sqrt(vwR)` is the HKSJ t statistic. RTSA computes its
  p-value from t(k−1), but **compares the same statistic with the
  normal-theory boundaries** and builds the TSA CI with `c_k·sqrt(vwR)`.
- tsahr instead converts the HKSJ t to its normal equivalent,
  `sign·qnorm(1−p/2)`, before comparing with the boundaries, and returns NA at
  k=1 (help `tsa_hr`, "Z-curve scale").
- The MD path in RTSA's `synthesize()` ignores `re_method`, so MD is always DL.
- **Zero events.** Double-zero trials are removed, and 0.5 is added to every cell
  of single-zero trials (n + 1 per arm). Only `zero_adj=0.5` is allowed.
- **Possible RTSA issue.** The MH-RD variance in `metaPrepare` reads
  `((A*B*nI)^3 + (C*D*nC)^3)/(nI*nC*N)^2`, which does not match the
  Greenland-Robins form `(A·B·n_C³ + C·D·n_I³)/(n_I n_C N²)`. Whether it is a bug
  is **UNVERIFIED**; do not use RTSA MH-RD as an oracle.

**Cross-check (`chk3.R`).** On RTSA `perioOxy` (15 trials):
- RTSA's DL cumulative Z equals metafor `cumul(rma(method="DL"))` to 5
  decimals: 1.66052, −0.13585, −0.28117, −0.87293, −0.98080, −1.47432, −1.80200,
  −1.75679, −1.83715, −1.98721, −1.21878, −1.47239, −1.09306, −1.29116, −1.32824.
- RTSA's IV fixed-effect Z equals metafor FE.
- RTSA's MH Z matches metafor `rma.mh` up to look 8 and then differs (−2.6438 vs
  −2.6459) because RTSA applies the 0.5 correction to the single-zero Golfam trial
  and metafor's MH does not.

**What the sources say about the random-effects theory:**
- CTU: the statistical-information axis is reliable only if τ² is (p.33).
- tsahr: applying OBF to a random-effects Z with τ² re-estimated at every look
  is "an approximation (as in the official Copenhagen Trial Unit TSA software),
  not an exact result".
- Shuster & Neu (quoted in CSC2017): reweighting after each trial "violates the
  critical independent increment property".

---

## 8. Numerical oracles

### 8.1 Published CTU outputs (manual §5), with their full inputs

| ID | Inputs | Published output | Status |
|---|---|---|---|
| CTU-5.2 | P_C=14%, relative benefit increase 20%, α=5% two-sided, β=20%, no heterogeneity adjustment, information = patients | RIS = **5218** | 5217 on printed inputs (5217.26 before rounding) |
| CTU-5.3a | P_C=27.6% (median control), RRR 20%, α=1%, β=10%, D²=49.0% | RIS = **7150** | Reproduced (7150.48) |
| CTU-5.3b | Same, RRR 36.9% (low-bias pooled) | RIS = **1964** | 1962.4 with D²=0.490 (within 0.1%) |
| CTU-5.4 | P_C=3.9%, RRR 33%, α=5%, β=20%, I²=0 | RIS = **5942** | **5972** in the run-only probe (5971.5 before rounding) |
| CTU-5.5 | P_C=5%, RRR 25%, α=5%, β=20%, D²=20% | RIS = **10,508** | Reproduced (10,507.69) |
| CTU-Table 3 | CABG atrial fibrillation; RIS 1964; 99% CIs (pooled RR / conventional / adjusted): 1999 1 trial, 55 events, 200 pts: 0.24 / 0.14-0.42 / 0.03-7.74; 2000 3, 74, 288: 0.39 / 0.15-0.99 / 0.02-7.18; 2001 5, 143, 649: 0.57 / 0.24-1.34 / 0.12-2.87; 2002 8, 204, 932: 0.52 / 0.30-0.90 / 0.22-1.21; 2003a 10, 285, 1168: 0.55 / 0.37-0.81 / 0.35-0.85; 2003b 13, 391, 1722: 0.53 / 0.35-0.79 / 0.34-0.83; 2004 19, 641, 2832: 0.61 / 0.46-0.82 / –; 2005 20, 679, 2999: 0.63 / 0.49-0.85 / –; 2006 25, 768, 3310: 0.67 / 0.53-0.86 / –; 2007 27, 775, 3372: 0.67 / 0.53-0.86 / – (CTU p.93) | Adjusted CIs | **Trial-level data not in the manual** (Møller 2008 *Eur Heart J* 29:2601). Usable only if the data are obtained. Also shows "–" after the RIS. |
| CTU-5.2/5.4/5.5 Z-curves | – | Figures only, no numbers | Not usable |

### 8.2 Published RIS from other primary papers

- **W2009 Table 2** (§2): use as a check of the D²/I² adjustment step,
  e.g. SS 8,421 → HIS 9,726 (I² 13.4%) → DIS 14,164 (D² 40.5%).
- **W2017 Fig 1a**: TTM cardiac arrest, 4 trials, P_C=60%, RRR 17%, D²=23%,
  α=5%, β=20%. RIS = **977**; naive CI 0.70-1.00; TSA-adjusted CI
  **0.63-1.12**. Recomputed with D²=23% this gives 970.4; 977 needs D²≈23.5%.
  This is rounding in the published inputs, so treat it as ±1%.
- **W2017 Fig 1b**: 5 trials, D²=65%, RIS **2040**. Recomputed: 2134.8. **Not
  reproducible** from the rounded inputs; P_C may have changed (UNVERIFIED).

### 8.3 RTSA reference runs (CRAN 0.2.2; data `perioOxy`, 15 trials, table order)

Run A: `RTSA(type="analysis", data=perioOxy, outcome="RR", mc=0.8, side=2,
alpha=0.05, beta=0.2, es_alpha="esOF", fixed=TRUE)`, MH weights.

- pC = 0.128899 (Σe_C/Σn_C). RIS = **4845**. root = 1.03876. SMA_RIS = 5032.81.
- Cumulative N: 143, 643, 2029, 4041, 4201, 4497, 4707, 5538, 5598, 5636,
  5796, 5967, 6552, 6785, 7219.

| Look | IF (sma_timing) | z_fixed (MH) | upper bound | TSA-adj CI (RR) |
|---|---|---|---|---|
| 1 | 0.029515 | 1.66050 | 20 | 0.0013160-2525.8 |
| 2 | 0.13271 | −0.90702 | 20 | 0.0065401-100.96 |
| 3 | 0.41878 | −0.83296 | 3.3423 | 0.66143-1.2835 |
| 4 | 0.83406 | −1.95320 | 2.2498 | 0.71067-1.0254 |
| 5 | 0.86708 | −1.96740 | 2.2904 | 0.71248-1.0270 |
| 6 | 0.92817 | −2.43200 | 2.2171 | 0.70335-0.98491 |
| 7 | 0.97152 | −2.75210 | 2.1858 | 0.69170-0.95988 |
| final (synthetic) | 1.0388 | – | 2.1018 | – |

  The lower boundary crosses at look 6. The stage-wise results are:
  median-unbiased RR 0.850454, CI 0.731864-0.989, p = 0.0354632. Note that the
  look-5 bound (2.2904) is larger than the look-4 bound (2.2498). This
  non-monotone result was not investigated.

Run C: as A but `random_adj="D2", re_method="DL"` (random effects).

- HARIS = **13,201**, consistent with D² = 0.6330. metafor gives τ²=0.0652616,
  I²=48.37% and D²=0.632957 on the full data. root = 1.0064.
- Upper bounds at looks 3-8: 5.6343, 3.8994, 3.8727, 3.7324, 3.6593, 3.3145.
  Looks 9-10 are skipped (increment < 1%). Looks 11-15: 3.2767, 3.2466, 3.0555,
  3.0310, 2.9206.
- z_random at the same looks: −0.28117, −0.87293, −0.98080, −1.47430,
  −1.80200, −1.75680, then −1.21880, −1.47240, −1.09310, −1.29120, −1.32820.
- Random TSA CI at look 15: 0.63901-1.1827.

Run D: as C plus `futility="non-binding", es_beta="esOF"`.

- root = 1.07664. SMA_HARIS = 14,213.
- Futility at looks 12-15: ±0.21843, ±0.29496, ±0.31274, ±0.43402.

Run E (closest to CTU): `tsa_beta_bound=TRUE, power_adj=FALSE, weights="IV"`.

- RIS = HARIS = 13,201, with no inflation.
- Upper bounds at looks 3-8: 5.6140, 3.8860, 3.8597, 3.7200, 3.6472, 3.3032.
  Looks 11-15: 3.2658, 3.2359, 3.0452, 3.0209, 2.9109. Final (IF=1): 1.9747.
- Inner wedge at looks 8, 11-15: 0.14860, 0.12491, 0.14163, 0.33736, 0.36301,
  0.48930.

These are RTSA oracles, not CTU oracles. Their boundaries depend on RTSA-only
choices (the 5% first-look rule, the inflation `root`, and its handling of
IF>1).

### 8.4 Boundary-only oracles (exact, implementation-independent)

The gsDesign, RTSA and ldbounds tables in §4.1, §4.3 and §4.5 can serve as
regression oracles for the boundary layer. They were computed with gsDesign
3.11.0.

### 8.5 CTU sample and run-only checks

CTU-sample `High perioperative oxygen SSI.TSA` contains:
- 7 trials: Greif 2000 13/250 vs 28/250; Pryor 2004 20/80 vs 9/80; Belda 2005
  22/148 vs 35/143; Mayzler 2005 2/19 vs 3/19; ENIGMA 2007 77/997 vs 106/1015;
  Gardelle 2008 17/69 vs 10/74; PROXI 2008 130/694 vs 141/706.
- One boundary: two-sided α 5%, β 20%, incidences 13.09% vs 16.36% (RRR 20%),
  `heterogeneityCorrectionValue 0.67`, OBF α and β spending, looks after
  Greif, Belda, ENIGMA and PROXI.

The sample was run normally in CTU TSA 0.9.5.10 Beta. The
[fixture record](../../r/RCMetaR/tests/testthat/fixtures/tsa/README.md) retains
the observed RIS, summary and exported plot alongside the CABG settings probe.

---

## 9. Criticisms and limitations that should shape report wording

- **The moving target and the choice of RIS parameters.** The RIS depends on the
  effect, P_C and D², which are often chosen after seeing the data. W2017 calls
  this the "moving target" and requires a peer-reviewed protocol. CTU (p.31-32)
  and Imb2016 stress sensitivity ranges.
- **The heterogeneity adjustment is too simplistic** (K&W2014 via W2017: "it is
  too simplistic to just increase the required information size with the
  variance increase"). Under random effects the power depends on the **number
  of trials**, not just on participants; extreme heterogeneity gives extreme
  sizes (K&W2014 abstract fragments; RTSA vignette simulations show that D²
  adjustment does not reach 80% power under random effects).
- **Unreliable τ² and D² with few trials.** CTU p.28 (fewer than about 10
  trials, time-lag bias); W2009 (D² may have greater variance than I²); CSC2017
  ("should not be used with less than five studies").
- **Violated independent increments.** A random-effects Z with τ² re-estimated
  at each look, and reweighting after each trial, break the canonical Brownian
  motion assumption (Shuster & Neu via CSC2017). tsahr calls the boundaries an
  approximation, as does CTU in effect (p.33).
- **The significance-testing framing.** Higgins (via CSC2017): sequential
  approaches "encourage the use of significance tests and the inappropriate
  division of results as 'significant' or 'not significant'". He also argues
  that information should be the sum of weights rather than participants, which
  needs P_C and heterogeneity pre-specified.
- **Cochrane status.** CSC2017 classed TSA and other sequential methods as
  "Further evaluation required". It neither recommended nor banned them.
  Reports should not imply Cochrane endorsement. A later CSC statement may
  exist but was not retrieved (**UNVERIFIED**).
- **Bias is not addressed.** TSA controls random error only. W2017 says
  conclusions are reliable only when trials are at low risk of bias. CTU says
  time-lag and publication bias are unaccounted for (p.48, p.106).
- **Retrospective use.** The RTSA vignette says retrospective sequential
  analysis gives type I error control only "in the scenario that the current
  state is the truth" and that p-values should not be decision markers.
  Sequential decision and design biases are discussed there, citing Kulinskaya
  2015.
- **LIL λ values** come from simulations with limited ranges (CTU p.48-49).
- **Futility is non-binding** in CTU. Crossing the inner wedge supports only "the
  intervention effect is not greater than the one anticipated", with risk β of
  being a "false futile" finding (CTU p.53, 96).

---

## Appendix A: reproduction scripts

The scripts below were run with R 4.6.1, with
`.libPaths(c("<scratch rlib>", .libPaths()))` and gsDesign 3.11.0, ldbounds
2.0.2, RTSA 0.2.2 and metafor 5.0.1. `getInnerWedge` is not in the CRAN binary.
It was sourced from the GitHub `R/RTSA_helperfunctions.R` (commit `dc13c0b`)
into an environment whose parent is `asNamespace("RTSA")`.

```r
# chk1: RIS reproduction and boundary agreement
ris_ctu <- function(pc, rrr, alpha, beta, AF = 1, increase = FALSE) {
  pe <- if (increase) pc * (1 + rrr) else pc * (1 - rrr)
  ps <- (pc + pe) / 2
  4 * (qnorm(1 - alpha/2) + qnorm(1 - beta))^2 * ps * (1 - ps) / (pc - pe)^2 * AF
}
ris_ctu(0.14, 0.20, 0.05, 0.20, increase = TRUE)   # 5217.26 -> 5217
ris_ctu(0.276, 0.20, 0.01, 0.10, 1/(1 - 0.49))     # 7150.48
ris_ctu(0.05, 0.25, 0.05, 0.20, 1/(1 - 0.20))      # 10507.69
t <- c(0.1, 0.25, 0.5, 0.75, 1)
gsDesign::gsDesign(k = 5, test.type = 2, alpha = 0.025, beta = 0.1, timing = t,
                   sfu = gsDesign::sfLDOF)$upper$bound
RTSA:::boundaries(timing = t, alpha = 0.05, beta = 0.1, side = 2,
                  futility = "none", es_alpha = "esOF")$alpha_ubound
ldbounds::ldBounds(t, iuse = 1, alpha = 0.05, sides = 2)$upper.bounds

# chk2: CTU inner wedge reconstruction (t = 0.2..1, beta = 0.2)
t  <- c(0.2, 0.4, 0.6, 0.8, 1)
cA <- gsDesign::gsDesign(k = 5, test.type = 2, alpha = 0.025, beta = 0.2,
                         timing = t, sfu = gsDesign::sfLDOF)$upper$bound
cB <- gsDesign::gsDesign(k = 5, test.type = 2, alpha = 0.2, beta = 0.5,
                         timing = t, sfu = gsDesign::sfLDOF)$upper$bound
(cA[5] + cB[5]) * sqrt(t) - cB                      # CTU-style futility wedge

# chk3: RTSA oracle runs
library(RTSA); data(perioOxy)
RTSA(type = "analysis", data = perioOxy, outcome = "RR", mc = 0.8, side = 2,
     alpha = 0.05, beta = 0.2, es_alpha = "esOF", fixed = TRUE)
RTSA(type = "analysis", data = perioOxy, outcome = "RR", mc = 0.8, side = 2,
     alpha = 0.05, beta = 0.2, es_alpha = "esOF", random_adj = "D2", re_method = "DL")
```
