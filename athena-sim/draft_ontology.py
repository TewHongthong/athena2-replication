#!/usr/bin/env python3
"""LLM draft of the ontology of one independent standard (one model, one pass, prompt fixed before the run).

The prompt (draft/draft_prompt.md) holds the schema, the identifier-kind list and the text of the pinned standard
document. The human ontology is not read by this script and is not part of the prompt.

    python draft_ontology.py prompt  --standard godot            print the prompt that would be sent
    python draft_ontology.py freeze                              record the hashes of template, documents, prompts, pin
    python draft_ontology.py run     --standard godot            one request; needs the freeze and OPENAI_API_KEY
    python draft_ontology.py check   --standard godot            repeat the loader checks on the stored draft

Outputs of `run`, in packs/<standard>/llm/:
    prompt.txt       the prompt as sent
    response.txt     the raw answer, byte for byte
    meta.json        model, provider, response id, token counts, finish reason, hashes
    llm_ontology.json  the answer after the only permitted transformation (removing one Markdown code fence)
    check.json       the loader checks and the schema findings

A run refuses to start if response.txt already exists: there is one pass per standard. A draft that fails the loader
checks is reported as rejected and is not edited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from athena import llm, pins  # noqa: E402

TEMPLATE = os.path.join(HERE, "draft", "draft_prompt.md")
FREEZE = os.path.join(HERE, "draft", "draft_freeze.json")
STANDARDS_JSON = os.path.join(REPO, "standards", "standards.json")
SRC_DIR = os.path.join(REPO, "standards", "src")
DEFAULT_PIN = "luna_draft"

# identifiers and display names of the Standard and Language nodes given to the model
SUBJECTS = {
    "godot": {"standard_id": "GODOT", "language_id": "cpp", "language_name": "C++", "extensions": '".cpp", ".h"'},
    "dotnet-runtime": {"standard_id": "DOTNET", "language_id": "csharp", "language_name": "C#", "extensions": '".cs"'},
    "odoo": {"standard_id": "ODOO", "language_id": "python", "language_name": "Python", "extensions": '".py"'},
}
CASINGS = {None, "PascalCase", "camelCase", "snake_case", "SCREAMING_SNAKE_CASE", "kebab-case"}
SEVERITIES = {"MUST", "SHOULD", "MAY"}
NODE_TYPES = {"Standard", "Language", "IdentifierKind", "NamingRule"}
RELATIONS = {"APPLIES_TO", "DEFINED_IN"}


class DraftError(Exception):
    pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str) -> str:
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


def out_dir(std: str) -> str:
    return os.path.join(HERE, "packs", std, "llm")


def load_standard_entry(std: str) -> dict:
    with open(STANDARDS_JSON, "r", encoding="utf-8") as f:
        d = json.load(f)
    for e in d["standards"]:
        if e["id"] == std:
            return {**e, "pinned_on": d["pinned_on"]}
    raise DraftError(f"standard {std!r} is not in {STANDARDS_JSON}")


def read_document(std: str, entry: dict) -> str:
    """Text of the pinned standard document, checked against the SHA-256 recorded in standards.json."""
    name = os.path.basename(entry["doc_path"])
    path = os.path.join(SRC_DIR, std, name)
    if not os.path.exists(path):
        raise DraftError(f"{path} not found; run standards/fetch_standards.py first")
    with open(path, "rb") as f:
        raw = f.read()
    want = entry["sha256"][name]
    if sha256_bytes(raw) != want:
        raise DraftError(f"{path}: SHA-256 {sha256_bytes(raw)} does not match standards.json ({want})")
    return raw.decode("utf-8")


def build_prompt(std: str, template: str | None = None) -> str:
    if std not in SUBJECTS:
        raise DraftError(f"unknown standard {std!r}; choose from {', '.join(SUBJECTS)}")
    s, entry = SUBJECTS[std], load_standard_entry(std)
    text = read_document(std, entry)
    if template is None:
        with open(TEMPLATE, "r", encoding="utf-8") as f:
            template = f.read()
    values = {
        "<STANDARD_ID>": s["standard_id"],
        "<STANDARD_NAME>": entry["title"],
        "<PUBLISHER>": entry["attribution"],
        "<URL>": entry["doc_repo"][:-4] if entry["doc_repo"].endswith(".git") else entry["doc_repo"],
        "<RETRIEVED_DATE>": entry["pinned_on"],
        "<LANGUAGE_ID>": s["language_id"],
        "<LANGUAGE_NAME>": s["language_name"],
        "<EXTENSIONS>": s["extensions"],
    }
    for k, v in values.items():
        template = template.replace(k, v)
    if template.count("<STANDARD_TEXT>") != 1:
        raise DraftError("the template must contain <STANDARD_TEXT> exactly once")
    return template.replace("<STANDARD_TEXT>", text)       # last, so the document text is never rewritten


# ------------------------------------------------------------------ freeze
def pin_entry(name: str, pins_path: str | None = None) -> dict:
    d = pins.load_pins(pins_path)
    e = d["models"].get(name)
    if e is None:
        raise DraftError(f"no pin entry {name!r}")
    if e.get("status") == "incomplete":
        raise DraftError(f"pin entry {name!r} is incomplete")
    return e


def freeze_record(pin_name: str = DEFAULT_PIN, pins_path: str | None = None) -> dict:
    prompts = {}
    docs = {}
    for std in SUBJECTS:
        p = build_prompt(std)
        prompts[std] = sha256_bytes(p.encode("utf-8"))
        docs[std] = load_standard_entry(std)["sha256"][os.path.basename(load_standard_entry(std)["doc_path"])]
    return {
        "schema": 1,
        "template_sha256": sha256_file(TEMPLATE),
        "document_sha256": docs,
        "prompt_sha256": prompts,
        "pin": pin_name,
        "pin_sha256": pins.entry_sha256(pin_entry(pin_name, pins_path)),
    }


def verify_freeze(std: str, prompt: str, pin_name: str, pins_path: str | None = None) -> dict:
    if not os.path.exists(FREEZE):
        raise DraftError("no freeze file; run `freeze` and keep it before any run")
    with open(FREEZE, "r", encoding="utf-8") as f:
        fz = json.load(f)
    if fz.get("pin") != pin_name:
        raise DraftError(f"the freeze names pin {fz.get('pin')!r}, not {pin_name!r}")
    if fz["pin_sha256"] != pins.entry_sha256(pin_entry(pin_name, pins_path)):
        raise DraftError("the pin entry changed after the freeze")
    if fz["template_sha256"] != sha256_file(TEMPLATE):
        raise DraftError("the prompt template changed after the freeze")
    if fz["prompt_sha256"].get(std) != sha256_bytes(prompt.encode("utf-8")):
        raise DraftError(f"the prompt for {std} differs from the frozen one")
    return fz


# ------------------------------------------------------------------ extraction and checks
def strip_fence(text: str) -> str:
    """The only permitted transformation: remove one Markdown code fence around the whole answer."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    return t


