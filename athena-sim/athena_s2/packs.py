"""The two Study 2 packs, godot-s2 and dotnet-runtime-s2.

A pack is a Vol. 2 pack (athena.packs.Vol2Pack) with its own ontology and core table (athena-sim/packs/<pack>/) and
its own benchmark (tools/export_tasks_s2.py), read from `corpus_dir` or $ATHENA_S2_BENCH/<pack> (or its bench/
folder). The standard document is that of the Study 1 standard (standards/src/godot, standards/src/dotnet-runtime),
so none, fulldoc, chunk, bm25, dense and naming see the same text as in Study 1. Only the human ontology exists.
"""
from __future__ import annotations

import os
from typing import Optional

from athena.ontology import Ontology
from athena.packs import ROOT, STANDARDS_DIR, BenchmarkDir, Pack, Vol2Pack, _read_json

S2_PACKS = {"godot-s2": ("godot", "godot_ontology.json"),
            "dotnet-runtime-s2": ("dotnet-runtime", "dotnet_ontology.json")}
BENCH_ROOT_ENV = "ATHENA_S2_BENCH"


class Study2Pack(Vol2Pack):
    def __init__(self, name: str, bench_dir: Optional[str] = None, variant: str = "human"):
        if name not in S2_PACKS:
            raise ValueError(f"unknown Study 2 pack {name!r} (choose {', '.join(S2_PACKS)})")
        if variant != "human":
            raise ValueError("the Study 2 packs have only the human ontology")
        self.id, self.variant = name, variant
        self.standard_doc_id, onto_file = S2_PACKS[name]
        self.base = os.path.join(ROOT, "packs", name)
        onto_path = os.path.join(self.base, onto_file)
        core_path = os.path.join(self.base, "core_rules.json")
        for pth in (onto_path, core_path):
            if not os.path.exists(pth):
                raise FileNotFoundError(f"pack {name!r} needs {pth}")
        Pack.__init__(self, Ontology(onto_path))
        self.title = self.ontology.name
        self._core_path = core_path
        core = _read_json(core_path).get("core", {})
        self._core = {(lang, kind): list(ids) for lang, kinds in core.items() for kind, ids in kinds.items()}
        self.rules_ontology = self.ontology
        self.rules_comparable = True
        bench = bench_dir or (os.path.join(os.environ[BENCH_ROOT_ENV], name) if os.environ.get(BENCH_ROOT_ENV) else None)
        if bench and not os.path.isdir(os.path.join(bench, "violations")) and os.path.isdir(os.path.join(bench, "bench", "violations")):
            bench = os.path.join(bench, "bench")
        if not bench or not os.path.isdir(os.path.join(bench, "violations")):
            raise FileNotFoundError(f"pack {name!r} needs the benchmark folder written by tools/export_tasks_s2.py "
                                    f"(snippets/ and violations/); pass --corpus <folder> or set ${BENCH_ROOT_ENV} "
                                    f"to the folder that holds one such folder per pack")
        self.bench = BenchmarkDir(bench)
        self._doc = None

    def _document(self):
        if self._doc is None:
            meta = next(s for s in _read_json(os.path.join(STANDARDS_DIR, "standards.json"))["standards"]
                        if s["id"] == self.standard_doc_id)
            path = os.path.join(STANDARDS_DIR, "src", self.standard_doc_id, os.path.basename(meta["doc_path"]))
            with open(path, "r", encoding="utf-8", newline="") as f:
                text = f.read().replace("\r\n", "\n")
            self._doc = (path, text, "md" if path.endswith(".md") else "rst")
        return self._doc

    def fingerprint(self):
        fp = super().fingerprint()
        fp["standard_document_id"] = self.standard_doc_id
        return fp


def load_pack(name: str, corpus_dir: Optional[str] = None, variant: str = "human") -> Study2Pack:
    return Study2Pack(name, corpus_dir, variant)
