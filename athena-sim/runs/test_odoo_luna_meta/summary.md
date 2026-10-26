# Athena Sim summary

1260 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_odoo_luna_meta` (test split) was started from freeze `frozen_odoo_luna_meta.json` (sha256 3c8f9aff15dd).

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | none | 210 | 100.0% | 95.2% [91-97] | 100.0% | 100.0% [98-100] | - | 1.0% | 0.956 -> 0.999 | - | 3.92 | 85791/43853 | 0.0305 |
| openai:openai/gpt-6-luna | fulldoc | 210 | 100.0% | 91.0% [86-94] | 98.6% | 98.6% [96-100] | - | 1.0% | 0.956 -> 0.998 | - | 3.62 | 2485251/34271 | 0.2657 |
| openai:openai/gpt-6-luna | chunk | 210 | 100.0% | 96.7% [93-98] | 100.0% | 100.0% [98-100] | - | 0.5% | 0.956 -> 0.999 | - | 3.60 | 158433/39244 | 0.0355 |
| openai:openai/gpt-6-luna | bm25 | 210 | 99.5% | 93.8% [90-96] | 98.1% | 98.1% [95-99] | - | 1.0% | 0.956 -> 0.999 | - | 3.69 | 171799/38972 | 0.0367 |
| openai:openai/gpt-6-luna | dense | 210 | 100.0% | 93.8% [90-96] | 100.0% | 100.0% [98-100] | - | 1.0% | 0.956 -> 0.999 | - | 3.77 | 125646/41985 | 0.0336 |
| openai:openai/gpt-6-luna | graph | 210 | 100.0% | 97.1% [94-99] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.956 -> 0.999 | 100.0% | 3.08 | 92931/30730 | 0.0247 |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:openai/gpt-6-luna | none | 100.0% [210] |
| openai:openai/gpt-6-luna | fulldoc | 98.6% [210] |
| openai:openai/gpt-6-luna | chunk | 100.0% [210] |
| openai:openai/gpt-6-luna | bm25 | 98.1% [210] |
| openai:openai/gpt-6-luna | dense | 100.0% [210] |
| openai:openai/gpt-6-luna | graph | 100.0% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | fulldoc vs none | core_ok | 70 | 0 | 3 | 67 | -1.4 | 0.25 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | core_ok | 70 | 0 | 2 | 68 | -1.9 | 0.5 | 1 |
| openai:openai/gpt-6-luna | dense vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | exact_match | 70 | 2 | 8 | 60 | -4.3 | 0.109 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | exact_match | 70 | 4 | 3 | 63 | +1.4 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | exact_match | 70 | 3 | 6 | 61 | -1.4 | 0.508 | 1 |
| openai:openai/gpt-6-luna | dense vs none | exact_match | 70 | 2 | 4 | 64 | -1.4 | 0.688 | 1 |
| openai:openai/gpt-6-luna | graph vs none | exact_match | 70 | 5 | 3 | 62 | +1.9 | 0.727 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
