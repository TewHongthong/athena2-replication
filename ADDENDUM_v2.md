# ADDENDUM to HYPOTHESES_v2

This file records steps taken after the freeze. HYPOTHESES_v2.md is not edited.

## A1. Model selector of the analysis commands

Section 6, step 6 passes pin names to `--models`. The analysis scripts match this option against the model identifiers stored in the trials, which differ from the pin names. The analysis was run with `--models luna,gemini,qwen3.5-9b,gemma-4`, which selects the same four models. No result depends on this choice.

## A2. Scope of the confirmatory run

The confirmatory analysis was given the test runs only, as in Section 6, so its eligibility section reports no dev data. The status of H1 does not come from that section: on the dev split every standard is at or above 90% zero-shot, so H1 is reported as not testable under its registered rule.

## A3. Trials that ended in an error or at the token limit

A trial that ended with an error or at the output limit is scored as produced and is not rerun.

## A4. Dose-response analysis (exploratory)

Added after the test data were seen and written before it is scored. For each (standard, model) cell, the compliance of every condition is related to the mean prompt size of that condition (`prompt_chars`) on the units that all conditions share, with the Spearman correlation and an exact permutation p-value. It is run on the meta-family test runs with `python analyse_secondary.py dose runs/test_*_meta`. It describes how conditions differ in size and outcome; it is not a causal estimate of the effect of context size and has no decision rule.

## A5. Descriptive tables

Exact-match rate, prompt and completion tokens, and cost per model and standard are reported as descriptive statistics from the trial files, without tests.

## A6. Labelled renames of H6

H6 is measured on the labelled renames in `renames.csv`, built by `athena-sim/make_h6_labels.py`. The conflict cases are the 40 hand-written controls of the scope check (`curation/tests_scope`) that state a binding conflict. The renames to fresh names are one per task of B1 (100 per standard: 30 development and 70 test), made by renaming the injected name back to the original name; the compliant code used that name, so there is no conflict by construction. The scope-aware check flags a rename if the binding check or the declaration check reports a conflict; the scope-blind check flags it if the new name already occurs in the snippet as a word. A task for which the check gives no verdict (a snippet that does not parse) is left out and counted. The 24 hand-written controls without a conflict, which include harmless name collisions, are reported separately in `renames_all.csv` and do not enter the test of H6.

## A7. Review of the verdicts of core_ok (exploratory)

Added after the test data were seen and written before the review was scored. The first author, who is not blind to the design, reviewed a sample of the verdicts of core_ok on the meta-family test runs. The frame is every trial that has a proposed name: 15,045 of 15,188 trials (68 trials that ended in an error and 75 trials without a parsed name are not in it). Twenty trials with core_ok = 1 and twenty with core_ok = 0 were drawn with a fixed seed. The reviewer saw the language, the kind of identifier, the proposed name, the code with that name applied, and the naming rules of the standard quoted from the pinned document. The reviewer did not see the injected name, the model, the condition, the text of the standard given in the prompt, the reasoning of the model, or the verdict of the program. The answers were complies, does not comply, and unsure, and the sheet was saved once, when complete. Agreement is reported for each stratum with a Wilson 95% interval and for all judged items; Cohen's kappa is not reported, because 99% of the trials in the frame have core_ok = 1. Two earlier rounds are not used. In the first, the sheet showed the code before the rename and did not state the question, and the reviewer judged that code. In the second, the sheet was not completed, and its answers were changed after the verdicts of the program for some items had been shown. The sample of the third round excludes the trials of both. The sheet and the comparison are made by `make_blind_sheet.py` and `score_blind.py`.

## A8. Godot parameters without the p_ or r_ prefix (exploratory)

Added after the test data were seen and written before it is counted. The core rule for parameters in the Godot pack checks snake_case only; the prefix rules for input and output parameters are excluded from the core (Table B1), so a parameter name without p_ or r_ can pass core_ok. The review of addendum A7 found two such names. To size the gap, the meta-family test trials of the Godot pack whose kind is parameter are counted with `python count_godot_prefix.py runs/test_godot_*_meta`. A trial is counted if it has a proposed name and did not end in an error. It is a prefix miss if its name does not start with p_ or r_; whether the prefix is the right one of the two is not checked, because the kind alone does not tell input from output. The count is reported for core_ok = 1 trials, for all counted trials, for each condition and each model, with Wilson 95% intervals, and the share of the original names of these tasks that start with p_ or r_ is given for reference. It is descriptive, has no test and no decision rule, and changes no result in the main tables.

