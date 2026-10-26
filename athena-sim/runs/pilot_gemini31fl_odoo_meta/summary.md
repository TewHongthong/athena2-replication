# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 1.38 | 14066/3428 | 0.0087 |
| openai:google/gemini-3.1-flash-lite | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 1.61 | 399176/3399 | 0.1049 |
| openai:google/gemini-3.1-flash-lite | chunk | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 1.35 | 25372/3556 | 0.0117 |
| openai:google/gemini-3.1-flash-lite | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 1.48 | 28186/3443 | 0.0122 |
| openai:google/gemini-3.1-flash-lite | dense | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 0.999 | - | 1.42 | 23263/3537 | 0.0111 |
| openai:google/gemini-3.1-flash-lite | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | 100.0% | 1.34 | 15116/3357 | 0.0088 |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
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
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
