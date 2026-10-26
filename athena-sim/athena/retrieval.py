"""The ways Athena Sim can give the LLM a coding standard (RQ3 conditions).

  none     the standard is only *named*; the LLM must rely on what it already knows
  fulldoc  the whole standard is pasted into the prompt (how Cursor/Copilot rule files are used)
  chunk    plain RAG, the design the original Athena pilot started from: the standard is cut into
           chunks and the top-k chunks most similar to the code are retrieved (lexical TF-IDF here,
           because the embedding model used in the pilot is unknown and no network is needed)
  bm25     the same chunks, the same query and the same top-k as `chunk`, ranked with Okapi BM25 instead of
           TF-IDF cosine; the scoring function is the only difference between the two lexical conditions
  graph    ontology-guided Graph RAG: only the rules that APPLIES_TO this language + identifier kind,
           ranked by severity/specificity, with few-shot examples (the journal paper's method); rules
           superseded through OVERRIDES edges are dropped and CONFLICTS_WITH pairs are flagged in the context
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

from .embed import DenseIndex, dense_query
from .ontology import render_rule

CONDITIONS = ("none", "fulldoc", "chunk", "bm25", "dense", "graph")
# what a run uses when --conditions is not given: `dense` needs an embedding model (--embed-pin), so it is asked for by name
DEFAULT_CONDITIONS = ("none", "fulldoc", "chunk", "bm25", "graph")

# Okapi BM25 parameters: the common Lucene defaults, fixed in code (so they are covered by the code hash of a
# freeze) and not exposed on the command line.
BM25_K1 = 1.2
BM25_B = 0.75

_STOP = set("""a an and are as at be by for from has have if in into is it its of on or that the this to
use used uses using with should shall must may can not no all any each when than then else also only
name names named code""".split())


def words(text: str) -> list:
    """Split identifiers (snake/camel) and prose into lower-case word tokens."""
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    toks = re.findall(r"[A-Za-z][A-Za-z0-9]+", text.replace("_", " "))
    return [t.lower() for t in toks if t.lower() not in _STOP and len(t) > 1]


class ChunkIndex:
    """Tiny TF-IDF cosine index over (chunk_id, text) pairs."""

    def __init__(self, chunks: list):
        self.chunks = chunks
        self.tf = [Counter(words(t)) for _, t in chunks]
        n = len(chunks)
        df = Counter()
        for c in self.tf:
            df.update(c.keys())
        self.idf = {w: math.log((n + 1) / (d + 1)) + 1.0 for w, d in df.items()}
        self.norm = [math.sqrt(sum((v * self.idf[w]) ** 2 for w, v in c.items())) or 1.0 for c in self.tf]

    def top(self, query_tokens: list, k: int) -> list:
        q = Counter(query_tokens)
        qn = math.sqrt(sum((v * self.idf.get(w, 1.0)) ** 2 for w, v in q.items())) or 1.0
        scored = []
        for i, c in enumerate(self.tf):
            dot = sum(v * self.idf.get(w, 1.0) * c[w] * self.idf.get(w, 1.0) for w, v in q.items() if w in c)
            scored.append((dot / (qn * self.norm[i]), i))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [i for s, i in scored[:k] if s > 0]


def retrieval_query(language: str, kind: str, name: str, code: str) -> list:
    """Query shared by the lexical conditions: language, kind (x3) and name (x2) for weight, plus the words of the code."""
    return words(f"{language} {kind} {kind} {kind} {name} {name}") + words(code)


class BM25Index:
    """Okapi BM25 index over (chunk_id, text) pairs; same interface as ChunkIndex.

    score(q, d) = sum over the query tokens t of  idf(t) * f(t, d) * (k1 + 1) / (f(t, d) + k1 * (1 - b + b * |d| / avgdl))
    idf(t)      = ln(1 + (N - n_t + 0.5) / (n_t + 0.5))      (never negative)
    A token repeated in the query contributes once per occurrence, which keeps the weighting that
    `retrieval_query` gives to the kind and the name.  Chunks with no token in common with the query are not returned.
    """

    def __init__(self, chunks: list, k1: float = BM25_K1, b: float = BM25_B):
        self.chunks, self.k1, self.b = chunks, k1, b
        self.tf = [Counter(words(t)) for _, t in chunks]
        self.len = [sum(c.values()) for c in self.tf]
        total = sum(self.len)
        self.avgdl = (total / len(chunks)) if total else 1.0
        df = Counter()
        for c in self.tf:
            df.update(c.keys())
        n = len(chunks)
        self.idf = {w: math.log(1.0 + (n - d + 0.5) / (d + 0.5)) for w, d in df.items()}

    def scores(self, query_tokens: list) -> list:
        q = Counter(query_tokens)
        out = []
        for i, c in enumerate(self.tf):
            norm = self.k1 * (1.0 - self.b + self.b * self.len[i] / self.avgdl)
            s = 0.0
            for w, qtf in q.items():
                f = c.get(w, 0)
                if f:
                    s += qtf * self.idf[w] * f * (self.k1 + 1.0) / (f + norm)
            out.append(s)
        return out

    def top(self, query_tokens: list, k: int) -> list:
        scored = sorted(((s, i) for i, s in enumerate(self.scores(query_tokens))), key=lambda x: (-x[0], x[1]))
        return [i for s, i in scored[:k] if s > 0]


@dataclass
class Context:
    text: str
    meta: dict = field(default_factory=dict)


class Retriever:
    def __init__(self, pack, chunk_k: int = 3, top_k: int | None = None, n_examples: int = 2, embedder=None):
        self.pack, self.chunk_k, self.top_k, self.n_examples = pack, chunk_k, top_k, n_examples
        self.embedder = embedder
        self._idx: dict = {}
        self._bm25: dict = {}
        self._dense: dict = {}

    def _chunk_index(self, sid):
        if sid not in self._idx:
            self._idx[sid] = ChunkIndex(self.pack.chunks(sid))
        return self._idx[sid]

    def _bm25_index(self, sid):
        if sid not in self._bm25:
            self._bm25[sid] = BM25Index(self.pack.chunks(sid))
        return self._bm25[sid]

    def _dense_index(self, sid):
        if self.embedder is None:
            raise ValueError("the dense condition needs an embedder (--embed-pin)")
        if sid not in self._dense:
            self._dense[sid] = DenseIndex(self.pack.chunks(sid), self.embedder)
        return self._dense[sid]

    def index(self, condition: str, sid):
        """The index behind a retrieval condition ('chunk', 'bm25' or 'dense'); built once per standard."""
        if condition == "dense":
            return self._dense_index(sid)
        return self._bm25_index(sid) if condition == "bm25" else self._chunk_index(sid)

    def context(self, condition: str, *, task: str, standard_id: str, language: str, kind: str,
                name: str, code: str) -> Context:
        pack = self.pack
        onto = getattr(pack, "rules_ontology", pack.ontology)      # Vol. 2: the rules may come from the drafted ontology
        sname = pack.standard_name(standard_id)
        if condition == "none":
            return Context(f"The team follows: {sname}.\nThe text of the standard is NOT provided - "
                           f"apply it from your own knowledge of it.", {"n_items": 0})
        if condition == "fulldoc":
            text = pack.fulltext(standard_id)
            return Context(f"{sname} - complete text:\n{text}", {"n_items": 1, "chars": len(text)})
        if condition in ("chunk", "bm25", "dense"):
            idx = self.index(condition, standard_id)
            q = dense_query(language, kind, name, code) if condition == "dense" else retrieval_query(language, kind, name, code)
            hits = idx.top(q, self.chunk_k)
            ids = [idx.chunks[i][0] for i in hits]
            body = "\n\n".join(idx.chunks[i][1] for i in hits) or "(no matching passage found)"
            return Context(f"{sname} - the {len(hits)} passage(s) most similar to the code:\n{body}",
                           {"n_items": len(hits), "retrieved_ids": ids})
        if condition == "graph":
            types = ("NamingRule",) if task == "rename" else ("CommentRule", "StructureRule")
            res = onto.resolve_rules(language, kind, types=types, standard_id=standard_id)
            rules = res.rules
            if self.top_k:
                rules = rules[: self.top_k]
            if not rules:
                return Context(f"{sname}: the ontology holds no specific rule for a {kind} in {language}; "
                               f"apply the general conventions of the standard.", {"n_items": 0, "retrieved_ids": []})
            body = "\n\n".join(render_rule(r, onto.examples(r["id"], self.n_examples) if self.n_examples else None)
                               for r in rules)
            meta = {"n_items": len(rules), "retrieved_ids": [r["id"] for r in rules]}
            # precedence: only present when the ontology has OVERRIDES / CONFLICTS_WITH edges that apply here
            if res.overridden:
                meta["overridden"] = [list(p) for p in res.overridden]
            conflicts = onto.conflicts_among(meta["retrieved_ids"])
            if conflicts:
                meta["conflicts"] = [list(p) for p in conflicts]
                body += "\n\nNote: " + "; ".join(f"{a} and {b}" for a, b in conflicts) \
                    + " disagree, and the standard does not say which one prevails."
            return Context(f"{sname} - rules retrieved for a {kind} in {language} (most important first):\n{body}",
                           meta)
        raise ValueError(f"unknown condition {condition!r}; choose from {CONDITIONS}")
