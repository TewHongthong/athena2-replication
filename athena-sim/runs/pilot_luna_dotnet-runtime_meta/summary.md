# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | none | 30 | 100.0% | 100.0% [89-100] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 4.51 | 11080/5302 | 0.0038 |
| openai:openai/gpt-6-luna | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 4.55 | 63070/3938 | 0.0083 |
| openai:openai/gpt-6-luna | chunk | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 3.83 | 19070/4845 | 0.0043 |
| openai:openai/gpt-6-luna | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 4.00 | 21852/5077 | 0.0047 |
| openai:openai/gpt-6-luna | dense | 30 | 100.0% | 100.0% [89-100] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 4.95 | 16016/7037 | 0.0051 |
| openai:openai/gpt-6-luna | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | 100.0% | 3.30 | 11530/3837 | 0.0031 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:openai/gpt-6-luna | none | 100.0% [30] |
| openai:openai/gpt-6-luna | fulldoc | 100.0% [30] |
| openai:openai/gpt-6-luna | chunk | 100.0% [30] |
| openai:openai/gpt-6-luna | bm25 | 100.0% [30] |
| openai:openai/gpt-6-luna | dense | 100.0% [30] |
| openai:openai/gpt-6-luna | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | fulldoc vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
