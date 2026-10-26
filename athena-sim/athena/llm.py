"""LLM back-ends.  Backend spec strings (used by --backend):

  openai:<model>      any OpenAI-compatible /chat/completions endpoint: OpenAI (e.g. openai:o3-mini),
                      OpenRouter, or a local llama-server (set OPENAI_BASE_URL, e.g. http://localhost:8080/v1)
  gemini:<model>      Google Gemini REST API (GEMINI_API_KEY)
  mock:oracle         NOT an LLM. Returns the ground truth (upper bound: proves the harness scores correctly)
  mock:echo           NOT an LLM. Returns the input unchanged (lower bound: "Athena did nothing")
  mock:autofix        NOT an LLM. Deterministic rule-based fixer (linter-autofix-style baseline for RQ4)
  replay:<file.jsonl> replays answers produced elsewhere (e.g. pasted from Cursor / Copilot); see `prompts --export`

Only the standard library is used (urllib), so nothing needs to be installed.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class Completion:
    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_s: float = 0.0
    model: str = ""
    finish: str = ""
    response_id: str = ""          # id of the response (OpenRouter: generation id, usable with /api/v1/generation)
    provider: str = ""             # serving provider when the endpoint reports it (OpenRouter does)
    system_fingerprint: str = ""   # backend configuration fingerprint when the provider reports one


class LLMError(Exception):
    pass


class Backend:
    spec = ""
    is_llm = True

    def complete(self, prompt: str, ctx: dict) -> Completion:  # pragma: no cover - interface
        raise NotImplementedError

    def describe(self) -> dict:
        return {"spec": self.spec, "is_llm": self.is_llm}


# ------------------------------------------------------------------ HTTP helper with retry
DEFAULT_USER_AGENT = "athena-sim"


def _user_agent() -> str:
    """User-Agent sent with every request.  Some gateways reject the default Python-urllib agent (HTTP 403);
    ATHENA_USER_AGENT overrides the default.  It is a transport detail and does not change the prompt."""
    return os.environ.get("ATHENA_USER_AGENT") or DEFAULT_USER_AGENT


def _post_json(url: str, payload: dict, headers: dict, timeout: float, retries: int) -> dict:
    data = json.dumps(payload).encode("utf-8")
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json", "User-Agent": _user_agent(), **headers})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:500]
            last = f"HTTP {e.code}: {body}"
            if e.code in (408, 409, 425, 429) or e.code >= 500:
                wait = min(60.0, 2.0 ** attempt)
                ra = e.headers.get("Retry-After") if e.headers else None
                if ra and ra.replace(".", "", 1).isdigit():
                    wait = min(120.0, float(ra))
                time.sleep(wait)
                continue
            raise LLMError(last)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = f"network error: {e}"
            time.sleep(min(60.0, 2.0 ** attempt))
    raise LLMError(f"giving up after {retries + 1} attempts; last error: {last}")


# ------------------------------------------------------------------ OpenAI-compatible
def is_reasoning_model(model: str) -> bool:
    return bool(re.match(r"^(o\d|gpt-5)", model.split("/")[-1]))


class OpenAIChat(Backend):
    def __init__(self, model, base_url=None, api_key_env="OPENAI_API_KEY", temperature=0.2, max_tokens=None,
                 reasoning_effort=None, timeout=180.0, retries=5, omit_temperature=False, extra_body=None,
                 no_think=False):
        self.model = model
        # omit_temperature: send no temperature (vendor default), e.g. for models whose endpoints do not accept one
        # extra_body: merged into the request last, e.g. OpenRouter {"provider": {...}, "reasoning": {...}}
        # no_think: chat_template_kwargs.enable_thinking = false (llama-server / vLLM serving a thinking model)
        self.omit_temperature, self.no_think = bool(omit_temperature), bool(no_think)
        self.extra_body = dict(extra_body or {})
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.key = os.environ.get(api_key_env, "")
        if not self.key and "api.openai.com" in self.base_url:
            raise LLMError(f"environment variable {api_key_env} is not set (needed for {self.base_url})")
        self.reasoning = is_reasoning_model(model)
        self.temperature, self.reasoning_effort = temperature, reasoning_effort
        self.max_tokens = max_tokens or (8192 if self.reasoning else 2048)
        self.timeout, self.retries = timeout, retries
        self.spec = f"openai:{model}"

    def describe(self):
        d = super().describe()
        d.update(model=self.model, base_url=self.base_url, reasoning_model=self.reasoning,
                 temperature=None if (self.reasoning or self.omit_temperature) else self.temperature,
                 max_tokens=self.max_tokens, reasoning_effort=self.reasoning_effort if self.reasoning else None)
        if self.omit_temperature:
            d["omit_temperature"] = True
        if self.no_think:
            d["no_think"] = True
        if self.extra_body:
            d["extra_body"] = self.extra_body
        return d

    def complete(self, prompt, ctx):
        p = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        if self.reasoning:                       # o1/o3/o4/gpt-5: no temperature, tokens include hidden reasoning
            p["max_completion_tokens"] = self.max_tokens
            if self.reasoning_effort:
                p["reasoning_effort"] = self.reasoning_effort
        else:
            p["max_tokens"] = self.max_tokens
            if not self.omit_temperature:
                p["temperature"] = self.temperature
        if self.no_think:
            p["chat_template_kwargs"] = {"enable_thinking": False}
        p.update(self.extra_body)
        headers = {"Authorization": f"Bearer {self.key}"} if self.key else {}
        t0 = time.time()
        r = _post_json(self.base_url + "/chat/completions", p, headers, self.timeout, self.retries)
        dt = time.time() - t0
        try:
            choice = r["choices"][0]
            text = choice["message"].get("content") or ""
        except (KeyError, IndexError, TypeError):
            raise LLMError(f"unexpected response shape: {str(r)[:300]}")
        u = r.get("usage") or {}
        return Completion(text, u.get("prompt_tokens"), u.get("completion_tokens"), dt,
                          r.get("model", self.model), choice.get("finish_reason") or "",
                          response_id=str(r.get("id") or ""), provider=str(r.get("provider") or ""),
                          system_fingerprint=str(r.get("system_fingerprint") or ""))


# ------------------------------------------------------------------ Gemini
class GeminiChat(Backend):
    def __init__(self, model, temperature=0.2, max_tokens=None, timeout=180.0, retries=5, api_key_env="GEMINI_API_KEY"):
        self.model = model
        self.base_url = (os.environ.get("GEMINI_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self.key = os.environ.get(api_key_env, "")
        if not self.key:
            raise LLMError(f"environment variable {api_key_env} is not set")
        self.temperature, self.max_tokens = temperature, max_tokens or 4096
        self.timeout, self.retries = timeout, retries
        self.spec = f"gemini:{model}"

    def describe(self):
        d = super().describe()
        d.update(model=self.model, temperature=self.temperature, max_tokens=self.max_tokens)
        return d

    def complete(self, prompt, ctx):
        p = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
             "generationConfig": {"temperature": self.temperature, "maxOutputTokens": self.max_tokens}}
        t0 = time.time()
        r = _post_json(f"{self.base_url}/models/{self.model}:generateContent", p,
                       {"x-goog-api-key": self.key}, self.timeout, self.retries)
        dt = time.time() - t0
        try:
            cand = r["candidates"][0]
            text = "".join(part.get("text", "") for part in cand["content"]["parts"])
        except (KeyError, IndexError, TypeError):
            raise LLMError(f"unexpected response shape: {str(r)[:300]}")
        u = r.get("usageMetadata") or {}
        out_tokens = (u.get("candidatesTokenCount") or 0) + (u.get("thoughtsTokenCount") or 0)
        return Completion(text, u.get("promptTokenCount"), out_tokens or None, dt, self.model,
                          cand.get("finishReason", ""))


# ------------------------------------------------------------------ mock / non-LLM solvers
def _split_words(name: str) -> list:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    return [w for w in re.split(r"[^A-Za-z0-9]+", s) if w]


def apply_casing(words: list, casing: str) -> str | None:
    lw = [w.lower() for w in words]
    if casing == "snake_case":
        return "_".join(lw)
    if casing in ("UPPER_SNAKE_CASE", "CONSTANT_CASE"):
        return "_".join(w.upper() for w in lw)
    if casing == "PascalCase":
        return "".join(w.capitalize() for w in lw)
    if casing in ("camelCase", "lowerCamelCase"):
        return lw[0] + "".join(w.capitalize() for w in lw[1:])
    if casing == "lowercase":
        return "".join(lw)
    if casing == "kebab-case":
        return "-".join(lw)
    return None


def autofix_name(injected: str, rule: dict) -> str:
    """What a linter --fix could do from the rule alone: recase, add a literal prefix/suffix. It cannot
    infer data types, so rules that need semantics (e.g. GSCS type prefixes) are left unfixed."""
    name = injected
    if rule.get("casing"):
        fixed = apply_casing(_split_words(name), rule["casing"])
        if fixed:
            name = fixed
    pre, suf = rule.get("prefix"), rule.get("suffix")
    if pre and "/" not in pre and not name.startswith(pre):
        name = pre + name
    if suf and not name.endswith(suf):
        name = name + suf
    return name


def _completion_text(task: str, reasoning: str, data: dict) -> str:
    return f"Reasoning: {reasoning}\nFINAL ANSWER:\n```json\n{json.dumps(data, ensure_ascii=False)}\n```"


class MockBackend(Backend):
    is_llm = False

    def __init__(self, mode):
        if mode not in ("oracle", "echo", "autofix"):
            raise LLMError("mock mode must be oracle, echo or autofix")
        self.mode, self.spec = mode, f"mock:{mode}"

    def describe(self):
        return {"spec": self.spec, "is_llm": False,
                "note": "deterministic stand-in, not a language model; results are not LLM results"}

    def complete(self, prompt, ctx):
        unit, pack, task = ctx["unit"], ctx["pack"], ctx["task"]
        if task == "rename":
            if self.mode == "oracle":
                name, why = unit.original, "ground truth"
            elif self.mode == "echo":
                name, why = unit.injected, "unchanged"
            else:
                name, why = autofix_name(unit.injected, pack.ontology.rule(unit.rule_id)), "rule-based recasing"
            data = {"original_name": unit.injected, "suggested_name": name, "rule_ids_applied": [unit.rule_id],
                    "reasoning": f"mock:{self.mode} ({why})"}
        else:
            if self.mode == "oracle":
                text = unit.reference_comment
            elif self.mode == "echo":
                text = "// TODO: document"
            else:  # template filler: every required label, empty
                rules = pack.ontology.rules_for(unit.language, unit.kind, types=("CommentRule",))
                labels = next((r["requiredLabels"] for r in rules if r.get("requiredLabels")), [])
                text = "/*\n" + "\n".join(f"{lb}:" for lb in labels) + "\n*/" if labels else "// TODO"
            data = {"comment": text, "format": "block", "rule_ids_applied": unit.rule_ids,
                    "reasoning": f"mock:{self.mode}"}
        return Completion(_completion_text(task, f"mock:{self.mode}", data), 0, 0, 0.0, f"mock:{self.mode}", "stop")


class ReplayBackend(Backend):
    """Answers come from a JSONL file: {"unit_id":..., "condition":..., "response":"..."} per line."""
    is_llm = True

    def __init__(self, path):
        self.spec = f"replay:{os.path.basename(path)}"
        self.path = path
        self.table = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    self.table[(r["unit_id"], r.get("condition", "*"))] = r["response"]

    def describe(self):
        return {"spec": self.spec, "is_llm": True, "note": "answers replayed from a file produced outside the harness"}

    def complete(self, prompt, ctx):
        key = (ctx["unit"].unit_id, ctx["condition"])
        text = self.table.get(key) or self.table.get((ctx["unit"].unit_id, "*"))
        if text is None:
            raise LLMError(f"no replay answer for {key}")
        return Completion(text, None, None, 0.0, self.spec, "stop")


def make_backend(spec: str, *, temperature=0.2, max_tokens=None, reasoning_effort=None, timeout=180.0,
                 retries=5, base_url=None, omit_temperature=False, extra_body=None, no_think=False) -> Backend:
    kind, _, rest = spec.partition(":")
    if kind == "openai" and rest:
        return OpenAIChat(rest, base_url=base_url, temperature=temperature, max_tokens=max_tokens,
                          reasoning_effort=reasoning_effort, timeout=timeout, retries=retries,
                          omit_temperature=omit_temperature, extra_body=extra_body, no_think=no_think)
    if kind != "openai" and (omit_temperature or extra_body or no_think):
        raise LLMError("--omit-temperature, --extra-body and --no-think apply to openai:<model> backends only")
    if kind == "gemini" and rest:
        return GeminiChat(rest, temperature=temperature, max_tokens=max_tokens, timeout=timeout, retries=retries)
    if kind == "mock" and rest:
        return MockBackend(rest)
    if kind == "replay" and rest:
        return ReplayBackend(rest)
    raise LLMError(f"bad --backend {spec!r}; use openai:<model>, gemini:<model>, mock:oracle|echo|autofix or replay:<file>")
