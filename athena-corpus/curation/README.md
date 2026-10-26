# Athena Task C curation (corpus -> benchmark)

Turns the 792 raw corpus files (`../corpus/`) into `../benchmark/snippets/<lang>/*.json` and
`../benchmark/violations/<lang>/*.json` following `benchmark_schema.md`. No LLM is used anywhere; every step is
deterministic (two runs give byte-identical files). Results and caveats: `../benchmark/curation_report.md`.

## Files

| File | Role |
|---|---|
| `curate.py` | main pipeline (parse -> gate -> pick targets -> inject + verify rename -> select -> write) |
| `rules.py` | ontology reader, the `CORE` rule table (which NamingRules gate/target which kinds), `EXCLUDED` rules with reasons |
| `core_table.py` | Vol. 2: loads and validates a pack's `core_rules.json` against its ontology and installs it with `rules.set_core()` (see "Athena Vol. 2 changes") |
| `lang_python.py` | Python extractor (stdlib `ast` + `tokenize`) |
| `lang_ts.py` | Java / C# / TypeScript(+TSX) / JavaScript(+JSX) extractors (tree-sitter) |
| `tsbind.py`, `tools/build_treesitter.sh` | tiny ctypes binding + script that builds the tree-sitter library from pinned GitHub commits |
| `facts.py` | shared data model |
| `validate_benchmark.py` | independent validator, **standard library only** (runs on any machine, no parsers needed) |
| `syntax_check.py` | every snippet and violated context parses standalone (needs the tree-sitter library) |
| `make_comment_units.py` | builds the comment-generation units (Task C, RQ2) in `../benchmark/comment_units/` from the curated snippets plus, where a language has fewer than 30 qualifying snippets, extra units mined from the 792-file corpus |
| `validate_comment_units.py` | independent validator for `comment_units/`, **standard library only** (skips the tree-sitter-dependent `expectedElements` re-check when the library is unavailable) |
| `make_report.py` | regenerates `../benchmark/curation_report.md` from `curation_stats.json` |
| `pipeline/` | vendored copies of the project's `violation_injector.py`, `output_validator.py`, `graph_loader.py`, `graph_rag.py` and the ontology used |
| `_transfer/` | tarballs used to move files between the sandbox and this folder; safe to delete |

Vendored copies (source: the Vol. 1 `ontology` folder; the ontology is the newer 206,806-byte version):

| File | sha256 (first 16) |
|---|---|
| `pipeline/violation_injector.py` | `f939131cc09a78c4…` |
| `pipeline/output_validator.py` | `d154237dfca677ea…` |
| `pipeline/graph_loader.py` | `a4b1b62954bb3baa…` |
| `pipeline/graph_rag.py` | `ac87c33552a180fa…` |
| `pipeline/athena_ontology.json` | `716026bb9e8fa0a6…` |

## Check the delivered benchmark (any machine, Python 3.10+)

```
cd athena-corpus/curation
python validate_benchmark.py --benchmark ../benchmark --corpus ..
```

## Re-run from scratch (Linux / WSL; needs git, gcc, network to github.com)

```
cd athena-corpus/curation
bash tools/build_treesitter.sh                      # writes libtsall.so here (pinned commits)
python curate.py --corpus .. --out ../benchmark_rerun --per-language 100
python validate_benchmark.py --benchmark ../benchmark_rerun --corpus ..
python syntax_check.py --benchmark ../benchmark_rerun
diff -r ../benchmark/snippets ../benchmark_rerun/snippets   # expect no differences
```

`pip install tree-sitter tree-sitter-java ...` (py-tree-sitter) was not available in the build session (PyPI/npm blocked),
which is why the library is built from source; an adapter for py-tree-sitter would be straightforward but has not been written or tested.

## Tuning knobs (top of `curate.py`)

`MIN_LINES`/`MAX_LINES` (6/40), `MAX_TARGETS` (6 identifiers per snippet), `MIN_TARGET_LEN` (3), `--per-language` (100).
Change the rule policy in `rules.py` (`CORE`, `rules_for_check`, `name_for_check`); the start-up check refuses a `CORE` entry the ontology cannot retrieve.

## Comment units (Task C, RQ2)

