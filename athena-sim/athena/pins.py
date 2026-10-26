"""Model pins: one named entry per model of the panel, so every run of a model uses the same request.

The pin file (default ../models/model_pins.json) holds, per entry, the backend spec, the endpoint, the sampling
settings and any extra request body (e.g. an OpenRouter provider lock).  `--model-pin NAME` expands an entry into the
run options; the entry's SHA-256 is recorded in the run config and in a freeze, so a test run can only start with
the pin that was frozen.
"""
from __future__ import annotations

import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PINS = os.path.normpath(os.path.join(ROOT, "..", "models", "model_pins.json"))

# entry field -> argparse attribute (applied when present in the entry)
_FIELDS = {"backend": "backend", "base_url": "base_url", "temperature": "temperature", "max_tokens": "max_tokens",
           "omit_temperature": "omit_temperature", "no_think": "no_think", "extra_body": "extra_body",
           "price_in": "price_in", "price_out": "price_out"}


class PinError(ValueError):
    pass


def load_pins(path: str | None = None) -> dict:
    path = path or DEFAULT_PINS
    if not os.path.exists(path):
        raise PinError(f"pin file {path} not found")
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    if not isinstance(d.get("models"), dict):
        raise PinError(f"{path}: expected an object with a 'models' mapping")
    return d


def entry_sha256(entry: dict) -> str:
    return hashlib.sha256(json.dumps(entry, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def resolve_backend_args(args) -> None:
    """Fill args from --model-pin, parse --extra-body, and check that a backend is given exactly once."""
    if isinstance(getattr(args, "extra_body", None), str):
        try:
            args.extra_body = json.loads(args.extra_body)
        except json.JSONDecodeError as e:
            raise PinError(f"--extra-body is not valid JSON: {e}") from e
        if not isinstance(args.extra_body, dict):
            raise PinError("--extra-body must be a JSON object")
    name = getattr(args, "model_pin", None)
    if name:
        _apply_pin(args, name)
    elif not getattr(args, "backend", None):
        raise PinError("give --backend or --model-pin")
    if getattr(args, "omit_temperature", False):
        args.temperature = None          # not sent, so not recorded as if it were


def _apply_pin(args, name: str) -> None:
    if getattr(args, "backend", None):
        raise PinError("give either --backend or --model-pin, not both")
    pins = load_pins(getattr(args, "pins", None))
    entry = pins["models"].get(name)
    if entry is None:
        raise PinError(f"no entry {name!r}; available: {', '.join(sorted(pins['models']))}")
    request = entry.get("request")
    if not isinstance(request, dict) or not request.get("backend"):
        raise PinError(f"entry {name!r} has no request.backend")
    if entry.get("status") == "incomplete":
        raise PinError(f"entry {name!r} is marked incomplete: {entry.get('missing', 'see the pin file')}")
    for field, attr in _FIELDS.items():
        if field in request:
            setattr(args, attr, request[field])
    args.model_pin_sha256 = entry_sha256(entry)
