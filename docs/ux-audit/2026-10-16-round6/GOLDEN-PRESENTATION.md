# Reviewed golden presentation changes

Three OR sequential/subgroup text sections change: Std. error → SE (log scale), plus table padding. All 415 original numerical fields remain exact (NUMERICAL-EQUIVALENCE.json). Numerical contracts/tolerances remain unchanged. The sanctioned presentation tool preserves the original frozen outputs rather than importing additional current fields.

## amino-binary-cumulative

```diff
--- 

+++ 

@@ -5,21 +5,21 @@

 Model Results
- Study added (k)                Estimate  Lower bound (95% CI)  Upper bound (95% CI)  Std. error  p-value
- Gonzalez, 1993 (k = 1)            0.571                 0.170                 1.916       0.617         
- Prins, 1993 (k = 2)               0.509                 0.204                 1.273       0.467    0.149
- Giamarellou, 1991 (k = 3)         0.430                 0.180                 1.032       0.446    0.059
- Maller, 1993 (k = 4)              0.657                 0.268                 1.609       0.457    0.358
- Sturm, 1989 (k = 5)               0.614                 0.265                 1.422       0.428    0.255
- Marik, 1991 (k = 6)               0.540                 0.275                 1.060       0.344    0.073
- Muijsken, 1988 (k = 7)            0.634                 0.334                 1.205       0.328    0.164
- Vigano, 1992 (k = 8)              0.668                 0.358                 1.246       0.318    0.205
- Hansen, 1988 (k = 9)              0.572                 0.305                 1.073       0.321    0.082
- De Vries, 1990 (k = 10)           0.646                 0.352                 1.188       0.310    0.160
- Mauracher, 1989 (k = 11)          0.594                 0.323                 1.095       0.312    0.095
- Nordstrom, 1990 (k = 12)          0.606                 0.345                 1.062       0.287    0.080
- Rozdzinski, 1993 (k = 13)         0.655                 0.398                 1.078       0.255    0.096
- Ter Braak, 1990 (k = 14)          0.706                 0.442                 1.127       0.239    0.145
- Tulkens, 1988 (k = 15)            0.712                 0.453                 1.121       0.231    0.143
- Van der Auwera, 1991 (k = 16)     0.696                 0.446                 1.086       0.227    0.110
- Klastersky, 1977 (k = 17)         0.775                 0.477                 1.258       0.247    0.302
- Vanhaeverbeek, 1993 (k = 18)      0.780                 0.486                 1.253       0.241    0.304
- Hollender, 1989 (k = 19)          0.770                 0.485                 1.222       0.236    0.267
+ Study added (k)                Estimate  Lower bound (95% CI)  Upper bound (95% CI)  SE (log scale)  p-value
+ Gonzalez, 1993 (k = 1)            0.571                 0.170                 1.916           0.617         
+ Prins, 1993 (k = 2)               0.509                 0.204                 1.273           0.467    0.149
+ Giamarellou, 1991 (k = 3)         0.430                 0.180                 1.032           0.446    0.059
+ Maller, 1993 (k = 4)              0.657                 0.268                 1.609           0.457    0.358
+ Sturm, 1989 (k = 5)               0.614                 0.265                 1.422           0.428    0.255
+ Marik, 1991 (k = 6)               0.540                 0.275                 1.060           0.344    0.073
+ Muijsken, 1988 (k = 7)            0.634                 0.334                 1.205           0.328    0.164
+ Vigano, 1992 (k = 8)              0.668                 0.358                 1.246           0.318    0.205
+ Hansen, 1988 (k = 9)              0.572                 0.305                 1.073           0.321    0.082
+ De Vries, 1990 (k = 10)           0.646                 0.352                 1.188           0.310    0.160
+ Mauracher, 1989 (k = 11)          0.594                 0.323                 1.095           0.312    0.095
+ Nordstrom, 1990 (k = 12)          0.606                 0.345                 1.062           0.287    0.080
+ Rozdzinski, 1993 (k = 13)         0.655                 0.398                 1.078           0.255    0.096
+ Ter Braak, 1990 (k = 14)          0.706                 0.442                 1.127           0.239    0.145
+ Tulkens, 1988 (k = 15)            0.712                 0.453                 1.121           0.231    0.143
+ Van der Auwera, 1991 (k = 16)     0.696                 0.446                 1.086           0.227    0.110
+ Klastersky, 1977 (k = 17)         0.775                 0.477                 1.258           0.247    0.302
+ Vanhaeverbeek, 1993 (k = 18)      0.780                 0.486                 1.253           0.241    0.304
+ Hollender, 1989 (k = 19)          0.770                 0.485                 1.222           0.236    0.267
```

## amino-binary-leave-one-out

