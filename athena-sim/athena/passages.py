"""Split a coding-standard document into passages for the retrieval conditions (TF-IDF, BM25, dense).

A passage is a paragraph of the document: a block of text between blank lines.  Each passage starts with the
headings that contain it, joined with " > ", so that a retrieved paragraph says which part of the standard it
comes from.  Headings are recognised in reStructuredText (a title line with an underline, with or without an
overline) and in Markdown (lines starting with `#`).  Blocks that belong to the paragraph before them are kept
with it: an indented block after a line that ends with `::` or after a `.. directive` (reStructuredText), and
the content of a fenced code block (Markdown).  A heading with no text under it before the next heading is not
a passage of its own.  A list is split into one passage per item (a numbered or bulleted item together with its
continuation lines), because every item of the standards' lists is a rule of its own.  Lines that only name a
reStructuredText label or a `highlight` directive are dropped.

The splitting is deterministic and uses no model, so the passages are the same on every machine.
"""
from __future__ import annotations

import re

_RST_ADORN = re.compile(r"^([=\-~^\"'`#*+._:])\1{2,}\s*$")
_MD_HEAD = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_FENCE = re.compile(r"^\s*(```|~~~)")
_MD_SETEXT = re.compile(r"^(=+|-+)\s*$")
_ITEM = re.compile(r"^(\d+[.)]|[-*+])\s+\S")
_NOISE = re.compile(r"^\.\. (_[^:]+:|highlight::.*)\s*$")


def _rst_blocks(lines):
    """Blocks in document order: ('head', level key, title) and ('text', [lines])."""
    out, cur, i, n = [], [], 0, len(lines)

    def flush():
        nonlocal cur
        if cur:
            out.append(("text", cur))
            cur = []

    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            flush()
            i += 1
            continue
        # overline + title + underline
        if _RST_ADORN.match(s) and i + 2 < n and lines[i + 1].strip() and _RST_ADORN.match(lines[i + 2].strip()) \
                and lines[i + 2].strip()[0] == s[0] and len(lines[i + 1].strip()) <= len(s):
            flush()
            out.append(("head", "over" + s[0], lines[i + 1].strip()))
            i += 3
            continue
        # title + underline
        if i + 1 < n and not _RST_ADORN.match(s) and _RST_ADORN.match(lines[i + 1].strip()) \
                and len(lines[i + 1].strip()) >= len(s) and line[:1] not in (" ", "\t"):
            flush()
            out.append(("head", lines[i + 1].strip()[0], s))
            i += 2
            continue
        cur.append(line)
        i += 1
    flush()
    return out


def _md_blocks(lines):
    out, cur, in_fence = [], [], False

    def flush():
        nonlocal cur
        if cur:
            out.append(("text", cur))
            cur = []

    for idx, line in enumerate(lines):
        if _FENCE.match(line):
            in_fence = not in_fence
            cur.append(line)
            continue
        if in_fence:
            cur.append(line)
            continue
        if _MD_SETEXT.match(line) and cur and len(cur) == 1 and len(line.strip()) >= 2 \
                and cur[0][:1] not in (" ", "\t") and not _ITEM.match(cur[0]):
            out.append(("head", 1 if line.strip()[0] == "=" else 2, cur[0].strip()))
            cur = []
            continue
        m = _MD_HEAD.match(line)
        if m:
            flush()
            out.append(("head", len(m.group(1)), m.group(2).strip()))
        elif not line.strip():
            flush()
        else:
            cur.append(line)
    flush()
    return out


def _merge_rst(blocks):
    """Attach indented blocks to the paragraph or directive they belong to."""
    out, literal = [], False
    for block in blocks:
        if block[0] != "text":
            out.append(block)
            literal = False
            continue
        lines = block[1]
        indented = lines[0][:1] in (" ", "\t")
        if out and out[-1][0] == "text" and indented and literal:
            out[-1] = ("text", out[-1][1] + [""] + lines)
            continue
        out.append(("text", lines))
        literal = lines[-1].rstrip().endswith("::") or lines[0].startswith(".. ")
    return out


def _split_items(lines):
    """One chunk per list item when the block is a list of two or more items; otherwise the block as it is."""
    if any(_FENCE.match(l) for l in lines):
        return [lines]
    starts = [i for i, l in enumerate(lines) if _ITEM.match(l)]
    if len(starts) < 2:
        return [lines]
    parts = [lines[:starts[0]]] if starts[0] > 0 else []
    for a, b in zip(starts, starts[1:] + [len(lines)]):
        parts.append(lines[a:b])
    return parts


def split_passages(text: str, fmt: str):
    """List of (passage_id, passage_text).  `fmt` is 'rst' or 'md'."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    if fmt == "rst":
        blocks = _merge_rst(_rst_blocks(lines))
    elif fmt == "md":
        blocks = _md_blocks(lines)
    else:
        raise ValueError(f"unknown document format {fmt!r} (rst or md)")
    stack, out, order = [], [], []      # headings that contain the paragraph; rst: adornment characters seen
    for block in blocks:
        if block[0] == "head":
            key, title = block[1], block[2]
            if fmt == "rst":
                if key not in order:
                    order.append(key)
                level = order.index(key)
            else:
                level = key
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            continue
        head = " > ".join(t for _, t in stack)
        for part in _split_items(block[1]):
            body = "\n".join(part).strip("\n")
            if not body.strip() or (len(part) == 1 and _NOISE.match(body.strip())):
                continue
            out.append((f"p{len(out) + 1:03d}", f"{head}\n\n{body}" if head else body))
    return out
