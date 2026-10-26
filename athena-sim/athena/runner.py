"""Experiment runner: sample units -> (retrieve -> prompt -> LLM -> parse -> score) -> append to trials.jsonl.

Every trial is one JSON line holding the full prompt, the raw answer, the parse, the metrics, timing and
token counts, so any table or figure can be regenerated later without calling the LLM again.  A run can be
stopped (Ctrl+C) and resumed with the same --run-id; finished trials are skipped, failed ones are retried.
"""
from __future__ import annotations

import datetime
import json
import os
import platform
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import __version__, freeze
from . import embed, pins, pipeline
from .evaluate import grade_comment, grade_rename, parse_completion
from .llm import LLMError, make_backend
from .packs import load_pack, select_split
from .prompts import build_prompt
from .retrieval import CONDITIONS, Retriever


def sample_units(units: list, per_language: int, seed: int) -> list:
    """Deterministic stratified sample: per language, round-robin over identifier kinds (seeded shuffle)."""
    by_lang: dict = {}
    for u in sorted(units, key=lambda u: u.unit_id):
        by_lang.setdefault(u.language, []).append(u)
    rnd, out = random.Random(seed), []
    for lang in sorted(by_lang):
        by_kind: dict = {}
        for u in by_lang[lang]:
            by_kind.setdefault(u.kind, []).append(u)
        for k in sorted(by_kind):
            rnd.shuffle(by_kind[k])
        cap = per_language if per_language > 0 else len(by_lang[lang])
        picked = []
        while len(picked) < cap and any(by_kind.values()):
            for k in sorted(by_kind):
                if by_kind[k] and len(picked) < cap:
                    picked.append(by_kind[k].pop())
        out += picked
    return out


def get_units(pack, args) -> list:
    """Units for this run: split filter first (dev by default), then the seeded stratified sample."""
    languages = [x.strip() for x in args.languages.split(",")] if args.languages else None
    units = pack.rename_units(languages) if args.task == "rename" else pack.comment_units(languages)
    units = sample_units(select_split(units, getattr(args, "split", "dev")), args.per_language, args.seed)
    return units[: args.limit] if args.limit else units


def unit_inputs(task: str, unit):
    if task == "rename":
        return unit.injected, unit.code_violation
    return unit.name, unit.code_bare


def make_prompt(pack, retriever, task, unit, condition, kind=None):
    """Prompt for one unit.  `kind` is the identifier kind to use; the benchmark's own kind (the Vol. 1 oracle)
    when it is not given."""
    kind = kind or unit.kind
    name, code = unit_inputs(task, unit)
    ctx = retriever.context(condition, task=task, standard_id=unit.standard_id, language=unit.language,
                            kind=kind, name=name, code=code)
    prompt = build_prompt(task, language=unit.language, kind=kind, name=name, code=code, context=ctx.text)
    return prompt, ctx


def oracle_free_kind(task, unit, pack=None) -> tuple:
    """(kind to put in the prompt, record fields) when the kind is inferred from the code instead of read from the benchmark.
    With `pack`, the record also says whether the inferred kind is a kind of the ontology that supplies the rules."""
    name, code = unit_inputs(task, unit)
    inf = pipeline.infer(unit.language, code, name)
    fields = {"kind_used": pipeline.kind_for_prompt(inf), "kind_inferred": inf["kind"],
              "kind_status": inf["status"], "kind_alt": inf["alt_kinds"], "kind_ok": inf["kind"] == unit.kind}
    if pack is not None and getattr(pack, "id", "") != "public5":
        onto = getattr(pack, "rules_ontology", pack.ontology)
        fields["kind_in_pack"] = (inf["kind"] in onto.kinds) if inf["kind"] else None
    return pipeline.kind_for_prompt(inf), fields


