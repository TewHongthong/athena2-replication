"""Stdlib-only reader for an Athena ontology (node-link JSON, see ontology_schema.md).

Equivalent to graph_loader.get_applicable_rules() + graph_rag.rank_rules() of the project's
pipeline, but without the networkx dependency so it runs on any plain Python 3.9+.

Precedence (ontology_schema.md, "Retrieval query shape"): among the rules that apply to a (language, kind),
a rule that is the target of an OVERRIDES edge whose source is also among them is dropped, and the surviving
pairs joined by CONFLICTS_WITH are reported.  See Ontology.resolve_rules().
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

SEVERITY_RANK = {"MUST": 3, "SHOULD": 2, "MAY": 1}
# same specificity fields as graph_rag.py, plus requiredLabels (used by the custom GSCS pack)
SPECIFICITY_FIELDS = ["prefix", "suffix", "minLength", "maxLength", "forbiddenPatterns",
                      "requiredElements", "requiredLabels"]


def specificity(rule: dict) -> int:
    return sum(1 for f in SPECIFICITY_FIELDS if rule.get(f))


def rank_key(rule: dict):
    return (-SEVERITY_RANK.get(rule.get("severity"), 0), -specificity(rule), rule["id"])


def render_rule(rule: dict, examples: list | None = None) -> str:
    """One rule as prompt text.  Regexes are shown only when short and not flagged hidePatterns."""
    kind = rule.get("identifierKind", "")
    head = f"[{rule.get('severity', '?')}] {rule['id']}" + (f" ({kind})" if kind else "")
    lines = [f"{head}: {rule.get('description', '').strip()}"]
    checks = []
    if rule.get("casing"):
        checks.append(f"casing={rule['casing']}")
    if rule.get("prefix"):
        checks.append(f"prefix={rule['prefix']}")
    if rule.get("suffix"):
        checks.append(f"suffix={rule['suffix']}")
    if rule.get("allowedPrefixes"):
        checks.append("type prefixes: " + ", ".join(rule["allowedPrefixes"]))
    if rule.get("minLength"):
        checks.append(f"min length={rule['minLength']}")
    if rule.get("maxLength"):
        checks.append(f"max length={rule['maxLength']}")
    if rule.get("forbiddenPatterns") and not rule.get("hidePatterns"):
        checks.append("forbidden: " + ", ".join(f"/{p}/" for p in rule["forbiddenPatterns"]))
    if rule.get("requiredLabels"):
        checks.append("must contain: " + "; ".join(rule["requiredLabels"]))
    elif rule.get("requiredElements"):
        checks.append("must contain: " + "; ".join(rule["requiredElements"]))
    if checks:
        lines.append("  checks: " + " | ".join(checks))
    for ex in examples or []:
        tag = "OK " if ex.get("isCompliant") else "BAD"
        note = f" -- {ex['explanation']}" if ex.get("explanation") else ""
        code = str(ex.get("code", "")).replace("\n", " ⏎ ")
        lines.append(f"  {tag}: `{code}`{note}")
    return "\n".join(lines)


class OverrideCycleError(ValueError):
    """The OVERRIDES edges among the rules applicable to one (language, kind) form a cycle."""


@dataclass
class Resolution:
    """Outcome of precedence resolution for one (language, kind).

    rules       the surviving rules, ranked (same order as rules_for)
    overridden  [(overridden rule id, id of a rule that overrides it)], sorted
    conflicts   [(id, id)] pairs of surviving rules joined by CONFLICTS_WITH, each pair sorted, list sorted
    """
    rules: list = field(default_factory=list)
    overridden: list = field(default_factory=list)
    conflicts: list = field(default_factory=list)


class Ontology:
    def __init__(self, path: str):
        with open(path, "rb") as f:
            raw = f.read()
        self.path = path
        self.sha256 = hashlib.sha256(raw).hexdigest()
        d = json.loads(raw.decode("utf-8"))
        self.name = d.get("graph", {}).get("name", "ontology")
        self.nodes = {n["id"]: n for n in d["nodes"]}
        self.languages = [n["id"] for n in d["nodes"] if n["type"] == "Language"]
        self.kinds = [n["id"] for n in d["nodes"] if n["type"] == "IdentifierKind"]
        self._applies: dict[str, dict[str, set]] = {}
        self._examples: dict[str, list[dict]] = {}
        self._defined_in: dict[str, str] = {}
        self._overrides: dict[str, set] = {}      # rule id -> ids of the rules it supersedes
        self._conflicts: set = set()              # frozenset({a, b}) per CONFLICTS_WITH edge
        for e in d["links"]:
            rel, s, t = e["relation"], e["source"], e["target"]
            if rel == "APPLIES_TO":
                a = self._applies.setdefault(s, {"lang": set(), "kind": set()})
                if t in self.languages:
                    a["lang"].add(t)
                else:
                    a["kind"].add(t)
            elif rel == "HAS_EXAMPLE":
                self._examples.setdefault(s, []).append(self.nodes[t])
            elif rel == "DEFINED_IN":
                self._defined_in[s] = t
            elif rel in ("OVERRIDES", "CONFLICTS_WITH"):
                for end in (s, t):
                    if end not in self.nodes:
                        raise ValueError(f"{rel} edge {s!r} -> {t!r} names an unknown node {end!r}")
                if s == t:
                    raise ValueError(f"{rel} edge from {s!r} to itself")
                if rel == "OVERRIDES":
                    self._overrides.setdefault(s, set()).add(t)
                else:
                    self._conflicts.add(frozenset((s, t)))

    # ---- lookups -------------------------------------------------------------
    def rule(self, rid: str) -> dict:
        return {"id": rid, **self.nodes[rid]}

    def standards_for_language(self, lang: str) -> list:
        """Ids of the standards that define at least one rule applying to `lang`."""
        sids = {self._defined_in[rid] for rid, a in self._applies.items() if lang in a["lang"] and rid in self._defined_in}
        return sorted(s for s in sids if self.nodes.get(s, {}).get("type") == "Standard")

    def standard_name(self, sid: str) -> str:
        return self.nodes.get(sid, {}).get("name", sid)

    def rules_for(self, lang: str, kind: str, types=("NamingRule",), standard_id: str | None = None,
                  active_standards=None) -> list[dict]:
        """Ranked rules that APPLIES_TO both `lang` and `kind`, after precedence (see resolve_rules)."""
        return self.resolve_rules(lang, kind, types, standard_id, active_standards).rules

    def resolve_rules(self, lang: str, kind: str, types=("NamingRule",), standard_id: str | None = None,
                      active_standards=None) -> Resolution:
        """Graph-RAG steps 1-3: applicable rules, OVERRIDES suppression, CONFLICTS_WITH report.

        standard_id        keep only rules defined in this standard (or in none), as before
        active_standards   keep only rules defined in one of these standards (or in none); lets a project
                           standard be combined with a built-in one so that its OVERRIDES edges take effect;
                           ignored when standard_id is given

        A rule is dropped when some other applicable rule has an OVERRIDES edge to it; this holds even if the
        overriding rule is itself overridden, so a chain A -> B -> C leaves only A.  A cycle among the
        applicable rules raises OverrideCycleError.  Rules without any such edge are untouched, so an ontology
        with no OVERRIDES / CONFLICTS_WITH edges gives exactly the ranked list of the earlier implementation.
        """
        allowed = None
        if active_standards is not None and not standard_id:
            allowed = set(active_standards)
        cand = {}
        for rid, a in self._applies.items():
            n = self.nodes.get(rid)
            if n is None or n["type"] not in types:
                continue
            if lang in a["lang"] and kind in a["kind"]:
                if standard_id and self._defined_in.get(rid) not in (None, standard_id):
                    continue
                if allowed is not None and self._defined_in.get(rid) not in (None, *allowed):
                    continue
                cand[rid] = {"id": rid, **n}
        overridden = {}
        for src in sorted(cand):
            for tgt in sorted(self._overrides.get(src, ())):
                if tgt in cand:
                    overridden.setdefault(tgt, src)
        if overridden:
            self._check_acyclic(cand)
        survivors = [r for rid, r in cand.items() if rid not in overridden]
        conflicts = sorted(tuple(sorted(p)) for p in self._conflicts if all(x in cand and x not in overridden for x in p))
        return Resolution(rules=sorted(survivors, key=rank_key), overridden=sorted(overridden.items()),
                          conflicts=conflicts)

    def _check_acyclic(self, cand: dict) -> None:
        state: dict[str, int] = {}

        def visit(rid, path):
            state[rid] = 1
            for tgt in sorted(self._overrides.get(rid, ())):
                if tgt not in cand:
                    continue
                if state.get(tgt) == 1:
                    raise OverrideCycleError("OVERRIDES cycle: " + " -> ".join(path + [rid, tgt]))
                if tgt not in state:
                    visit(tgt, path + [rid])
            state[rid] = 2

        for rid in sorted(cand):
            if rid not in state:
                visit(rid, [])

    def conflicts_among(self, rule_ids) -> list:
        """CONFLICTS_WITH pairs (each sorted, list sorted) whose two ends are both in `rule_ids`."""
        ids = set(rule_ids)
        return sorted(tuple(sorted(p)) for p in self._conflicts if p <= ids)

    def rules_of_standard(self, standard_id: str, types=("NamingRule", "CommentRule", "StructureRule")) -> list[dict]:
        out = [{"id": rid, **self.nodes[rid]} for rid, sid in self._defined_in.items()
               if sid == standard_id and self.nodes[rid]["type"] in types]
        return sorted(out, key=lambda r: r["id"])

    def examples(self, rid: str, max_n: int | None = 2) -> list[dict]:
        """Keep a compliant + a non-compliant example first (as graph_rag.py does)."""
        ex = self._examples.get(rid, [])
        good = [e for e in ex if e.get("isCompliant")]
        bad = [e for e in ex if not e.get("isCompliant")]
        mixed = []
        for i in range(max(len(good), len(bad))):
            if i < len(good):
                mixed.append(good[i])
            if i < len(bad):
                mixed.append(bad[i])
        return mixed if max_n is None else mixed[:max_n]
