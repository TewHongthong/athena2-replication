"""Parsing and scoring of one trial.

Rename task  -> exact match with the original name, mechanical rule compliance (same checker the benchmark was
                built with), collision with existing names, and a Similarity Index between the repaired code and
                the original compliant code (RQ1).  If the answer cannot be parsed or is not a valid identifier,
                the code is left unchanged (that is what the editor would do).
Comment task -> structural compliance only (required labels / delimiters); comment *quality* needs the rubric
                judge (RQ2) and is not scored here.
"""
from __future__ import annotations

import difflib
import functools
import json
import os
import re
import sys

_VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)
from output_validator import (ParsedOutput, check_comment_compliance, check_naming_compliance,  # noqa: E402
                              parse_llm_output)

TASK_KEY = {"rename": "identifier_renaming", "comment": "comment_generation"}
_IDENT = re.compile(r"^[^\W\d][\w$]*$")


def parse_completion(task: str, text: str) -> ParsedOutput:
    """vendor parser + two leniencies: drop <think> blocks, accept raw newlines inside JSON strings."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    p = parse_llm_output(TASK_KEY[task], text)
    if not p.ok and p.errors and p.errors[0].startswith("invalid JSON"):
        tail = text.split("FINAL ANSWER:", 1)[-1]
        m = re.search(r"\{.*\}", tail, re.S)
        if m:
            try:
                data = json.loads(m.group(0), strict=False)
                missing = {"rename": {"original_name", "suggested_name", "rule_ids_applied", "reasoning"},
                           "comment": {"comment", "format", "rule_ids_applied", "reasoning"}}[task] - set(data)
                if not missing:
                    return ParsedOutput(ok=True, data=data, raw=text)
            except json.JSONDecodeError:
                pass
    return p


# ----------------------------------------------------------------------------- similarity
# The "before" similarity of a unit is identical for every condition / repeat, so the results are memoised
# (difflib is the slowest part of a mock run).
@functools.lru_cache(maxsize=16384)
def sim_char(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


@functools.lru_cache(maxsize=16384)
def sim_token(a: str, b: str) -> float:
    tok = lambda s: re.findall(r"\w+|[^\w\s]", s)  # noqa: E731
    return difflib.SequenceMatcher(None, tok(a), tok(b), autojunk=False).ratio()


# ----------------------------------------------------------------------------- rename
def _word_re(name: str):
    return re.compile(r"(?<![\w$])" + re.escape(name) + r"(?![\w$])")


def apply_rename(code: str, old: str, new: str):
    """Rename every whole-word occurrence (what a rename provider would do inside this excerpt)."""
    return _word_re(old).subn(lambda m: new, code)


def name_for_check(lang: str, name: str) -> str:
    """Same normalisation as the benchmark's gate: PEP 8 non-public marker is not part of the casing check."""
    if lang == "python" and name.startswith("_") and not (name.startswith("__") and name.endswith("__")):
        return name.lstrip("_")
    return name


def _prefix_match(unit, rule, suggested):
    """Stricter than the rule check: did the answer keep the ORIGINAL type prefix (i_, f_, bln_ ...)?  Only defined
    for rules that list allowed prefixes (the GSCS type-prefix rules); None elsewhere."""
    allowed = rule.get("allowedPrefixes")
    if not allowed or "_" not in unit.original:
        return None
    want = unit.original.split("_")[0]
    if want not in allowed:
        return None
    return bool(suggested) and suggested.split("_")[0] == want


def grade_rename(unit, parsed: ParsedOutput, pack) -> dict:
    suggested = None
    if parsed.ok and isinstance(parsed.data.get("suggested_name"), str):
        suggested = parsed.data["suggested_name"].strip().strip("`")
    valid = bool(suggested) and bool(_IDENT.match(suggested))
    m = {"parse_ok": bool(parsed.ok), "suggested": suggested, "valid_identifier": valid}
    sim_before_c = sim_char(unit.code_violation, unit.code_original)
    sim_before_t = sim_token(unit.code_violation, unit.code_original)
    if valid:
        code_after, n = apply_rename(unit.code_violation, unit.injected, suggested)
        chk = name_for_check(unit.language, suggested)
        rule = pack.ontology.rule(unit.rule_id)
        v_ok, v_reasons = check_naming_compliance(chk, rule)
        core = [pack.ontology.rule(r) for r in pack.core_rules(unit.language, unit.kind)]
        failed = [r["id"] for r in core if not check_naming_compliance(chk, r)[0]]
        m.update(changed=suggested != unit.injected, exact_match=suggested == unit.original,
                 violated_rule_ok=v_ok, violated_rule_reasons=v_reasons,
                 core_ok=(not failed) if core else None, core_failed=failed,
                 collision=(suggested not in (unit.injected, unit.original)
                            and bool(_word_re(suggested).search(unit.code_violation))),
                 occurrences_renamed=n, name_sim=sim_char(suggested, unit.original),
                 prefix_match=_prefix_match(unit, rule, suggested))
    else:
        code_after = unit.code_violation
        m.update(changed=False, exact_match=False, violated_rule_ok=False, violated_rule_reasons=[],
                 core_ok=False, core_failed=[], collision=False, occurrences_renamed=0, name_sim=0.0,
                 prefix_match=_prefix_match(unit, pack.ontology.rule(unit.rule_id), None))
    m.update(sim_char_before=sim_before_c, sim_char_after=sim_char(code_after, unit.code_original),
             sim_token_before=sim_before_t, sim_token_after=sim_token(code_after, unit.code_original))
    return m


