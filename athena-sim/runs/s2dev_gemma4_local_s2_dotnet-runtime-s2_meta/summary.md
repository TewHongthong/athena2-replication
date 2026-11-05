# Athena Sim summary

133 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 19 | 100.0% | 94.7% [75-99] | 94.7% | 94.7% [75-99] | - | 0.0% | 0.998 -> 1.000 | - | 2.76 | 11119/2021 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 19 | 100.0% | 100.0% [83-100] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.998 -> 1.000 | - | 3.67 | 47010/2099 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 19 | 100.0% | 94.7% [75-99] | 94.7% | 94.7% [75-99] | - | 0.0% | 0.998 -> 1.000 | - | 3.14 | 19748/2231 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 19 | 100.0% | 94.7% [75-99] | 94.7% | 94.7% [75-99] | - | 0.0% | 0.998 -> 1.000 | - | 2.99 | 20086/2220 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 19 | 100.0% | 94.7% [75-99] | 94.7% | 94.7% [75-99] | - | 0.0% | 0.998 -> 1.000 | - | 2.98 | 14814/2173 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 19 | 100.0% | 89.5% [69-97] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.998 -> 0.999 | 100.0% | 3.35 | 12193/2461 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming | 19 | 100.0% | 100.0% [83-100] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.998 -> 1.000 | - | 2.89 | 16477/2004 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 94.7% [19] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 100.0% [19] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 94.7% [19] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 94.7% [19] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 94.7% [19] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 100.0% [19] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming | 100.0% [19] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | core_ok | 19 | 1 | 0 | 18 | +5.3 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | core_ok | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | core_ok | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | core_ok | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | core_ok | 19 | 1 | 0 | 18 | +5.3 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming vs none | core_ok | 19 | 1 | 0 | 18 | +5.3 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | exact_match | 19 | 1 | 0 | 18 | +5.3 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | exact_match | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | exact_match | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | exact_match | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | exact_match | 19 | 1 | 2 | 16 | -5.3 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming vs none | exact_match | 19 | 1 | 0 | 18 | +5.3 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
