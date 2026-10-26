# Athena Sim summary

1260 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_odoo_qwen35_9b_meta` (test split) was started from freeze `frozen_odoo_qwen35_9b_meta.json` (sha256 747a90156023).

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 210 | 97.1% | 70.5% [64-76] | 97.1% | 97.1% [94-99] | - | 4.3% | 0.956 -> 0.992 | - | 7.11 | 91494/30774 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 210 | 100.0% | 68.6% [62-74] | 100.0% | 100.0% [98-100] | - | 3.3% | 0.956 -> 0.993 | - | 12.74 | 2599524/28524 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 210 | 94.8% | 57.6% [51-64] | 94.3% | 94.3% [90-97] | - | 4.8% | 0.956 -> 0.990 | - | 8.05 | 168759/33701 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 210 | 98.1% | 69.0% [62-75] | 97.6% | 97.6% [95-99] | - | 2.9% | 0.956 -> 0.991 | - | 7.69 | 183156/32893 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 210 | 97.1% | 60.5% [54-67] | 96.2% | 96.2% [93-98] | - | 6.2% | 0.956 -> 0.988 | - | 7.37 | 132990/31661 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 210 | 100.0% | 91.9% [87-95] | 100.0% | 100.0% [98-100] | - | 1.4% | 0.956 -> 0.999 | 100.0% | 5.94 | 98634/25218 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 97.1% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 100.0% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 94.3% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 97.6% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 96.2% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 100.0% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | core_ok | 70 | 6 | 0 | 64 | +2.9 | 0.0312 | 0.25 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | core_ok | 70 | 5 | 10 | 55 | -2.9 | 0.302 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | core_ok | 70 | 4 | 3 | 63 | +0.5 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | core_ok | 70 | 6 | 8 | 56 | -1.0 | 0.791 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | core_ok | 70 | 6 | 0 | 64 | +2.9 | 0.0312 | 0.25 |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | exact_match | 70 | 14 | 17 | 39 | -1.9 | 0.72 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | exact_match | 70 | 8 | 21 | 41 | -12.9 | 0.0241 | 0.217 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | exact_match | 70 | 13 | 12 | 45 | -1.4 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | exact_match | 70 | 9 | 20 | 41 | -10.0 | 0.0614 | 0.369 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | exact_match | 70 | 27 | 0 | 43 | +21.4 | 1.49e-08 | 1.49e-07 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
