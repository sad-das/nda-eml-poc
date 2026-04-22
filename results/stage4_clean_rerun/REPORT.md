# NDA EML PoC Stage 4 report

Stage 4 implements Macro-node Dialectical Curriculum Discovery. Verified witnesses are promoted to DKG macro-nodes with `proposal_cost=1` while retaining `historical_expansion_cost` via raw EML expansion.

## Curriculum discoveries

| Level | Target | Macro | Found | Surface | Macro depth | Historical nodes | Generated | Scanned |
|---:|---|---|---:|---|---:|---:|---:|---:|
| 1 | exp_x | exp | 1 | `eml(x,1)` | 1 | 3 | 1446 | 1 |
| 1 | ln_x | ln | 1 | `eml(1,eml(eml(1,x),1))` | 3 | 7 | 1446 | 1 |
| 1 | e_const | e | 1 | `eml(1,1)` | 1 | 3 | 6 | 1 |
| 1 | zero_const | zero | 1 | `ln(1)` | 1 | 7 | 363 | 7 |
| 2 | x_minus_y | sub | 1 | `eml(ln(x),exp(y))` | 2 | 11 | 1194 | 329 |
| 2 | neg_x | neg | 1 | `sub(zero,x)` | 1 | 17 | 4914 | 36 |
| 2 | x_plus_y | add | 1 | `sub(sub(x,zero),sub(zero,y))` | 2 | 43 | 6252 | 2510 |
| 3 | x_times_y | mul | 1 | `exp(add(ln(x),ln(y)))` | 3 | 57 | 3249 | 1 |
| 3 | x_div_y | div | 1 | `exp(sub(ln(x),ln(y)))` | 3 | 25 | 4693 | 1 |
| 4 | x_square | square | 1 | `mul(x,x)` | 1 | 57 | 3765 | 1 |

## Flat raw-EML boundary

| Target | Raw max depth | Pool size | Found | Scanned |
|---|---:|---:|---:|---:|
| ln_x | 3 | 1446 | 1 | 53 |
| x_plus_y | 3 | 21612 | 0 | 21612 |
| x_times_y | 3 | 21612 | 0 | 21612 |
| x_div_y | 3 | 21612 | 0 | 21612 |
| x_square | 3 | 1446 | 0 | 1446 |

## Taylor trap
Accepted: `False`; reasons: `unbounded_node_growth;asymptotic_stress_failure`; train MSE: `3.350e-18`; asymptotic MSE: `2.948e-01`.

## RLCR cleanliness
Scalar penalties used: `0`. Fatal rejections are stored as graveyard topology, not reward shaping.