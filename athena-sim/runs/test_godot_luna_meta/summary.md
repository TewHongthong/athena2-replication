# Athena Sim summary

1260 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_godot_luna_meta` (test split) was started from freeze `frozen_godot_luna_meta.json` (sha256 e23ad1e1e6f2).

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | none | 210 | 100.0% | 92.9% [89-96] | 99.5% | 99.5% [97-100] | - | 0.0% | 0.931 -> 0.999 | - | 5.40 | 75000/46554 | 0.0308 |
| openai:openai/gpt-6-luna | fulldoc | 210 | 100.0% | 94.3% [90-97] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 0.999 | - | 4.19 | 422130/31741 | 0.0581 |
| openai:openai/gpt-6-luna | chunk | 210 | 100.0% | 94.8% [91-97] | 99.0% | 99.0% [97-100] | - | 0.0% | 0.931 -> 0.999 | - | 4.96 | 106239/39843 | 0.0305 |
| openai:openai/gpt-6-luna | bm25 | 210 | 100.0% | 95.2% [91-97] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 0.999 | - | 3.99 | 109152/40360 | 0.0311 |
| openai:openai/gpt-6-luna | dense | 210 | 100.0% | 96.2% [93-98] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 1.000 | - | 5.33 | 103848/42731 | 0.0318 |
| openai:openai/gpt-6-luna | graph | 210 | 100.0% | 86.2% [81-90] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 0.998 | 100.0% | 4.32 | 104682/35551 | 0.0282 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:openai/gpt-6-luna | none | 99.5% [210] |
| openai:openai/gpt-6-luna | fulldoc | 100.0% [210] |
| openai:openai/gpt-6-luna | chunk | 99.0% [210] |
| openai:openai/gpt-6-luna | bm25 | 100.0% [210] |
| openai:openai/gpt-6-luna | dense | 100.0% [210] |
| openai:openai/gpt-6-luna | graph | 100.0% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | fulldoc vs none | core_ok | 70 | 1 | 0 | 69 | +0.5 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | core_ok | 70 | 1 | 1 | 68 | -0.5 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | core_ok | 70 | 1 | 0 | 69 | +0.5 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | core_ok | 70 | 1 | 0 | 69 | +0.5 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | core_ok | 70 | 1 | 0 | 69 | +0.5 | 1 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | exact_match | 70 | 8 | 5 | 57 | +1.4 | 0.581 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | exact_match | 70 | 8 | 4 | 58 | +1.9 | 0.388 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | exact_match | 70 | 7 | 4 | 59 | +2.4 | 0.549 | 1 |
| openai:openai/gpt-6-luna | dense vs none | exact_match | 70 | 8 | 5 | 57 | +3.3 | 0.581 | 1 |
| openai:openai/gpt-6-luna | graph vs none | exact_match | 70 | 8 | 10 | 52 | -6.7 | 0.815 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
