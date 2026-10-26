# Third-party notices

The code of this package (harness, scripts, tests) is released under the MIT license (LICENSE).
The material below comes from other projects and keeps its own license.

## Code excerpts

The trial records (athena-sim/runs/*/trials.jsonl) and the benchmark files (benchmark/) contain excerpts of 6 to 40
lines of source code from three repositories, at the commits pinned in athena-corpus/pins/corpus_pins.json.
The excerpts keep the license of their repository.

| Repository | Code license | Copyright holders |
|---|---|---|
| godotengine/godot | MIT | Juan Linietsky, Ariel Manzur and the Godot community |
| dotnet/runtime | MIT | .NET Foundation and Contributors |
| odoo/odoo | LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html) | Odoo S.A. |

The source files of the repositories are not part of this package. Odoo is distributed as commit, path, blob
identifier and the script that fetches it (athena-corpus/curation/tools/fetch_corpus_pins.py).

## Coding standards and the ontologies built from them

The documents are in standards/src/ with the license file of their repository. Each ontology under
athena-sim/packs/<standard>/ is an adaptation of its standard and carries the license of that document:

| Standard | Document | Document license | Attribution |
|---|---|---|---|
| Godot | godotengine/godot-contributing-docs, cpp_usage_guidelines.rst | CC BY 3.0 | Juan Linietsky, Ariel Manzur and the Godot community |
| .NET runtime | dotnet/runtime, docs/coding-guidelines/coding-style.md | MIT | .NET Foundation and Contributors |
| Odoo | odoo/documentation, coding_guidelines.rst | CC BY-SA 4.0 | Odoo S.A. |

The ontology of Odoo (athena-sim/packs/odoo/) is shared under CC BY-SA 4.0. The ontology of Godot
(athena-sim/packs/godot/) is shared under CC BY 3.0 with the attribution above. The ontology of the .NET runtime
(athena-sim/packs/dotnet-runtime/) is shared under the MIT license.

## Other components

tree-sitter and tree-sitter-cpp (MIT) are built into athena-corpus/curation/libtsall.so.
