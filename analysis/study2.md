# Study 2 analysis (HYPOTHESES_v2_study2)

Packs: godot-s2, dotnet-runtime-s2. Comparisons on the test split, eligibility on dev. Unit = one task, mean of core_ok_s2 over its rounds. Intervals: cluster bootstrap over `file`, 10000 resamples, seed 20261018. Duplicate records of a key: the first by time stamp is used.

## Records

| run | family | model | lines | not JSON | records | with an error | duplicates not used |
|---|---|---|---|---|---|---|---|
| s2dev_gemini31fl_dotnet-runtime-s2_infer | infer | gemini31fl | 36 | 0 | 36 | 0 | 17 |
| s2dev_gemini31fl_dotnet-runtime-s2_meta | meta | gemini31fl | 263 | 1 | 262 | 0 | 129 |
| s2dev_gemini31fl_godot-s2_infer | infer | gemini31fl | 60 | 0 | 60 | 0 | 30 |
| s2dev_gemini31fl_godot-s2_meta | meta | gemini31fl | 404 | 1 | 403 | 0 | 193 |
| s2dev_gemma4_local_s2_dotnet-runtime-s2_infer | infer | gemma4_local_s2 | 19 | 0 | 19 | 0 | 0 |
| s2dev_gemma4_local_s2_dotnet-runtime-s2_meta | meta | gemma4_local_s2 | 133 | 0 | 133 | 0 | 0 |
| s2dev_gemma4_local_s2_godot-s2_infer | infer | gemma4_local_s2 | 30 | 0 | 30 | 0 | 0 |
| s2dev_gemma4_local_s2_godot-s2_meta | meta | gemma4_local_s2 | 210 | 0 | 210 | 0 | 0 |
| s2dev_luna_dotnet-runtime-s2_infer | infer | luna | 33 | 0 | 33 | 0 | 14 |
| s2dev_luna_dotnet-runtime-s2_meta | meta | luna | 266 | 0 | 266 | 0 | 133 |
| s2dev_luna_godot-s2_infer | infer | luna | 56 | 0 | 56 | 0 | 26 |
| s2dev_luna_godot-s2_meta | meta | luna | 272 | 1 | 271 | 0 | 61 |
| s2dev_qwen35_9b_s2_dotnet-runtime-s2_infer | infer | qwen35_9b_s2 | 19 | 0 | 19 | 0 | 0 |
| s2dev_qwen35_9b_s2_dotnet-runtime-s2_meta | meta | qwen35_9b_s2 | 133 | 0 | 133 | 0 | 0 |
| s2dev_qwen35_9b_s2_godot-s2_infer | infer | qwen35_9b_s2 | 30 | 0 | 30 | 0 | 0 |
| s2dev_qwen35_9b_s2_godot-s2_meta | meta | qwen35_9b_s2 | 210 | 0 | 210 | 0 | 0 |
| s2test_luna_dotnet-runtime-s2_infer | infer | luna | 135 | 0 | 135 | 0 | 0 |
| s2test_luna_dotnet-runtime-s2_meta | meta | luna | 945 | 0 | 945 | 0 | 0 |
| s2test_luna_godot-s2_infer | infer | luna | 210 | 0 | 210 | 0 | 0 |
| s2test_luna_godot-s2_meta | meta | luna | 1470 | 0 | 1470 | 0 | 0 |
| s2test_gemini31fl_dotnet-runtime-s2_infer | infer | gemini31fl | 135 | 0 | 135 | 0 | 0 |
| s2test_gemini31fl_dotnet-runtime-s2_meta | meta | gemini31fl | 945 | 0 | 945 | 0 | 0 |
| s2test_gemini31fl_godot-s2_infer | infer | gemini31fl | 210 | 0 | 210 | 0 | 0 |
| s2test_gemini31fl_godot-s2_meta | meta | gemini31fl | 1470 | 0 | 1470 | 0 | 0 |
| s2test_gemma4_local_s2_dotnet-runtime-s2_infer | infer | gemma4_local_s2 | 135 | 0 | 135 | 0 | 0 |
| s2test_gemma4_local_s2_dotnet-runtime-s2_meta | meta | gemma4_local_s2 | 945 | 0 | 945 | 0 | 0 |
| s2test_gemma4_local_s2_godot-s2_infer | infer | gemma4_local_s2 | 210 | 0 | 210 | 0 | 0 |
| s2test_gemma4_local_s2_godot-s2_meta | meta | gemma4_local_s2 | 1470 | 0 | 1470 | 0 | 0 |
| s2test_qwen35_9b_or_s2_dotnet-runtime-s2_infer | infer | qwen35_9b_or_s2 | 135 | 0 | 135 | 0 | 0 |
| s2test_qwen35_9b_or_s2_dotnet-runtime-s2_meta | meta | qwen35_9b_or_s2 | 946 | 0 | 946 | 1 | 0 |
| s2test_qwen35_9b_or_s2_godot-s2_infer | infer | qwen35_9b_or_s2 | 210 | 0 | 210 | 0 | 0 |
| s2test_qwen35_9b_or_s2_godot-s2_meta | meta | qwen35_9b_or_s2 | 1470 | 0 | 1470 | 0 | 0 |

