#!/usr/bin/env python3
"""Select the Study 2 tasks of one pack: the procedure of tools/select_tasks.py (D13: split by path hash, seeded draw
with a cap of 3 per file, the same policy if the pool is short) with the seed athena2-s2-v1.

  python3 tools/select_tasks_s2.py --pack godot-s2 --pool pool_s2/godot-s2_pool.tsv --out-dir selection_s2/
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import select_tasks  # noqa: E402

SEED = "athena2-s2-v1"
select_tasks.SEED = SEED          # read by select_tasks.shuffled() and written to the selection report

if __name__ == "__main__":
    sys.exit(select_tasks.main())
