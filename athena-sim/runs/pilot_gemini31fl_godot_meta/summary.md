# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 30 | 100.0% | 80.0% [63-90] | 96.7% | 96.7% [83-99] | - | 6.7% | 0.926 -> 0.995 | - | 1.43 | 12494/3720 | 0.0087 |
| openai:google/gemini-3.1-flash-lite | fulldoc | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.997 | - | 1.54 | 65924/3603 | 0.0219 |
| openai:google/gemini-3.1-flash-lite | chunk | 30 | 100.0% | 100.0% [89-100] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 1.000 | - | 1.39 | 17591/3673 | 0.0099 |
| openai:google/gemini-3.1-flash-lite | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.997 | - | 1.57 | 18028/3628 | 0.0099 |
| openai:google/gemini-3.1-flash-lite | dense | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.997 | - | 1.44 | 16686/3690 | 0.0097 |
| openai:google/gemini-3.1-flash-lite | graph | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.997 | 100.0% | 1.45 | 17054/4094 | 0.0104 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 96.7% [30] |
| openai:google/gemini-3.1-flash-lite | fulldoc | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | chunk | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | bm25 | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | dense | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | exact_match | 30 | 5 | 1 | 24 | +13.3 | 0.219 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | exact_match | 30 | 6 | 0 | 24 | +20.0 | 0.0312 | 0.312 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | exact_match | 30 | 5 | 0 | 25 | +16.7 | 0.0625 | 0.562 |
| openai:google/gemini-3.1-flash-lite | dense vs none | exact_match | 30 | 5 | 0 | 25 | +16.7 | 0.0625 | 0.562 |
| openai:google/gemini-3.1-flash-lite | graph vs none | exact_match | 30 | 5 | 1 | 24 | +13.3 | 0.219 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
