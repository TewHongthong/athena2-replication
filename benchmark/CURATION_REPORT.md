# Curation report of the benchmark

This report describes how the 300 rename tasks of the benchmark (100 per pack) were drawn from the pinned
repositories. The procedure was registered in HYPOTHESES_v2.md (D12, D13, D18) before the pools were counted. The
task files of each pack are in benchmark/<pack>/.

## Source

The code comes from the pinned commits listed in athena-corpus/pins/corpus_pins.json: godot (C++), dotnet-runtime
(C#) and odoo (Python). Only files and commits after the cutoff date 2026-06-01 shared by all models are used. The
source files are not part of the package; athena-corpus/curation/tools/fetch_corpus_pins.py fetches them and checks
every file against the git blob identifier in athena-corpus/pins/.

## Procedure

1. Units. A unit is a function or method body of 6 to 40 lines that does not overlap a parse error of its file.
   The extractors are based on tree-sitter for C++ and C# and on a Python extractor for Python.
2. Gate. A unit enters the pool only if every identifier that the ontology checks already passes all the core rules
   of its kind, so the injected name is the only violation in the snippet.
3. Target and violation (tools/build_pool.py). The eligible identifiers of a unit are put in a fixed random order,
   seeded per unit. The first one that gets a verified violation is the target. A candidate name is accepted only if
   it is a valid identifier, is not already in the unit, fails the rule under the checker, leaves the parse-tree
   shape of the file unchanged after renaming every occurrence, and gives no conflict in the scope-aware check.
   Candidates are tried in the order casing swap, forbidden pattern, abbreviation, prefix strip, suffix strip.
   No model is called. Units with identical code are dropped.
4. Split (tools/select_tasks.py). The SHA-256 of the file path, taken mod 100, puts the file on the development
   side (below 30) or the test side. All units of a file fall on the same side.
5. Selection. Within each pack and side the pool is sorted by (path, unit index) and shuffled with the seed
   "athena2-b1-v1:<pack>:<side>". Units are taken in that order, with at most 3 tasks per file, until 30
   (development) and 70 (test) tasks are reached.
6. Export (tools/export_tasks.py) and validation (validate_benchmark.py --core): 0 errors for all three packs.

## Counts

| | godot (C++) | dotnet-runtime (C#) | odoo (Python) |
|---|---|---|---|
| Units of 6 to 40 lines without parse error, before the gate | 771 | 2,895 | 1,680 |
| Pool after the gate and the injection check | 356 | 2,228 | 848 |
| Files in the pool | 64 | 375 | 260 |
| Pool, development / test | 128 / 228 | 636 / 1,592 | 240 / 608 |
| Tasks, development / test | 30 / 70 | 30 / 70 | 30 / 70 |
| Cap per file used | 3 | 3 | 3 |
| Tasks by kind | parameter 34, method 39, variable 24, function 3 | method 100 | parameter 100 |
| Injection method | casing swap 100 | casing swap 100 | casing swap 100 |

Godot tasks by kind and side: development function 2, method 10, parameter 12, variable 6; test function 1,
method 29, parameter 22, variable 18. The counts of every pack are also in benchmark/<pack>/tasks_summary.json.

## Core rules without a target

The extractors were not changed to add targets. A core slot with no injection target is untested.

- godot: struct, union, type alias, macro and namespace (the C++ extractor gives no kind to the last three and
  merges struct and union into class).
- dotnet-runtime: local function (declarations with the exempt label are skipped), so only methods are injected.
- odoo: module and package (the Python extractor gives no such kinds).

Every violation was made by a casing swap, the first method in the order above. Results must not be generalised to
the other kinds or to other injection methods.

## Decision taken after the pool was counted

With the original core of Odoo (constant, module, package) the pool held 5 units and gave 3 tasks, none on the
development side. The rule ODOO-PARAMETER-CASE was then moved into the core, because the extractor already marks
the first parameter named self, cls, mcs or metacls as exempt. The core_rules.json of Odoo changed from sha256
82279a45... to 8f32b8ff...; the ontology file is unchanged. The decision follows the count, and the paper reports
it as a threat to validity.

## Reproducing

    python3 athena-corpus/curation/tools/build_pool.py --pack <pack> --language <language> \
        --corpus athena-corpus/corpus_v2 --ontology athena-sim/packs/<pack>/<ontology file> \
        --core athena-sim/packs/<pack>/core_rules.json --out-dir pool/
    python3 athena-corpus/curation/tools/select_tasks.py --pack <pack> --pool pool/<pack>_pool.tsv --out-dir selection/
    python3 athena-corpus/curation/tools/export_tasks.py   (arguments: see the docstring of the script)

Python 3.12 or later is needed: under 3.10 five Odoo files are not parsed.
