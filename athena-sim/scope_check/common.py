"""Shared helpers for the scope-aware check (see ADDENDUM.md)."""
import bisect
import re


def word_re(name):
    # identical to athena/evaluate.py::_word_re
    return re.compile(r"(?<![\w$])" + re.escape(name) + r"(?![\w$])")


def apply_rename(code, old, new):
    # identical to athena/evaluate.py::apply_rename
    return word_re(old).subn(lambda m: new, code)


class OffsetMap:
    """Map an offset in the renamed code back to the offset in the code before the rename."""

    def __init__(self, before, old, new):
        self.starts_b = [m.start() for m in word_re(old).finditer(before)]
        self.delta = len(new) - len(old)
        self.starts_a = [s + i * self.delta for i, s in enumerate(self.starts_b)]

    def __call__(self, off_after):
        k = bisect.bisect_left(self.starts_a, off_after)  # renamed tokens strictly before this offset
        return off_after - k * self.delta


IDENTITY = lambda o: o  # noqa: E731


def compare(occ_b, occ_a):
    """occ_*: dict occurrence-id -> declaration key (after: already in before coordinates).
    Returns (conflict, reasons). Conflict if the before->after declaration mapping over aligned occurrences is
    not one-to-one, or occurrences do not align."""
    reasons = []
    fwd, back = {}, {}
    common = set(occ_b) & set(occ_a)
    for oid in sorted(common, key=str):
        kb, ka = occ_b[oid], occ_a[oid]
        fwd.setdefault(kb, set()).add(ka)
        back.setdefault(ka, set()).add(kb)
    for kb, s in fwd.items():
        if len(s) > 1:
            reasons.append(f"split: {kb} -> {sorted(map(str, s))}")
    for ka, s in back.items():
        if len(s) > 1:
            reasons.append(f"merge/capture: {sorted(map(str, s))} -> {ka}")
    only_b = set(occ_b) - set(occ_a)
    only_a = set(occ_a) - set(occ_b)
    if only_b or only_a:
        reasons.append(f"unaligned occurrences: before-only {len(only_b)}, after-only {len(only_a)}")
    return bool(reasons), reasons