def trial_key(pack_id, task, unit_id, condition, backend_spec, repeat):
    return f"{pack_id}|{task}|{unit_id}|{condition}|{backend_spec}|{repeat}"


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def run_trial(pack, retriever, backend, task, unit, condition, repeat, run_id, price_in, price_out, store_prompt,
              no_oracle=False):
    key = trial_key(pack.id, task, unit.unit_id, condition, backend.spec, repeat)
    rec = {"key": key, "run_id": run_id, "ts": _now(), "pack": pack.id, "task": task, "unit_id": unit.unit_id,
           "split": unit.split, "snippet_id": unit.snippet_id, "language": unit.language, "standard_id": unit.standard_id,
           "kind": unit.kind, "condition": condition, "backend": backend.spec, "repeat": repeat, "error": None}
    if task == "rename":
        rec.update(rule_id=unit.rule_id, original=unit.original, injected=unit.injected, injection=unit.method)
        if getattr(unit, "file", ""):
            rec["file"] = unit.file
    else:
        rec.update(name=unit.name, rule_ids=unit.rule_ids)
    try:
        kind = None
        if no_oracle:
            kind, fields = oracle_free_kind(task, unit, pack)
            rec.update(fields)
        prompt, ctx = make_prompt(pack, retriever, task, unit, condition, kind)
        meta = dict(ctx.meta)
        if task == "rename" and "retrieved_ids" in meta:
            # did retrieval bring back the violated rule?  (chunks of the gscs pack are whole sections, not rules)
            rule_level = (condition == "graph" and getattr(pack, "rules_comparable", True)) or \
                         (condition in ("chunk", "bm25", "dense") and pack.id == "public5")
            meta["hit"] = (unit.rule_id in meta["retrieved_ids"]) if rule_level else None
        rec["retrieval"] = meta
        rec["prompt_chars"] = len(prompt)
        if store_prompt:
            rec["prompt"] = prompt
        comp = backend.complete(prompt, {"unit": unit, "pack": pack, "task": task, "condition": condition,
                                         "repeat": repeat})
        parsed = parse_completion(task, comp.text)
        metrics = (grade_rename if task == "rename" else grade_comment)(unit, parsed, pack)
        if no_oracle and task == "rename":
            rec["scope"] = pipeline.scope(unit.language, unit.code_violation, unit.injected, metrics.get("suggested"))
        cost = None
        if comp.prompt_tokens is not None and comp.completion_tokens is not None and (price_in or price_out):
            cost = (comp.prompt_tokens * (price_in or 0) + comp.completion_tokens * (price_out or 0)) / 1e6
        rec.update(model=comp.model, prompt_tokens=comp.prompt_tokens, completion_tokens=comp.completion_tokens,
                   latency_s=round(comp.latency_s, 3), finish=comp.finish, cost_usd=cost,
                   raw_response=comp.text, parsed=parsed.data, parse_errors=parsed.errors, metrics=metrics)
        # who actually answered (only recorded when the endpoint reports it)
        for k in ("response_id", "provider", "system_fingerprint"):
            if getattr(comp, k, ""):
                rec[k] = getattr(comp, k)
    except LLMError as e:
        rec["error"] = f"LLMError: {e}"
    except Exception as e:  # a harness bug must not silently look like a model failure
        rec["error"] = f"{type(e).__name__}: {e}"
    return rec


def load_done_keys(path: str) -> set:
    done = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("error") is None:
                    done.add(r["key"])
    return done


