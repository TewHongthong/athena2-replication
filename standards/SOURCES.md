# Independent standards (WP1)

The primary data is in `standards.json` (the scripts read from that file); this file is a human-readable summary.
Every license field was read from the repository's own LICENSE file, not from a tag.

| id | language | pinned document (repo @ commit) | path | document license | code license |
|---|---|---|---|---|---|
| `godot` | C++ | godotengine/godot-contributing-docs @ `54e2d5c5eda4` | `development/engine/cpp_usage_guidelines.rst` (7,280 B) | CC BY 3.0 (attribution: "Juan Linietsky, Ariel Manzur and the Godot community") | MIT (godotengine/godot) |
| `dotnet-runtime` | C# | dotnet/runtime @ `0232cf718cdf` | `docs/coding-guidelines/coding-style.md` (8,103 B) | MIT | MIT |
| `odoo` | Python | odoo/documentation @ `a31e1d9cba35` | `content/contributing/development/coding_guidelines.rst` (48,100 B) | CC BY-SA 4.0 | LGPL-3.0 (odoo/odoo) |

## Differences from what was recorded in D3

1. **Godot — the document is not MIT.** MIT is the license of the code (`godotengine/godot`); the document is CC BY 3.0 and is no longer in `godot-docs` (there is no `contributing/` folder) but has moved to `godotengine/godot-contributing-docs`.
2. **Godot — the pinned C++ page is `cpp_usage_guidelines.rst` on `main`** (sections: Automated style checks, Disallowed features, Naming, Spacing, Header includes, Comments). The page `code_style.rst` (16,334 B; C++/Objective-C, Java, Python) exists only on the `language-styleguides` branch (commit `8a47080d13271a02a8962d089036e5a7635e464f`, Sep 2025) and is not on `main` — **it is not pinned** (decision: use only `cpp_usage_guidelines.rst` on `main`; the naming rules cited in the outline are in the Naming section of this page — checked: types/namespaces PascalCase, macros/constants UPPER_SNAKE_CASE, everything else snake_case, parameters `p_*` and `r_*`).
3. **Odoo — the document is CC BY-SA 4.0**; LGPL-3.0 is the license of the code (`odoo/odoo`).

## Consequences for distribution

- The documents themselves are not committed: the script downloads them into `standards/src/`, which is git-ignored.
- An ontology written as a paraphrase of a CC-licensed document may be an adaptation (CC BY 3.0 requires attribution; CC BY-SA 4.0 requires adaptations to be shared under BY-SA or a compatible license).
- **Decision:** distribute each standard's ontology together with the license of its source document — Godot = CC BY 3.0 (attribution "Juan Linietsky, Ariel Manzur and the Godot community"), Odoo = CC BY-SA 4.0, dotnet-runtime = MIT — kept separate from the artifact's MIT-licensed code (a separate license/NOTICE per standard).
- Still to do before submitting the artifact: confirm with the advisor / the university that this approach is acceptable (this is not legal advice).

## Code (for the WP2 corpus — not pinned yet)

| repo | HEAD at the time of pinning | license |
|---|---|---|
| godotengine/godot | `5ec712e220b7deac64d61dc9f968e72edb910039` | MIT |
| dotnet/runtime | `0232cf718cdfa6e99e42c3eff4c953004f5cf6c1` | MIT |
| odoo/odoo | `0599e811ab0dcbb3c3ca78b9bf86b288265c6cd1` | LGPL-3.0 |

The commits of the files actually used in the corpus must be pinned separately in WP2 (after the models' cutoff).

## Usage

```
python standards/fetch_standards.py            # download into standards/src/<id>/ and verify SHA-256
python standards/fetch_standards.py --only odoo
```

Only `git` and Python are required; exits with code 1 if a SHA-256 does not match.

## Agreement

The human-authored ontologies for these three standards are created by the author, with an assistant that only records the answers on a form, and before the LLM-drafted ontology is seen (HYPOTHESES_v2 §3.1).
