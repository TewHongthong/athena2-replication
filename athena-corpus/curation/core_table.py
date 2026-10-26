#!/usr/bin/env python3
"""Per-pack CORE rule table (Vol. 2).

The ontology has no field that marks a naming rule as conditional ("only exception classes", "only test
methods"), so the rules that every identifier of a kind must satisfy cannot be read off the ontology alone.
A pack therefore carries a side file, `core_rules.json`, next to the ontology:

    {
      "schema": 1,
      "core":     {"<language>": {"<kind>": ["RULE-ID", ...], ...}},
      "excluded": {"RULE-ID": "reason the rule is not a core rule", ...}
    }

`core`      rules checked at the gate and used as injection targets for that (language, kind).
`excluded`  rules that apply to some (language, kind) of the ontology but are not core, each with a reason.

validate() cross-checks the file against the ontology and fails when a naming rule that applies to a listed
language is neither core nor excluded, so a rule added to the ontology cannot be silently ignored.

Usage:  python core_table.py --ontology <athena_ontology.json> --core <core_rules.json>
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "pipeline"))
from output_validator import _CASING_PATTERNS  # noqa: E402
import rules as R  # noqa: E402

SCHEMA = 1


def load(path: str) -> dict:
    with open(path, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


def to_table(d: dict) -> dict:
    """{(language, kind): [rule ids]} from the JSON structure (no validation)."""
    return {(lang, kind): list(ids) for lang, kinds in d.get("core", {}).items() for kind, ids in kinds.items()}


def mechanically_checkable(rule: dict) -> bool:
    prefix = rule.get("prefix")
    return bool(rule.get("casing") in _CASING_PATTERNS
                or (prefix and "/" not in prefix)
                or rule.get("suffix") or rule.get("minLength") or rule.get("maxLength")
                or rule.get("forbiddenPatterns"))


def validate(d: dict, onto: "R.Ontology") -> list:
    """Problems found in the table `d` against `onto` (empty list = consistent)."""
    problems = []
    if d.get("schema") != SCHEMA:
        problems.append(f"schema must be {SCHEMA}, got {d.get('schema')!r}")
    core, excluded = d.get("core"), d.get("excluded", {})
    if not isinstance(core, dict) or not core:
        return problems + ["'core' must be a non-empty object {language: {kind: [rule ids]}}"]
    if not isinstance(excluded, dict):
        return problems + ["'excluded' must be an object {rule id: reason}"]
    classified = set()
    for lang, kinds in core.items():
        if lang not in onto.languages:
            problems.append(f"language {lang!r} is not in the ontology")
        if not isinstance(kinds, dict) or not kinds:
            problems.append(f"core[{lang!r}] must be a non-empty object {{kind: [rule ids]}}")
            continue
        for kind, ids in kinds.items():
            if kind not in onto.kinds:
                problems.append(f"({lang}, {kind}): kind {kind!r} is not in the ontology")
            if not isinstance(ids, list) or not ids or len(set(ids)) != len(ids):
                problems.append(f"({lang}, {kind}): needs a non-empty list of distinct rule ids")
                continue
            app = set(onto.applicable(lang, kind))
            for rid in ids:
                classified.add(rid)
                node = onto.nodes.get(rid)
                if node is None or node.get("type") != "NamingRule":
                    problems.append(f"({lang}, {kind}): {rid} is not a NamingRule of the ontology")
                    continue
                if rid not in app:
                    problems.append(f"({lang}, {kind}): {rid} does not apply to this language and kind")
                if not mechanically_checkable(node):
                    problems.append(f"({lang}, {kind}): {rid} has no mechanically checkable attribute")
    for rid, why in excluded.items():
        node = onto.nodes.get(rid)
        if node is None or node.get("type") != "NamingRule":
            problems.append(f"excluded: {rid} is not a NamingRule of the ontology")
        if not isinstance(why, str) or not why.strip():
            problems.append(f"excluded: {rid} needs a reason")
        if rid in classified:
            problems.append(f"{rid} is both core and excluded")
    # coverage: every naming rule that applies to a listed language is classified
    for lang in core:
        if lang not in onto.languages:
            continue
        for kind in onto.kinds:
            for rid in onto.applicable(lang, kind):
                if rid not in classified and rid not in excluded:
                    problems.append(f"({lang}, {kind}): {rid} is neither core nor excluded")
    return problems


def apply(path: str, onto: "R.Ontology") -> list:
    """Load `path`, validate it, and (only when it is consistent) install it with rules.set_core().
    Returns the problems; nothing is installed when there are any."""
    d = load(path)
    problems = validate(d, onto)
    if not problems:
        R.set_core(to_table(d), d.get("excluded", {}))
        problems = onto.validate_core()
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ontology", default=R.DEFAULT_ONTOLOGY)
    ap.add_argument("--core", required=True)
    a = ap.parse_args()
    onto = R.Ontology(a.ontology)
    problems = apply(a.core, onto)
    if problems:
        print(f"{len(problems)} problems")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    n_rules = sum(len(v) for v in R.CORE.values())
    print(f"core table OK: {len(R.CORE)} (language, kind) pairs, {n_rules} core rule slots, {len(R.EXCLUDED)} excluded rules")


if __name__ == "__main__":
    main()