```
cd athena-corpus/curation
python make_comment_units.py --corpus .. --out ../benchmark      # writes benchmark/comment_units/
python validate_comment_units.py --benchmark ../benchmark --corpus ..
```

Deterministic, no LLM. One unit per qualifying snippet (kind `function`/`method`/`class` only;
`interface`/`enum`/`const`/`constructor` are skipped) plus, for languages with fewer than 30 such
units, extra units mined directly from the 792-file corpus (`origin: "extra"`, id `cx_<lang>_NNN`,
deterministic selection order, capped at 2 per file / 25% per repo / 40 per language). The
reference comment is read from the **pinned corpus file**, not the already-dedented snippet text,
since for every language but Python the doc comment sits above the snippet's own line range
(Python's docstring is the unit's first body statement, so it comes from the snippet's own
`codeContext`). `signature`/`expectedElements` (params/returns/throws) are inferred from the code
itself (`ast` for Python, tree-sitter elsewhere), never from the comment, so grading can tell a void
method apart from one that must document a return value. See `curation_report.md` for counts,
rejection reasons and known gaps (several CommentRule formats have no mechanical check at all).

## Athena Vol. 2 changes

Everything above describes the Vol. 1 pipeline; the files in this folder are a copy of it. Only the tree-sitter layer was changed:

- `tools/build_treesitter.sh` also builds `tree-sitter-cpp` at `c009222808634c1014f82438d4883753516a2c24` (2026-09-17; untagged, newer than the last release v0.23.4 of 2024-11-11; parser ABI 15). The five Vol. 1 pins are unchanged.
- `tsbind.py`: `LANG_SYMBOLS` gained `"cpp": "tree_sitter_cpp"`.
- `tools/smoke_test_treesitter.py`: parses one hand-written snippet per language and exits 1 on any parse error or missing library.
- The rebuilt `libtsall.so` (git-ignored) gave the same parse trees as the Vol. 1 library on one small snippet per Vol. 1 language (java, csharp, typescript, tsx, javascript); that is a spot check, not a full regression.
- A C++ extractor is available in `lang_ts.py` (see `CPP_EXTRACTOR_PLAN.md`).
- `curate.py` accepts `--languages cpp`. C++ has no built-in `CORE` table: pass `--core <core_rules.json>`. The default `--languages` is still the five Vol. 1 languages, and a run without `--core` uses the hard-coded Vol. 1 tables and special cases unchanged.
- `core_rules.json` (one per pack, next to the pack's ontology) lists, per language and identifier kind, the naming rules that every identifier of that kind must satisfy, plus every other naming rule that applies to the language under `excluded` with a reason. The ontology has no field that marks a rule as conditional, so this file is where that decision is recorded. `python core_table.py --ontology <ontology.json> --core <core_rules.json>` checks that every listed rule exists, applies to its language and kind, and is mechanically checkable, and that no naming rule of the language is left unclassified. With `--core`, the Vol. 1 special cases in `rules_for_check()` are off and `EXCLUDED` is taken from the file. Format: `{"schema": 1, "core": {"<language>": {"<kind>": ["RULE-ID"]}}, "excluded": {"RULE-ID": "reason"}}`.
- `validate_benchmark.py` takes `--languages` and `--core` too. `make_report.py` (its text and numbers are specific to the five Vol. 1 languages), `syntax_check.py` and `make_index.py` still handle those five languages only.
- `tests_core/test_core_table.py` checks `core_table.py` against an ontology made in memory (the Vol. 1 ontology plus a C++ language and a few generic `TESTONLY-*` rules, which are not rules of any real standard) and runs `curate.py --core` and `validate_benchmark.py --core` on a tiny C++ corpus. Run `python3 -m unittest tests_core/test_core_table.py` from this folder.
- The Vol. 2 pool is not built here yet: `curate.py` still selects up to `--per-language` snippets as in Vol. 1. The D18 selection (one violation per task, random target, hand-off to `tools/select_tasks.py`) is a separate step.
- Probe on 10 hand-picked Godot files (`5ec712e220b7`): 10 of 10 files parse with at least one error node (macros such as `RequiredResult`/`RequiredParam`, operator overloads), while 1,264 of 1,386 `function_definition` nodes (91.2%) contain no error node. Only the per-function numbers matter for snippet extraction, and the sample is neither random nor representative.
