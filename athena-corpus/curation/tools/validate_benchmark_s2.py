#!/usr/bin/env python3
"""Validate a Study 2 benchmark with validate_benchmark.py, unchanged except that the reproduction of the injection
method also knows the Study 2 method prefix_swap: the required prefix replaced with the prefix of a sibling kind
(Godot p_ <-> r_; dotnet-runtime _, s_, t_). Every other check is that of Study 1.

  python3 tools/validate_benchmark_s2.py --benchmark bench/godot-s2 --corpus ../corpus_v2 \\
      --ontology ../../athena-sim/packs/godot-s2/godot_ontology.json --languages cpp \\
      --core ../../athena-sim/packs/godot-s2/core_rules.json
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import rules as R  # noqa: E402

SIBLINGS = {"p_": ("r_",), "r_": ("p_",), "_": ("s_", "t_"), "s_": ("_", "t_"), "t_": ("_", "s_")}
_study1_candidates = R.iter_candidates


def iter_candidates(standard_name, rule):
    """The candidates of Study 1, then prefix_swap for a rule whose prefix has sibling prefixes."""
    yield from _study1_candidates(standard_name, rule)
    p = rule.get("prefix")
    if p in SIBLINGS and standard_name.startswith(p) and len(standard_name) > len(p):
        for s in SIBLINGS[p]:
            yield ("prefix_swap", s + standard_name[len(p):])


R.iter_candidates = iter_candidates

import validate_benchmark  # noqa: E402

if __name__ == "__main__":
    validate_benchmark.main()
