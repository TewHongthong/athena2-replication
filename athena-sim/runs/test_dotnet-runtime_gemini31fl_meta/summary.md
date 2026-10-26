# Athena Sim summary

1260 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_dotnet-runtime_gemini31fl_meta` (test split) was started from freeze `frozen_dotnet-runtime_gemini31fl_meta.json` (sha256 87e1d50cbfb7).

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 210 | 100.0% | 88.6% [84-92] | 98.6% | 98.6% [96-100] | - | 0.0% | 0.988 -> 0.998 | - | 1.30 | 92340/22940 | 0.0575 |
| openai:google/gemini-3.1-flash-lite | fulldoc | 210 | 100.0% | 99.5% [97-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.988 -> 1.000 | - | 1.34 | 489030/23504 | 0.1575 |
| openai:google/gemini-3.1-flash-lite | chunk | 210 | 100.0% | 96.7% [93-98] | 98.6% | 98.6% [96-100] | - | 0.0% | 0.988 -> 1.000 | - | 1.34 | 146052/23484 | 0.0717 |
| openai:google/gemini-3.1-flash-lite | bm25 | 210 | 100.0% | 97.1% [94-99] | 98.6% | 98.6% [96-100] | - | 0.0% | 0.988 -> 1.000 | - | 1.30 | 167472/23459 | 0.0771 |
| openai:google/gemini-3.1-flash-lite | dense | 210 | 100.0% | 97.1% [94-99] | 98.6% | 98.6% [96-100] | - | 0.0% | 0.988 -> 1.000 | - | 1.51 | 134205/23855 | 0.0693 |
| openai:google/gemini-3.1-flash-lite | graph | 210 | 100.0% | 99.0% [97-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.988 -> 1.000 | 100.0% | 1.28 | 95490/24239 | 0.0602 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 98.6% [210] |
| openai:google/gemini-3.1-flash-lite | fulldoc | 100.0% [210] |
| openai:google/gemini-3.1-flash-lite | chunk | 98.6% [210] |
| openai:google/gemini-3.1-flash-lite | bm25 | 98.6% [210] |
| openai:google/gemini-3.1-flash-lite | dense | 98.6% [210] |
| openai:google/gemini-3.1-flash-lite | graph | 100.0% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | core_ok | 70 | 1 | 0 | 69 | +1.4 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | core_ok | 70 | 1 | 0 | 69 | +1.4 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | exact_match | 70 | 12 | 0 | 58 | +11.0 | 0.000488 | 0.00488 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | exact_match | 70 | 10 | 1 | 59 | +8.1 | 0.0117 | 0.0703 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | exact_match | 70 | 11 | 0 | 59 | +8.6 | 0.000977 | 0.00879 |
| openai:google/gemini-3.1-flash-lite | dense vs none | exact_match | 70 | 11 | 0 | 59 | +8.6 | 0.000977 | 0.00879 |
| openai:google/gemini-3.1-flash-lite | graph vs none | exact_match | 70 | 11 | 0 | 59 | +10.5 | 0.000977 | 0.00879 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
