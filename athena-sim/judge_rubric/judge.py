"""Rate each item in items.jsonl with one LLM judge (see ADDENDUM.md). Standard library only.
Resumable: items already rated OK in the output file are skipped.

  python judge.py --judge museglimmer --limit 10        # quick check (prints cost)
  python judge.py --judge museglimmer --workers 6       # all items
OpenRouter judges read the API key from the environment variable OPENROUTER_API_KEY.
"""
import argparse, hashlib, json, os, re, sys, threading, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CRITERIA = ["accuracy", "completeness", "clarity", "conformance"]

PROMPT = """You are an expert code reviewer. Rate the documentation comment below, written for one code element, \
against the rubric. The code is the ground truth; judge only the comment.

LANGUAGE: {language}
CODE ELEMENT: {kind} `{name}`

APPLICABLE COMMENT RULES (from the team's coding standard):
{rules}

CODE (the element this comment documents; for Python the comment is its docstring):
```{language}
{code}
```

COMMENT TO RATE:
```
{comment}
```

RUBRIC - give each criterion an integer from 1 to 5:
1. accuracy - Is everything the comment says true of this code?
   5 fully accurate; 4 accurate with a trivial imprecision; 3 one noticeable inaccuracy or a vague claim;
   2 several inaccuracies; 1 mostly wrong, describes other behaviour, or invents parameters, return values or exceptions.
2. completeness - Does it cover what a reader needs and what the rules require: purpose, each parameter,
   the return value, exceptions the code throws?
   5 everything present; 4 one minor item missing; 3 an important item missing; 2 most items missing;
   1 essentially no useful content (for example an empty template).
3. clarity - Is it concise, readable and informative, rather than repeating the code or the name?
   5 clear and informative; 4 clear but slightly wordy or generic; 3 understandable but vague, wordy or tautological;
   2 hard to follow; 1 confusing or unreadable.
4. conformance - Does it follow the applicable rules beyond syntax: required elements or labels present AND filled
   with meaningful content, and the required comment style? Labels whose content cannot be known from the code
   (author, dates, revision history) may hold placeholders without penalty.
   5 fully conforms; 4 one minor deviation; 3 partly conforms; 2 mostly does not conform; 1 ignores the rules.
If the comment is empty or is not a comment, give 1 for every criterion.

Answer with ONE JSON object and nothing else:
{{"justification": "<one or two sentences>", "accuracy": <1-5>, "completeness": <1-5>, "clarity": <1-5>, "conformance": <1-5>}}"""

SCHEMA = {"type": "object", "required": ["justification"] + CRITERIA,
          "properties": dict({"justification": {"type": "string"}},
                             **{c: {"type": "integer", "minimum": 1, "maximum": 5} for c in CRITERIA})}


def render_rules(rules):
    out = []
    for r in rules:
        s = f"- [{r['id']}] {r.get('description', '').strip()}"
        if r.get("required_elements"): s += "\n  Required elements: " + ", ".join(r["required_elements"])
        if r.get("required_labels"): s += "\n  Required labels: " + ", ".join(r["required_labels"])
        if r.get("optional_labels"): s += "\n  Labels that may stay empty: " + ", ".join(r["optional_labels"])
        out.append(s)
    return "\n".join(out) or "- (none listed)"


def build_prompt(item):
    return PROMPT.format(language=item["language"], kind=item["kind"], name=item["name"],
                         rules=render_rules(item["rules"]), code=item["code"], comment=item["comment"])


# strict schema for OpenAI-style structured outputs (enum instead of min/max for wider provider support)
STRICT_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["justification"] + CRITERIA,
                 "properties": dict({"justification": {"type": "string"}},
                                    **{c: {"type": "integer", "enum": [1, 2, 3, 4, 5]} for c in CRITERIA})}
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def messages(cfg, prompt):
    m = [{"role": "system", "content": cfg["system"]}] if cfg.get("system") else []
    return m + [{"role": "user", "content": prompt}]


