#!/usr/bin/env python3
"""Atlas reader GUI check; requires an assigned browser slot."""
import os
from pathlib import Path
import shutil
import sys

node = shutil.which('node')
if not node:
    raise SystemExit('Existing node is unavailable; no install attempted.')
os.nice(10)
if os.getpriority(os.PRIO_PROCESS, 0) < 10:
    raise SystemExit('nice 10 is mandatory. Browser not started.')
os.execv(node, [node, str(Path(__file__).with_name('check_gui.cjs')), *sys.argv[1:]])
