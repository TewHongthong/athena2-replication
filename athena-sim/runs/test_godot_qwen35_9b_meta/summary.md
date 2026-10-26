# Athena Sim summary

1260 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_godot_qwen35_9b_meta` (test split) was started from freeze `frozen_godot_qwen35_9b_meta.json` (sha256 628fb3e8371d).

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 210 | 98.6% | 64.3% [58-70] | 92.9% | 92.9% [89-96] | - | 2.9% | 0.931 -> 0.990 | - | 7.48 | 80310/32505 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 210 | 100.0% | 77.6% [72-83] | 96.2% | 96.2% [93-98] | - | 1.0% | 0.931 -> 0.993 | - | 8.38 | 438570/32752 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 210 | 98.1% | 69.5% [63-75] | 95.2% | 95.2% [91-97] | - | 1.0% | 0.931 -> 0.992 | - | 7.77 | 112005/33415 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 210 | 98.1% | 72.4% [66-78] | 92.9% | 92.9% [89-96] | - | 0.0% | 0.931 -> 0.994 | - | 7.68 | 114975/33993 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 210 | 100.0% | 70.5% [64-76] | 96.7% | 96.7% [93-98] | - | 1.9% | 0.931 -> 0.994 | - | 7.42 | 109485/31980 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 210 | 99.5% | 84.8% [79-89] | 99.5% | 99.5% [97-100] | - | 0.0% | 0.931 -> 0.996 | 100.0% | 8.32 | 110202/36214 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 92.9% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 96.2% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 95.2% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 92.9% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 96.7% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 99.5% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | core_ok | 70 | 12 | 4 | 54 | +3.3 | 0.0768 | 0.461 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | core_ok | 70 | 11 | 6 | 53 | +2.4 | 0.332 | 0.729 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | core_ok | 70 | 10 | 9 | 51 | +0.0 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | core_ok | 70 | 13 | 5 | 52 | +3.8 | 0.0963 | 0.481 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | core_ok | 70 | 14 | 1 | 55 | +6.7 | 0.000977 | 0.00879 |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | exact_match | 70 | 26 | 7 | 37 | +13.3 | 0.00132 | 0.0105 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | exact_match | 70 | 22 | 14 | 34 | +5.2 | 0.243 | 0.729 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | exact_match | 70 | 27 | 13 | 30 | +8.1 | 0.0385 | 0.269 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | exact_match | 70 | 24 | 14 | 32 | +6.2 | 0.143 | 0.573 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | exact_match | 70 | 31 | 4 | 35 | +20.5 | 3.47e-06 | 3.47e-05 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