def schema_findings(d, std: str) -> list:
    """Departures from the prompt (informational; they do not decide acceptance)."""
    s = SUBJECTS[std]
    out = []
    nodes = d.get("nodes", []) if isinstance(d, dict) else []
    links = d.get("links", []) if isinstance(d, dict) else []
    ids = [n.get("id") for n in nodes if isinstance(n, dict)]
    if len(ids) != len(set(ids)):
        out.append("duplicate node ids")
    types_ = [n.get("type") for n in nodes if isinstance(n, dict)]
    for t in sorted({t for t in types_ if t not in NODE_TYPES}):
        out.append(f"node type outside the prompt: {t!r}")
    if types_.count("Standard") != 1:
        out.append(f"{types_.count('Standard')} Standard nodes (expected 1)")
    if types_.count("Language") != 1:
        out.append(f"{types_.count('Language')} Language nodes (expected 1)")
    by_id = {n["id"]: n for n in nodes if isinstance(n, dict) and "id" in n}
    for n in nodes:
        if not isinstance(n, dict):
            continue
        if n.get("type") == "NamingRule":
            rid = n.get("id", "?")
            if not str(rid).startswith(s["standard_id"] + "-"):
                out.append(f"{rid}: id does not start with {s['standard_id']}-")
            if n.get("casing") not in CASINGS:
                out.append(f"{rid}: casing {n.get('casing')!r} outside the list")
            if n.get("severity") not in SEVERITIES:
                out.append(f"{rid}: severity {n.get('severity')!r} outside the list")
            if n.get("sourceStandardId") != s["standard_id"]:
                out.append(f"{rid}: sourceStandardId {n.get('sourceStandardId')!r}")
    applies, defined = {}, {}
    for e in links:
        if not isinstance(e, dict):
            continue
        if e.get("relation") not in RELATIONS:
            out.append(f"relation outside the prompt: {e.get('relation')!r}")
        if e.get("source") not in by_id or e.get("target") not in by_id:
            out.append(f"link with an unknown end: {e.get('source')!r} -> {e.get('target')!r}")
        if e.get("relation") == "APPLIES_TO":
            applies.setdefault(e.get("source"), set()).add(e.get("target"))
        if e.get("relation") == "DEFINED_IN":
            defined.setdefault(e.get("source"), set()).add(e.get("target"))
    for n in nodes:
        if isinstance(n, dict) and n.get("type") == "NamingRule":
            rid = n.get("id")
            tg = applies.get(rid, set())
            if s["language_id"] not in tg:
                out.append(f"{rid}: no APPLIES_TO link to the language")
            if not any(by_id.get(t, {}).get("type") == "IdentifierKind" for t in tg):
                out.append(f"{rid}: no APPLIES_TO link to an identifier kind")
            if s["standard_id"] not in defined.get(rid, set()):
                out.append(f"{rid}: no DEFINED_IN link to the standard")
    return out


