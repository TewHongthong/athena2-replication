#!/usr/bin/env python3
"""athena2 - Athena Vol. 2 command line (v0.1): the pipeline without the Vol. 1 oracles.

  python athena2.py rename --language python --file snippet.py --name MyVar --model-pin gemma4
        suggest a compliant name for one identifier of a snippet and check it (kind inferred from the code,
        rule check, scope check); prints the proposal, --json prints it as JSON
  python athena2.py run|freeze|show|prompts ...     the experiment commands of athena_sim.py, always with --no-oracle
                                                    (and --pack public5 unless a pack is given)
  python athena2.py report|packs ...                the same as in athena_sim.py

The kind and scope steps come from ../athena-corpus/curation (or $ATHENA_CURATION).  See README.md.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import athena_sim  # noqa: E402
from athena import pipeline  # noqa: E402
from athena.llm import LLMError, make_backend  # noqa: E402
from athena.packs import load_pack  # noqa: E402
from athena.pins import PinError, resolve_backend_args  # noqa: E402
from athena import embed  # noqa: E402
from athena.retrieval import CONDITIONS, Retriever  # noqa: E402

PASS_THROUGH = {"run", "freeze", "show", "prompts"}      # get --no-oracle
DELEGATED = PASS_THROUGH | {"report", "packs", "embed-check"}


def build_parser():
    ap = argparse.ArgumentParser(prog="athena2", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"athena2 {pipeline.VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rename", help="suggest and check a name for one identifier")
    r.add_argument("--pack", default="public5", choices=["public5"])
    r.add_argument("--corpus", default=None, help="athena-corpus folder of the pack (default ../athena-corpus or $ATHENA_CORPUS)")
    r.add_argument("--language", required=True, help="cpp, csharp, python, java, typescript, javascript")
    src = r.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="snippet file (UTF-8)")
    src.add_argument("--code", help="snippet text")
    r.add_argument("--name", required=True, help="the identifier that breaks the standard")
    r.add_argument("--standard", default=None, help="standard id (default: the only standard that covers the language)")
    r.add_argument("--condition", default="graph", choices=CONDITIONS)
    r.add_argument("--top-k", type=int, default=None)
    r.add_argument("--chunk-k", type=int, default=3)
    r.add_argument("--embed-pin", default=None, dest="embed_pin", help="dense: embedding pin entry")
    r.add_argument("--examples", type=int, default=2)
    r.add_argument("--timeout", type=float, default=180.0)
    r.add_argument("--retries", type=int, default=5)
    r.add_argument("--json", action="store_true", help="print the full proposal as JSON")
    athena_sim.add_run_args(r)
    for name in sorted(DELEGATED):
        sub.add_parser(name, help=f"as athena_sim.py {name}", add_help=False)
    return ap


def cmd_rename(a) -> int:
    try:
        resolve_backend_args(a)
    except PinError as e:
        print(f"model pin error: {e}", file=sys.stderr)
        return 2
    code = a.code
    if a.file:
        with open(a.file, "r", encoding="utf-8") as f:
            code = f.read()
    try:
        pack = load_pack(a.pack, a.corpus)
        backend = make_backend(a.backend, temperature=a.temperature, max_tokens=a.max_tokens,
                               reasoning_effort=a.reasoning_effort, timeout=a.timeout, retries=a.retries,
                               base_url=a.base_url, omit_temperature=a.omit_temperature, extra_body=a.extra_body,
                               no_think=a.no_think)
        pipeline.check_pack(pack)
        embedder = embed.from_args(a, a.condition == "dense")
        p = pipeline.propose_rename(pack, Retriever(pack, a.chunk_k, a.top_k, a.examples, embedder), backend, language=a.language,
                                    code=code, name=a.name, standard_id=a.standard, condition=a.condition)
    except (pipeline.PipelineError, LLMError, FileNotFoundError, ValueError, embed.EmbedError, PinError) as e:
        print(f"athena2: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(p.to_dict(), indent=2, ensure_ascii=False))
    else:
        ki = p.kind_inferred
        print(f"{p.status.upper()}: {p.name} -> {p.suggested or '(none)'}   [{p.reason}]")
        print(f"  kind: {p.kind} (inference: {ki['status']}" + (f", alternatives {ki['alt_kinds']}" if ki["alt_kinds"] else "") + ")")
        print(f"  standard: {p.standard_id}; condition: {p.condition}; rules in the prompt: {p.retrieval.get('retrieved_ids', '-')}")
        if p.rule_ids_applied:
            print(f"  rules applied by the model: {', '.join(p.rule_ids_applied)}")
        if p.reasoning:
            print(f"  model: {p.reasoning}")
    return 0 if p.status in ("accepted", "unchecked") else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in DELEGATED:
        cmd, rest = argv[0], argv[1:]
        if cmd in PASS_THROUGH:
            rest = ["--no-oracle"] + rest
            if cmd != "packs" and "--pack" not in rest:
                rest = ["--pack", "public5"] + rest
        return athena_sim.main([cmd] + rest)
    a = build_parser().parse_args(argv)
    return cmd_rename(a)


if __name__ == "__main__":
    sys.exit(main())