## A9. Uncertainty at ceiling, ontology relations, coverage, and conflict diagnostics (exploratory)

Added after the test data were seen and written before its results were read. It changes no verdict and no result in the main tables, adds no decision rule, and uses no new model call. The analyses are computed with `python analyse_a9.py --meta runs/test_*_meta --llm runs/test_*_llm --labels renames_all.csv`.

For H3, each of the 12 cells is described by the number of tasks on which selection scores higher, lower, and equal to fulldoc (the mean of core_ok over the three rounds of a task), and by the number of source files with a difference. For each cell, the exact one-sided 95% upper limit of the share of tasks on which selection could be lower is reported, computed once over tasks and once over source files, the second being the larger and valid under clustering. The limits are compared with the margin of 2 percentage points in words only.

For H2, the gain of selection is reported with the room left by none (100 minus the zero-shot compliance of the cell) and the share of that room that selection closes, and the permutation p-value is read as not interpretable, because the gain is the difference of two quantities one of which is bounded at 100%.

The number of overrides and conflicts relations is counted in each human and drafted ontology, together with the number of rules selected for each test task, so that the prompts of selection can be compared with a lookup by language and kind.

A coverage table lists, for each standard and each identifier kind in its test tasks, the number of test tasks, whether the core rules of the human ontology check the kind, and whether the human and the drafted ontology hold a rule for it.

For H6, the confusion matrices (flagged and not flagged, by conflict and no conflict) are reported by set (hand-written controls and renames to fresh names) and by language for the scope-aware check and the word screen. The 12 local-function cases of the renaming of all planned targets are stated apart from the 300 renames of H6.

## A10. A program that applies the casing rule (exploratory)

Added after the test data were seen and written before its result is computed. It uses no model, changes no verdict and no result in the main tables, and has no decision rule. For each test task of the three packs, a program takes the injected name, the kind of the identifier, and the core rules of the human ontology for that kind and language, splits the name into words (at underscores and at changes of case, keeping a run of capital letters as one word), and joins the words in the casing that the rules require, with the prefix and the suffix of the rule if it has any. The proposed name is scored with the same function as the trials of the models (`core_ok` and `exact_match`), and the result is reported for each pack with a 95% Wilson interval over tasks, next to the observed `core_ok` of condition none and of selection (Table IV). The program does not read the original name, and it is deterministic, so it has one result per task. Rules that the core of the human ontology excludes, such as the prefixes p_ and r_ of Godot parameters (Table B1), are not applied, so the program has the same blind spot as the checker. The result is a reference for a program that knows the kind and the rule, not a measure of what a model could do without them. It is computed with `python repair_baseline.py`.

## A11. Dependence in the intervals of Table IV, trials at the output limit, and the naming part of the standards (exploratory)

Added after the test data were seen. It changes no verdict and no result in the main tables, adds no decision rule, and uses no new model call. Its wording was fixed before the analysis was computed, with the two exceptions stated below, which were written after its results had been read. It is computed with `python analyse_a11.py --meta runs/test_*_meta`.

First, for each model-standard cell and each condition, `core_ok` is recomputed with the task as the unit: the mean over the three rounds of a task is taken first, and the cell is reported with the proportion over trials and its Wilson interval, as in Table IV, next to the mean of the task means with a Wilson interval whose number of observations is the number of tasks, a percentile bootstrap over tasks, and a cluster bootstrap over source files, the last two with the resamples and the seed of the confirmatory analysis. The Wilson interval over tasks is the first exception: it was added after the bootstrap intervals were seen to be degenerate in the cells in which every task scores 1.

Second, the trials whose output ended at the limit are removed, the cells they affect are recomputed, and their number is reported together with the paired difference between selection and each retrieval condition before and after. Addendum A3 keeps such a trial as produced; this analysis does not change that rule, it reports what the rule costs.

