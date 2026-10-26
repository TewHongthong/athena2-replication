#!/usr/bin/env python3
"""Minimal ctypes binding to the tree-sitter C runtime (standard library only).

Why this exists: the session that built the benchmark had no access to PyPI/npm, so
`pip install tree-sitter tree-sitter-java ...` was not possible. The tree-sitter runtime
and the grammar repositories were instead cloned from GitHub and compiled into a single
shared library (see tools/build_treesitter.sh); this module loads that library and
exposes each parse tree as plain Python objects (`Node`).

Languages: java, csharp, typescript, tsx, javascript (Vol. 1) and cpp (Vol. 2).
Only the handful of C functions needed for read-only tree walking are bound.
"""
from __future__ import annotations

import ctypes as C
import os

LANG_SYMBOLS = {
    "java": "tree_sitter_java",
    "csharp": "tree_sitter_c_sharp",
    "typescript": "tree_sitter_typescript",
    "tsx": "tree_sitter_tsx",
    "javascript": "tree_sitter_javascript",
    "cpp": "tree_sitter_cpp",   # Athena Vol. 2
}


class _TSNode(C.Structure):
    _fields_ = [("context", C.c_uint32 * 4), ("id", C.c_void_p), ("tree", C.c_void_p)]


class Node:
    """A materialised parse-tree node. Offsets are BYTE offsets into the UTF-8 source."""

    __slots__ = ("type", "named", "start", "end", "field", "parent", "children", "is_error", "is_missing")

    def __init__(self, type_, named, start, end, field, parent):
        self.type = type_
        self.named = named
        self.start = start
        self.end = end
        self.field = field
        self.parent = parent
        self.children: list[Node] = []
        self.is_error = False
        self.is_missing = False

    def child(self, field: str):
        for c in self.children:
            if c.field == field:
                return c
        return None

    def children_of(self, field: str):
        return [c for c in self.children if c.field == field]

    def named_children(self):
        return [c for c in self.children if c.named]

    def text(self, src: bytes) -> str:
        return src[self.start:self.end].decode("utf-8", errors="replace")

    def walk(self):
        stack = [self]
        while stack:
            n = stack.pop()
            yield n
            stack.extend(reversed(n.children))

    def __repr__(self):  # pragma: no cover - debugging aid
        return f"<{self.type} {self.start}-{self.end}>"


class TreeSitter:
    def __init__(self, libpath: str):
        self.lib = C.CDLL(libpath)
        L = self.lib
        L.ts_parser_new.restype = C.c_void_p
        L.ts_parser_set_language.argtypes = [C.c_void_p, C.c_void_p]
        L.ts_parser_set_language.restype = C.c_bool
        L.ts_parser_parse_string.argtypes = [C.c_void_p, C.c_void_p, C.c_char_p, C.c_uint32]
        L.ts_parser_parse_string.restype = C.c_void_p
        L.ts_tree_root_node.argtypes = [C.c_void_p]
        L.ts_tree_root_node.restype = _TSNode
        L.ts_tree_delete.argtypes = [C.c_void_p]
        for fn, res in [("ts_node_start_byte", C.c_uint32), ("ts_node_end_byte", C.c_uint32),
                        ("ts_node_child_count", C.c_uint32), ("ts_node_is_named", C.c_bool),
                        ("ts_node_is_error", C.c_bool), ("ts_node_is_missing", C.c_bool),
                        ("ts_node_has_error", C.c_bool), ("ts_node_type", C.c_char_p)]:
            f = getattr(L, fn)
            f.argtypes = [_TSNode]
            f.restype = res
        L.ts_node_child.argtypes = [_TSNode, C.c_uint32]
        L.ts_node_child.restype = _TSNode
        L.ts_node_field_name_for_child.argtypes = [_TSNode, C.c_uint32]
        L.ts_node_field_name_for_child.restype = C.c_char_p
        self.parser = L.ts_parser_new()
        self._langs = {}
        for name, sym in LANG_SYMBOLS.items():
            f = getattr(L, sym)
            f.restype = C.c_void_p
            self._langs[name] = f()

    def parse(self, lang: str, src: bytes):
        """Parse `src` (bytes). Returns (root Node, has_error)."""
        L = self.lib
        if not L.ts_parser_set_language(self.parser, self._langs[lang]):
            raise RuntimeError(f"language ABI mismatch for {lang}")
        tree = L.ts_parser_parse_string(self.parser, None, src, len(src))
        root = L.ts_tree_root_node(tree)
        has_err = bool(L.ts_node_has_error(root))
        out = self._materialise(root, None, None)
        L.ts_tree_delete(tree)
        return out, has_err

    def _materialise(self, tsn, field, parent):
        L = self.lib
        node = Node(L.ts_node_type(tsn).decode(), bool(L.ts_node_is_named(tsn)),
                    L.ts_node_start_byte(tsn), L.ts_node_end_byte(tsn), field, parent)
        node.is_error = bool(L.ts_node_is_error(tsn))
        node.is_missing = bool(L.ts_node_is_missing(tsn))
        n = L.ts_node_child_count(tsn)
        for i in range(n):
            ch = L.ts_node_child(tsn, i)
            fname = L.ts_node_field_name_for_child(tsn, i)
            node.children.append(self._materialise(ch, fname.decode() if fname else None, node))
        return node


def find_library(explicit: str | None = None) -> str:
    cands = [explicit, os.environ.get("ATHENA_TS_LIB"),
             os.path.join(os.path.dirname(os.path.abspath(__file__)), "libtsall.so"),
             os.path.join(os.path.dirname(os.path.abspath(__file__)), "tsall.dll"),
             "/home/claude/ts/build/libtsall.so"]
    for c in cands:
        if c and os.path.exists(c):
            return c
    raise FileNotFoundError("tree-sitter shared library not found; run tools/build_treesitter.sh "
                            "or set ATHENA_TS_LIB")


def sexp(node: Node, src: bytes, depth=0, max_depth=99, out=None):
    """Pretty-print helper for exploring node types while developing extractors."""
    out = [] if out is None else out
    if depth > max_depth:
        return out
    label = (node.field + ": " if node.field else "") + node.type
    txt = ""
    if not node.children:
        txt = " " + repr(node.text(src)[:40])
    if node.named:
        out.append("  " * depth + label + txt)
    for c in node.children:
        if c.named:
            sexp(c, src, depth + 1, max_depth, out)
    return out
