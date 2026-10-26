# Athena Sim summary

1260 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_dotnet-runtime_qwen35_9b_meta` (test split) was started from freeze `frozen_dotnet-runtime_qwen35_9b_meta.json` (sha256 3f1220453dc0).

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 210 | 96.7% | 48.6% [42-55] | 91.4% | 91.4% [87-95] | - | 1.9% | 0.988 -> 0.995 | - | 10.19 | 90225/35230 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 210 | 93.8% | 88.1% [83-92] | 92.9% | 92.9% [89-96] | - | 0.0% | 0.988 -> 0.999 | - | 7.34 | 471585/27367 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 210 | 97.6% | 84.8% [79-89] | 94.8% | 94.8% [91-97] | - | 0.5% | 0.988 -> 0.998 | - | 7.54 | 141081/31999 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 210 | 97.6% | 74.8% [68-80] | 93.8% | 93.8% [90-96] | - | 0.5% | 0.988 -> 0.998 | - | 8.40 | 160902/36339 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 210 | 97.6% | 61.0% [54-67] | 84.8% | 84.8% [79-89] | - | 2.4% | 0.988 -> 0.997 | - | 9.76 | 130272/42703 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 210 | 100.0% | 96.2% [93-98] | 98.6% | 98.6% [96-100] | - | 0.0% | 0.988 -> 1.000 | 100.0% | 6.27 | 93165/26673 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 91.4% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 92.9% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 94.8% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 93.8% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 84.8% [210] |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 98.6% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | core_ok | 70 | 12 | 8 | 50 | +1.4 | 0.503 | 0.668 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | core_ok | 70 | 13 | 6 | 51 | +3.3 | 0.167 | 0.668 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | core_ok | 70 | 11 | 6 | 53 | +2.4 | 0.332 | 0.668 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | core_ok | 70 | 9 | 17 | 44 | -6.7 | 0.169 | 0.668 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | core_ok | 70 | 13 | 0 | 57 | +7.1 | 0.000244 | 0.00146 |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | exact_match | 70 | 46 | 3 | 21 | +39.5 | 6.98e-11 | 6.28e-10 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | exact_match | 70 | 45 | 3 | 22 | +36.2 | 1.31e-10 | 1.05e-09 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | exact_match | 70 | 36 | 10 | 24 | +26.2 | 0.000156 | 0.00109 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | exact_match | 70 | 30 | 12 | 28 | +12.4 | 0.00792 | 0.0396 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | exact_match | 70 | 51 | 0 | 19 | +47.6 | 8.88e-16 | 8.88e-15 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
