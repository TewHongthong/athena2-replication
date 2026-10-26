# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen35b | none | 30 | 100.0% | 73.3% [56-86] | 96.7% | 96.7% [83-99] | - | 6.7% | 0.926 -> 0.991 | - | 14.27 | 11800/4441 | - |
| openai:qwen35b | fulldoc | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.993 | - | 13.74 | 62980/4192 | - |
| openai:qwen35b | chunk | 30 | 100.0% | 86.7% [70-95] | 100.0% | 100.0% [89-100] | - | 6.7% | 0.926 -> 0.996 | - | 12.89 | 16635/4412 | - |
| openai:qwen35b | bm25 | 30 | 100.0% | 76.7% [59-88] | 100.0% | 100.0% [89-100] | - | 6.7% | 0.926 -> 0.996 | - | 13.83 | 17025/4640 | - |
| openai:qwen35b | dense | 30 | 100.0% | 90.0% [74-97] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.995 | - | 12.97 | 15764/4112 | - |
| openai:qwen35b | graph | 30 | 100.0% | 90.0% [74-97] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.993 | 100.0% | 14.96 | 16258/4694 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:qwen35b | none | 96.7% [30] |
| openai:qwen35b | fulldoc | 100.0% [30] |
| openai:qwen35b | chunk | 100.0% [30] |
| openai:qwen35b | bm25 | 100.0% [30] |
| openai:qwen35b | dense | 100.0% [30] |
| openai:qwen35b | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen35b | fulldoc vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:qwen35b | chunk vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:qwen35b | bm25 vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:qwen35b | dense vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:qwen35b | graph vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:qwen35b | fulldoc vs none | exact_match | 30 | 6 | 0 | 24 | +20.0 | 0.0312 | 0.312 |
| openai:qwen35b | chunk vs none | exact_match | 30 | 6 | 2 | 22 | +13.3 | 0.289 | 1 |
| openai:qwen35b | bm25 vs none | exact_match | 30 | 6 | 5 | 19 | +3.3 | 1 | 1 |
| openai:qwen35b | dense vs none | exact_match | 30 | 7 | 2 | 21 | +16.7 | 0.18 | 1 |
| openai:qwen35b | graph vs none | exact_match | 30 | 6 | 1 | 23 | +16.7 | 0.125 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
