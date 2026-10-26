# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:flashnext:instruct | none | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 32.50 | 13229/3777 | - |
| openai:flashnext:instruct | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 35.06 | 371519/3946 | - |
| openai:flashnext:instruct | chunk | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 23.77 | 23351/4397 | - |
| openai:flashnext:instruct | bm25 | 30 | 100.0% | 86.7% [70-95] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 0.995 | - | 23.15 | 25863/4757 | - |
| openai:flashnext:instruct | dense | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 26.17 | 21742/4351 | - |
| openai:flashnext:instruct | graph | 30 | 100.0% | 100.0% [89-100] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.952 -> 1.000 | 100.0% | 27.79 | 14249/3567 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
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
| openai:flashnext:instruct | fulldoc vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:flashnext:instruct | chunk vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:flashnext:instruct | bm25 vs none | exact_match | 30 | 0 | 3 | 27 | -10.0 | 0.25 | 1 |
| openai:flashnext:instruct | dense vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:flashnext:instruct | graph vs none | exact_match | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
