"""Standard packs: a coding standard + its ontology + the experiment units built on it.

Two packs ship with Athena Sim:
  public5 - PEP 8, Google Java, .NET, Google TypeScript, Airbnb JS; units come from the curated
            benchmark in ../athena-corpus/benchmark (real open-source code + injected violations).
  gscs    - "General Style and Coding Standards for Software Projects" (the docx used by the original
            Athena pilot).  A user-defined standard the LLM cannot have memorised; units come from
            small hand-authored seed snippets (packs/gscs/build_gscs_pack.py).
"""
from __future__ import annotations

import ast
import glob
import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

from .ontology import Ontology, render_rule
from .passages import split_passages

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # .../athena-sim
DEFAULT_CORPUS = os.path.normpath(os.path.join(ROOT, "..", "athena-corpus"))
CACHE_DIR = os.environ.get("ATHENA_SIM_CACHE") or os.path.join(ROOT, ".cache")   # parsed-benchmark cache


@dataclass
class Unit:
    """One rename experiment: an identifier whose name was corrupted; the LLM must repair it."""
    unit_id: str
    snippet_id: str
    language: str
    standard_id: str
    kind: str
    original: str            # ground-truth compliant name
    injected: str            # the violating name shown to the LLM
    rule_id: str             # rule the injected name violates
    method: str
    code_original: str       # compliant code (ground truth)
    code_violation: str      # code with the injected name (what the LLM sees)
    split: str = ""          # "dev" (tune on this) or "test" (touch once); decided per snippet
    file: str = ""           # source file of the snippet ("<repo>:<path>" from its provenance; "" if unknown)


@dataclass
class CommentUnit:
    """One comment-generation experiment: a function whose header comment was removed."""
    unit_id: str
    snippet_id: str
    language: str
    standard_id: str
    kind: str
    name: str
    code_bare: str           # code without the header comment (what the LLM sees)
    reference_comment: str   # the original header comment (reference, not ground truth)
    rule_ids: list = field(default_factory=list)
    split: str = ""
    expected_elements: Optional[list] = None   # which CommentRule requiredElements actually apply to
                                               # this unit's signature (e.g. a void method has no 'returns');
                                               # None (gscs units) means "no signature-based filtering"


DEV_PERCENT = 30      # share of snippets that go to the development split when the data does not name one


def _source_file(snip: dict) -> str:
    """Identify the file a snippet was taken from: "<repo>:<path>" from its provenance, "" when either is missing."""
    prov = snip.get("provenance") or {}
    repo, path = prov.get("repo"), prov.get("path")
    return f"{repo}:{path}" if repo and path else ""


def split_of(snippet_id: str, explicit: Optional[str] = None) -> str:
    """dev/test split, decided per SNIPPET (all violations of one snippet stay together, so a test unit never
    shares its code with a dev unit).  Data files may name the split explicitly (the gscs pack does); otherwise
    it is a fixed hash of the snippet id, so it never changes between runs or machines."""
    if explicit in ("dev", "test"):
        return explicit
    h = int(hashlib.sha256(("athena-split-v1|" + snippet_id).encode("utf-8")).hexdigest(), 16) % 100
    return "dev" if h < DEV_PERCENT else "test"


def select_split(units: list, split: str) -> list:
    return list(units) if split == "all" else [u for u in units if u.split == split]


def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_many(paths, workers: int = 16) -> list:
    if len(paths) < 8:
        return [_read_json(p) for p in paths]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_read_json, paths))


def _sha256_files(paths):
    h = hashlib.sha256()
    for p in paths:
        if os.path.exists(p):
            with open(p, "rb") as f:
                h.update(f.read().replace(b"\r\n", b"\n"))
    return h.hexdigest()