def post(url, body, timeout=600, headers=None):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def post_retry(url, body, headers=None, tries=5):
    """Retries rate limits, server errors and network errors with backoff; other HTTP errors are raised."""
    for k in range(tries):
        try:
            r = post(url, body, headers=headers)
            if isinstance(r, dict) and r.get("error") and not r.get("choices"):
                code = r["error"].get("code", 0) if isinstance(r["error"], dict) else 0
                if code in (429, 500, 502, 503, 504) and k < tries - 1:
                    time.sleep(2 ** (k + 1)); continue
                raise RuntimeError(f"API error: {json.dumps(r['error'])[:300]}")
            return r
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")
            if e.code in (408, 429, 500, 502, 503, 504) and k < tries - 1:
                time.sleep(2 ** (k + 1)); continue
            raise RuntimeError(f"HTTP {e.code}: {msg[:300]}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if k < tries - 1:
                time.sleep(2 ** (k + 1)); continue
            raise RuntimeError(f"network: {e}")


def call(cfg, prompt, state):
    """Returns dict(text, prompt_tokens, output_tokens, finish, cost, provider, served_model)."""
    be = cfg["backend"]
    if be == "mock":
        h = int(hashlib.sha256(prompt.encode()).hexdigest(), 16)
        sc = {c: 1 + (h >> (8 * i)) % 5 for i, c in enumerate(CRITERIA)}
        return dict(text=json.dumps(dict(justification="mock", **sc)), prompt_tokens=len(prompt) // 4, output_tokens=20,
                    finish="stop", cost=0.0, provider="mock", served_model="mock")
    opts = cfg.get("options", {})
    if be == "openrouter":
        key = os.environ.get(cfg.get("api_key_env", "OPENROUTER_API_KEY"), "").strip()
        if not key:
            raise SystemExit("Set the OPENROUTER_API_KEY environment variable first.")
        body = {"model": cfg["model"], "messages": messages(cfg, prompt), "temperature": opts.get("temperature", 0),
                "max_tokens": cfg.get("max_tokens", opts.get("num_predict", 400)), "usage": {"include": True}}
        if cfg.get("send_seed", True):
            body["seed"] = opts.get("seed", 0)
        fmt = state.get("format", cfg.get("structured", "json_schema"))
        if fmt == "json_schema":
            body["response_format"] = {"type": "json_schema",
                                       "json_schema": {"name": "rubric_scores", "strict": True, "schema": STRICT_SCHEMA}}
        elif fmt == "json_object":
            body["response_format"] = {"type": "json_object"}
        body.update(cfg.get("extra_body", {}))
        hdr = {"Authorization": f"Bearer {key}", "X-Title": "athena-rubric-judge"}
        try:
            r = post_retry(OPENROUTER_URL, body, headers=hdr)
        except RuntimeError as e:
            low = str(e).lower()
            if fmt == "json_schema" and ("response_format" in low or "schema" in low or "structured" in low):
                state["format"] = "json_object"; body["response_format"] = {"type": "json_object"}
                r = post_retry(OPENROUTER_URL, body, headers=hdr)
            else:
                raise
        u = r.get("usage") or {}
        ch = r["choices"][0]
        return dict(text=ch["message"].get("content") or "", prompt_tokens=u.get("prompt_tokens"),
                    output_tokens=u.get("completion_tokens"), finish=ch.get("finish_reason"), cost=u.get("cost"),
                    provider=r.get("provider"), served_model=r.get("model"))
    if be == "ollama":
        body = {"model": cfg["model"], "messages": messages(cfg, prompt), "stream": False,
                "format": SCHEMA, "options": opts}
        if state.get("think_ok", True) and "think" in cfg: body["think"] = cfg["think"]
        url = cfg["base_url"].rstrip("/") + "/api/chat"
        try:
            r = post(url, body)
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")
            if "think" in msg.lower() and "think" in body:
                state["think_ok"] = False; body.pop("think")
                r = post(url, body)
            else:
                raise RuntimeError(f"HTTP {e.code}: {msg[:300]}")
        return dict(text=r["message"].get("content", ""), prompt_tokens=r.get("prompt_eval_count"),
                    output_tokens=r.get("eval_count"), finish=r.get("done_reason"), cost=None, provider="ollama",
                    served_model=cfg["model"])
    body = {"model": cfg["model"], "messages": messages(cfg, prompt), "temperature": opts.get("temperature", 0),
            "seed": opts.get("seed", 0), "max_tokens": opts.get("num_predict", 400),
            "response_format": {"type": "json_object"}}
    body.update(cfg.get("extra_body", {}))
    r = post(cfg["base_url"].rstrip("/") + "/v1/chat/completions", body)
    u = r.get("usage", {})
    return dict(text=r["choices"][0]["message"].get("content", ""), prompt_tokens=u.get("prompt_tokens"),
                output_tokens=u.get("completion_tokens"), finish=r["choices"][0].get("finish_reason"), cost=None,
                provider=None, served_model=r.get("model"))


def parse(text):
    cands = [text] + re.findall(r"\{.*\}", text or "", re.S)
    for c in cands:
        try:
            d = json.loads(c)
        except Exception:
            continue
        if isinstance(d, dict) and all(isinstance(d.get(k), int) and 1 <= d[k] <= 5 for k in CRITERIA):
            return {k: d[k] for k in CRITERIA}, str(d.get("justification", ""))[:500]
    return None, ""


def rate(cfg, judge_key, it, state):
    prompt = build_prompt(it)
    rec = dict(item=it["id"], judge=judge_key, model=cfg["model"])
    s = time.time(); cost = 0.0; res = {}
    for attempt in range(2):
        try:
            res = call(cfg, prompt if attempt == 0 else prompt + "\n\nReturn only the JSON object.", state)
            err = None
        except SystemExit:
            raise
        except Exception as e:
            res, err = {}, f"error: {str(e)[:300]}"
        cost += res.get("cost") or 0.0
        scores, just = parse(res.get("text", ""))
        if scores: break
    rec.update(ok=bool(scores), scores=scores, justification=just,
               raw=None if scores else (res.get("text") or err or "")[:1500],
               prompt_tokens=res.get("prompt_tokens"), output_tokens=res.get("output_tokens"), finish=res.get("finish") or err,
               cost_usd=round(cost, 8), provider=res.get("provider"), served_model=res.get("served_model"),
               attempts=attempt + 1, seconds=round(time.time() - s, 2), ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    if cfg["backend"] == "openrouter":
        rec["format"] = state.get("format", cfg.get("structured", "json_schema"))
    if cfg["backend"] == "ollama":
        rec["think_sent"] = state.get("think_ok", True) and "think" in cfg
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", required=True); ap.add_argument("--config", default=os.path.join(HERE, "judges.json"))
    ap.add_argument("--items", default=os.path.join(HERE, "items.jsonl")); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=1); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    allcfg = json.load(open(a.config, encoding="utf-8"))
    cfg = allcfg[a.judge]
    cfg.setdefault("options", allcfg.get("_defaults", {}).get("options", {}))
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out = a.out or os.path.join(HERE, "results", f"judgments_{a.judge}.jsonl")
    items = [json.loads(l) for l in open(a.items, encoding="utf-8")]
    done, spent = set(), 0.0
    if os.path.exists(out):
        for l in open(out, encoding="utf-8"):
            r = json.loads(l); spent += r.get("cost_usd") or 0.0
            if r.get("ok"): done.add(r["item"])
    todo = [it for it in items if it["id"] not in done]
    if a.limit: todo = todo[:a.limit]
    cap = cfg.get("max_cost_usd")
    info = dict(judge=a.judge, label=cfg.get("label"), backend=cfg["backend"], model=cfg["model"],
                options=cfg.get("options"), max_tokens=cfg.get("max_tokens"), extra_body=cfg.get("extra_body"),
                system=cfg.get("system"), think=cfg.get("think"), started=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    json.dump(info, open(os.path.join(HERE, "results", f"judge_{a.judge}_info.json"), "w"), indent=1)
    print(f"judge {a.judge} ({cfg['model']}): {len(items)} items, {len(done)} done, {len(todo)} to rate, "
          f"spent so far ${spent:.3f}" + (f", cap ${cap:.2f}" if cap else ""), flush=True)
    state, lock, t0, n, n_bad = {}, threading.Lock(), time.time(), 0, 0
    w = max(1, a.workers)
    with open(out, "a", encoding="utf-8") as f, ThreadPoolExecutor(w) as ex:
        for i in range(0, len(todo), w * 2):
            if cap and spent >= cap:
                print(f"STOP: cost cap ${cap:.2f} reached (spent ${spent:.3f}). Raise max_cost_usd in judges.json only if intended.", flush=True)
                break
            for rec in ex.map(lambda it: rate(cfg, a.judge, it, state), todo[i:i + w * 2]):
                with lock:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
                    n += 1; n_bad += not rec["ok"]; spent += rec.get("cost_usd") or 0.0
                    if n % 25 == 0 or n == len(todo):
                        el = time.time() - t0
                        print(f"  {n}/{len(todo)}  not ok {n_bad}  spent ${spent:.3f}  {el/n:.2f}s/item  "
                              f"ETA {(len(todo)-n)*el/n/60:.0f} min", flush=True)
    print("finished" if n == len(todo) else "stopped early", out, flush=True)


if __name__ == "__main__":
    main()
