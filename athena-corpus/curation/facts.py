#!/usr/bin/env python3
"""Shared data model for the identifier extractors (Athena Task C curation).

Every extractor (Python `ast`, tree-sitter for Java/C#/TypeScript/JavaScript) turns one
source file into a `FileFacts`: the declared identifiers, every identifier-like token with a
"role", and the candidate snippet ("unit") line ranges. All offsets are BYTE offsets into the
exact source bytes recovered from the corpus file, so they can be used for renaming without
any re-decoding ambiguity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# ns (namespace) decides which tokens are renamed together with a declaration:
#   local  - variable / parameter / local constant     -> decl(local) + plain refs
#   member - field / property / method / enum member   -> decl(member) + member-access tokens (+ plain refs)
#   type   - class / interface / enum / function       -> decl(type) + type-position tokens + plain refs
NS_OF_KIND_DEFAULT = {
    "variable": "local", "parameter": "local", "constant": "local",
    "field": "member", "property": "member", "method": "member", "enum_member": "member",
    "class": "type", "interface": "type", "enum": "type", "function": "type",
    "boolean_variable": "local",
}

# token roles
DECL, REF, MEMBER, TYPE, KEY, KWARG, SHORTHAND, IMPORT, OTHER = (
    "decl", "ref", "member", "type", "key", "kwarg", "shorthand", "import", "other")


@dataclass
class Tok:
    start: int
    end: int
    text: str
    role: str
    node_type: str = ""


@dataclass
class Decl:
    name: str
    kind: Optional[str]          # ontology IdentifierKind id, or None when the kind is not modelled
    start: int                   # byte offset of the name token
    end: int
    ns: str = "local"
    exempt: Optional[str] = None  # reason this declaration is not checked / not used as a target
    extra: dict = field(default_factory=dict)


@dataclass
class UnitCand:
    start_line: int              # 0-based, inclusive
    end_line: int                # 0-based, inclusive
    label: str                   # e.g. "function foo", "method Foo.bar", "class Foo"
    top_level: bool = True


@dataclass
class Span:
    start: int
    end: int


@dataclass
class FileFacts:
    language: str
    src: bytes
    line_starts: list            # byte offset of each line start
    decls: list = field(default_factory=list)
    toks: list = field(default_factory=list)
    units: list = field(default_factory=list)
    comment_spans: list = field(default_factory=list)   # comments / docstrings (byte spans)
    error_spans: list = field(default_factory=list)     # spans containing parse errors
    string_spans: list = field(default_factory=list)    # string-literal text (byte spans)
    fstring_refs: list = field(default_factory=list)    # python: (start, end, {names}) per f-string with expressions
    shape: object = None                                # opaque structural fingerprint of the parse
    parse_ok: bool = True
    skip_reason: Optional[str] = None
    reverify: object = None                             # callable(new_src: bytes) -> fingerprint


def line_starts_of(src: bytes) -> list:
    out = [0]
    for i, b in enumerate(src):
        if b == 10:
            out.append(i + 1)
    return out


def line_of(line_starts: list, offset: int) -> int:
    """0-based line index containing byte `offset`."""
    lo, hi = 0, len(line_starts) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if line_starts[mid] <= offset:
            lo = mid
        else:
            hi = mid - 1
    return lo


def dedent_lines(lines: list) -> list:
    """Remove the common leading-whitespace prefix of all non-blank lines (str lines)."""
    prefix = None
    for ln in lines:
        if not ln.strip():
            continue
        ws = ln[: len(ln) - len(ln.lstrip(" \t"))]
        if prefix is None:
            prefix = ws
        else:
            n = 0
            for a, b in zip(prefix, ws):
                if a != b:
                    break
                n += 1
            prefix = prefix[:n]
    if not prefix:
        return list(lines)
    return [ln[len(prefix):] if ln.startswith(prefix) else ln.lstrip(" \t") for ln in lines]
