# Athena Sim summary

1470 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_gemma4_local_s2_godot-s2_meta` (test split) was started from freeze `frozen_godot-s2_gemma4_local_s2_meta.json` (sha256 eef90303daa7).

## rename - pack `godot-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 210 | 99.0% | 78.1% [72-83] | 81.9% | 81.9% [76-87] | - | 2.9% | 0.990 -> 0.995 | - | 3.40 | 87378/32208 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 210 | 95.2% | 83.3% [78-88] | 90.0% | 90.0% [85-93] | - | 0.0% | 0.990 -> 0.996 | - | 4.93 | 461388/38360 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 210 | 99.0% | 91.9% [87-95] | 91.9% | 91.9% [87-95] | - | 1.4% | 0.990 -> 0.999 | - | 3.05 | 129441/27006 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 210 | 99.0% | 92.9% [89-96] | 93.3% | 93.3% [89-96] | - | 1.4% | 0.990 -> 0.999 | - | 2.94 | 131763/27545 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 210 | 100.0% | 87.6% [82-91] | 88.6% | 88.6% [84-92] | - | 0.5% | 0.990 -> 0.998 | - | 3.54 | 115377/32992 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 210 | 100.0% | 95.2% [91-97] | 99.0% | 99.0% [97-100] | - | 0.0% | 0.990 -> 0.999 | 100.0% | 3.16 | 121188/28783 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming | 210 | 97.6% | 73.8% [67-79] | 85.7% | 85.7% [80-90] | - | 0.0% | 0.990 -> 0.990 | - | 4.50 | 119298/42146 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 81.9% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 90.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 91.9% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 93.3% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 88.6% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 99.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming | 85.7% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | core_ok | 70 | 15 | 8 | 47 | +8.1 | 0.21 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | core_ok | 70 | 16 | 5 | 49 | +10.0 | 0.0266 | 0.186 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | core_ok | 70 | 15 | 3 | 52 | +11.4 | 0.00754 | 0.0603 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | core_ok | 70 | 11 | 5 | 54 | +6.7 | 0.21 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | core_ok | 70 | 18 | 1 | 51 | +17.1 | 7.63e-05 | 0.000916 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming vs none | core_ok | 70 | 14 | 11 | 45 | +3.8 | 0.69 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | exact_match | 70 | 17 | 10 | 43 | +5.2 | 0.248 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | exact_match | 70 | 20 | 5 | 45 | +13.8 | 0.00408 | 0.0367 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | exact_match | 70 | 19 | 3 | 48 | +14.8 | 0.000855 | 0.00941 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | exact_match | 70 | 15 | 5 | 50 | +9.5 | 0.0414 | 0.248 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | exact_match | 70 | 21 | 4 | 45 | +17.1 | 0.000911 | 0.00941 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming vs none | exact_match | 70 | 15 | 20 | 35 | -4.3 | 0.5 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
