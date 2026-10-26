# Athena Sim summary

1260 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_godot_gemma4_local_meta` (test split) was started from freeze `frozen_godot_gemma4_local_meta.json` (sha256 090b24f26ad9).

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 210 | 100.0% | 83.3% [78-88] | 98.6% | 98.6% [96-100] | - | 0.0% | 0.931 -> 0.996 | - | 2.85 | 87093/25939 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 210 | 100.0% | 96.7% [93-98] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 1.000 | - | 3.70 | 461103/24870 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 210 | 100.0% | 92.4% [88-95] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 0.999 | - | 3.13 | 120552/26858 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 210 | 100.0% | 91.4% [87-95] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 0.999 | - | 2.90 | 123822/27109 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 210 | 100.0% | 96.2% [93-98] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 0.999 | - | 3.06 | 117984/27402 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 210 | 100.0% | 91.9% [87-95] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 0.999 | 100.0% | 3.07 | 117681/27776 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 98.6% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 100.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 100.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 100.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 100.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 100.0% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | core_ok | 70 | 1 | 0 | 69 | +1.4 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | core_ok | 70 | 1 | 0 | 69 | +1.4 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | core_ok | 70 | 1 | 0 | 69 | +1.4 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | core_ok | 70 | 1 | 0 | 69 | +1.4 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | core_ok | 70 | 1 | 0 | 69 | +1.4 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | exact_match | 70 | 13 | 3 | 54 | +13.3 | 0.0213 | 0.191 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | exact_match | 70 | 10 | 3 | 57 | +9.0 | 0.0923 | 0.738 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | exact_match | 70 | 10 | 3 | 57 | +8.1 | 0.0923 | 0.738 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | exact_match | 70 | 11 | 1 | 58 | +12.9 | 0.00635 | 0.0635 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | exact_match | 70 | 11 | 4 | 55 | +8.6 | 0.118 | 0.738 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