def execute(args) -> int:
    pack = load_pack(args.pack, args.corpus, getattr(args, "ontology_variant", "human"))
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    for c in conditions:
        if c not in CONDITIONS:
            print(f"unknown condition {c!r}; choose from {CONDITIONS}", file=sys.stderr)
            return 2
    no_oracle = bool(getattr(args, "no_oracle", False))
    if no_oracle:
        try:
            pipeline.check_pack(pack)
        except pipeline.PipelineError as e:
            print(f"--no-oracle: {e}", file=sys.stderr)
            return 2
    units = get_units(pack, args)
    if not units:
        print(f"pack {pack.id!r} has no {args.task} units in split {args.split!r}"
              + (f" for {args.languages}" if args.languages else ""), file=sys.stderr)
        return 2
    try:
        backend = make_backend(args.backend, temperature=args.temperature, max_tokens=args.max_tokens,
                               reasoning_effort=args.reasoning_effort, timeout=args.timeout, retries=args.retries,
                               base_url=args.base_url, omit_temperature=getattr(args, "omit_temperature", False),
                               extra_body=getattr(args, "extra_body", None), no_think=getattr(args, "no_think", False))
    except LLMError as e:
        print(f"backend error: {e}", file=sys.stderr)
        return 2
    try:
        embedder = embed.from_args(args, "dense" in conditions)
    except (embed.EmbedError, pins.PinError) as e:
        print(f"embedding model error: {e}", file=sys.stderr)
        return 2
    retriever = Retriever(pack, chunk_k=args.chunk_k, top_k=args.top_k, n_examples=args.examples, embedder=embedder)

    run_id = args.run_id or datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{pack.id}-{args.task}-{args.split}"
    run_dir = os.path.join(args.out, run_id)

    # ---- test-split guard: real models (and pasted Cursor/Copilot answers) may touch the test split only from a freeze
    frozen_info, rerun = None, False
    if backend.is_llm and args.split != "dev":
        if args.split == "all":
            print("--split all mixes dev and test; run --split dev or --split test (all is for mock backends only)",
                  file=sys.stderr)
            return 2
        if not args.frozen:
            print("the test split can only be run from a frozen setup. Tune on --split dev, then:\n"
                  "  python athena_sim.py freeze <same options as run> --out frozen.json\n"
                  "  python athena_sim.py run <same options> --split test --frozen frozen.json", file=sys.stderr)
            return 2
        err, rerun = freeze.check_test_run(args.frozen, args, pack, run_id)
        if err:
            print(err, file=sys.stderr)
            return 2
        frozen_info = {"file": os.path.basename(args.frozen), "sha256": freeze._sha_file(args.frozen), "rerun": rerun}
        freeze.append_ledger(args.frozen, run_id=run_id, event="start", backend=backend.spec, rerun=rerun,
                             trials=len(units) * len(conditions) * args.repeats)
    os.makedirs(run_dir, exist_ok=True)
    trials_path = os.path.join(run_dir, "trials.jsonl")
    done = load_done_keys(trials_path)

    todo = []
    for r in range(args.repeats):
        for u in units:
            for c in conditions:
                if trial_key(pack.id, args.task, u.unit_id, c, backend.spec, r) not in done:
                    todo.append((u, c, r))
    total = len(units) * len(conditions) * args.repeats
    print(f"run {run_id}: pack={pack.id} task={args.task} backend={backend.spec} units={len(units)} "
          f"conditions={conditions} repeats={args.repeats} -> {total} trials ({total - len(todo)} already done)")

    for c in conditions:                       # warm the lexical indexes before threads start
        if c in ("chunk", "bm25", "dense"):
            for sid in {u.standard_id for u in units}:
                retriever.index(c, sid)

    cfg_path = os.path.join(run_dir, "config.json")
    cfg = {"run_id": run_id, "harness_version": __version__, "status": "running", "started": _now(),
           "python": sys.version.split()[0], "platform": platform.platform(), "args": vars(args),
           "backend": backend.describe(), "pack": pack.fingerprint(), "conditions": conditions,
           "embedding": embedder.describe() if embedder else None,
           "split": args.split, "frozen": frozen_info,
           "oracle_free": ({"pipeline_version": pipeline.VERSION, "curation_sha256": pipeline.curation_fingerprint()}
                           if no_oracle else None),
           "n_units": len(units), "unit_ids": [u.unit_id for u in units]}
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False, default=str)

    t0, n_ok, n_err, consec, status = time.time(), 0, 0, 0, "complete"
    try:
        with open(trials_path, "a", encoding="utf-8") as out, ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
            futs = [ex.submit(run_trial, pack, retriever, backend, args.task, u, c, r, run_id,
                              args.price_in, args.price_out, not args.no_store_prompt, no_oracle)
                    for (u, c, r) in todo]
            for i, fut in enumerate(as_completed(futs), 1):
                rec = fut.result()
                out.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
                out.flush()
                if rec["error"]:
                    n_err, consec = n_err + 1, consec + 1
                    print(f"  ! {rec['key']}: {rec['error'][:200]}", file=sys.stderr)
                    if consec >= args.max_errors:
                        status = "aborted (too many consecutive errors)"
                        for f2 in futs:
                            f2.cancel()
                        break
                else:
                    n_ok, consec = n_ok + 1, 0
                if i % max(1, args.progress) == 0 or i == len(todo):
                    el = time.time() - t0
                    eta = el / i * (len(todo) - i)
                    print(f"  {i}/{len(todo)} done ({n_err} errors)  {el:.0f}s elapsed, ~{eta:.0f}s left")
    except KeyboardInterrupt:
        status = "interrupted (resume with --run-id " + run_id + ")"
        print("\ninterrupted - progress is saved; rerun with the same --run-id to continue", file=sys.stderr)

    cfg.update(status=status, finished=_now(), trials_ok=n_ok, trials_error=n_err)
    if frozen_info:
        freeze.append_ledger(args.frozen, run_id=run_id, event="end", status=status, trials_ok=n_ok, trials_error=n_err)
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False, default=str)
    from .report import write_reports
    write_reports(run_dir)
    print(f"run {run_id}: {status}. results in {run_dir}")
    return 0 if status == "complete" else 1


