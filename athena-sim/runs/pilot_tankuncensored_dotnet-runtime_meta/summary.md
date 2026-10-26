# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:Uncensored | none | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 2.89 | 11937/3698 | - |
| openai:Uncensored | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 2.67 | 66417/3319 | - |
| openai:Uncensored | chunk | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 2.43 | 20586/3260 | - |
| openai:Uncensored | bm25 | 30 | 100.0% | 93.3% [79-98] | 96.7% | 96.7% [83-99] | - | 0.0% | 0.987 -> 1.000 | - | 2.36 | 23738/3603 | - |
| openai:Uncensored | dense | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 2.52 | 16958/4058 | - |
| openai:Uncensored | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | 100.0% | 2.34 | 12357/3660 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:Uncensored | none | 100.0% [30] |
| openai:Uncensored | fulldoc | 100.0% [30] |
| openai:Uncensored | chunk | 100.0% [30] |
| openai:Uncensored | bm25 | 96.7% [30] |
| openai:Uncensored | dense | 100.0% [30] |
| openai:Uncensored | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:Uncensored | fulldoc vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | chunk vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | bm25 vs none | core_ok | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:Uncensored | dense vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | fulldoc vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | chunk vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | bm25 vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:Uncensored | dense vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | graph vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