Records used: 12608; keys with errors only (left out): 0. Scorer check: 12532 trials with a valid name re-scored, 0 differ from the stored core_ok_s2. Units clustered by the field: 115, by snippet id: 0, alone: 0.

## Drift check (HYPOTHESES_v2 Section 2.1: canary before and after, condition none)

| model | units | before (%) | after (%) | change (pp) | pass->fail | fail->pass | McNemar p | same name (%) | model/provider/fingerprint | flagged |
|---|---|---|---|---|---|---|---|---|---|---|
| luna | 49 | 95.9 | 98.0 | +2.0 | 0 | 1 | 1 | 98.0 | same | no |
| gemini31fl | 49 | 93.9 | 91.8 | -2.0 | 2 | 1 | 1 | 91.8 | same | no |
| gemma4_local_s2 | 49 | 89.8 | 85.7 | -4.1 | 2 | 0 | 0.5 | 93.9 | same | no |
| qwen35_9b_or_s2 | 49 | 34.7 | 32.7 | -2.0 | 6 | 5 | 1 | 49.0 | same | no |

- luna: first trial openai/gpt-6-luna / OpenAI / None; last trial openai/gpt-6-luna / OpenAI / None; distinct values 1.
- gemini31fl: first trial google/gemini-3.1-flash-lite / Google / None; last trial google/gemini-3.1-flash-lite / Google / None; distinct values 1.
- gemma4_local_s2: first trial gemma-4-26b-a4b-it-ud-q4_k_m / None / b11433-50569eb87; last trial gemma-4-26b-a4b-it-ud-q4_k_m / None / b11433-50569eb87; distinct values 1.
- qwen35_9b_or_s2: first trial qwen/qwen3.5-9b / DeepInfra / None; last trial qwen/qwen3.5-9b / DeepInfra / None; distinct values 1.

Flagged: changed model, provider or system_fingerprint between the first and the last trial of the model, or McNemar p < 0.05. A flag changes no data; see the sensitivity analysis.

## Eligibility for H1-S2 (Section 2.3: mean core_ok_s2 of none on dev, over the models; included if below 0.90)

| standard | none on dev (%) | models | included | per model (%) |
|---|---|---|---|---|
| godot-s2 | 79.2 | 4 | yes | luna: 96.7, gemini31fl: 96.7, qwen35_9b_s2: 43.3, gemma4_local_s2: 80.0 |
| dotnet-runtime-s2 | 81.6 | 4 | yes | luna: 100.0, gemini31fl: 100.0, qwen35_9b_s2: 31.6, gemma4_local_s2: 94.7 |

## H1-S2 (confirmatory): selection vs none, exact two-sided sign test, Holm over these tests

| standard | model | tasks | better | worse | tied | mean diff (pp) | p | p (Holm) | supports |
|---|---|---|---|---|---|---|---|---|---|
| godot-s2 | gemini31fl | 70 | 18 | 1 | 51 | +12.9 | 7.63e-05 | 0.000458 | yes |
| godot-s2 | gemma4_local_s2 | 70 | 18 | 1 | 51 | +17.1 | 7.63e-05 | 0.000458 | yes |
| godot-s2 | luna | 70 | 1 | 1 | 68 | +0.5 | 1 | 1 | no |
| godot-s2 | qwen35_9b_or_s2 | 70 | 53 | 0 | 17 | +50.5 | 2.22e-16 | 1.78e-15 | yes |
| dotnet-runtime-s2 | gemini31fl | 45 | 1 | 0 | 44 | +2.2 | 1 | 1 | no |
| dotnet-runtime-s2 | gemma4_local_s2 | 45 | 4 | 0 | 41 | +6.7 | 0.125 | 0.5 | no |
| dotnet-runtime-s2 | luna | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 | no |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | 45 | 38 | 0 | 7 | +60.7 | 7.28e-12 | 5.09e-11 | yes |

