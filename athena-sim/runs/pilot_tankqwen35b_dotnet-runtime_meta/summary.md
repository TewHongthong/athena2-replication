# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen35b | none | 30 | 100.0% | 80.0% [63-90] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 0.998 | - | 16.75 | 11937/4976 | - |
| openai:qwen35b | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 13.62 | 66417/3840 | - |
| openai:qwen35b | chunk | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 12.02 | 20586/3762 | - |
| openai:qwen35b | bm25 | 30 | 100.0% | 93.3% [79-98] | 96.7% | 96.7% [83-99] | - | 0.0% | 0.987 -> 1.000 | - | 13.45 | 23738/4518 | - |
| openai:qwen35b | dense | 30 | 100.0% | 86.7% [70-95] | 96.7% | 96.7% [83-99] | - | 0.0% | 0.987 -> 1.000 | - | 15.66 | 16958/4964 | - |
| openai:qwen35b | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | 100.0% | 12.66 | 12357/3811 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:qwen35b | none | 100.0% [30] |
| openai:qwen35b | fulldoc | 100.0% [30] |
| openai:qwen35b | chunk | 100.0% [30] |
| openai:qwen35b | bm25 | 96.7% [30] |
| openai:qwen35b | dense | 96.7% [30] |
| openai:qwen35b | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen35b | fulldoc vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:qwen35b | chunk vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:qwen35b | bm25 vs none | core_ok | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:qwen35b | dense vs none | core_ok | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:qwen35b | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:qwen35b | fulldoc vs none | exact_match | 30 | 5 | 0 | 25 | +16.7 | 0.0625 | 0.625 |
| openai:qwen35b | chunk vs none | exact_match | 30 | 4 | 0 | 26 | +13.3 | 0.125 | 1 |
| openai:qwen35b | bm25 vs none | exact_match | 30 | 5 | 1 | 24 | +13.3 | 0.219 | 1 |
| openai:qwen35b | dense vs none | exact_match | 30 | 3 | 1 | 26 | +6.7 | 0.625 | 1 |
| openai:qwen35b | graph vs none | exact_match | 30 | 5 | 0 | 25 | +16.7 | 0.0625 | 0.625 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
