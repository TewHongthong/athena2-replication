#!/usr/bin/env python3
"""
Task C — violation injector.

Turns a standard-compliant identifier + the ontology rule(s) that apply to
it into a controlled non-compliant variant, for the Similarity Index setup
described in Athena Journal Outline.md § 4:

    "Create code that does not follow the standard with a script that injects
     violations (swap casing, abbreviate the name, single-character name), feed
     it into Athena, and measure the difference from the standard-compliant code"
    (translated from the Thai original)

Design principle: every injected violation is *self-verifying*. Instead of
hand-crafting "this should violate rule X" and hoping it's true, each
candidate is run through output_validator.check_naming_compliance() — the
exact same mechanical checker that will later grade Athena's fix — and only
kept if that checker actually flags it. This closes the loop between the
ground-truth generator and the grading metric, so a violation file can never
silently fail to be a real violation of the rule it claims.

Three injection strategies, chosen by which attributes the target rule has:
  - casing swap       — reformat the name into any casing OTHER than the
                         rule's required one
  - abbreviation       — shorten to something that fails minLength /
                         forbiddenPatterns (the classic "l", "tmp", "x1")
  - prefix/suffix strip — remove a required prefix/suffix (e.g. turn
                         IsConnected into Connected, dropping the Is-prefix
                         DOTNET-BOOLEAN-AFFIRMATIVE-PREFIX requires)

A rule with none of these attributes set (rare — most either have casing or
are pure forbiddenPatterns) simply yields no injection; the caller should
try a different rule for that identifier.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from output_validator import check_naming_compliance  # noqa: E402

# --- word splitting / casing reformatting ------------------------------------

_CAMEL_BOUNDARY = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])|[0-9]+")


def split_into_words(name: str) -> list[str]:
    """Best-effort split of any casing style into lowercase word tokens."""
    if "_" in name:
        return [w for w in name.split("_") if w]
    if "-" in name:
        return [w for w in name.split("-") if w]
    words = _CAMEL_BOUNDARY.findall(name)
    return [w for w in words if w] or [name]


def casing_variants(name: str) -> dict[str, str]:
    words = [w.lower() for w in split_into_words(name)]
    if not words:
        words = [name.lower()]
    return {
        "snake_case": "_".join(words),
        "UPPER_SNAKE_CASE": "_".join(w.upper() for w in words),
        "PascalCase": "".join(w.capitalize() for w in words),
        "camelCase": words[0] + "".join(w.capitalize() for w in words[1:]),
        "kebab-case": "-".join(words),
        "lowercase": "".join(words),
    }


# --- abbreviation / forbidden-pattern candidates -----------------------------

_GENERIC_BAD_NAMES = ["l", "I", "O", "x", "x1", "tmp", "temp", "val", "v", "d", "n", "o0", "obj"]


def abbreviation_candidates(name: str) -> list[str]:
    words = split_into_words(name)
    out = []
    if words:
        out.append("".join(w[0] for w in words).lower())  # initials, e.g. total_price -> tp
        out.append(words[0][:2].lower())  # truncate first word
    out += _GENERIC_BAD_NAMES
    # de-dup, keep order, drop anything identical to the original name
    seen, result = set(), []
    for c in out:
        if c and c != name and c not in seen:
            seen.add(c)
            result.append(c)
    return result


def _alternation_prefix_candidates(pattern: str, base_name: str) -> list[str]:
    """Patterns like '^(not|cant|isnt|dont)[A-Z]' name a forbidden PREFIX as
    an alternation. Extract the alternatives and splice each onto the base
    name so e.g. IsConnected -> notConnected/notIsConnected — best-effort,
    filtered by the self-verification step in inject_violation() either way."""
    m = re.match(r"^\^?\(([^)]+)\)", pattern)
    if not m:
        return []
    alts = [a for a in m.group(1).split("|") if a.isalpha()]
    if not base_name:
        return []
    rest_cap = base_name[0].upper() + base_name[1:]
    candidates = []
    for alt in alts:
        candidates.append(alt + rest_cap)
        candidates.append(alt.capitalize() + rest_cap)
    return candidates


def forbidden_pattern_candidates(patterns: list[str], base_name: str) -> list[str]:
    """Best-effort: try a literal reading of simple exact-match patterns
    (e.g. '^l$' -> 'l'), an alternation-prefix reading (e.g.
    '^(not|...)​[A-Z]' -> 'notConnected'), then fall back to the generic
    abbreviation pool — and keep whatever actually matches one of the
    patterns."""
    literal_candidates = []
    alternation_candidates = []
    for p in patterns:
        m = re.fullmatch(r"\^([A-Za-z0-9_]+)\$", p)
        if m:
            literal_candidates.append(m.group(1))
        alternation_candidates.extend(_alternation_prefix_candidates(p, base_name))
    pool = literal_candidates + alternation_candidates + abbreviation_candidates(base_name)
    matches = []
    for cand in pool:
        for p in patterns:
            try:
                if re.search(p, cand):
                    matches.append(cand)
                    break
            except re.error:
                continue
    # de-dup preserving order
    seen, result = set(), []
    for c in matches:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


# --- main injector ------------------------------------------------------------

@dataclass
class InjectionResult:
    original_name: str
    injected_name: str
    identifier_kind: str
    violated_rule_id: str
    injection_method: str
    expected_violation_reasons: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def inject_violation(standard_name: str, identifier_kind: str, rule: dict) -> Optional[InjectionResult]:
    """Try to produce a name that check_naming_compliance() flags as
    non-compliant against `rule`. Returns None if no strategy applicable to
    this rule's attributes succeeds (caller should try another rule)."""

    candidates: list[tuple[str, str]] = []  # (method, candidate_name)

    if rule.get("casing"):
        for casing_name, candidate in casing_variants(standard_name).items():
            if casing_name != rule["casing"]:
                candidates.append(("casing_swap", candidate))

    if rule.get("forbiddenPatterns"):
        for cand in forbidden_pattern_candidates(rule["forbiddenPatterns"], standard_name):
            candidates.append(("forbidden_pattern", cand))

    if rule.get("minLength"):
        for cand in abbreviation_candidates(standard_name):
            candidates.append(("abbreviate", cand))

    prefix = rule.get("prefix")
    if prefix and "/" not in prefix and standard_name.lower().startswith(prefix.lower()):
        stripped = standard_name[len(prefix):] or "value"
        candidates.append(("prefix_strip", stripped))

    suffix = rule.get("suffix")
    if suffix and standard_name.lower().endswith(suffix.lower()):
        stripped = standard_name[: -len(suffix)] or "value"
        candidates.append(("suffix_strip", stripped))

    for method, candidate in candidates:
        if candidate == standard_name:
            continue
        ok, reasons = check_naming_compliance(candidate, rule)
        if not ok:
            return InjectionResult(
                original_name=standard_name,
                injected_name=candidate,
                identifier_kind=identifier_kind,
                violated_rule_id=rule["id"],
                injection_method=method,
                expected_violation_reasons=reasons,
            )
    return None