Holm family: 8 tests; supports = adjusted p < 0.05 and a positive mean difference. Tests that support H1-S2: 4 of 8.

## H2-S2: selection - naming (margin 2 pp)

| standard | model | tasks | files | mean diff (pp) | 95% CI (pp) | cell | prompt chars sel / naming | prompt tokens sel / naming |
|---|---|---|---|---|---|---|---|---|
| godot-s2 | gemini31fl | 70 | 33 | +17.6 | [+10.6, +25.6] | supported | 2,086 / 2,088 | 564 / 555 |
| godot-s2 | gemma4_local_s2 | 70 | 33 | +13.3 | [+7.2, +20.1] | supported | 2,086 / 2,088 | 577 / 568 |
| godot-s2 | luna | 70 | 33 | +1.0 | [+0.0, +2.5] | supported | 2,086 / 2,088 | 513 / 500 |
| godot-s2 | qwen35_9b_or_s2 | 70 | 33 | +14.8 | [+8.5, +21.9] | supported | 2,086 / 2,088 | 540 / 529 |
| dotnet-runtime-s2 | gemini31fl | 45 | 36 | +0.0 | [+0.0, +0.0] | supported | 2,396 / 3,388 | 609 / 835 |
| dotnet-runtime-s2 | gemma4_local_s2 | 45 | 36 | +0.0 | [+0.0, +0.0] | supported | 2,396 / 3,388 | 622 / 848 |
| dotnet-runtime-s2 | luna | 45 | 36 | +0.0 | [+0.0, +0.0] | supported | 2,396 / 3,388 | 557 / 773 |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | 45 | 36 | +3.0 | [-0.7, +7.5] | supported | 2,396 / 3,388 | 596 / 812 |

Summary: **supported**.

## H3-S2: selection - fulldoc (margin 2 pp) and selection vs the retrieval conditions

| standard | model | tasks | files | mean diff (pp) | 95% CI (pp) | vs fulldoc |
|---|---|---|---|---|---|---|
| godot-s2 | gemini31fl | 70 | 33 | +6.7 | [+2.4, +12.2] | non-inferior |
| godot-s2 | gemma4_local_s2 | 70 | 33 | +9.0 | [+3.7, +15.2] | non-inferior |
| godot-s2 | luna | 70 | 33 | +3.3 | [+0.9, +6.6] | non-inferior |
| godot-s2 | qwen35_9b_or_s2 | 70 | 33 | +27.6 | [+19.0, +37.0] | non-inferior |
| dotnet-runtime-s2 | gemini31fl | 45 | 36 | +0.0 | [+0.0, +0.0] | non-inferior |
| dotnet-runtime-s2 | gemma4_local_s2 | 45 | 36 | +0.0 | [+0.0, +0.0] | non-inferior |
| dotnet-runtime-s2 | luna | 45 | 36 | +0.0 | [+0.0, +0.0] | non-inferior |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | 45 | 36 | -0.7 | [-2.4, +0.0] | inconclusive |