def _load_graph_loader():
    sys.path.insert(0, os.path.join(REPO, "ontology"))
    import graph_loader as GL  # noqa: E402
    return GL


def loader_checks(path: str, std: str, use_graph_loader: bool = True) -> dict:
    """The checks that decide acceptance: the stdlib reader of the harness, the reader of the curation code, and
    (when networkx is installed) graph_loader. Each entry is "ok" or the error text."""
    res = {}
    try:
        from athena.ontology import Ontology as HarnessOntology
        o = HarnessOntology(path)
        res["harness_reader"] = "ok"
        s = SUBJECTS[std]
        if s["language_id"] not in o.languages:
            res["harness_reader"] = f"language {s['language_id']!r} not in the ontology"
    except Exception as e:  # noqa: BLE001 - every failure is reported
        res["harness_reader"] = f"{type(e).__name__}: {e}"
    try:
        sys.path.insert(0, os.path.join(REPO, "athena-corpus", "curation"))
        sys.path.insert(0, os.path.join(REPO, "athena-corpus", "curation", "pipeline"))
        import rules as R
        r = R.Ontology(path)
        res["curation_reader"] = "ok"
        res["n_rules"] = len([n for n in r.nodes.values() if n.get("type") == "NamingRule"])
    except Exception as e:  # noqa: BLE001
        res["curation_reader"] = f"{type(e).__name__}: {e}"
        r = None
    if not use_graph_loader:
        res["graph_loader"] = "skipped"
    else:
        try:
            import networkx  # noqa: F401
        except ImportError:
            res["graph_loader"] = "skipped: networkx is not installed"
        else:
            import networkx as nx
            from networkx.readwrite import json_graph
            ver = tuple(int(x) for x in nx.__version__.split(".")[:2] if x.isdigit())
            orig = json_graph.node_link_graph
            adapted = ver < (3, 4)
            if adapted:                       # graph_loader passes edges=; networkx before 3.4 calls it link=

                def _compat(data, *a, **kw):
                    if "edges" in kw:
                        kw["link"] = kw.pop("edges")
                    return orig(data, *a, **kw)
                json_graph.node_link_graph = _compat
            try:
                GL = _load_graph_loader()
                bad = r.crosscheck_with_graph_loader(GL) if r is not None else ["curation reader failed"]
                res["graph_loader"] = "ok" if not bad else f"{len(bad)} mismatches with the curation reader"
                if adapted and not bad:
                    res["graph_loader_note"] = f"networkx {nx.__version__} with the edges= to link= adapter"
            except Exception as e:  # noqa: BLE001
                res["graph_loader"] = f"{type(e).__name__}: {e}"
            finally:
                json_graph.node_link_graph = orig
    return res


def accepted(checks: dict) -> bool:
    return all(v == "ok" or str(v).startswith("skipped") for k, v in checks.items() if k not in ("n_rules", "graph_loader_note"))


