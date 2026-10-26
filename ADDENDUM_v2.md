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