| standard | model | condition | tasks | better | worse | tied | mean diff (pp) | p | p (Holm) | higher |
|---|---|---|---|---|---|---|---|---|---|---|
| godot-s2 | gemini31fl | chunk | 70 | 2 | 1 | 67 | +1.4 | 1 | 1 | no |
| godot-s2 | gemini31fl | bm25 | 70 | 5 | 1 | 64 | +3.8 | 0.219 | 1 | no |
| godot-s2 | gemini31fl | dense | 70 | 6 | 1 | 63 | +2.9 | 0.125 | 1 | no |
| godot-s2 | gemma4_local_s2 | chunk | 70 | 8 | 1 | 61 | +7.1 | 0.0391 | 0.664 | no |
| godot-s2 | gemma4_local_s2 | bm25 | 70 | 7 | 1 | 62 | +5.7 | 0.0703 | 1 | no |
| godot-s2 | gemma4_local_s2 | dense | 70 | 9 | 0 | 61 | +10.5 | 0.00391 | 0.0742 | no |
| godot-s2 | luna | chunk | 70 | 4 | 1 | 65 | +2.4 | 0.375 | 1 | no |
| godot-s2 | luna | bm25 | 70 | 4 | 1 | 65 | +1.9 | 0.375 | 1 | no |
| godot-s2 | luna | dense | 70 | 5 | 0 | 65 | +3.3 | 0.0625 | 1 | no |
| godot-s2 | qwen35_9b_or_s2 | chunk | 70 | 28 | 0 | 42 | +26.7 | 7.45e-09 | 1.64e-07 | yes |
| godot-s2 | qwen35_9b_or_s2 | bm25 | 70 | 29 | 0 | 41 | +26.7 | 3.73e-09 | 8.57e-08 | yes |
| godot-s2 | qwen35_9b_or_s2 | dense | 70 | 37 | 0 | 33 | +36.2 | 1.46e-11 | 3.49e-10 | yes |
| dotnet-runtime-s2 | gemini31fl | chunk | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 | no |
| dotnet-runtime-s2 | gemini31fl | bm25 | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 | no |
| dotnet-runtime-s2 | gemini31fl | dense | 45 | 1 | 0 | 44 | +0.7 | 1 | 1 | no |
| dotnet-runtime-s2 | gemma4_local_s2 | chunk | 45 | 1 | 0 | 44 | +2.2 | 1 | 1 | no |
| dotnet-runtime-s2 | gemma4_local_s2 | bm25 | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 | no |
| dotnet-runtime-s2 | gemma4_local_s2 | dense | 45 | 1 | 0 | 44 | +2.2 | 1 | 1 | no |
| dotnet-runtime-s2 | luna | chunk | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 | no |
| dotnet-runtime-s2 | luna | bm25 | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 | no |
| dotnet-runtime-s2 | luna | dense | 45 | 1 | 0 | 44 | +1.5 | 1 | 1 | no |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | chunk | 45 | 17 | 0 | 28 | +23.7 | 1.53e-05 | 0.000305 | yes |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | bm25 | 45 | 19 | 0 | 26 | +25.2 | 3.81e-06 | 8.01e-05 | yes |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | dense | 45 | 11 | 1 | 33 | +17.8 | 0.00635 | 0.114 | no |

Holm family: 24 tests (chunk is TF-IDF).

| standard | model | vs fulldoc | higher than chunk, bm25 and dense | cell |
|---|---|---|---|---|
| godot-s2 | gemini31fl | non-inferior | no | inconclusive |
| godot-s2 | gemma4_local_s2 | non-inferior | no | inconclusive |
| godot-s2 | luna | non-inferior | no | inconclusive |
| godot-s2 | qwen35_9b_or_s2 | non-inferior | yes | supported |
| dotnet-runtime-s2 | gemini31fl | non-inferior | no | inconclusive |
| dotnet-runtime-s2 | gemma4_local_s2 | non-inferior | no | inconclusive |
| dotnet-runtime-s2 | luna | non-inferior | no | inconclusive |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | inconclusive | no | inconclusive |

Summary: **inconclusive**.

## H4-S2 (exploratory): kind and facets inferred - from metadata, selection (margin 5 pp)

| standard | model | tasks | files | mean diff (pp) | 95% CI (pp) | cell |
|---|---|---|---|---|---|---|
| godot-s2 | gemini31fl | 70 | 33 | -13.3 | [-24.0, -4.3] | inconclusive |
| godot-s2 | gemma4_local_s2 | 70 | 33 | -11.4 | [-22.1, -2.7] | inconclusive |
| godot-s2 | luna | 70 | 33 | -11.4 | [-20.8, -3.4] | inconclusive |
| godot-s2 | qwen35_9b_or_s2 | 70 | 33 | -17.6 | [-30.0, -7.1] | clearly against |
| dotnet-runtime-s2 | gemini31fl | 45 | 36 | +0.0 | [+0.0, +0.0] | supported |
| dotnet-runtime-s2 | gemma4_local_s2 | 45 | 36 | +0.0 | [+0.0, +0.0] | supported |
| dotnet-runtime-s2 | luna | 45 | 36 | +0.0 | [+0.0, +0.0] | supported |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | 45 | 36 | +0.7 | [+0.0, +2.4] | supported |

Summary: **not supported**.

## Results by condition (exploratory)

core_ok_s2, Study 1 core_ok (casing; n/a where the Study 1 core has no rule for the kind), the required prefix (right, a sibling prefix, no prefix or no valid name) and exact_match in % (mean over tasks of the mean over rounds); tokens are means per trial; cost is the sum in USD; at limit = trials that ended at the output limit.

