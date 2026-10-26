#!/usr/bin/env python3
"""
Output validation for Athena's two tasks (per the outline's "things still
needed" list for Section 3: "Output validation (JSON schema + syntax check)").

Two layers:
  1. parse_llm_output() — pulls the "FINAL ANSWER:" JSON block out of a raw
     LLM completion (the chain-of-thought text before it is discarded here,
     but callers can keep the raw text for logging/debugging) and checks it
     has the required fields for the task type.
  2. check_naming_compliance() — a small, dependency-free rule checker that
     mechanically verifies a proposed identifier against a NamingRule's own
     casing/prefix/suffix/length/forbiddenPatterns attributes. This is not
     just an output-validation convenience: it is exactly the function the
     Task C benchmark harness needs for the automatic "compliance rate"
     metric behind RQ1, so a suggested name can be graded without a human
     in the loop.

check_comment_compliance() does the lighter-weight equivalent for comments:
it can only mechanically check the *shape* (does the comment start with
the right marker for the required format, does it contain @param-style tags
when requiredElements asks for them) — judging whether the comment content
is actually correct/clear is left to the rubric-based human/LLM-judge
evaluation described in the outline's Task C metrics, not this function.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

REQUIRED_FIELDS = {
    "identifier_renaming": {"original_name", "suggested_name", "rule_ids_applied", "reasoning"},
    "comment_generation": {"comment", "format", "rule_ids_applied", "reasoning"},
}

_FINAL_ANSWER_MARKER = "FINAL ANSWER:"


@dataclass
class ParsedOutput:
    ok: bool
    data: dict | None = None
    errors: list[str] = field(default_factory=list)
    raw: str = ""


def parse_llm_output(task_type: str, raw_completion: str) -> ParsedOutput:
    """Extract and validate the JSON block after 'FINAL ANSWER:'."""
    if task_type not in REQUIRED_FIELDS:
        return ParsedOutput(ok=False, errors=[f"unknown task_type {task_type!r}"], raw=raw_completion)

    if _FINAL_ANSWER_MARKER in raw_completion:
        tail = raw_completion.split(_FINAL_ANSWER_MARKER, 1)[1]
    else:
        tail = raw_completion  # be lenient: model may have skipped the marker

    # Pull the first {...} block (handles a ```json fenced block too).
    match = re.search(r"\{.*\}", tail, re.DOTALL)
    if not match:
        return ParsedOutput(ok=False, errors=["no JSON object found after FINAL ANSWER marker"], raw=raw_completion)

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        return ParsedOutput(ok=False, errors=[f"invalid JSON: {e}"], raw=raw_completion)

    missing = REQUIRED_FIELDS[task_type] - set(data.keys())
    if missing:
        return ParsedOutput(ok=False, data=data, errors=[f"missing required field(s): {sorted(missing)}"], raw=raw_completion)

    return ParsedOutput(ok=True, data=data, raw=raw_completion)


# --- Casing checkers --------------------------------------------------------

_CASING_PATTERNS = {
    "snake_case": r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$",
    "UPPER_SNAKE_CASE": r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$",
    "CONSTANT_CASE": r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$",
    "PascalCase": r"^[A-Z][a-zA-Z0-9]*$",
    "camelCase": r"^[a-z][a-zA-Z0-9]*$",
    "lowerCamelCase": r"^[a-z][a-zA-Z0-9]*$",
    "kebab-case": r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$",
    "lowercase": r"^[a-z][a-z0-9]*$",
}


def check_naming_compliance(name: str, rule: dict) -> tuple[bool, list[str]]:
    """Mechanically check `name` against one NamingRule's own attributes.
    Returns (is_compliant, reasons_for_any_failure). An attribute the rule
    leaves unset (None/empty) is simply not checked — e.g. a rule with no
    `casing` set (like PEP8-AVOID-CONFUSING-CHARS, which is pure
    forbiddenPatterns) only checks forbiddenPatterns.
    """
    reasons = []

    casing = rule.get("casing")
    if casing:
        pattern = _CASING_PATTERNS.get(casing)
        if pattern is None:
            reasons.append(f"unrecognized casing value {casing!r} in rule (cannot mechanically check)")
        elif not re.match(pattern, name):
            reasons.append(f"name {name!r} does not match {casing} pattern")

    prefix = rule.get("prefix")
    if prefix and "/" not in prefix and not name.startswith(prefix):
        # prefixes like "is/has" are disjunctive hints, not a literal string
        # to match — skip those (handled by the LLM's judgment / a human
        # rubric), only check single, literal prefixes mechanically.
        reasons.append(f"name {name!r} does not start with required prefix {prefix!r}")

    suffix = rule.get("suffix")
    if suffix and not name.endswith(suffix):
        reasons.append(f"name {name!r} does not end with required suffix {suffix!r}")

    min_len = rule.get("minLength")
    if min_len and len(name) < min_len:
        reasons.append(f"name {name!r} shorter than minLength={min_len}")

    max_len = rule.get("maxLength")
    if max_len and len(name) > max_len:
        reasons.append(f"name {name!r} longer than maxLength={max_len}")

    for pattern in rule.get("forbiddenPatterns") or []:
        try:
            if re.search(pattern, name):
                reasons.append(f"name {name!r} matches forbidden pattern {pattern!r}")
        except re.error:
            reasons.append(f"forbiddenPatterns entry {pattern!r} is not a valid regex (skipped)")

    return (len(reasons) == 0, reasons)


def check_comment_compliance(comment: str, rule: dict) -> tuple[bool, list[str]]:
    """Lightweight structural check for a CommentRule: format marker present,
    requiredElements show up as recognizable tags. Cannot judge whether the
    comment's *content* is accurate — that's the rubric/human-eval layer."""
    reasons = []
    fmt = rule.get("format")
    marker_checks = {
        "javadoc": ("/**", "*/"),
        "jsdoc": ("/**", "*/"),
        "xmldoc": ("///", None),
        "docstring-google": ('"""', '"""'),
    }
    if fmt in marker_checks:
        start, end = marker_checks[fmt]
        if start not in comment:
            reasons.append(f"expected a {fmt} comment to contain {start!r}")
        if end and end not in comment[len(start):]:
            reasons.append(f"expected a {fmt} comment to be closed with {end!r}")

    element_tag_hints = {
        "params": ["@param", "<param"],
        "returns": ["@return", "<returns"],
        "throws": ["@throws", "<exception"],
        "exception": ["@throws", "<exception"],
        "value": ["<value"],
        "typeparam": ["<typeparam"],
        "summary": [],  # summary is just the prose itself — nothing to grep for
    }
    for el in rule.get("requiredElements") or []:
        hints = element_tag_hints.get(el)
        if not hints:
            continue
        if not any(h in comment for h in hints):
            reasons.append(f"requiredElements includes {el!r} but no recognizable tag ({hints}) found in comment")

    return (len(reasons) == 0, reasons)


if __name__ == "__main__":
    # Small self-test against a couple of the ontology's own rules.
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from graph_loader import load_graph, ONTOLOGY_PATH

    g = load_graph(ONTOLOGY_PATH)
    var_snake_rule = {"id": "PEP8-VAR-SNAKE", **g.nodes["PEP8-VAR-SNAKE"]}
    for candidate in ["max_retries", "maxRetries", "MAXRETRIES"]:
        ok, reasons = check_naming_compliance(candidate, var_snake_rule)
        print(f"{candidate!r} vs PEP8-VAR-SNAKE -> compliant={ok} {reasons}")

    confusing_rule = {"id": "PEP8-AVOID-CONFUSING-CHARS", **g.nodes["PEP8-AVOID-CONFUSING-CHARS"]}
    for candidate in ["l", "count"]:
        ok, reasons = check_naming_compliance(candidate, confusing_rule)
        print(f"{candidate!r} vs PEP8-AVOID-CONFUSING-CHARS -> compliant={ok} {reasons}")

    sample_completion = (
        "Reasoning: the name 'l' is a bare 'l', which PEP8-AVOID-CONFUSING-CHARS forbids, "
        "and it should also be snake_case (already is, trivially).\n"
        "FINAL ANSWER:\n"
        '```json\n{"original_name": "l", "suggested_name": "total_price", '
        '"rule_ids_applied": ["PEP8-AVOID-CONFUSING-CHARS", "PEP8-VAR-SNAKE"], '
        '"reasoning": "l is a forbidden ambiguous name; total_price is descriptive and snake_case"}\n```'
    )
    parsed = parse_llm_output("identifier_renaming", sample_completion)
    print("\nparsed:", parsed.ok, parsed.data, parsed.errors)
