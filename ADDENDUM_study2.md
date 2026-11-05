# ADDENDUM to HYPOTHESES_v2_study2

This file records what was decided or found while Study 2 was built and in its development round, where the registered amendment does not fix it or where the work differs from its text. Entries S2-A1 to S2-A10 were written before the freeze of Study 2 and before any test trial. HYPOTHESES_v2_study2.md is changed only where its Section 6 allows it (S2-A10). Steps taken after the freeze are added as later entries before they are scored.

## S2-A1. Pool rule, unit length and benchmark size

The amendment does not say whether a unit enters the pool when only one of the two injection methods gives a verified violation. This was decided after the sizes of the pools were seen: a unit enters when at least one method gives a verified violation. With both methods required, dotnet-runtime would have had 34 tasks; Godot has 100 tasks under either rule. The unit length of dotnet-runtime was kept at the registered 6 to 60 lines after the sizes at 100 and at 150 lines, 100 tasks each, had been seen. Its pool held 66 units in 53 files, so the policy of D13 for a short pool applied and 64 tasks were drawn, 19 dev and 45 test. Godot has 100 tasks, 30 dev and 70 test.

## S2-A2. Assignment of the injection method

The amendment draws the method with a fixed seed so that half of the tasks of each pack remove the required prefix and half replace it with the prefix of a sibling kind. The method is assigned after the task draw. On each split the tasks are put in a random order seeded with `athena2-s2-v1:<pack>:method:<split>`; the dev split receives ceil(n/2) removals and the test split floor(n/2), and a task whose unit gives a verified violation for one method only receives that method. Removal cannot be used when the name without its prefix already exists in the unit, as in `_count = count;`, so replacement was forced for 7 dev and 16 test tasks of Godot and for 7 dev and 21 test tasks of dotnet-runtime. Every split is balanced: removal and replacement are 15 and 15 (dev) and 35 and 35 (test) for Godot, and 10 and 9 (dev) and 22 and 23 (test) for dotnet-runtime.

## S2-A3. Conditions on the targets and the validation

Two conditions are not stated in the amendment. A target must be the only declaration of its name in the unit, because a class can hold a nested type that declares the same name. The validation uses `validate_benchmark_s2.py`, which is `validate_benchmark.py` of Study 1 with one addition: it reproduces the replacement method. Both packs pass with 0 errors.

The benchmark holds, for Godot, 97 input_parameter and 3 output_parameter tasks, and for dotnet-runtime, 62 instance_field and 2 static_field tasks. No task tests the prefix t_ of thread-static fields. Of the Godot tasks, 34 are on a unit that was a task of Study 1; of the dotnet-runtime tasks, 2 are on a unit that contains a task of Study 1, and 3 are on a type nested in the unit of another task.

## S2-A4. Ontologies and prompts

The prompt template of Study 1 names the kind of the identifier in every condition, and the amendment changes no prompt wording, so the prompts name the Study 2 kinds. The name of a Study 2 kind states its facet (input_parameter, instance_field), so even the prompt of condition none tells the model the facet, though not the prefix. The eligibility rule of Section 2.3 is the check that condition none is not at the ceiling.

For the inferred label, the Godot definition of the kinds (`packs/godot-s2/KINDS.md`) reads "a reference or a pointer to a type that is not const" where the amendment reads "a reference or a pointer that is not const": the const that counts is that of the type referred to.

`DOTNET-FIELD-NONPUBLIC-CASE` is outside the core, with its reason in `core_rules.json`, so the casing after the prefix is not checked and `_Count` passes core_ok_s2. The rule descriptions in the Study 2 ontologies are those of Study 1.

## S2-A5. Model pins

The pins of Study 2 are in `models/model_pins_s2.json`, a new file, because a test of Study 1 fixes the set of names in `models/model_pins.json`. The hosted pins and the embedding pin are copied with the same SHA-256 as in Study 1; the two local pins differ from those of Study 1 only in the output limit, 8,192 tokens.

## S2-A6. Development round: two copies of the run script

For the hosted models two copies of the run script ran at the same time, so many keys of GPT-6 Luna and Gemini 3.1 Flash-Lite were written twice: 61 and 133 records on the meta runs of Godot and dotnet-runtime for GPT-6 Luna, 193 and 129 for Gemini 3.1 Flash-Lite, and some on the infer runs. Three lines were written into each other and cannot be read. No key is missing and no trial ended in an error. The locally served models ran once. The rule that the first record of a key without an error, by its time stamp, is the trial of the round was proposed before the results were computed, and was confirmed after both choices were seen to give the same decision: the mean of condition none is 79.2% (Godot) and 81.6% (dotnet-runtime) with the first record and 77.5% and 80.3% with the last. The other records are counted and not used. The script was changed so that a second copy stops at once; the round was not repeated, because no task, core, checker or prompt changed.