| standard | model | condition | tasks | trials | core_ok_s2 | S1 core_ok | prefix right | sibling | no prefix | exact | prompt tok | completion tok | cost | at limit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| godot-s2 | luna | none | 70 | 210 | 98.6 | 100.0 | 98.6 | 1.4 | 0.0 | 98.6 | 358 | 264 | 0.0352 | 0 |
| godot-s2 | luna | fulldoc | 70 | 210 | 95.7 | 100.0 | 95.7 | 4.3 | 0.0 | 90.5 | 2,011 | 158 | 0.0588 | 0 |
| godot-s2 | luna | naming | 70 | 210 | 98.1 | 100.0 | 98.1 | 1.9 | 0.0 | 86.7 | 500 | 176 | 0.0290 | 0 |
| godot-s2 | luna | chunk | 70 | 210 | 96.7 | 100.0 | 96.7 | 3.3 | 0.0 | 96.2 | 545 | 202 | 0.0327 | 0 |
| godot-s2 | luna | bm25 | 70 | 210 | 97.1 | 100.0 | 97.1 | 2.4 | 0.5 | 97.1 | 555 | 200 | 0.0326 | 0 |
| godot-s2 | luna | dense | 70 | 210 | 95.7 | 100.0 | 95.7 | 3.3 | 1.0 | 95.7 | 483 | 204 | 0.0316 | 0 |
| godot-s2 | luna | graph | 70 | 210 | 99.0 | 100.0 | 99.0 | 0.5 | 0.5 | 92.9 | 513 | 162 | 0.0278 | 0 |
| godot-s2 | luna | graph[infer] | 70 | 210 | 87.6 | 100.0 | 87.6 | 6.7 | 5.7 | 82.9 | 509 | 213 | 0.0330 | 0 |
| godot-s2 | gemini31fl | none | 70 | 210 | 85.2 | 100.0 | 85.2 | 3.8 | 11.0 | 73.3 | 403 | 134 | 0.0634 | 0 |
| godot-s2 | gemini31fl | fulldoc | 70 | 210 | 91.4 | 100.0 | 91.4 | 8.1 | 0.5 | 88.6 | 2,184 | 120 | 0.1526 | 0 |
| godot-s2 | gemini31fl | naming | 70 | 210 | 80.5 | 100.0 | 80.5 | 19.5 | 0.0 | 69.5 | 555 | 138 | 0.0726 | 0 |
| godot-s2 | gemini31fl | chunk | 70 | 210 | 96.7 | 100.0 | 96.7 | 1.4 | 1.9 | 92.9 | 603 | 124 | 0.0707 | 0 |
| godot-s2 | gemini31fl | bm25 | 70 | 210 | 94.3 | 100.0 | 94.3 | 1.4 | 4.3 | 92.4 | 614 | 123 | 0.0709 | 0 |
| godot-s2 | gemini31fl | dense | 70 | 210 | 95.2 | 100.0 | 95.2 | 1.9 | 2.9 | 87.1 | 536 | 127 | 0.0681 | 0 |
| godot-s2 | gemini31fl | graph | 70 | 210 | 98.1 | 100.0 | 98.1 | 1.4 | 0.5 | 85.2 | 564 | 136 | 0.0726 | 0 |
| godot-s2 | gemini31fl | graph[infer] | 70 | 210 | 84.8 | 100.0 | 84.8 | 5.7 | 9.5 | 74.3 | 559 | 138 | 0.0727 | 0 |
| godot-s2 | gemma4_local_s2 | none | 70 | 210 | 81.9 | 99.0 | 81.9 | 1.4 | 16.7 | 78.1 | 416 | 153 | - | 0 |
| godot-s2 | gemma4_local_s2 | fulldoc | 70 | 210 | 90.0 | 95.2 | 90.0 | 5.2 | 4.8 | 83.3 | 2,197 | 183 | - | 1 |
| godot-s2 | gemma4_local_s2 | naming | 70 | 210 | 85.7 | 97.6 | 85.7 | 11.9 | 2.4 | 73.8 | 568 | 201 | - | 1 |
| godot-s2 | gemma4_local_s2 | chunk | 70 | 210 | 91.9 | 99.0 | 91.9 | 2.4 | 5.7 | 91.9 | 616 | 129 | - | 0 |
| godot-s2 | gemma4_local_s2 | bm25 | 70 | 210 | 93.3 | 99.0 | 93.3 | 2.4 | 4.3 | 92.9 | 627 | 131 | - | 0 |
| godot-s2 | gemma4_local_s2 | dense | 70 | 210 | 88.6 | 100.0 | 88.6 | 3.8 | 7.6 | 87.6 | 549 | 157 | - | 0 |
| godot-s2 | gemma4_local_s2 | graph | 70 | 210 | 99.0 | 100.0 | 99.0 | 0.0 | 1.0 | 95.2 | 577 | 137 | - | 0 |
| godot-s2 | gemma4_local_s2 | graph[infer] | 70 | 210 | 87.6 | 99.5 | 87.6 | 3.8 | 8.6 | 82.4 | 572 | 149 | - | 0 |
| godot-s2 | qwen35_9b_or_s2 | none | 70 | 210 | 49.5 | 95.2 | 49.5 | 2.9 | 47.6 | 39.5 | 383 | 196 | 0.0142 | 0 |
| godot-s2 | qwen35_9b_or_s2 | fulldoc | 70 | 210 | 72.4 | 97.1 | 72.4 | 21.4 | 6.2 | 64.8 | 2,089 | 395 | 0.0563 | 3 |
| godot-s2 | qwen35_9b_or_s2 | naming | 70 | 210 | 85.2 | 99.0 | 85.2 | 11.0 | 3.8 | 67.1 | 529 | 272 | 0.0197 | 2 |
| godot-s2 | qwen35_9b_or_s2 | chunk | 70 | 210 | 73.3 | 99.0 | 73.3 | 9.0 | 17.6 | 71.4 | 573 | 188 | 0.0179 | 0 |
| godot-s2 | qwen35_9b_or_s2 | bm25 | 70 | 210 | 73.3 | 98.1 | 73.3 | 6.7 | 20.0 | 72.4 | 582 | 211 | 0.0189 | 0 |
| godot-s2 | qwen35_9b_or_s2 | dense | 70 | 210 | 63.8 | 97.6 | 63.8 | 11.4 | 24.8 | 62.9 | 509 | 243 | 0.0184 | 1 |
| godot-s2 | qwen35_9b_or_s2 | graph | 70 | 210 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 91.4 | 540 | 172 | 0.0168 | 0 |
| godot-s2 | qwen35_9b_or_s2 | graph[infer] | 70 | 210 | 82.4 | 99.5 | 82.4 | 4.8 | 12.9 | 74.3 | 535 | 214 | 0.0180 | 1 |
| dotnet-runtime-s2 | luna | none | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 504 | 180 | 0.0190 | 0 |
| dotnet-runtime-s2 | luna | fulldoc | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 2,237 | 141 | 0.0397 | 0 |
| dotnet-runtime-s2 | luna | naming | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 773 | 141 | 0.0199 | 0 |
| dotnet-runtime-s2 | luna | chunk | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 844 | 163 | 0.0224 | 0 |
| dotnet-runtime-s2 | luna | bm25 | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 904 | 163 | 0.0232 | 0 |
| dotnet-runtime-s2 | luna | dense | 45 | 135 | 98.5 | n/a | 98.5 | 1.5 | 0.0 | 98.5 | 710 | 168 | 0.0209 | 0 |
| dotnet-runtime-s2 | luna | graph | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 93.3 | 557 | 137 | 0.0168 | 0 |
| dotnet-runtime-s2 | luna | graph[infer] | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 91.9 | 557 | 140 | 0.0170 | 0 |
| dotnet-runtime-s2 | gemini31fl | none | 45 | 135 | 97.8 | n/a | 97.8 | 2.2 | 0.0 | 94.1 | 553 | 115 | 0.0420 | 0 |
| dotnet-runtime-s2 | gemini31fl | fulldoc | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 2,442 | 112 | 0.1050 | 0 |
| dotnet-runtime-s2 | gemini31fl | naming | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 835 | 113 | 0.0510 | 0 |
| dotnet-runtime-s2 | gemini31fl | chunk | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 942 | 114 | 0.0549 | 0 |
| dotnet-runtime-s2 | gemini31fl | bm25 | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 1,014 | 114 | 0.0573 | 0 |
| dotnet-runtime-s2 | gemini31fl | dense | 45 | 135 | 99.3 | n/a | 99.3 | 0.7 | 0.0 | 99.3 | 770 | 111 | 0.0485 | 0 |
| dotnet-runtime-s2 | gemini31fl | graph | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 609 | 130 | 0.0469 | 0 |
| dotnet-runtime-s2 | gemini31fl | graph[infer] | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 609 | 129 | 0.0467 | 0 |
| dotnet-runtime-s2 | gemma4_local_s2 | none | 45 | 135 | 93.3 | n/a | 93.3 | 0.0 | 6.7 | 93.3 | 566 | 129 | - | 0 |
| dotnet-runtime-s2 | gemma4_local_s2 | fulldoc | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 2,455 | 108 | - | 0 |
| dotnet-runtime-s2 | gemma4_local_s2 | naming | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 848 | 107 | - | 0 |
| dotnet-runtime-s2 | gemma4_local_s2 | chunk | 45 | 135 | 97.8 | n/a | 97.8 | 0.0 | 2.2 | 97.8 | 955 | 116 | - | 0 |
| dotnet-runtime-s2 | gemma4_local_s2 | bm25 | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 100.0 | 1,027 | 120 | - | 0 |
| dotnet-runtime-s2 | gemma4_local_s2 | dense | 45 | 135 | 97.8 | n/a | 97.8 | 2.2 | 0.0 | 97.8 | 783 | 112 | - | 0 |
| dotnet-runtime-s2 | gemma4_local_s2 | graph | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 93.3 | 622 | 132 | - | 0 |
| dotnet-runtime-s2 | gemma4_local_s2 | graph[infer] | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 89.6 | 622 | 131 | - | 0 |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | none | 45 | 135 | 38.5 | n/a | 38.5 | 0.0 | 61.5 | 37.0 | 542 | 165 | 0.0107 | 0 |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | fulldoc | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 99.3 | 2,358 | 127 | 0.0344 | 0 |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | naming | 45 | 135 | 96.3 | n/a | 96.3 | 0.0 | 3.7 | 94.1 | 812 | 133 | 0.0137 | 0 |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | chunk | 45 | 135 | 75.6 | n/a | 75.6 | 0.0 | 24.4 | 74.1 | 909 | 481 | 0.0220 | 5 |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | bm25 | 45 | 135 | 74.1 | n/a | 74.1 | 0.0 | 25.9 | 72.6 | 976 | 362 | 0.0205 | 3 |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | dense | 45 | 135 | 81.5 | n/a | 81.5 | 0.0 | 18.5 | 80.7 | 750 | 208 | 0.0143 | 1 |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | graph | 45 | 135 | 99.3 | n/a | 99.3 | 0.0 | 0.7 | 91.1 | 596 | 156 | 0.0112 | 0 |
| dotnet-runtime-s2 | qwen35_9b_or_s2 | graph[infer] | 45 | 135 | 100.0 | n/a | 100.0 | 0.0 | 0.0 | 94.8 | 596 | 168 | 0.0115 | 0 |