# ----------------------------------------------------------------------------- comment
_COMMENT_START = ("/*", "//", "#", '"""', "'''", "<!--", "///")

# Mirror output_validator.check_comment_compliance()'s internal tables (not exported by that
# module) so n_checks can count exactly the mechanical checks that function can fail.
_MARKER_CHECKS = {"javadoc": ("/**", "*/"), "jsdoc": ("/**", "*/"), "xmldoc": ("///", None),
                 "docstring-google": ('"""', '"""')}
_ELEMENT_TAG_HINTS = {"params": ["@param", "<param"], "returns": ["@return", "<returns"],
                     "throws": ["@throws", "<exception"], "exception": ["@throws", "<exception"],
                     "value": ["<value"], "typeparam": ["<typeparam"], "summary": []}


def _filter_required_elements(rule: dict, expected_elements) -> dict:
    """A rule's requiredElements are checked only if they are in the unit's expected_elements
    (a void method is not required to have @return); expected_elements=None (e.g. gscs units,
    which carry no signature metadata) leaves the rule unchanged."""
    if expected_elements is None or not rule.get("requiredElements"):
        return rule
    kept = [el for el in rule["requiredElements"] if el in expected_elements]
    return {**rule, "requiredElements": kept} if kept != rule["requiredElements"] else rule


def n_checks_for(must_rules: list, expected_elements) -> int:
    """Number of concrete mechanical checks (delimiter + recognizable requiredElements tags) that
    could fail for this unit; a rule whose format/requiredElements have no mechanical counterpart
    in check_comment_compliance (e.g. Python's plain-line-comment, most Airbnb JS comment rules)
    contributes 0, which is exactly the "vacuous check" case report.py surfaces."""
    n = 0
    for r in must_rules:
        if r.get("format") in _MARKER_CHECKS:
            n += 1
        r = _filter_required_elements(r, expected_elements)
        for el in r.get("requiredElements") or []:
            if _ELEMENT_TAG_HINTS.get(el):
                n += 1
    return n


def grade_comment(unit, parsed: ParsedOutput, pack) -> dict:
    comment = None
    if parsed.ok and isinstance(parsed.data.get("comment"), str):
        comment = parsed.data["comment"]
    m = {"parse_ok": bool(parsed.ok), "comment": comment}
    rules = pack.ontology.rules_for(unit.language, unit.kind, types=("CommentRule",))
    must = [r for r in rules if r.get("severity") == "MUST"]
    expected_elements = getattr(unit, "expected_elements", None)
    n_checks = n_checks_for(must, expected_elements)
    if comment is None:
        m.update(comment_ok=False, labels_present=0, labels_total=0, labels_filled=0, labels_fill_total=0, delimiter_ok=False,
                 failed_rules=[r["id"] for r in must], sim_reference=0.0, n_checks=n_checks)
        return m
    low = comment.lower()
    failed, present, total, filled, fill_total = [], 0, 0, 0, 0
    for r in must:
        r = _filter_required_elements(r, expected_elements)
        ok, _ = check_comment_compliance(comment, r)
        found = []
        for lb in r.get("requiredLabels") or []:
            total += 1
            idx = low.find(lb.lower())
            if idx >= 0:
                present += 1
                found.append((idx, lb))
            else:
                ok = False
        found.sort()
        blank_ok = {x.lower() for x in r.get("optionalFilledLabels") or []}   # e.g. "Revised By" on a new function
        fill_total += sum(1 for _, lb in found if lb.lower() not in blank_ok)
        for i, (idx, lb) in enumerate(found):          # a label counts as filled if text follows it
            if lb.lower() in blank_ok:
                continue
            end = found[i + 1][0] if i + 1 < len(found) else len(comment)
            seg = comment[idx + len(lb):end].replace("*/", "").replace('"""', "")
            if re.search(r"[A-Za-z0-9]", seg):
                filled += 1
        if not ok:
            failed.append(r["id"])
    m.update(comment_ok=(not failed) if must else None, labels_present=present, labels_total=total,
             labels_filled=filled, labels_fill_total=fill_total, delimiter_ok=comment.lstrip().startswith(_COMMENT_START),
             failed_rules=failed, n_checks=n_checks,
             sim_reference=sim_char(" ".join(comment.split()), " ".join(unit.reference_comment.split())))
    return m
