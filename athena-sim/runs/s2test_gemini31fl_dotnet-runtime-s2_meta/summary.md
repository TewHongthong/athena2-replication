# Athena Sim summary

945 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_gemini31fl_dotnet-runtime-s2_meta` (test split) was started from freeze `frozen_dotnet-runtime-s2_gemini31fl_meta.json` (sha256 01ee544608b8).

## rename - pack `dotnet-runtime-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 135 | 100.0% | 94.1% [89-97] | 97.8% | 97.8% [94-99] | - | 0.0% | 0.997 -> 1.000 | - | 1.50 | 74661/15567 | 0.0420 |
| openai:google/gemini-3.1-flash-lite | fulldoc | 135 | 100.0% | 100.0% [97-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | - | 1.41 | 329676/15082 | 0.1050 |
| openai:google/gemini-3.1-flash-lite | chunk | 135 | 100.0% | 100.0% [97-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | - | 1.41 | 127185/15384 | 0.0549 |
| openai:google/gemini-3.1-flash-lite | bm25 | 135 | 100.0% | 100.0% [97-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | - | 1.39 | 136923/15403 | 0.0573 |
| openai:google/gemini-3.1-flash-lite | dense | 135 | 100.0% | 99.3% [96-100] | 99.3% | 99.3% [96-100] | - | 0.0% | 0.997 -> 1.000 | - | 1.40 | 103929/15020 | 0.0485 |
| openai:google/gemini-3.1-flash-lite | graph | 135 | 100.0% | 100.0% [97-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | 100.0% | 1.41 | 82251/17559 | 0.0469 |
| openai:google/gemini-3.1-flash-lite | naming | 135 | 100.0% | 100.0% [97-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | - | 1.40 | 112731/15239 | 0.0510 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 97.8% [135] |
| openai:google/gemini-3.1-flash-lite | fulldoc | 100.0% [135] |
| openai:google/gemini-3.1-flash-lite | chunk | 100.0% [135] |
| openai:google/gemini-3.1-flash-lite | bm25 | 100.0% [135] |
| openai:google/gemini-3.1-flash-lite | dense | 99.3% [135] |
| openai:google/gemini-3.1-flash-lite | graph | 100.0% [135] |
| openai:google/gemini-3.1-flash-lite | naming | 100.0% [135] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | core_ok | 45 | 1 | 0 | 44 | +2.2 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | core_ok | 45 | 1 | 0 | 44 | +2.2 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | core_ok | 45 | 1 | 0 | 44 | +2.2 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | core_ok | 45 | 1 | 0 | 44 | +1.5 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | core_ok | 45 | 1 | 0 | 44 | +2.2 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | naming vs none | core_ok | 45 | 1 | 0 | 44 | +2.2 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | exact_match | 45 | 3 | 0 | 42 | +5.9 | 0.25 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | exact_match | 45 | 3 | 0 | 42 | +5.9 | 0.25 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | exact_match | 45 | 3 | 0 | 42 | +5.9 | 0.25 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | exact_match | 45 | 3 | 0 | 42 | +5.2 | 0.25 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | exact_match | 45 | 3 | 0 | 42 | +5.9 | 0.25 | 1 |
| openai:google/gemini-3.1-flash-lite | naming vs none | exact_match | 45 | 3 | 0 | 42 | +5.9 | 0.25 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
