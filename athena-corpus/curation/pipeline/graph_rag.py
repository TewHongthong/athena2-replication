#!/usr/bin/env python3
"""
Task B.3 — Graph RAG retriever (ranked) for the Athena coding-standard ontology.

Builds on graph_loader.get_applicable_rules (the unranked retrieval-query shape
from ontology_schema.md) and adds:
  - ranking (severity, then specificity, then rule id for stable order)
  - top_k truncation (token-budget control for the prompt builder)
  - max_examples_per_rule truncation
  - a convenience `retrieve_context()` that returns a single structured object
    ready to hand to prompt_builder.build_prompt()

No extension/UI target exists to wire this into right now (confirmed with the
user 2026-09-25 — the "Athena" VS Code extension was never actually built; the
zips/folders that were supposed to hold it contain only the old conference
LaTeX template). So this module is designed to be called directly — as a
library, from a CLI, or from the Task C benchmark harness — rather than wired
into an extension backend. See pipeline_demo.py for an end-to-end example.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graph_loader import load_graph, get_applicable_rules, ONTOLOGY_PATH  # noqa: E402

SEVERITY_RANK = {"MUST": 3, "SHOULD": 2, "MAY": 1}

# Attributes that make a NamingRule/CommentRule more *specific* than a bare
# casing rule — used as the secondary ranking key so the most constraining,
# most actionable rules surface first in the prompt (primacy matters for LLM
# attention, and a prompt has a finite few-shot budget).
SPECIFICITY_FIELDS = ["prefix", "suffix", "minLength", "maxLength", "forbiddenPatterns", "requiredElements"]


def _specificity(rule_attrs: dict) -> int:
    score = 0
    for field_name in SPECIFICITY_FIELDS:
        v = rule_attrs.get(field_name)
        if v:  # non-null, non-empty string/list
            score += 1
    return score


def rank_rules(retrieved: list[dict]) -> list[dict]:
    """Sort retrieve results (as returned by get_applicable_rules) by
    (severity desc, specificity desc, rule id asc) for deterministic,
    attention-friendly prompt ordering."""

    def key(item):
        rule = item["rule"]
        sev = SEVERITY_RANK.get(rule.get("severity"), 0)
        spec = _specificity(rule)
        return (-sev, -spec, rule["id"])

    return sorted(retrieved, key=key)


@dataclass
class RetrievedRule:
    rule: dict
    examples: list[dict]


@dataclass
class RetrievalContext:
    language: str
    identifier_kind: str
    rules: list[RetrievedRule] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.rules) == 0


def retrieve_context(
    graph,
    language: str,
    identifier_kind: str,
    top_k: Optional[int] = None,
    max_examples_per_rule: Optional[int] = 2,
    active_standard_id: Optional[str] = None,
    rule_types: Optional[set[str]] = None,
) -> RetrievalContext:
    """The retriever's single public entry point. Returns a RetrievalContext
    ranked and truncated, ready for prompt_builder.build_prompt().

    top_k=None means "no cap" (fine at this ontology's scale — usually 1-4
    rules per (language, identifierKind) pair); pass a number to bound the
    prompt's token budget when scaling to many more standards later.

    rule_types: restrict to {"NamingRule"} or {"CommentRule"} (or leave None
    for both). Task-aware retrieval matters here — an identifier-renaming
    prompt doesn't need inline-comment-style rules just because both rule
    types happen to be tagged with the same IdentifierKind; prompt_builder's
    two task types pass this through automatically via retrieve_for_task().
    """
    raw = get_applicable_rules(graph, language, identifier_kind, active_standard_id=active_standard_id)
    if rule_types is not None:
        raw = [item for item in raw if item["rule"]["type"] in rule_types]
    ranked = rank_rules(raw)
    if top_k is not None:
        ranked = ranked[:top_k]

    rules = []
    for item in ranked:
        examples = item["examples"]
        if max_examples_per_rule is not None:
            # Prefer keeping at least one compliant + one non-compliant example
            # when truncating, rather than the first N in arbitrary order.
            compliant = [e for e in examples if e.get("isCompliant")]
            noncompliant = [e for e in examples if not e.get("isCompliant")]
            kept = []
            for pair in zip(compliant, noncompliant):
                kept.extend(pair)
            kept += compliant[len(kept) // 2:] + noncompliant[len(kept) // 2:]
            examples = kept[:max_examples_per_rule] if kept else examples[:max_examples_per_rule]
        rules.append(RetrievedRule(rule=item["rule"], examples=examples))

    return RetrievalContext(language=language, identifier_kind=identifier_kind, rules=rules)


TASK_TO_RULE_TYPES = {
    "identifier_renaming": {"NamingRule"},
    "comment_generation": {"CommentRule"},
}


def retrieve_for_task(graph, task_type: str, language: str, identifier_kind: str, **kwargs) -> RetrievalContext:
    """Convenience wrapper: picks the right rule_types for the two Athena
    task types (see prompt_builder.TaskType) so callers don't have to know
    the NamingRule/CommentRule split themselves."""
    if task_type not in TASK_TO_RULE_TYPES:
        raise ValueError(f"Unknown task_type {task_type!r}, expected one of {list(TASK_TO_RULE_TYPES)}")
    return retrieve_context(graph, language, identifier_kind, rule_types=TASK_TO_RULE_TYPES[task_type], **kwargs)


if __name__ == "__main__":
    g = load_graph(ONTOLOGY_PATH)
    demo_cases = [("python", "variable"), ("javascript", "class"), ("csharp", "boolean_variable")]
    for lang, kind in demo_cases:
        ctx = retrieve_context(g, lang, kind, top_k=5, max_examples_per_rule=2)
        print(f"\n=== {lang} / {kind}: {len(ctx.rules)} ranked rule(s) ===")
        for rr in ctx.rules:
            r = rr.rule
            print(f"  [{r['severity']:>6}] {r['id']}  (specificity={_specificity(r)}, examples kept={len(rr.examples)})")