## Tasks whose snippet holds another identifier with the required prefix

- godot-s2: 22 of 70 tasks (by kind: input_parameter 22).
  Examples: cpp_033__p_options__GODOT-PARAM-INPUT-PREFIX: p_length; cpp_035__p_source_id__GODOT-PARAM-INPUT-PREFIX: p_tile_set, p_tile_set_scenes_collection_source; cpp_037__p_stream_id__GODOT-PARAM-INPUT-PREFIX: p_pitch_scale; cpp_038__p_use_heaps__GODOT-PARAM-INPUT-PREFIX: p_device; cpp_043__p_popup_warning__GODOT-PARAM-INPUT-PREFIX: p_node.

| model | none core_ok_s2 with (%) | tasks | without (%) | tasks |
|---|---|---|---|---|
| luna | 100.0 | 22 | 97.9 | 48 |
| gemini31fl | 89.4 | 22 | 83.3 | 48 |
| gemma4_local_s2 | 97.0 | 22 | 75.0 | 48 |
| qwen35_9b_or_s2 | 57.6 | 22 | 45.8 | 48 |

- dotnet-runtime-s2: 16 of 45 tasks (by kind: instance_field 16).
  Examples: csharp_020___method__DOTNET-FIELD-INSTANCE-PREFIX: _factory; csharp_021___current__DOTNET-FIELD-INSTANCE-PREFIX: _buffer, _pos; csharp_027___paddingBytesCount__DOTNET-FIELD-INSTANCE-PREFIX: _contents; csharp_029___current__DOTNET-FIELD-INSTANCE-PREFIX: _remaining; csharp_031___lo__DOTNET-FIELD-INSTANCE-PREFIX: _exponent, _hi, _sign.

