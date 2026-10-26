# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 30 | 100.0% | 90.0% [74-97] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 0.999 | - | 1.33 | 12146/3139 | 0.0077 |
| openai:google/gemini-3.1-flash-lite | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 1.37 | 68816/3258 | 0.0221 |
| openai:google/gemini-3.1-flash-lite | chunk | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 1.36 | 21335/3246 | 0.0102 |
| openai:google/gemini-3.1-flash-lite | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 1.44 | 24742/3278 | 0.0111 |
| openai:google/gemini-3.1-flash-lite | dense | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 1.35 | 17387/3260 | 0.0092 |
| openai:google/gemini-3.1-flash-lite | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | 100.0% | 1.34 | 12596/3373 | 0.0082 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | fulldoc | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | chunk | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | bm25 | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | dense | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | exact_match | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | exact_match | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | exact_match | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | exact_match | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | exact_match | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
