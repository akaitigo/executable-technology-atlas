"""Atlas: root-assigned browser slot and mandatory actual nice10."""
import os
from pathlib import Path
import shutil
node=shutil.which('node')
if not node:raise SystemExit('Atlas: existing node unavailable; no install')
os.nice(10)
if os.getpriority(os.PRIO_PROCESS,0)<10:raise SystemExit('Atlas: priority guard failed; browser not started')
os.execv(node,[node,str(Path(__file__).with_name('check_gui.cjs'))])
