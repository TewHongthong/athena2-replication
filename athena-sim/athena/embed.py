"""Dense retrieval: an embedding pin, a client for an OpenAI-compatible /embeddings endpoint, and a vector index.

The embedding model is pinned like a panel model: an entry under "embeddings" in the pin file
(default ../models/model_pins.json) names the model id sent to the server, the templates that turn a query and a
passage into the text that is embedded, and the identity of the model file.  `--embed-pin NAME` selects the entry;
its SHA-256 is recorded in the run configuration and in a freeze.  An entry marked "incomplete" is refused.

The endpoint is read from $ATHENA_EMBED_BASE_URL (no address is stored in the pin file).  Every vector is cached on
disk under the pin's hash, so a text is embedded once per pin: the same query or passage always gets the same vector,
and a run can be repeated without the server once its texts are cached.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import threading
import time
import urllib.error
import urllib.request

from .pins import entry_sha256, load_pins

DEFAULT_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "athena2", "embeddings")
ENV_BASE_URL = "ATHENA_EMBED_BASE_URL"
ENV_CACHE = "ATHENA_EMBED_CACHE"
ENV_KEY = "ATHENA_EMBED_API_KEY"

_REQUIRED = ("model", "query_template", "document_template", "batch")


class EmbedError(RuntimeError):
    pass


def dense_query(language: str, kind: str, name: str, code: str) -> str:
    """The text a query is built from: the same information as the lexical query (language, kind, name and code),
    written as it would be read."""
    return f"{language} {kind} named {name}\n{code}"


def _normalise(v: list) -> list:
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v] if n else v


def _dot(a: list, b: list) -> float:
    return sum(x * y for x, y in zip(a, b))


class Embedder:
    """Embeds query and passage texts with the model of one pin entry; vectors are L2-normalised and cached."""

    def __init__(self, name: str, entry: dict, base_url: str | None = None, cache_dir: str | None = None,
                 timeout: float = 120.0, retries: int = 3):
        request = entry.get("request")
        if not isinstance(request, dict) or any(k not in request for k in _REQUIRED):
            raise EmbedError(f"embedding entry {name!r} needs request fields {', '.join(_REQUIRED)}")
        if entry.get("status") == "incomplete":
            raise EmbedError(f"embedding entry {name!r} is marked incomplete: {entry.get('missing', 'see the pin file')}")
        if "{query}" not in request["query_template"] or "{text}" not in request["document_template"]:
            raise EmbedError(f"embedding entry {name!r}: query_template needs {{query}} and document_template needs {{text}}")
        self.name, self.entry, self.request = name, entry, request
        self.sha256 = entry_sha256(entry)
        self.base_url = (base_url or os.environ.get(ENV_BASE_URL) or "").rstrip("/")
        self.timeout, self.retries = timeout, retries
        self.requests_made = 0
        self._lock = threading.Lock()
        self._mem: dict = {}
        cache_dir = cache_dir or os.environ.get(ENV_CACHE) or DEFAULT_CACHE
        os.makedirs(cache_dir, exist_ok=True)
        self._path = os.path.join(cache_dir, f"{name}-{self.sha256[:16]}.jsonl")
        if os.path.exists(self._path):
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        r = json.loads(line)
                        self._mem[r["k"]] = r["v"]

    # ------------------------------------------------------------------------------------------ public
    def describe(self) -> dict:
        return {"embed_pin": self.name, "embed_pin_sha256": self.sha256, "model": self.request["model"],
                "cache": self._path, "cached_vectors": len(self._mem), "requests": self.requests_made}

    def embed(self, texts: list, role: str) -> list:
        """role = 'query' or 'document'; returns one normalised vector per text, in order."""
        if role not in ("query", "document"):
            raise ValueError("role must be 'query' or 'document'")
        wrapped = [self._wrap(t, role) for t in texts]
        keys = [hashlib.sha256((role + "\0" + w).encode("utf-8")).hexdigest() for w in wrapped]
        with self._lock:
            missing = []
            for k, w in zip(keys, wrapped):
                if k not in self._mem and (k, w) not in missing:
                    missing.append((k, w))
        step = max(1, int(self.request["batch"]))
        for i in range(0, len(missing), step):
            part = missing[i:i + step]
            vecs = self._request([w for _, w in part])
            with self._lock, open(self._path, "a", encoding="utf-8", newline="\n") as f:
                for (k, _w), v in zip(part, vecs):
                    v = _normalise([float(x) for x in v])
                    self._mem[k] = v
                    f.write(json.dumps({"k": k, "v": v}) + "\n")
        with self._lock:
            return [self._mem[k] for k in keys]

    # ----------------------------------------------------------------------------------------- internals
    def _wrap(self, text: str, role: str) -> str:
        if role == "query":
            return self.request["query_template"].replace("{query}", text)
        return self.request["document_template"].replace("{text}", text)

    def _request(self, inputs: list) -> list:
        if not self.base_url:
            raise EmbedError(f"{len(inputs)} text(s) are not in the cache and ${ENV_BASE_URL} is not set")
        body = json.dumps({"model": self.request["model"], "input": inputs}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if os.environ.get(ENV_KEY):
            headers["Authorization"] = "Bearer " + os.environ[ENV_KEY]
        last = None
        for attempt in range(self.retries + 1):
            try:
                req = urllib.request.Request(self.base_url + "/embeddings", data=body, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    data = json.loads(r.read().decode("utf-8"))
                self.requests_made += 1
                rows = sorted(data["data"], key=lambda d: d.get("index", 0))
                if len(rows) != len(inputs):
                    raise EmbedError(f"asked for {len(inputs)} embeddings, got {len(rows)}")
                return [d["embedding"] for d in rows]
            except urllib.error.HTTPError as e:
                last = EmbedError(f"embedding server answered {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
                if e.code < 500:
                    break
            except (urllib.error.URLError, OSError, KeyError, ValueError, EmbedError) as e:
                last = e if isinstance(e, EmbedError) else EmbedError(f"embedding request failed: {e}")
            time.sleep(1.0 + attempt)
        raise last


class DenseIndex:
    """Cosine index over (chunk_id, text) pairs; same interface as BM25Index (`chunks`, `top`) except that `top`
    takes the query text and always returns min(k, number of chunks) chunks, because a cosine score has no zero."""

    def __init__(self, chunks: list, embedder: Embedder):
        self.chunks, self.embedder = chunks, embedder
        self.vecs = embedder.embed([t for _, t in chunks], "document") if chunks else []

    def scores(self, query_text: str) -> list:
        q = self.embedder.embed([query_text], "query")[0]
        return [_dot(q, v) for v in self.vecs]

    def top(self, query_text: str, k: int) -> list:
        scored = sorted(((s, i) for i, s in enumerate(self.scores(query_text))), key=lambda x: (-x[0], x[1]))
        return [i for _s, i in scored[:k]]


def load_embedder(name: str, pins_path: str | None = None, **kw) -> Embedder:
    pins = load_pins(pins_path)
    entry = (pins.get("embeddings") or {}).get(name)
    if entry is None:
        raise EmbedError(f"no embedding entry {name!r}; available: {', '.join(sorted(pins.get('embeddings') or {})) or 'none'}")
    return Embedder(name, entry, **kw)


def from_args(args, needed: bool) -> Embedder | None:
    """The embedder for `--embed-pin`, or None when no condition needs one."""
    if not needed:
        return None
    name = getattr(args, "embed_pin", None)
    if not name:
        raise EmbedError("the dense condition needs --embed-pin NAME (an entry under 'embeddings' in the pin file)")
    emb = load_embedder(name, getattr(args, "pins", None))
    args.embed_pin_sha256 = emb.sha256
    return emb


# ------------------------------------------------------------------------------------------------ server check
_CHECK_PASSAGES = ["Local variables and parameters are written in lower_snake_case.",
                   "Class and struct names are written in PascalCase.",
                   "Constants are written in UPPER_SNAKE_CASE.",
                   "Every public function has a documentation comment."]
_CHECK_QUERIES = [(("python", "variable", "MyValue", "def f():\n    MyValue = 1\n    return MyValue"), 0),
                  (("python", "class", "my_class", "class my_class:\n    pass"), 1),
                  (("python", "constant", "maxSize", "maxSize = 10"), 2)]


def check(embedder: Embedder) -> dict:
    """Embed a few passages and queries and report whether the nearest passage is the expected one.  This tests the
    serving setup (pooling, end-of-text handling, templates), not the experiment: the expected passages are obvious."""
    docs = embedder.embed(_CHECK_PASSAGES, "document")
    rows, ok = [], 0
    for q, want in _CHECK_QUERIES:
        v = embedder.embed([dense_query(*q)], "query")[0]
        sims = [_dot(v, d) for d in docs]
        got = max(range(len(sims)), key=lambda i: (sims[i], -i))
        ok += got == want
        rows.append({"query": q[:3], "expected": want, "nearest": got, "similarities": [round(x, 3) for x in sims]})
    return {"dimension": len(docs[0]), "norm": round(math.sqrt(_dot(docs[0], docs[0])), 6), "rows": rows,
            "correct": ok, "of": len(_CHECK_QUERIES), "describe": embedder.describe()}