| model | none core_ok_s2 with (%) | tasks | without (%) | tasks |
|---|---|---|---|---|
| luna | 100.0 | 16 | 100.0 | 29 |
| gemini31fl | 100.0 | 16 | 96.6 | 29 |
| gemma4_local_s2 | 100.0 | 16 | 89.7 | 29 |
| qwen35_9b_or_s2 | 52.1 | 16 | 31.0 | 29 |

## Agreement of the inferred kind and facets with metadata

- godot-s2: 57 of 70 tasks agree. input_parameter -> input_parameter: 54; input_parameter -> output_parameter: 4; input_parameter -> parameter: 9; output_parameter -> output_parameter: 3.
- dotnet-runtime-s2: 45 of 45 tasks agree. instance_field -> instance_field: 44; static_field -> static_field: 1.

## Reference program (as addendum A10; no model)

core_ok_s2 is scored for the kind from metadata; none and selection are the mean over the models of core_ok_s2 on the same split.

| standard | kind from | tasks | core_ok_s2 % [95% Wilson] | exact % [95% Wilson] | core_ok_s2 by method | none % | selection % |
|---|---|---|---|---|---|---|---|
| godot-s2 | metadata | 70 | 100.0 [94.8, 100.0] | 100.0 [94.8, 100.0] | prefix_strip 35/35, prefix_swap 35/35 | 78.8 | 99.0 |
| godot-s2 | inferred | 70 | 81.4 [70.8, 88.8] | 81.4 [70.8, 88.8] | prefix_strip 29/35, prefix_swap 28/35 | 78.8 | 99.0 |
| dotnet-runtime-s2 | metadata | 45 | 100.0 [92.1, 100.0] | 100.0 [92.1, 100.0] | prefix_strip 22/22, prefix_swap 23/23 | 82.4 | 99.8 |
| dotnet-runtime-s2 | inferred | 45 | 100.0 [92.1, 100.0] | 100.0 [92.1, 100.0] | prefix_strip 22/22, prefix_swap 23/23 | 82.4 | 99.8 |