class Pack:
    id = ""
    title = ""

    def __init__(self, ontology: Ontology):
        self.ontology = ontology

    # -- standard text -----------------------------------------------------------------
    def standard_ids(self):
        return [n["id"] for n in self.ontology.nodes.values() if n["type"] == "Standard"]

    def standard_name(self, sid: str) -> str:
        return self.ontology.standard_name(sid)

    def fulltext(self, sid: str) -> str:
        """The whole standard as one block of text (the 'whole document in the prompt' condition)."""
        rules = self.ontology.rules_of_standard(sid)
        lines = [f"{self.standard_name(sid)} ({sid}) - all rules"]
        lines += [render_rule(r) for r in rules]
        return "\n\n".join(lines)

    def chunks(self, sid: str) -> list:
        """Chunks for the plain-RAG condition: list of (chunk_id, text). Default: one chunk per rule."""
        return [(r["id"], render_rule(r)) for r in self.ontology.rules_of_standard(sid)]

    # -- grading -----------------------------------------------------------------------
    def core_rules(self, lang: str, kind: str) -> list:
        raise NotImplementedError

    # -- units -------------------------------------------------------------------------
    def rename_units(self, languages=None) -> list:
        raise NotImplementedError

    def comment_units(self, languages=None) -> list:
        return []

    def fingerprint(self) -> dict:
        return {"pack": self.id, "ontology": os.path.basename(self.ontology.path),
                "ontology_sha256": self.ontology.sha256}


# ------------------------------------------------------------------------------------------
class BenchmarkDir:
    """Reads the curated benchmark layout: snippets/<lang>/*.json and violations/<lang>/*.json."""

    def __init__(self, root: str):
        self.root = root
        self._snips: dict = {}

    def snippet(self, lang: str, snippet_id: str) -> dict:
        key = (lang, snippet_id)
        if key not in self._snips:
            self._snips[key] = _read_json(os.path.join(self.root, "snippets", lang, snippet_id + ".json"))
        return self._snips[key]

    def _languages(self) -> list:
        vdir = os.path.join(self.root, "violations")
        if not os.path.isdir(vdir):
            return []
        return sorted(l for l in os.listdir(vdir) if os.path.isdir(os.path.join(vdir, l)))

    def rename_units(self, languages=None) -> list:
        units = []
        for lang in self._languages():
            if not languages or lang in languages:
                units += self._lang_units(lang)
        return units

    # Reading ~3,500 small JSON files can take minutes on a OneDrive / network folder, so the parsed units are
    # cached per language (an interrupted first run keeps the languages it finished).  The cache key is cheap on
    # purpose: file names + the mtime of the language folders and index files.  If you edit a benchmark file IN
    # PLACE, delete the .cache folder.
    def _signature(self, lang: str) -> str:
        h = hashlib.sha1()
        for sub in ("snippets", "violations"):
            ld = os.path.join(self.root, sub, lang)
            if not os.path.isdir(ld):
                continue
            h.update(f"{sub}/{lang}|{os.stat(ld).st_mtime_ns}\n".encode())
            with os.scandir(ld) as it:
                for name in sorted(e.name for e in it):
                    h.update(name.encode() + b"\n")
            idx = os.path.join(self.root, sub + "_index.tsv")
            if os.path.exists(idx):
                st = os.stat(idx)
                h.update(f"{sub}_index|{st.st_size}|{st.st_mtime_ns}\n".encode())
        return h.hexdigest()

    def _lang_units(self, lang: str) -> list:
        memo = self.__dict__.setdefault("_memo", {})
        if lang in memo:
            return memo[lang]
        cache = tag = None
        try:
            tag = hashlib.sha1(os.path.abspath(self.root).encode()).hexdigest()[:8]
            cache = os.path.join(CACHE_DIR, f"bench-{tag}-v4-{lang}-{self._signature(lang)[:16]}.json")
            if os.path.exists(cache):
                with open(cache, "r", encoding="utf-8") as f:
                    memo[lang] = [Unit(**d) for d in json.load(f)]
                return memo[lang]
        except (OSError, ValueError, TypeError):
            pass
        memo[lang] = units = self._read_lang(lang)
        if cache:
            try:
                os.makedirs(CACHE_DIR, exist_ok=True)
                for old in glob.glob(os.path.join(CACHE_DIR, f"bench-{tag}-*-{lang}-*.json")):
                    os.remove(old)
                tmp = cache + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump([asdict(u) for u in units], f, ensure_ascii=False)
                os.replace(tmp, cache)
            except OSError:
                pass
        return units

    def _read_lang(self, lang: str) -> list:
        # high latency per file on network / OneDrive folders, so read many files at once
        vpaths = sorted(glob.glob(os.path.join(self.root, "violations", lang, "*.json")))
        viols = _read_many(vpaths)
        need = sorted({v["snippetId"] for v in viols} - {sid for (lg, sid) in self._snips if lg == lang})
        for sid, snip in zip(need, _read_many([os.path.join(self.root, "snippets", lang, sid + ".json") for sid in need])):
            self._snips[(lang, sid)] = snip
        units = []
        for path, v in zip(vpaths, viols):
            s = self._snips[(lang, v["snippetId"])]
            units.append(Unit(
                unit_id=os.path.splitext(os.path.basename(path))[0], snippet_id=v["snippetId"],
                language=lang, standard_id=s["standardId"], kind=v["identifierKind"],
                original=v["originalName"], injected=v["injectedName"], rule_id=v["violatedRuleId"],
                method=v.get("injectionMethod", ""), code_original=s["codeContext"],
                code_violation=v["codeContextWithViolation"],
                split=split_of(v["snippetId"], v.get("split") or s.get("split")),
                file=_source_file(s)))
        return units

    def comment_units(self, languages=None) -> list:
        if getattr(self, "_comment_memo", None) is None:
            units = []
            cdir = os.path.join(self.root, "comment_units")
            if os.path.isdir(cdir):
                paths = [(lang, path) for lang in sorted(os.listdir(cdir))
                         for path in sorted(glob.glob(os.path.join(cdir, lang, "*.json")))]
                for (lang, path), c in zip(paths, _read_many([p for _, p in paths])):
                    units.append(CommentUnit(
                        unit_id=os.path.splitext(os.path.basename(path))[0], snippet_id=c["snippetId"],
                        language=lang, standard_id=c["standardId"], kind=c["identifierKind"], name=c["name"],
                        code_bare=c["codeBare"], reference_comment=c["referenceComment"],
                        rule_ids=c.get("ruleIds", []), split=split_of(c["snippetId"], c.get("split")),
                        expected_elements=c.get("expectedElements")))
            self._comment_memo = units
        return [u for u in self._comment_memo if not languages or u.language in languages]