```diff
--- 

+++ 

@@ -5,22 +5,22 @@

 Model Results
- Study omitted                        Estimate  Lower bound (95% CI)  Upper bound (95% CI)  Std. error  p-value
- All studies                             0.770                 0.485                 1.222       0.236    0.267
- Study omitted: Gonzalez, 1993           0.783                 0.477                 1.285       0.253    0.332
- Study omitted: Prins, 1993              0.796                 0.489                 1.296       0.249    0.359
- Study omitted: Giamarellou, 1991        0.811                 0.513                 1.281       0.233    0.369
- Study omitted: Maller, 1993             0.715                 0.437                 1.172       0.252    0.184
- Study omitted: Sturm, 1989              0.791                 0.494                 1.265       0.240    0.327
- Study omitted: Marik, 1991              0.864                 0.543                 1.375       0.237    0.538
- Study omitted: Muijsken, 1988           0.724                 0.446                 1.175       0.247    0.191
- Study omitted: Vigano, 1992             0.750                 0.468                 1.200       0.240    0.230
- Study omitted: Hansen, 1988             0.851                 0.542                 1.336       0.230    0.484
- Study omitted: De Vries, 1990           0.724                 0.449                 1.166       0.243    0.184
- Study omitted: Mauracher, 1989          0.813                 0.515                 1.283       0.233    0.375
- Study omitted: Nordstrom, 1990          0.772                 0.474                 1.257       0.249    0.298
- Study omitted: Rozdzinski, 1993         0.738                 0.442                 1.231       0.261    0.244
- Study omitted: Ter Braak, 1990          0.726                 0.443                 1.189       0.252    0.204
- Study omitted: Tulkens, 1988            0.764                 0.476                 1.227       0.242    0.266
- Study omitted: Van der Auwera, 1991     0.791                 0.494                 1.265       0.240    0.327
- Study omitted: Klastersky, 1977         0.696                 0.458                 1.059       0.214    0.091
- Study omitted: Vanhaeverbeek, 1993      0.764                 0.476                 1.226       0.242    0.265
- Study omitted: Hollender, 1989          0.780                 0.486                 1.253       0.241    0.304
+ Study omitted                        Estimate  Lower bound (95% CI)  Upper bound (95% CI)  SE (log scale)  p-value
+ All studies                             0.770                 0.485                 1.222           0.236    0.267
+ Study omitted: Gonzalez, 1993           0.783                 0.477                 1.285           0.253    0.332
+ Study omitted: Prins, 1993              0.796                 0.489                 1.296           0.249    0.359
+ Study omitted: Giamarellou, 1991        0.811                 0.513                 1.281           0.233    0.369
+ Study omitted: Maller, 1993             0.715                 0.437                 1.172           0.252    0.184
+ Study omitted: Sturm, 1989              0.791                 0.494                 1.265           0.240    0.327
+ Study omitted: Marik, 1991              0.864                 0.543                 1.375           0.237    0.538
+ Study omitted: Muijsken, 1988           0.724                 0.446                 1.175           0.247    0.191
+ Study omitted: Vigano, 1992             0.750                 0.468                 1.200           0.240    0.230
+ Study omitted: Hansen, 1988             0.851                 0.542                 1.336           0.230    0.484
+ Study omitted: De Vries, 1990           0.724                 0.449                 1.166           0.243    0.184
+ Study omitted: Mauracher, 1989          0.813                 0.515                 1.283           0.233    0.375
+ Study omitted: Nordstrom, 1990          0.772                 0.474                 1.257           0.249    0.298
+ Study omitted: Rozdzinski, 1993         0.738                 0.442                 1.231           0.261    0.244
+ Study omitted: Ter Braak, 1990          0.726                 0.443                 1.189           0.252    0.204
+ Study omitted: Tulkens, 1988            0.764                 0.476                 1.227           0.242    0.266
+ Study omitted: Van der Auwera, 1991     0.791                 0.494                 1.265           0.240    0.327
+ Study omitted: Klastersky, 1977         0.696                 0.458                 1.059           0.214    0.091
+ Study omitted: Vanhaeverbeek, 1993      0.764                 0.476                 1.226           0.242    0.265
+ Study omitted: Hollender, 1989          0.780                 0.486                 1.253           0.241    0.304
```

## amino-binary-subgroup

```diff
--- 

+++ 

@@ -5,6 +5,6 @@

 Model Results
- Subgroups        k  Estimate  Lower bound (95% CI)  Upper bound (95% CI)  Std. error  p-value  z-value
- Subgroup early  10     0.623                 0.271                 1.434       0.425    0.266   -1.113
- Subgroup late    9     0.827                 0.476                 1.438       0.282    0.501   -0.673
- Overall         19     0.770                 0.485                 1.222       0.236    0.267   -1.111
+ Subgroups        k  Estimate  Lower bound (95% CI)  Upper bound (95% CI)  SE (log scale)  p-value  z-value
+ Subgroup early  10     0.623                 0.271                 1.434           0.425    0.266   -1.113
+ Subgroup late    9     0.827                 0.476                 1.438           0.282    0.501   -0.673
+ Overall         19     0.770                 0.485                 1.222           0.236    0.267   -1.111
 
```
