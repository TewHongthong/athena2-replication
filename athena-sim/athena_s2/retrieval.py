"""The conditions of Study 2: those of Study 1 (athena.retrieval, unchanged) and `naming`.

  naming   the passages of the pinned standard document whose heading path or own text matches the fixed
           expression of addendum A11 (NAMING_RE, the same pattern as analyse_a11.py), in document order. The
           passages are those of athena.passages, as for chunk, bm25 and dense.
"""
from __future__ import annotations

import re

from athena.retrieval import CONDITIONS as STUDY1_CONDITIONS
from athena.retrieval import Context, Retriever

CONDITIONS = ("none", "fulldoc", "naming") + tuple(c for c in STUDY1_CONDITIONS if c not in ("none", "fulldoc"))
# what a run uses when --conditions is not given (dense needs --embed-pin and is asked for by name, as in Study 1)
DEFAULT_CONDITIONS = tuple(c for c in CONDITIONS if c != "dense")

NAMING_RE = re.compile(r"\bnam(e|es|ing)\b|\bidentifier|\bcasing\b|camelcase|snake_case|pascalcase"
                       r"|\bprefix|\bsuffix|\babbreviat", re.I)


def naming_passages(chunks: list) -> list:
    """(passage id, text) of the passages whose heading path or own text concerns naming, in document order."""
    out = []
    for pid, body in chunks:
        head = body.split("\n\n", 1)[0] if "\n\n" in body else ""
        if (head and NAMING_RE.search(head)) or NAMING_RE.search(body):
            out.append((pid, body))
    return out


class RetrieverS2(Retriever):
    """athena.retrieval.Retriever with the naming condition; every other condition is the Study 1 code."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._naming: dict = {}

    def context(self, condition: str, *, task: str, standard_id: str, language: str, kind: str,
                name: str, code: str) -> Context:
        if condition != "naming":
            return super().context(condition, task=task, standard_id=standard_id, language=language, kind=kind,
                                   name=name, code=code)
        if standard_id not in self._naming:
            self._naming[standard_id] = naming_passages(self.pack.chunks(standard_id))
        hits = self._naming[standard_id]
        sname = self.pack.standard_name(standard_id)
        body = "\n\n".join(b for _, b in hits) or "(no matching passage found)"
        return Context(f"{sname} - the {len(hits)} passage(s) of the standard about naming:\n{body}",
                       {"n_items": len(hits), "retrieved_ids": [pid for pid, _ in hits]})
