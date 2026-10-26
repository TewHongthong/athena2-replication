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
