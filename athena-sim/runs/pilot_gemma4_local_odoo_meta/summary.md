# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 30 | 100.0% | 100.0% [89-100] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.952 -> 1.000 | - | 2.60 | 14456/3376 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 8.55 | 400046/3382 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 3.22 | 25762/3739 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 3.07 | 28576/3728 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 3.04 | 23653/3785 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | 100.0% | 2.53 | 15506/3196 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 100.0% [30] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 100.0% [30] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 100.0% [30] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 100.0% [30] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 100.0% [30] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