## S2-A7. Development round: eligibility

Condition none reached 79.2% on Godot and 81.6% on dotnet-runtime, both below 90%, so both standards are included and the Holm family of H1-S2 has 2 × 4 = 8 tests. No trial ended at the output limit. Answers that could not be parsed, 5 of Qwen3.5-9B on dotnet-runtime and 1 of Gemma 4 26B on Godot, count as failures, as registered. No defect was found and nothing was changed after the round.

## S2-A8. The analysis, written before the freeze

The analysis was written after the development round and before the freeze, in `athena-sim/athena_s2/analysis.py`, which the freeze includes in its code hash. It is run with the commands of `athena-sim/README_study2.md`, the README of Study 2 in the package. It fixes the following, which the amendment leaves open.

- Records: the family of a run is read from its `config.json`; when a key was written more than once, the first record without an error by its time stamp is used and the others are counted; a key with errors only is reported and left out.
- H3-S2 in a cell is supported when selection is non-inferior to fulldoc and higher than each of chunk (TF-IDF), bm25 and dense, the last with one Holm family over all cells, and clearly against when selection is inferior to fulldoc. H2-S2 to H4-S2 are summarised as in HYPOTHESES_v2 Section 2.4. For H1-S2 the number of tests that support it is reported, with no summary verdict.
- The Study 1 core_ok applies the core of the Study 1 pack to the Study 1 kind (parameter or field). It is not defined for dotnet-runtime, whose Study 1 core has no rule for fields.
- The required prefix is that of the core rule of the task's kind; a name without it carries a sibling prefix (another prefix of the same core table) or none.
- A snippet shows the required prefix on another identifier when, after comments and string and character literals are removed, an identifier other than the injected name starts with that prefix and is longer than it.
- The reference program is that of addendum A10 of Study 1, with one step added: it removes a leading prefix of the core table before it adds the required one. It is run once with the kind from metadata and once with the inferred kind.
- The drift check follows HYPOTHESES_v2 Section 2.1: the identity of the model is compared between its first and its last trial over the canary and test trials; if a model is flagged, H1-S2, H2-S2 and H3-S2 are recomputed without it.

The script was run on the development round as a check of the procedure; it gives the eligibility values of S2-A7.

## S2-A9. Canary set

Sections 2.1 and 5 of the amendment give 60 canary units, 30 per pack. dotnet-runtime has 19 dev tasks, so the canary set is every dev task, 49 units: 30 of Godot and 19 of dotnet-runtime.

## S2-A10. A command name corrected in the amendment

Section 6, step 3 named `validate_benchmark.py`; the validation of Study 2 is run with `validate_benchmark_s2.py` (S2-A3). As Section 6 allows, the name was corrected in HYPOTHESES_v2_study2.md before the freeze. The file had been released in version 1.7.0 of the package; no other word was changed, and the freeze records the corrected file.

## S2-A11. Qwen3.5-9B: the test round moved to a hosted deployment

During the test round the machine that served the locally served pins stopped and could not be started again. GPT-6 Luna, Gemini 3.1 Flash-Lite and Gemma 4 26B had completed both canary runs and all test runs. Qwen3.5-9B (`qwen35_9b_s2`) had completed its canary before and 1,091 of its 2,760 test trials; the harness had stopped three of its test runs after 20 consecutive connection errors, and they had been resumed with the same run identifiers. No result of the test round had been computed when this entry was written.

The test round of Qwen3.5-9B is run again in full on a hosted deployment of the same open weights, under a new pin, `qwen35_9b_or_s2`, in a new file, `models/model_pins_s2_or.json`; `models/model_pins_s2.json` is not changed. The pin sends the request of `qwen35_9b_s2` (temperature 0.2, output limit 8,192 tokens, thinking off) to OpenRouter, model `qwen/qwen3.5-9b`, with the provider locked to DeepInfra at bf16 and no fallback. Thinking is turned off with the reasoning parameter of OpenRouter (`reasoning.enabled: false`) instead of the chat-template argument used by the local server. DeepInfra was chosen among the three bf16 endpoints for its stated quantization, its uptime and its support of every parameter sent; if it becomes unavailable during the round, the replacement is reported. The file also holds the embedding pin, copied with the same SHA-256, so the dense condition reads the same query embeddings.

Before the freeze the request was checked on 4 Godot dev units under conditions none and fulldoc (8 trials, written outside the run folders and not used): every trial was served by DeepInfra, the prompt token counts equal those of the local server on the same keys, and no answer holds thinking text; one trial ended at the output limit.