def evaluate(std: str, response_text: str, finish: str, odir: str, use_graph_loader: bool = True) -> dict:
    """Extract the JSON, write llm_ontology.json, run the checks, write check.json; returns the check record."""
    rec = {"finish": finish, "json": None, "checks": {}, "schema_findings": [], "accepted": False}
    if finish == "length":
        rec["rejected_because"] = "the answer was cut by the output limit (finish_reason=length)"
    body = strip_fence(response_text)
    try:
        d = json.loads(body)
        rec["json"] = "ok"
    except json.JSONDecodeError as e:
        rec["json"] = f"JSONDecodeError: {e}"
        rec.setdefault("rejected_because", "the answer is not valid JSON")
        d = None
    if d is not None and not (isinstance(d, dict) and isinstance(d.get("nodes"), list) and isinstance(d.get("links"), list)):
        rec["json"] = "not a node-link object with 'nodes' and 'links'"
        rec.setdefault("rejected_because", rec["json"])
        d = None
    if d is not None:
        path = os.path.join(odir, "llm_ontology.json")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body + "\n")
        rec["schema_findings"] = schema_findings(d, std)
        rec["checks"] = loader_checks(path, std, use_graph_loader)
        if not accepted(rec["checks"]):
            rec.setdefault("rejected_because", "the loader checks failed")
        rec["accepted"] = accepted(rec["checks"]) and finish != "length"
        rec["ontology_sha256"] = sha256_file(path)
    with open(os.path.join(odir, "check.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return rec


# ------------------------------------------------------------------ run
def make_backend_from_pin(pin_name: str, pins_path: str | None = None):
    ns = types.SimpleNamespace(model_pin=pin_name, pins=pins_path, backend=None, extra_body=None,
                               omit_temperature=False, temperature=0.2, max_tokens=None, base_url=None,
                               no_think=False, price_in=None, price_out=None)
    pins.resolve_backend_args(ns)
    be = llm.make_backend(ns.backend, temperature=ns.temperature, max_tokens=ns.max_tokens, base_url=ns.base_url,
                          omit_temperature=ns.omit_temperature, extra_body=ns.extra_body, no_think=ns.no_think,
                          timeout=600.0)
    return be, ns


def run(std: str, pin_name: str = DEFAULT_PIN, pins_path: str | None = None, backend=None, ns=None,
        use_graph_loader: bool = True) -> dict:
    prompt = build_prompt(std)
    fz = verify_freeze(std, prompt, pin_name, pins_path)
    odir = out_dir(std)
    if os.path.exists(os.path.join(odir, "response.txt")):
        raise DraftError(f"{odir}/response.txt exists: there is one pass per standard")
    if backend is None:
        backend, ns = make_backend_from_pin(pin_name, pins_path)
    if not getattr(backend, "is_llm", True):
        raise DraftError("a mock backend is not accepted for a real draft")
    os.makedirs(odir, exist_ok=True)
    with open(os.path.join(odir, "prompt.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(prompt)
    c = backend.complete(prompt, {})
    with open(os.path.join(odir, "response.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(c.text)
    price_in = getattr(ns, "price_in", None) or 0.0
    price_out = getattr(ns, "price_out", None) or 0.0
    cost = ((c.prompt_tokens or 0) * price_in + (c.completion_tokens or 0) * price_out) / 1e6
    meta = {"standard": std, "pin": pin_name, "pin_sha256": fz["pin_sha256"], "backend": backend.describe(),
            "model": c.model, "provider": c.provider, "response_id": c.response_id,
            "system_fingerprint": c.system_fingerprint, "finish": c.finish,
            "prompt_tokens": c.prompt_tokens, "completion_tokens": c.completion_tokens,
            "latency_s": round(c.latency_s, 2), "cost_usd_estimate": round(cost, 5),
            "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
            "response_sha256": sha256_bytes(c.text.encode("utf-8"))}
    with open(os.path.join(odir, "meta.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
        f.write("\n")
    rec = evaluate(std, c.text, c.finish, odir, use_graph_loader)
    return {"meta": meta, "check": rec}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("prompt", "run", "check"):
        p = sub.add_parser(name)
        p.add_argument("--standard", required=True, choices=sorted(SUBJECTS))
        if name == "run":
            p.add_argument("--pin", default=DEFAULT_PIN)
            p.add_argument("--pins", default=None)
    fz = sub.add_parser("freeze")
    fz.add_argument("--pin", default=DEFAULT_PIN)
    fz.add_argument("--pins", default=None)
    fz.add_argument("--force", action="store_true", help="overwrite an existing freeze file")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "prompt":
            p = build_prompt(a.standard)
            sys.stdout.write(p)
            sys.stderr.write(f"\n[{len(p)} characters; about {len(p) // 4} tokens; sha256 {sha256_bytes(p.encode('utf-8'))}]\n")
        elif a.cmd == "freeze":
            if os.path.exists(FREEZE) and not a.force:
                raise DraftError(f"{FREEZE} exists; the freeze is not overwritten without --force")
            rec = freeze_record(a.pin, a.pins)
            with open(FREEZE, "w", encoding="utf-8", newline="\n") as f:
                json.dump(rec, f, indent=2, ensure_ascii=False)
                f.write("\n")
            print(json.dumps(rec, indent=2))
        elif a.cmd == "run":
            r = run(a.standard, a.pin, a.pins)
            m, c = r["meta"], r["check"]
            print(f"{a.standard}: finish={m['finish']} tokens in/out={m['prompt_tokens']}/{m['completion_tokens']} "
                  f"cost~${m['cost_usd_estimate']} accepted={c['accepted']}")
            print("checks:", json.dumps(c["checks"]))
            if c.get("schema_findings"):
                print(f"{len(c['schema_findings'])} schema findings (see check.json)")
            if not c["accepted"]:
                print("REJECTED:", c.get("rejected_because"))
        elif a.cmd == "check":
            odir = out_dir(a.standard)
            with open(os.path.join(odir, "response.txt"), "r", encoding="utf-8") as f:
                txt = f.read()
            with open(os.path.join(odir, "meta.json"), "r", encoding="utf-8") as f:
                meta = json.load(f)
            rec = evaluate(a.standard, txt, meta["finish"], odir)
            print(json.dumps(rec, indent=2))
    except (DraftError, llm.LLMError, pins.PinError) as e:
        sys.stderr.write(f"error: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
