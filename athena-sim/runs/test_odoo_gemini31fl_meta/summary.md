# Athena Sim summary

1260 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_odoo_gemini31fl_meta` (test split) was started from freeze `frozen_odoo_gemini31fl_meta.json` (sha256 266e8dd30a4d).

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 210 | 100.0% | 95.2% [91-97] | 100.0% | 100.0% [98-100] | - | 1.0% | 0.956 -> 0.998 | - | 1.43 | 96348/23647 | 0.0596 |
| openai:google/gemini-3.1-flash-lite | fulldoc | 210 | 100.0% | 87.6% [82-91] | 100.0% | 100.0% [98-100] | - | 2.4% | 0.956 -> 0.997 | - | 1.65 | 2792118/23325 | 0.7330 |
| openai:google/gemini-3.1-flash-lite | chunk | 210 | 100.0% | 93.8% [90-96] | 100.0% | 100.0% [98-100] | - | 1.9% | 0.956 -> 0.999 | - | 1.43 | 182307/24387 | 0.0822 |
| openai:google/gemini-3.1-flash-lite | bm25 | 210 | 100.0% | 92.9% [89-96] | 100.0% | 100.0% [98-100] | - | 1.4% | 0.956 -> 0.999 | - | 1.35 | 198483/24276 | 0.0860 |
| openai:google/gemini-3.1-flash-lite | dense | 210 | 100.0% | 92.9% [89-96] | 100.0% | 100.0% [98-100] | - | 1.4% | 0.956 -> 0.999 | - | 1.34 | 140985/24571 | 0.0721 |
| openai:google/gemini-3.1-flash-lite | graph | 210 | 100.0% | 97.6% [95-99] | 100.0% | 100.0% [98-100] | - | 1.4% | 0.956 -> 0.999 | 100.0% | 1.29 | 103698/23156 | 0.0607 |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 100.0% [210] |
| openai:google/gemini-3.1-flash-lite | fulldoc | 100.0% [210] |
| openai:google/gemini-3.1-flash-lite | chunk | 100.0% [210] |
| openai:google/gemini-3.1-flash-lite | bm25 | 100.0% [210] |
| openai:google/gemini-3.1-flash-lite | dense | 100.0% [210] |
| openai:google/gemini-3.1-flash-lite | graph | 100.0% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | exact_match | 70 | 1 | 13 | 56 | -7.6 | 0.00183 | 0.0183 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | exact_match | 70 | 5 | 6 | 59 | -1.4 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | exact_match | 70 | 3 | 6 | 61 | -2.4 | 0.508 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | exact_match | 70 | 2 | 5 | 63 | -2.4 | 0.453 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | exact_match | 70 | 4 | 2 | 64 | +2.4 | 0.688 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