Third, for each standard the part of the document that concerns naming is measured against the whole text that fulldoc sends and the rules that selection sends. The document is split into passages as the retrieval conditions split it, and a passage is counted as naming if its heading path matches a fixed expression for naming, identifiers, casing, prefixes, suffixes and abbreviation, or, in a second selection, if its own text matches that expression; the expression and the headings counted are reported with the result. Sizes are given in characters, and the tokens of a prompt that carried the naming part alone are estimated from the tokens the provider counted for the fulldoc prompt of the same cell, at its measured rate of characters per token. This estimate and the second selection are the second exception: they replaced a count with the tokenizer of the prompts and a selection by heading alone, after the tokenizers of the hosted models were found not to be available offline and the document of one standard was found to hold no heading that concerns naming.

## A12. Round-to-round disagreement, the difference H4 could detect, the flags of the scope-aware check, and two cells read by hand (exploratory)

Added after the test data were seen. It changes no verdict and no result in the main tables, adds no decision rule, and uses no new model call. Its wording was fixed before the analysis was computed. It is computed with `python analyse_a12.py --meta runs/test_*_meta --llm runs/test_*_llm`.

First, the agreement between the three rounds of a task is reported. For each model-standard cell and each condition, the tasks are counted by the number of rounds whose suggestion `core_ok` accepts, none, one, two or all three, and the share of tasks whose rounds do not agree is reported next to the proportion over trials of Table IV, so that a cell in which the rounds of every task agree can be told from a cell whose mean rests on tasks the model answers differently from round to round. The same counts are reported pooled over the cells of a condition, and the units whose rounds disagree in every cell of a model are listed.

Second, for H4 the difference the design could detect is reported next to the equivalence margin of 5 pp: the standard error over the resamples of the cluster bootstrap over source files is taken, with the seed and the number of resamples of that analysis, and the half-width of the observed interval and the difference detectable at the 5% level with 80% power are reported for each standard and pooled, together with the number of units and of source files that enter each. The standard whose LLM-drafted ontology holds no naming rule for the kind the benchmark injects is reported apart, because there the quantity measures coverage and not a difference.

Third, the renames to fresh names of H6 that the scope-aware check flags are listed one by one, with the language, the identifier kind, the name before and after, and the reason the binding check or the declaration check gives, next to the flags the scope-blind word screen raises on the same renames; the number of each and the number of renames for which a check gives no verdict are reported. The labelled renames are those `make_h6_labels.py` builds, rebuilt for this analysis from the frozen benchmark.

Fourth, two cells are read by hand and quoted. For GPT-6 Luna on the Godot standard, the first ten parameter trials by unit identifier whose proposed name lacks the `p_` or `r_` prefix are quoted with the original name, the injected name and the suggestion, next to the suggestion the selection condition gives for the same unit; the condition read is `none`, because the prefix rule lies outside the core rules and such a name is what addendum A8 counts. For the dense retrieval condition on the .NET runtime standard, the passages retrieved for the first ten units by identifier whose suggestion `core_ok` rejects in that condition are quoted with their identifiers and heading paths, next to the rules selection sends for those units. No count is derived from either reading; it is reported to show what the proportions of Table IV and of A8 rest on. The first of the two readings was changed after the selection condition of GPT-6 Luna on the Godot standard was found to hold no trial that `core_ok` rejects; it is stated here because the wording of the rest of this addendum was fixed before its analysis was computed.

## A13. The accuracy of the inferred kind, the paired outcomes behind the
## differences of H3, and the source file clusters of the test split (exploratory)

Three analyses of the frozen runs, added after the test results were seen. They
carry no decision rule and call no model again. Provisional values of all three
were computed while this addendum was planned, so none of them is confirmatory.

First, the kind the pipeline infers is compared with the kind in the unit
metadata on the test split, per standard, with the pairs it confuses and the
trials whose kind is wrong and whose core_ok still passes. A drop in compliance
bounds what a wrong kind can cost; it does not give the rate at which the kind
is wrong, because two kinds can select the same casing rule.

Second, the wins, ties and losses of the paired tasks behind every mean
difference of H3 are reported next to that difference, for selection against
the full document and against no standard. A cell in which no task differs
shows that the two prompts agree on the tasks of this benchmark; it is not a
bound on the size of a difference, and a count of cells that pass the registered
rule does not separate the two.

Third, the number of source file clusters among the test tasks of each standard
is reported, with the tasks per cluster and the largest cluster. This is the
number the cluster bootstrap resamples, and it is smaller than the number of
files in the pinned corpus.

The records of a run's csv include the records of every run that shares its
keys, so a trial can appear more than once there. One record per unit, repeat
and model is kept, the last one read, which is the rule report.load_trials
applies to the json records.
