"""Athena Sim, Study 2 (HYPOTHESES_v2_study2): the Study 1 harness with the Study 2 packs, the naming condition, the
Study 2 kind inference and a freeze that also covers this package.

Importing these modules changes nothing in the Study 1 modules. athena_s2.install.install() connects the Study 2
parts to the Study 1 runner inside the process that calls it (athena2_s2.py), so every condition of Study 1 runs
through the same Study 1 code, and the Study 1 files stay as frozen.
"""

__version__ = "0.1.0"
