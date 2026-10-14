# Review 1 — reviewed golden text changes

All 415 original fields were exact before refreshing. Only these three text sections changed; archive figure bytes, numerical fields, policies and tolerances remain untouched. The sanctioned tool was `uv run python scripts/regenerate_golden_presentation.py build/qt6-verification/golden-compatibility-review1`.

## amino-binary-random / Summary

```diff
--- 
+++ 
@@ -19,5 +19,4 @@
  0.212                                2.799
 
 Calculation scale: log - estimate: -0.262, lower: -0.724, upper: 0.200, std. error: 0.236
-Overall-effect null: log(Odds Ratio) = 0; Odds Ratio = 1.
 95% prediction interval: the underlying effect in a new study; this is not the confidence interval of the pooled estimate.```

## continuous-random / Summary

```diff
--- 
+++ 
@@ -18,5 +18,4 @@
  Lower bound (95% PI)  Upper bound (95% PI)
  -0.072                               0.789
 
-Overall-effect null: Standardized Mean Difference = 0 (untransformed scale).
 95% prediction interval: the underlying effect in a new study; this is not the confidence interval of the pooled estimate.```

## lymph-diagnostic-random-dor / Odds Ratio Summary

```diff
--- 
+++ 
@@ -8,7 +8,7 @@
  Q       df  p-value     I²     τ²
  42.259  16  < 0.001  62.1%  0.704
 
-Odds Ratio -Test for overall effect
+Odds Ratio -Test for overall effect (H₀: diagnostic Odds Ratio = 1)
  Z      p-value
  7.980  < 0.001
 
@@ -17,5 +17,4 @@
  1.699                               54.783
 
 Calculation scale: log - estimate: 2.267, lower: 1.710, upper: 2.823, std. error: 0.284
-Overall-effect null: log(Diagnostic Odds Ratio) = 0; Diagnostic Odds Ratio = 1.
 95% prediction interval: the underlying effect in a new study; this is not the confidence interval of the pooled estimate.```
