# Athena Sim summary

1260 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_godot_gemini31fl_meta` (test split) was started from freeze `frozen_godot_gemini31fl_meta.json` (sha256 272e62ff557e).

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 210 | 100.0% | 81.0% [75-86] | 99.0% | 99.0% [97-100] | - | 1.4% | 0.931 -> 0.996 | - | 1.55 | 84363/26119 | 0.0603 |
| openai:google/gemini-3.1-flash-lite | fulldoc | 210 | 100.0% | 93.8% [90-96] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 0.999 | - | 1.47 | 458373/24582 | 0.1515 |
| openai:google/gemini-3.1-flash-lite | chunk | 210 | 100.0% | 92.9% [89-96] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 0.998 | - | 1.40 | 117822/24815 | 0.0667 |
| openai:google/gemini-3.1-flash-lite | bm25 | 210 | 100.0% | 91.4% [87-95] | 98.6% | 98.6% [96-100] | - | 0.0% | 0.931 -> 0.998 | - | 1.42 | 121092/24961 | 0.0677 |
| openai:google/gemini-3.1-flash-lite | dense | 210 | 100.0% | 95.2% [91-97] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 0.999 | - | 1.39 | 115254/25077 | 0.0664 |
| openai:google/gemini-3.1-flash-lite | graph | 210 | 100.0% | 90.0% [85-93] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 0.998 | 100.0% | 1.38 | 114951/27259 | 0.0696 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 99.0% [210] |
| openai:google/gemini-3.1-flash-lite | fulldoc | 100.0% [210] |
| openai:google/gemini-3.1-flash-lite | chunk | 100.0% [210] |
| openai:google/gemini-3.1-flash-lite | bm25 | 98.6% [210] |
| openai:google/gemini-3.1-flash-lite | dense | 100.0% [210] |
| openai:google/gemini-3.1-flash-lite | graph | 100.0% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | core_ok | 70 | 1 | 0 | 69 | +1.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | core_ok | 70 | 1 | 0 | 69 | +1.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | core_ok | 70 | 0 | 1 | 69 | -0.5 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | core_ok | 70 | 1 | 0 | 69 | +1.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | core_ok | 70 | 1 | 0 | 69 | +1.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | exact_match | 70 | 17 | 2 | 51 | +12.9 | 0.000729 | 0.0051 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | exact_match | 70 | 16 | 0 | 54 | +11.9 | 3.05e-05 | 0.000275 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | exact_match | 70 | 15 | 1 | 54 | +10.5 | 0.000519 | 0.00415 |
| openai:google/gemini-3.1-flash-lite | dense vs none | exact_match | 70 | 17 | 0 | 53 | +14.3 | 1.53e-05 | 0.000153 |
| openai:google/gemini-3.1-flash-lite | graph vs none | exact_match | 70 | 14 | 4 | 52 | +9.0 | 0.0309 | 0.185 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
