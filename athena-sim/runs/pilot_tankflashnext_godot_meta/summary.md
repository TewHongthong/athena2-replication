# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:flashnext:instruct | none | 30 | 100.0% | 73.3% [56-86] | 96.7% | 96.7% [83-99] | - | 6.7% | 0.926 -> 0.993 | - | 29.78 | 11800/4293 | - |
| openai:flashnext:instruct | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.999 | - | 28.70 | 62980/4024 | - |
| openai:flashnext:instruct | chunk | 30 | 96.7% | 90.0% [74-97] | 96.7% | 96.7% [83-99] | - | 0.0% | 0.926 -> 0.996 | - | 32.00 | 16635/5224 | - |
| openai:flashnext:instruct | bm25 | 30 | 100.0% | 93.3% [79-98] | 96.7% | 96.7% [83-99] | - | 3.3% | 0.926 -> 0.999 | - | 30.72 | 17025/5390 | - |
| openai:flashnext:instruct | dense | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.997 | - | 28.14 | 15764/4512 | - |
| openai:flashnext:instruct | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.998 | 100.0% | 29.38 | 16258/4476 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:flashnext:instruct | none | 96.7% [30] |
| openai:flashnext:instruct | fulldoc | 100.0% [30] |
| openai:flashnext:instruct | chunk | 96.7% [30] |
| openai:flashnext:instruct | bm25 | 96.7% [30] |
| openai:flashnext:instruct | dense | 100.0% [30] |
| openai:flashnext:instruct | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:flashnext:instruct | fulldoc vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:flashnext:instruct | chunk vs none | core_ok | 30 | 1 | 1 | 28 | +0.0 | 1 | 1 |
| openai:flashnext:instruct | bm25 vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:flashnext:instruct | dense vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:flashnext:instruct | graph vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:flashnext:instruct | fulldoc vs none | exact_match | 30 | 8 | 1 | 21 | +23.3 | 0.0391 | 0.352 |
| openai:flashnext:instruct | chunk vs none | exact_match | 30 | 8 | 3 | 19 | +16.7 | 0.227 | 1 |
| openai:flashnext:instruct | bm25 vs none | exact_match | 30 | 7 | 1 | 22 | +20.0 | 0.0703 | 0.492 |
| openai:flashnext:instruct | dense vs none | exact_match | 30 | 7 | 0 | 23 | +23.3 | 0.0156 | 0.156 |
| openai:flashnext:instruct | graph vs none | exact_match | 30 | 8 | 1 | 21 | +23.3 | 0.0391 | 0.352 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
