# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | none | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.926 -> 0.999 | - | 4.65 | 11067/7467 | 0.0048 |
| openai:openai/gpt-6-luna | fulldoc | 30 | 100.0% | 90.0% [74-97] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.996 | - | 4.33 | 60657/4616 | 0.0084 |
| openai:openai/gpt-6-luna | chunk | 30 | 100.0% | 100.0% [89-100] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 1.000 | - | 4.15 | 15835/5878 | 0.0045 |
| openai:openai/gpt-6-luna | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 1.000 | - | 4.23 | 16219/6265 | 0.0048 |
| openai:openai/gpt-6-luna | dense | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 1.000 | - | 4.68 | 14983/6117 | 0.0046 |
| openai:openai/gpt-6-luna | graph | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.997 | 100.0% | 4.26 | 15483/5011 | 0.0041 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
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
| openai:openai/gpt-6-luna | fulldoc vs none | exact_match | 30 | 2 | 3 | 25 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | exact_match | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | exact_match | 30 | 2 | 1 | 27 | +3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | exact_match | 30 | 2 | 1 | 27 | +3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | exact_match | 30 | 2 | 2 | 26 | +0.0 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
