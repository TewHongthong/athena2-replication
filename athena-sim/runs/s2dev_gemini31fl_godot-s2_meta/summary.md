# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `godot-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 30 | 100.0% | 83.3% [66-93] | 90.0% | 90.0% [74-97] | - | 6.7% | 0.991 -> 0.997 | - | 1.77 | 12797/4134 | 0.0094 |
| openai:google/gemini-3.1-flash-lite | fulldoc | 30 | 100.0% | 86.7% [70-95] | 90.0% | 90.0% [74-97] | - | 3.3% | 0.991 -> 0.997 | - | 1.59 | 66227/3559 | 0.0219 |
| openai:google/gemini-3.1-flash-lite | chunk | 30 | 100.0% | 93.3% [79-98] | 93.3% | 93.3% [79-98] | - | 6.7% | 0.991 -> 0.998 | - | 1.39 | 19031/3694 | 0.0103 |
| openai:google/gemini-3.1-flash-lite | bm25 | 30 | 100.0% | 93.3% [79-98] | 93.3% | 93.3% [79-98] | - | 3.3% | 0.991 -> 0.998 | - | 1.42 | 19206/3705 | 0.0104 |
| openai:google/gemini-3.1-flash-lite | dense | 30 | 100.0% | 90.0% [74-97] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.991 -> 0.998 | - | 1.43 | 16480/3800 | 0.0098 |
| openai:google/gemini-3.1-flash-lite | graph | 30 | 100.0% | 76.7% [59-88] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.991 -> 0.989 | 100.0% | 1.68 | 17627/4172 | 0.0107 |
| openai:google/gemini-3.1-flash-lite | naming | 30 | 100.0% | 60.0% [42-75] | 86.7% | 86.7% [70-95] | - | 0.0% | 0.991 -> 0.984 | - | 1.63 | 17357/3994 | 0.0103 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 90.0% [30] |
| openai:google/gemini-3.1-flash-lite | fulldoc | 90.0% [30] |
| openai:google/gemini-3.1-flash-lite | chunk | 93.3% [30] |
| openai:google/gemini-3.1-flash-lite | bm25 | 93.3% [30] |
| openai:google/gemini-3.1-flash-lite | dense | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | graph | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | naming | 86.7% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | core_ok | 30 | 1 | 1 | 28 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | core_ok | 30 | 2 | 1 | 27 | +3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | core_ok | 30 | 3 | 2 | 25 | +3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | core_ok | 30 | 3 | 0 | 27 | +10.0 | 0.25 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | core_ok | 30 | 3 | 0 | 27 | +10.0 | 0.25 | 1 |
| openai:google/gemini-3.1-flash-lite | naming vs none | core_ok | 30 | 2 | 3 | 25 | -3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | exact_match | 30 | 2 | 1 | 27 | +3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | exact_match | 30 | 4 | 1 | 25 | +10.0 | 0.375 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | exact_match | 30 | 5 | 2 | 23 | +10.0 | 0.453 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | exact_match | 30 | 3 | 1 | 26 | +6.7 | 0.625 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | exact_match | 30 | 2 | 4 | 24 | -6.7 | 0.688 | 1 |
| openai:google/gemini-3.1-flash-lite | naming vs none | exact_match | 30 | 1 | 8 | 21 | -23.3 | 0.0391 | 0.469 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
