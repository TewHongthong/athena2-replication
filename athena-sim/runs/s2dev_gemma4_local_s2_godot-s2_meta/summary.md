# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `godot-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 30 | 100.0% | 73.3% [56-86] | 80.0% | 80.0% [63-90] | - | 3.3% | 0.991 -> 0.994 | - | 4.25 | 13187/5826 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 30 | 96.7% | 83.3% [66-93] | 96.7% | 96.7% [83-99] | - | 0.0% | 0.991 -> 0.998 | - | 3.92 | 66617/3812 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 30 | 100.0% | 93.3% [79-98] | 96.7% | 96.7% [83-99] | - | 0.0% | 0.991 -> 1.000 | - | 3.25 | 19421/4090 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.991 -> 1.000 | - | 3.03 | 19596/4105 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 30 | 100.0% | 90.0% [74-97] | 96.7% | 96.7% [83-99] | - | 0.0% | 0.991 -> 0.998 | - | 3.47 | 16870/4506 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 30 | 100.0% | 86.7% [70-95] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.991 -> 0.998 | 100.0% | 3.11 | 18017/3942 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming | 30 | 100.0% | 73.3% [56-86] | 96.7% | 96.7% [83-99] | - | 0.0% | 0.991 -> 0.995 | - | 3.35 | 17747/4126 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 80.0% [30] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 96.7% [30] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 96.7% [30] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 100.0% [30] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 96.7% [30] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 100.0% [30] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming | 96.7% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | core_ok | 30 | 6 | 1 | 23 | +16.7 | 0.125 | 0.875 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | core_ok | 30 | 5 | 0 | 25 | +16.7 | 0.0625 | 0.5 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | core_ok | 30 | 6 | 0 | 24 | +20.0 | 0.0312 | 0.344 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | core_ok | 30 | 6 | 1 | 23 | +16.7 | 0.125 | 0.875 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | core_ok | 30 | 6 | 0 | 24 | +20.0 | 0.0312 | 0.344 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming vs none | core_ok | 30 | 6 | 1 | 23 | +16.7 | 0.125 | 0.875 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | exact_match | 30 | 4 | 1 | 25 | +10.0 | 0.375 | 0.875 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | exact_match | 30 | 6 | 0 | 24 | +20.0 | 0.0312 | 0.344 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | exact_match | 30 | 7 | 0 | 23 | +23.3 | 0.0156 | 0.188 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | exact_match | 30 | 6 | 1 | 23 | +16.7 | 0.125 | 0.875 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | exact_match | 30 | 5 | 1 | 24 | +13.3 | 0.219 | 0.875 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming vs none | exact_match | 30 | 4 | 4 | 22 | +0.0 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