Four frozen setups, `frozen_PACK_qwen35_9b_or_s2_FAMILY.json`, are made with the options of the other setups; the code, the packs, the hypotheses and the other pins are those of the freeze. The model then runs its canary before (49 units), the four test runs and its canary after, as the other models did.

The analysis uses the hosted runs for Qwen3.5-9B in H1-S2 to H4-S2, the cell tables and the drift check, so the Holm family of H1-S2 keeps 8 tests. The 1,091 local test trials and the local canary before are reported by count and not used. Eligibility (S2-A7) was decided on the development round, which Qwen3.5-9B ran on the local pin, and is not recomputed. The command of the analysis names the run folders so that the local test runs are left out, with no other option:

    python analyse_study2.py runs/s2dev_* runs/s2test_luna_* runs/s2test_gemini31fl_* runs/s2test_gemma4_local_s2_* runs/s2test_qwen35_9b_or_s2_* --canary runs/s2canary_*_luna_* runs/s2canary_*_gemini31fl_* runs/s2canary_*_gemma4_local_s2_* runs/s2canary_*_qwen35_9b_or_s2_* --out ../analysis/study2.md --json ../analysis/study2.json

The Qwen3.5-9B cells therefore come from a bf16 hosted deployment, while its development round and Study 1 used the 8-bit local deployment (UD-Q8_K_XL). The provider does not state the revision of the weights it serves and sends no system fingerprint, so the drift check of this model compares the model and the provider only.

## S2-A12. Test round: how the runs went

Order. The locally served models ran one at a time on the serving machine, Gemma 4 26B and then Qwen3.5-9B; the hosted models ran at the same time from a second script, GPT-6 Luna and then Gemini 3.1 Flash-Lite. Each model ran its canary before, its four test runs and its canary after, in that order. Qwen3.5-9B then ran on the hosted pin (S2-A11), in the same order.

Query embeddings. Before the locally served models started, the queries of the test split were embedded into the cache by the harness with the mock backend (`--backend mock:oracle --split test --conditions dense`), with the embedding pin and server of the freeze; the mock backend calls no model, writes no ledger and writes outside the run folders. A second pass with the embedding server stopped returned every test task (70 Godot and 45 dotnet-runtime) from the cache. The hosted runs read the cache only.

Interruptions. The network link to the serving machine dropped during the Godot meta run of Gemma 4 26B; the run stopped making progress and was started again with the same run identifier, so its ledger holds two start events and one end event, with no rerun. Each of the three local test runs of Qwen3.5-9B that the harness stopped (S2-A11) ended after 20 consecutive connection errors (refused, reset or timed out). In the hosted round of Qwen3.5-9B one trial ended with a rate-limit error from the provider after six attempts and was run again by the second pass of the script. Records with an error are not used (S2-A8); no key of the runs in the analysis has errors only, and no line of any run is unreadable.

Hosted Qwen3.5-9B round. All 2,858 trials completed: the canary before and after (49 units each) and 2,760 test trials, every one served by DeepInfra under the model id `qwen/qwen3.5-9b` with no system fingerprint. Sixteen test trials (0.58%) and one canary trial on each side ended at the output limit. In the drift check, core_ok_s2 under none on the 49 canary units was 17 before and 16 after (6 units from pass to fail, 5 from fail to pass; exact McNemar p = 1.000) and the identity did not change, so the model is not flagged.

Comparison of the two deployments of Qwen3.5-9B (descriptive). Both deployments ran the canary before on the same 49 dev units under condition none (`s2canary_before_qwen35_9b_s2_*` and `s2canary_before_qwen35_9b_or_s2_*`). Reported: core_ok_s2 of each, the discordant pairs with the exact two-sided McNemar p, and the share of units with the same proposed name. The comparison decides nothing, changes no data and is not part of any hypothesis. It is computed with `athena-sim/analyse_s2_a12.py`, which reads the trials as the analysis does (S2-A8), after this entry was written.

## S2-A13. The kind used by the condition with the inferred kind

The manuscript explains the result of H4-S2 on Godot by the kind that the condition with the inferred kind used. Every trial records that kind (`kind_used`, with `kind_inferred` and `facets_inferred`). It was counted after the test results had been read, and this entry was written after the count, so the count is descriptive, is not part of any hypothesis and changes no data.

On the Godot test tasks the kind used equals the kind from metadata on 57 of the 70 tasks. Four input parameters were taken as output parameters, because their type is a pointer or a reference to a type that is not const, and nine as parameters of a function outside a class, which carry no prefix rule, because the snippet of a method defined inside a class body does not show the class. All 45 dotnet-runtime test tasks agree. The kind used of a task is the same in every model and round.

The count reads the selection trials (condition graph) of the test infer runs that the analysis uses (S2-A11), with the reading rules of S2-A8, and is computed with `athena-sim/analyse_s2_a13.py`.
