# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:Uncensored | none | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 5.63 | 13229/3790 | - |
| openai:Uncensored | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 6.91 | 371519/3686 | - |
| openai:Uncensored | chunk | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 4.73 | 23351/4240 | - |
| openai:Uncensored | bm25 | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 3.39 | 25863/4192 | - |
| openai:Uncensored | dense | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 3.30 | 21742/4357 | - |
| openai:Uncensored | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | 100.0% | 2.95 | 14249/3624 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:Uncensored | none | 100.0% [30] |
| openai:Uncensored | fulldoc | 100.0% [30] |
| openai:Uncensored | chunk | 100.0% [30] |
| openai:Uncensored | bm25 | 100.0% [30] |
| openai:Uncensored | dense | 100.0% [30] |
| openai:Uncensored | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:Uncensored | fulldoc vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | chunk vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | bm25 vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | dense vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | fulldoc vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | chunk vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | bm25 vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:Uncensored | dense vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:Uncensored | graph vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
