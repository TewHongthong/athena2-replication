# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:flashnext:instruct | none | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 0.999 | - | 27.04 | 11937/3938 | - |
| openai:flashnext:instruct | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 26.90 | 66417/3934 | - |
| openai:flashnext:instruct | chunk | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 26.13 | 20586/4199 | - |
| openai:flashnext:instruct | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 24.49 | 23738/3927 | - |
| openai:flashnext:instruct | dense | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 27.08 | 16958/4151 | - |
| openai:flashnext:instruct | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | 100.0% | 25.25 | 12357/3712 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:flashnext:instruct | none | 100.0% [30] |
| openai:flashnext:instruct | fulldoc | 100.0% [30] |
| openai:flashnext:instruct | chunk | 100.0% [30] |
| openai:flashnext:instruct | bm25 | 100.0% [30] |
| openai:flashnext:instruct | dense | 100.0% [30] |
| openai:flashnext:instruct | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:flashnext:instruct | fulldoc vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:flashnext:instruct | chunk vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:flashnext:instruct | bm25 vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:flashnext:instruct | dense vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:flashnext:instruct | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:flashnext:instruct | fulldoc vs none | exact_match | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:flashnext:instruct | chunk vs none | exact_match | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:flashnext:instruct | bm25 vs none | exact_match | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:flashnext:instruct | dense vs none | exact_match | 30 | 1 | 1 | 28 | +0.0 | 1 | 1 |
| openai:flashnext:instruct | graph vs none | exact_match | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