def inject_for_identifier(graph, language: str, identifier: dict, active_standard_id: Optional[str] = None) -> list[InjectionResult]:
    """Given a snippet's identifier entry ({"name", "kind", ...}) and the
    ontology graph, retrieve its applicable NamingRules and try to inject a
    violation against each one. Returns one InjectionResult per rule that a
    strategy successfully violated (an identifier can violate several rules
    at once in principle, but each injection file targets one rule so the
    ground truth stays unambiguous)."""
    from graph_loader import get_applicable_rules

    raw = get_applicable_rules(graph, language, identifier["kind"], active_standard_id=active_standard_id)
    results = []
    for item in raw:
        rule = item["rule"]
        if rule.get("type") != "NamingRule":
            continue
        res = inject_violation(identifier["name"], identifier["kind"], rule)
        if res is not None:
            results.append(res)
    return results


if __name__ == "__main__":
    import json

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from graph_loader import load_graph, ONTOLOGY_PATH

    g = load_graph(ONTOLOGY_PATH)
    demo_identifiers = [
        ("python", {"name": "total_price", "kind": "variable"}),
        ("csharp", {"name": "IsConnected", "kind": "boolean_variable"}),
        ("javascript", {"name": "userAccountBalance", "kind": "variable"}),
    ]
    for lang, ident in demo_identifiers:
        print(f"\n=== {lang} / {ident['name']} ({ident['kind']}) ===")
        results = inject_for_identifier(g, lang, ident)
        if not results:
            print("  (no injection candidate found for any applicable rule)")
        for r in results:
            print(f"  [{r.violated_rule_id}] {r.injection_method}: {r.original_name!r} -> {r.injected_name!r}")
            print(f"    reasons: {r.expected_violation_reasons}")
