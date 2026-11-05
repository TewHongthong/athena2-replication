# Athena Sim summary

1470 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_luna_godot-s2_meta` (test split) was started from freeze `frozen_godot-s2_luna_meta.json` (sha256 c97468b959e1).

## rename - pack `godot-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | none | 210 | 100.0% | 98.6% [96-100] | 98.6% | 98.6% [96-100] | - | 0.0% | 0.990 -> 1.000 | - | 5.49 | 75243/55444 | 0.0352 |
| openai:openai/gpt-6-luna | fulldoc | 210 | 100.0% | 90.5% [86-94] | 95.7% | 95.7% [92-98] | - | 0.0% | 0.990 -> 0.998 | - | 4.06 | 422373/33137 | 0.0588 |
| openai:openai/gpt-6-luna | chunk | 210 | 100.0% | 96.2% [93-98] | 96.7% | 96.7% [93-98] | - | 0.0% | 0.990 -> 1.000 | - | 5.32 | 114489/42423 | 0.0327 |
| openai:openai/gpt-6-luna | bm25 | 210 | 100.0% | 97.1% [94-99] | 97.1% | 97.1% [94-99] | - | 0.0% | 0.990 -> 1.000 | - | 4.37 | 116454/41960 | 0.0326 |
| openai:openai/gpt-6-luna | dense | 210 | 100.0% | 95.7% [92-98] | 95.7% | 95.7% [92-98] | - | 0.0% | 0.990 -> 0.999 | - | 5.34 | 101469/42881 | 0.0316 |
| openai:openai/gpt-6-luna | graph | 210 | 100.0% | 92.9% [89-96] | 99.0% | 99.0% [97-100] | - | 0.0% | 0.990 -> 0.998 | 100.0% | 4.33 | 107793/34118 | 0.0278 |
| openai:openai/gpt-6-luna | naming | 210 | 100.0% | 86.7% [81-91] | 98.1% | 98.1% [95-99] | - | 0.0% | 0.990 -> 0.995 | - | 5.08 | 105063/37048 | 0.0290 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:openai/gpt-6-luna | none | 98.6% [210] |
| openai:openai/gpt-6-luna | fulldoc | 95.7% [210] |
| openai:openai/gpt-6-luna | chunk | 96.7% [210] |
| openai:openai/gpt-6-luna | bm25 | 97.1% [210] |
| openai:openai/gpt-6-luna | dense | 95.7% [210] |
| openai:openai/gpt-6-luna | graph | 99.0% [210] |
| openai:openai/gpt-6-luna | naming | 98.1% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | fulldoc vs none | core_ok | 70 | 1 | 4 | 65 | -2.9 | 0.375 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | core_ok | 70 | 0 | 3 | 67 | -1.9 | 0.25 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | core_ok | 70 | 0 | 3 | 67 | -1.4 | 0.25 | 1 |
| openai:openai/gpt-6-luna | dense vs none | core_ok | 70 | 0 | 4 | 66 | -2.9 | 0.125 | 1 |
| openai:openai/gpt-6-luna | graph vs none | core_ok | 70 | 1 | 1 | 68 | +0.5 | 1 | 1 |
| openai:openai/gpt-6-luna | naming vs none | core_ok | 70 | 1 | 2 | 67 | -0.5 | 1 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | exact_match | 70 | 1 | 8 | 61 | -8.1 | 0.0391 | 0.43 |
| openai:openai/gpt-6-luna | chunk vs none | exact_match | 70 | 0 | 4 | 66 | -2.4 | 0.125 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | exact_match | 70 | 0 | 3 | 67 | -1.4 | 0.25 | 1 |
| openai:openai/gpt-6-luna | dense vs none | exact_match | 70 | 0 | 4 | 66 | -2.9 | 0.125 | 1 |
| openai:openai/gpt-6-luna | graph vs none | exact_match | 70 | 1 | 7 | 62 | -5.7 | 0.0703 | 0.703 |
| openai:openai/gpt-6-luna | naming vs none | exact_match | 70 | 1 | 12 | 57 | -11.9 | 0.00342 | 0.041 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