def export_prompts(args) -> int:
    """Write every prompt (units x conditions) to a JSONL so it can be pasted into Cursor / Copilot / a chat UI;
    bring the answers back with --backend replay:<file>."""
    pack = load_pack(args.pack, args.corpus, getattr(args, "ontology_variant", "human"))
    units = get_units(pack, args)
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    try:
        embedder = embed.from_args(args, "dense" in conditions)
    except (embed.EmbedError, pins.PinError) as e:
        print(f"embedding model error: {e}", file=sys.stderr)
        return 2
    retriever = Retriever(pack, chunk_k=args.chunk_k, top_k=args.top_k, n_examples=args.examples, embedder=embedder)
    path = args.export
    no_oracle = bool(getattr(args, "no_oracle", False))
    if no_oracle:
        try:
            pipeline.check_pack(pack)
        except pipeline.PipelineError as e:
            print(f"--no-oracle: {e}", file=sys.stderr)
            return 2
    with open(path, "w", encoding="utf-8") as f:
        for u in units:
            for c in conditions:
                kind = oracle_free_kind(args.task, u, pack)[0] if no_oracle else None
                prompt, _ = make_prompt(pack, retriever, args.task, u, c, kind)
                f.write(json.dumps({"unit_id": u.unit_id, "condition": c, "prompt": prompt,
                                    "response": ""}, ensure_ascii=False) + "\n")
    print(f"wrote {len(units) * len(conditions)} prompts to {path} (fill the 'response' field, then run with "
          f"--backend replay:{path})")
    return 0


def freeze_cmd(args) -> int:
    """Write the fingerprint of the setup that will be used for the test split."""
    pack = load_pack(args.pack, args.corpus, getattr(args, "ontology_variant", "human"))
    args.split = "test"
    units = get_units(pack, args)
    if not units:
        print("no test units for these options", file=sys.stderr)
        return 2
    if not os.path.exists(freeze.HYPOTHESES):
        print("warning: HYPOTHESES.md not found - write and keep it before freezing", file=sys.stderr)
    try:           # records the hash of the embedding pin in the args, so that it is part of the freeze
        embed.from_args(args, "dense" in [c.strip() for c in args.conditions.split(",")])
    except (embed.EmbedError, pins.PinError) as e:
        print(f"embedding model error: {e}", file=sys.stderr)
        return 2
    fp = freeze.write_frozen(args.out_file, args, pack, args.note or "")
    print(f"frozen setup written to {args.out_file}\n"
          f"  test units: {len(units)}  conditions: {fp['settings']['conditions']}  backend: {fp['settings']['backend']}\n"
          f"  code hash: {fp['code_sha256']['ALL'][:12]}  hypotheses hash: {(fp['hypotheses_sha256'] or 'none')[:12]}\n"
          f"Now run the test split ONCE:\n  python athena_sim.py run <same options> --split test --frozen {args.out_file}")
    return 0
