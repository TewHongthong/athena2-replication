# Athena Sim summary

1260 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_odoo_gemma4_local_meta` (test split) was started from freeze `frozen_odoo_gemma4_local_meta.json` (sha256 9e44991fa339).

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 210 | 100.0% | 94.8% [91-97] | 100.0% | 100.0% [98-100] | - | 1.0% | 0.956 -> 0.999 | - | 2.65 | 99081/24218 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 210 | 100.0% | 96.7% [93-98] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.956 -> 1.000 | - | 8.81 | 2798211/23571 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 210 | 100.0% | 96.7% [93-98] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.956 -> 1.000 | - | 3.22 | 185088/25940 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 210 | 100.0% | 94.8% [91-97] | 100.0% | 100.0% [98-100] | - | 0.5% | 0.956 -> 1.000 | - | 3.04 | 201264/26348 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 210 | 100.0% | 94.3% [90-97] | 100.0% | 100.0% [98-100] | - | 1.4% | 0.956 -> 0.999 | - | 2.98 | 143718/26288 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 210 | 100.0% | 98.6% [96-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.956 -> 1.000 | 100.0% | 2.53 | 106431/22429 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 100.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 100.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 100.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 100.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 100.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 100.0% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | exact_match | 70 | 2 | 1 | 67 | +1.9 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | exact_match | 70 | 2 | 0 | 68 | +1.9 | 0.5 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | exact_match | 70 | 1 | 1 | 68 | -0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | exact_match | 70 | 1 | 2 | 67 | -0.5 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | exact_match | 70 | 3 | 0 | 67 | +3.8 | 0.25 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
