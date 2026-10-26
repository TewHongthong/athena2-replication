# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen35b | none | 30 | 100.0% | 83.3% [66-93] | 100.0% | 100.0% [89-100] | - | 6.7% | 0.952 -> 0.998 | - | 29.75 | 13229/4792 | - |
| openai:qwen35b | fulldoc | 30 | 100.0% | 90.0% [74-97] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 0.998 | - | 29.89 | 371519/4588 | - |
| openai:qwen35b | chunk | 30 | 96.7% | 70.0% [52-83] | 96.7% | 96.7% [83-99] | - | 3.3% | 0.952 -> 0.996 | - | 20.20 | 23351/4734 | - |
| openai:qwen35b | bm25 | 30 | 100.0% | 73.3% [56-86] | 100.0% | 100.0% [89-100] | - | 6.7% | 0.952 -> 0.996 | - | 17.53 | 25863/4417 | - |
| openai:qwen35b | dense | 30 | 100.0% | 76.7% [59-88] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 0.997 | - | 22.37 | 21742/4508 | - |
| openai:qwen35b | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | 100.0% | 21.40 | 14249/3770 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:qwen35b | none | 100.0% [30] |
| openai:qwen35b | fulldoc | 100.0% [30] |
| openai:qwen35b | chunk | 96.7% [30] |
| openai:qwen35b | bm25 | 100.0% [30] |
| openai:qwen35b | dense | 100.0% [30] |
| openai:qwen35b | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen35b | fulldoc vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:qwen35b | chunk vs none | core_ok | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:qwen35b | bm25 vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:qwen35b | dense vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:qwen35b | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:qwen35b | fulldoc vs none | exact_match | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:qwen35b | chunk vs none | exact_match | 30 | 1 | 5 | 24 | -13.3 | 0.219 | 1 |
| openai:qwen35b | bm25 vs none | exact_match | 30 | 1 | 4 | 25 | -10.0 | 0.375 | 1 |
| openai:qwen35b | dense vs none | exact_match | 30 | 2 | 4 | 24 | -6.7 | 0.688 | 1 |
| openai:qwen35b | graph vs none | exact_match | 30 | 4 | 0 | 26 | +13.3 | 0.125 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
