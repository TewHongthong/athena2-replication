# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 2.41 | 12536/3176 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 3.43 | 69206/3218 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 2.72 | 21725/3145 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 2.70 | 25132/3268 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 2.65 | 17777/3293 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | 100.0% | 2.40 | 12986/3117 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
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
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | exact_match | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | exact_match | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | exact_match | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | exact_match | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | exact_match | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
