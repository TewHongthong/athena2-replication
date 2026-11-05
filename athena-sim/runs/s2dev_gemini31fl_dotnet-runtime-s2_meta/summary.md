# Athena Sim summary

133 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 19 | 100.0% | 89.5% [69-97] | 94.7% | 94.7% [75-99] | - | 0.0% | 0.998 -> 1.000 | - | 1.57 | 10872/2134 | 0.0059 |
| openai:google/gemini-3.1-flash-lite | fulldoc | 19 | 94.7% | 89.5% [69-97] | 94.7% | 94.7% [75-99] | - | 0.0% | 0.998 -> 1.000 | - | 1.54 | 46763/2338 | 0.0152 |
| openai:google/gemini-3.1-flash-lite | chunk | 19 | 100.0% | 89.5% [69-97] | 94.7% | 94.7% [75-99] | - | 0.0% | 0.998 -> 1.000 | - | 1.46 | 19501/2181 | 0.0081 |
| openai:google/gemini-3.1-flash-lite | bm25 | 19 | 100.0% | 94.7% [75-99] | 94.7% | 94.7% [75-99] | - | 0.0% | 0.998 -> 1.000 | - | 1.61 | 19839/2147 | 0.0082 |
| openai:google/gemini-3.1-flash-lite | dense | 19 | 100.0% | 94.7% [75-99] | 94.7% | 94.7% [75-99] | - | 0.0% | 0.998 -> 1.000 | - | 1.48 | 14567/2098 | 0.0068 |
| openai:google/gemini-3.1-flash-lite | graph | 19 | 100.0% | 100.0% [83-100] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.998 -> 1.000 | 100.0% | 1.77 | 11946/2501 | 0.0067 |
| openai:google/gemini-3.1-flash-lite | naming | 19 | 100.0% | 100.0% [83-100] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.998 -> 1.000 | - | 1.44 | 16230/2179 | 0.0073 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 94.7% [19] |
| openai:google/gemini-3.1-flash-lite | fulldoc | 94.7% [19] |
| openai:google/gemini-3.1-flash-lite | chunk | 94.7% [19] |
| openai:google/gemini-3.1-flash-lite | bm25 | 94.7% [19] |
| openai:google/gemini-3.1-flash-lite | dense | 94.7% [19] |
| openai:google/gemini-3.1-flash-lite | graph | 100.0% [19] |
| openai:google/gemini-3.1-flash-lite | naming | 100.0% [19] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | core_ok | 19 | 1 | 1 | 17 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | core_ok | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | core_ok | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | core_ok | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | core_ok | 19 | 1 | 0 | 18 | +5.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | naming vs none | core_ok | 19 | 1 | 0 | 18 | +5.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | exact_match | 19 | 1 | 1 | 17 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | exact_match | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | exact_match | 19 | 1 | 0 | 18 | +5.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | exact_match | 19 | 1 | 0 | 18 | +5.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | exact_match | 19 | 2 | 0 | 17 | +10.5 | 0.5 | 1 |
| openai:google/gemini-3.1-flash-lite | naming vs none | exact_match | 19 | 2 | 0 | 17 | +10.5 | 0.5 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
