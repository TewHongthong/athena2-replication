# Athena Sim summary

1470 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_gemini31fl_godot-s2_meta` (test split) was started from freeze `frozen_godot-s2_gemini31fl_meta.json` (sha256 b56db8802442).

## rename - pack `godot-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 210 | 100.0% | 73.3% [67-79] | 85.2% | 85.2% [80-89] | - | 4.3% | 0.990 -> 0.993 | - | 1.44 | 84648/28178 | 0.0634 |
| openai:google/gemini-3.1-flash-lite | fulldoc | 210 | 100.0% | 88.6% [84-92] | 91.4% | 91.4% [87-95] | - | 0.0% | 0.990 -> 0.996 | - | 1.40 | 458658/25300 | 0.1526 |
| openai:google/gemini-3.1-flash-lite | chunk | 210 | 100.0% | 92.9% [89-96] | 96.7% | 96.7% [93-98] | - | 1.0% | 0.990 -> 0.998 | - | 1.39 | 126711/26040 | 0.0707 |
| openai:google/gemini-3.1-flash-lite | bm25 | 210 | 100.0% | 92.4% [88-95] | 94.3% | 94.3% [90-97] | - | 2.4% | 0.990 -> 0.999 | - | 1.39 | 129033/25763 | 0.0709 |
| openai:google/gemini-3.1-flash-lite | dense | 210 | 100.0% | 87.1% [82-91] | 95.2% | 95.2% [91-97] | - | 1.9% | 0.990 -> 0.997 | - | 1.43 | 112647/26595 | 0.0681 |
| openai:google/gemini-3.1-flash-lite | graph | 210 | 100.0% | 85.2% [80-89] | 98.1% | 98.1% [95-99] | - | 0.0% | 0.990 -> 0.994 | 100.0% | 1.37 | 118458/28644 | 0.0726 |
| openai:google/gemini-3.1-flash-lite | naming | 210 | 100.0% | 69.5% [63-75] | 80.5% | 80.5% [75-85] | - | 0.0% | 0.990 -> 0.987 | - | 1.45 | 116568/28995 | 0.0726 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 85.2% [210] |
| openai:google/gemini-3.1-flash-lite | fulldoc | 91.4% [210] |
| openai:google/gemini-3.1-flash-lite | chunk | 96.7% [210] |
| openai:google/gemini-3.1-flash-lite | bm25 | 94.3% [210] |
| openai:google/gemini-3.1-flash-lite | dense | 95.2% [210] |
| openai:google/gemini-3.1-flash-lite | graph | 98.1% [210] |
| openai:google/gemini-3.1-flash-lite | naming | 80.5% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | core_ok | 70 | 17 | 8 | 45 | +6.2 | 0.108 | 0.323 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | core_ok | 70 | 17 | 1 | 52 | +11.4 | 0.000145 | 0.0013 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | core_ok | 70 | 16 | 2 | 52 | +9.0 | 0.00131 | 0.0105 |
| openai:google/gemini-3.1-flash-lite | dense vs none | core_ok | 70 | 16 | 3 | 51 | +10.0 | 0.00443 | 0.0266 |
| openai:google/gemini-3.1-flash-lite | graph vs none | core_ok | 70 | 18 | 1 | 51 | +12.9 | 7.63e-05 | 0.000763 |
| openai:google/gemini-3.1-flash-lite | naming vs none | core_ok | 70 | 14 | 17 | 39 | -4.8 | 0.72 | 1 |
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | exact_match | 70 | 25 | 9 | 36 | +15.2 | 0.00904 | 0.0452 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | exact_match | 70 | 25 | 2 | 43 | +19.5 | 5.65e-06 | 6.78e-05 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | exact_match | 70 | 24 | 2 | 44 | +19.0 | 1.05e-05 | 0.000115 |
| openai:google/gemini-3.1-flash-lite | dense vs none | exact_match | 70 | 22 | 5 | 43 | +13.8 | 0.00151 | 0.0106 |
| openai:google/gemini-3.1-flash-lite | graph vs none | exact_match | 70 | 22 | 9 | 39 | +11.9 | 0.0294 | 0.118 |
| openai:google/gemini-3.1-flash-lite | naming vs none | exact_match | 70 | 18 | 19 | 33 | -3.8 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
