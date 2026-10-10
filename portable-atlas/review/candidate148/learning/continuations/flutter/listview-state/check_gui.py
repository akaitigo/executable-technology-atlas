#!/usr/bin/env python3
"""専用profileのChromium確認。優先度設定失敗時は起動しない。"""
import os
from pathlib import Path
import shutil
import sys

node = shutil.which('node')
if not node:
    raise SystemExit('既存nodeがありません。installは行いません。')
os.nice(10)
if os.getpriority(os.PRIO_PROCESS, 0) < 10:
    raise SystemExit('nice 10を適用できません。browserを起動しません。')
os.execv(node, [node, str(Path(__file__).with_name('check_gui.cjs')), *sys.argv[1:]])