- godot-s2 (inferred) cpp_031__p_result__GODOT-PARAM-INPUT-PREFIX: `r_result` -> `result` (kind used parameter); original `p_result`; core_ok_s2 False
- godot-s2 (inferred) cpp_052__p_buffer__GODOT-PARAM-INPUT-PREFIX: `buffer` -> `r_buffer` (kind used output_parameter); original `p_buffer`; core_ok_s2 False
- godot-s2 (inferred) cpp_053__p_next_pointer__GODOT-PARAM-INPUT-PREFIX: `next_pointer` -> `r_next_pointer` (kind used output_parameter); original `p_next_pointer`; core_ok_s2 False
- godot-s2 (inferred) cpp_065__p_object__GODOT-PARAM-INPUT-PREFIX: `r_object` -> `r_object` (kind used output_parameter); original `p_object`; core_ok_s2 False
- godot-s2 (inferred) cpp_066__p_sink__GODOT-PARAM-INPUT-PREFIX: `sink` -> `sink` (kind used parameter); original `p_sink`; core_ok_s2 False
- godot-s2 (inferred) cpp_073__p_result__GODOT-PARAM-INPUT-PREFIX: `result` -> `result` (kind used parameter); original `p_result`; core_ok_s2 False
- godot-s2 (inferred) cpp_074__p_sink__GODOT-PARAM-INPUT-PREFIX: `sink` -> `sink` (kind used parameter); original `p_sink`; core_ok_s2 False
- godot-s2 (inferred) cpp_079__p_hash__GODOT-PARAM-INPUT-PREFIX: `r_hash` -> `hash` (kind used parameter); original `p_hash`; core_ok_s2 False
- godot-s2 (inferred) cpp_080__p_sink__GODOT-PARAM-INPUT-PREFIX: `r_sink` -> `sink` (kind used parameter); original `p_sink`; core_ok_s2 False
- godot-s2 (inferred) cpp_082__p_other__GODOT-PARAM-INPUT-PREFIX: `r_other` -> `other` (kind used parameter); original `p_other`; core_ok_s2 False