def _load_core_table(rules_py: str) -> dict:
    """Read the CORE table out of curation/rules.py without importing it."""
    with open(rules_py, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "CORE" for t in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError(f"CORE table not found in {rules_py}")


class Public5Pack(Pack):
    id = "public5"
    title = "PEP 8 / Google Java / .NET / Google TypeScript / Airbnb JS (curated benchmark)"

    def __init__(self, corpus_dir: Optional[str] = None):
        corpus = corpus_dir or os.environ.get("ATHENA_CORPUS") or DEFAULT_CORPUS
        self.corpus = corpus
        onto_path = os.path.join(corpus, "curation", "pipeline", "athena_ontology.json")
        rules_py = os.path.join(corpus, "curation", "rules.py")
        for p in (onto_path, rules_py, os.path.join(corpus, "benchmark")):
            if not os.path.exists(p):
                raise FileNotFoundError(f"public5 pack needs {p} (set --corpus or ATHENA_CORPUS)")
        super().__init__(Ontology(onto_path))
        self._core = _load_core_table(rules_py)
        self.bench = BenchmarkDir(os.path.join(corpus, "benchmark"))

    def core_rules(self, lang, kind):
        return list(self._core.get((lang, kind), []))

    def rename_units(self, languages=None):
        return self.bench.rename_units(languages)

    def comment_units(self, languages=None):
        return self.bench.comment_units(languages)

    def fingerprint(self):
        fp = super().fingerprint()
        idx = [os.path.join(self.bench.root, "snippets_index.tsv"), os.path.join(self.bench.root, "violations_index.tsv")]
        fp["benchmark_index_sha256"] = _sha256_files(idx)
        fp["comment_units_index_sha256"] = _sha256_files([os.path.join(self.bench.root, "comment_units_index.tsv")])
        return fp


class GscsPack(Pack):
    id = "gscs"
    title = "General Style and Coding Standards for Software Projects (user-defined, from the pilot docx)"

    def __init__(self):
        base = os.path.join(ROOT, "packs", "gscs")
        onto_path = os.path.join(base, "gscs_ontology.json")
        if not os.path.exists(onto_path):
            raise FileNotFoundError(f"{onto_path} missing - run: python packs/gscs/build_gscs_pack.py")
        super().__init__(Ontology(onto_path))
        self.base = base
        self.bench = BenchmarkDir(os.path.join(base, "benchmark"))
        with open(os.path.join(base, "gscs_source.txt"), "r", encoding="utf-8") as f:
            self._source = f.read()

    def fulltext(self, sid):
        return self._source.strip()

    def chunks(self, sid):
        """One chunk per '## ' section of the source document."""
        out, cur_title, cur = [], None, []
        for line in self._source.splitlines():
            if line.startswith("## "):
                if cur_title is not None:
                    out.append((cur_title, "\n".join(cur).strip()))
                cur_title, cur = line[3:].strip(), [line]
            else:
                cur.append(line)
        if cur_title is not None:
            out.append((cur_title, "\n".join(cur).strip()))
        return out

    def core_rules(self, lang, kind):
        return [r["id"] for r in self.ontology.rules_for(lang, kind, types=("NamingRule",))]

    def rename_units(self, languages=None):
        return self.bench.rename_units(languages)

    def comment_units(self, languages=None):
        return self.bench.comment_units(languages)

    def fingerprint(self):
        fp = super().fingerprint()
        fp["source_sha256"] = hashlib.sha256(self._source.replace("\r\n", "\n").encode("utf-8")).hexdigest()
        # hash the units as loaded (not the files again): same content -> same hash, and no extra file reads
        h = hashlib.sha256()
        for u in sorted(self.rename_units() + self.comment_units(), key=lambda u: (type(u).__name__, u.unit_id)):
            h.update(json.dumps(asdict(u), sort_keys=True, ensure_ascii=False).encode("utf-8"))
        fp["units_sha256"] = h.hexdigest()
        return fp


STANDARDS_DIR = os.path.normpath(os.path.join(ROOT, "..", "standards"))
VOL2_ONTOLOGY_FILES = {"godot": "godot_ontology.json", "dotnet-runtime": "dotnet_ontology.json", "odoo": "odoo_ontology.json"}
VOL2_PACKS = tuple(VOL2_ONTOLOGY_FILES)
ONTOLOGY_VARIANTS = ("human", "llm")
BENCH_ROOT_ENV = "ATHENA_V2_BENCH"


class Vol2Pack(Pack):
    """One of the three independent standards of Vol. 2 (godot, dotnet-runtime, odoo).

    The benchmark is the output of tools/export_tasks.py (snippets/ and violations/ in the layout of Vol. 1); its folder
    is `corpus_dir` or $ATHENA_V2_BENCH/<pack>.  Grading always uses the human ontology and its `core_rules.json`.
    `variant` says where the rules shown to the model come from: 'human' (the ontology of the author) or 'llm' (the
    ontology drafted by the LLM, packs/<pack>/llm/llm_ontology.json).  The standard text for the none / fulldoc / chunk /
    bm25 / dense conditions is the pinned document in standards/src, cut into paragraphs by athena/passages.py.
    """

    def __init__(self, name: str, bench_dir: Optional[str] = None, variant: str = "human"):
        if variant not in ONTOLOGY_VARIANTS:
            raise ValueError(f"unknown ontology variant {variant!r} (choose {' or '.join(ONTOLOGY_VARIANTS)})")
        self.id = name
        self.variant = variant
        self.base = os.path.join(ROOT, "packs", name)
        onto_path = os.path.join(self.base, VOL2_ONTOLOGY_FILES[name])
        core_path = os.path.join(self.base, "core_rules.json")
        for pth in (onto_path, core_path):
            if not os.path.exists(pth):
                raise FileNotFoundError(f"pack {name!r} needs {pth}")
        super().__init__(Ontology(onto_path))
        self.title = self.ontology.name
        self._core_path = core_path
        core = _read_json(core_path).get("core", {})
        self._core = {(lang, kind): list(ids) for lang, kinds in core.items() for kind, ids in kinds.items()}
        if variant == "llm":
            llm_path = os.path.join(self.base, "llm", "llm_ontology.json")
            if not os.path.exists(llm_path):
                raise FileNotFoundError(f"ontology variant 'llm' needs {llm_path}")
            self.rules_ontology = Ontology(llm_path)
        else:
            self.rules_ontology = self.ontology
        self.rules_comparable = variant == "human"      # rule ids of the drafted ontology are not those of the benchmark
        bench = bench_dir or (os.path.join(os.environ[BENCH_ROOT_ENV], name) if os.environ.get(BENCH_ROOT_ENV) else None)
        if bench and not os.path.isdir(os.path.join(bench, "violations")) and os.path.isdir(os.path.join(bench, "bench", "violations")):
            bench = os.path.join(bench, "bench")        # <root>/<pack>/bench/ as left by the pool build
        if not bench or not os.path.isdir(os.path.join(bench, "violations")):
            raise FileNotFoundError(f"pack {name!r} needs the benchmark folder written by tools/export_tasks.py "
                                    f"(snippets/ and violations/); pass --corpus <folder> or set ${BENCH_ROOT_ENV} "
                                    f"to the folder that holds one such folder per pack")
        self.bench = BenchmarkDir(bench)
        self._doc = None

    # -- the standard document ---------------------------------------------------------------
    def _document(self):
        if self._doc is None:
            meta = next(s for s in _read_json(os.path.join(STANDARDS_DIR, "standards.json"))["standards"]
                        if s["id"] == self.id)
            path = os.path.join(STANDARDS_DIR, "src", self.id, os.path.basename(meta["doc_path"]))
            with open(path, "r", encoding="utf-8", newline="") as f:
                text = f.read().replace("\r\n", "\n")
            self._doc = (path, text, "md" if path.endswith(".md") else "rst")
        return self._doc

    def fulltext(self, sid):
        return self._document()[1].strip()

    def chunks(self, sid):
        _, text, fmt = self._document()
        return split_passages(text, fmt)

    def core_rules(self, lang, kind):
        return list(self._core.get((lang, kind), []))

    def rename_units(self, languages=None):
        return self.bench.rename_units(languages)

    def fingerprint(self):
        fp = super().fingerprint()
        fp["ontology_variant"] = self.variant
        fp["rules_ontology_sha256"] = self.rules_ontology.sha256
        fp["core_rules_sha256"] = _sha256_files([self._core_path])
        fp["standard_document_sha256"] = _sha256_files([self._document()[0]])
        fp["benchmark_index_sha256"] = _sha256_files([os.path.join(self.bench.root, n) for n in
                                                      ("snippets_index.tsv", "violations_index.tsv", "tasks.tsv")])
        return fp


def load_pack(name: str, corpus_dir: Optional[str] = None, variant: str = "human") -> Pack:
    if name in VOL2_PACKS:
        return Vol2Pack(name, corpus_dir, variant)
    if variant != "human":
        raise ValueError(f"pack {name!r} has only the human ontology (variant {variant!r} is for {', '.join(VOL2_PACKS)})")
    if name == "public5":
        return Public5Pack(corpus_dir)
    if name == "gscs":
        return GscsPack()
    raise ValueError(f"unknown pack {name!r} (choose public5, gscs, {', '.join(VOL2_PACKS)})")
