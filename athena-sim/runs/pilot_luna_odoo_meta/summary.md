# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | none | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.952 -> 0.999 | - | 5.19 | 12412/6330 | 0.0044 |
| openai:openai/gpt-6-luna | fulldoc | 30 | 100.0% | 90.0% [74-97] | 96.7% | 96.7% [83-99] | - | 3.3% | 0.952 -> 0.998 | - | 4.59 | 355192/5031 | 0.0380 |
| openai:openai/gpt-6-luna | chunk | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.952 -> 0.996 | - | 4.84 | 21954/5728 | 0.0051 |
| openai:openai/gpt-6-luna | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.952 -> 0.999 | - | 4.74 | 24284/5901 | 0.0054 |
| openai:openai/gpt-6-luna | dense | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.952 -> 0.999 | - | 4.62 | 20510/6177 | 0.0051 |
| openai:openai/gpt-6-luna | graph | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.952 -> 0.998 | 100.0% | 3.87 | 13432/4540 | 0.0036 |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:openai/gpt-6-luna | none | 100.0% [30] |
| openai:openai/gpt-6-luna | fulldoc | 96.7% [30] |
| openai:openai/gpt-6-luna | chunk | 100.0% [30] |
| openai:openai/gpt-6-luna | bm25 | 100.0% [30] |
| openai:openai/gpt-6-luna | dense | 100.0% [30] |
| openai:openai/gpt-6-luna | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | fulldoc vs none | core_ok | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | exact_match | 30 | 1 | 3 | 26 | -6.7 | 0.625 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | exact_match | 30 | 1 | 2 | 27 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
