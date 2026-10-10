#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Owned temp-copy negative checks; canonical evidence is read-only."""
import os
import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit
from observe import publish,capture
from verify import HERE,INPUTS,digest,validate_saved


def state():
    return {p.name:(digest(p.read_bytes()),p.stat().st_mtime_ns) for p in (HERE/"evidence").iterdir()}


before=state()
for command in ("verify.py","observe.py"):
    subprocess.run([sys.executable,"-B",command],cwd=HERE,check=True)
assert state()==before
saved=validate_saved()
invalid=copy.deepcopy(saved)
invalid["queries"][0]["metric_rows"][0][3]=280
for result,error_type in ((subprocess.CompletedProcess([],1,b"",b"injected runner failure"),RuntimeError),
                          (subprocess.CompletedProcess([],0,json.dumps(invalid).encode(),b""),AssertionError)):
    try:
        with patch("observe.subprocess.run",return_value=result):
            capture()
    except error_type:
        pass
    else:
        raise AssertionError("failed runner/oracle published")
    assert state()==before, "failed capture changed prior success"
with tempfile.TemporaryDirectory(prefix=".contract-",dir=HERE) as directory:
    root=Path(directory)
    for label in ("artifact-tamper","missing-artifact","source-tamper","roadmap-tamper"):
        candidate=root/label; candidate.mkdir()
        shutil.copytree(HERE/"evidence",candidate/"evidence")
        for name in INPUTS:
            (candidate/name).parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(HERE/name,candidate/name)
        if label=="missing-artifact":
            (candidate/"evidence/verification.json").unlink()
        else:
            target={"artifact-tamper":"evidence/stdout.json","source-tamper":"queries.json","roadmap-tamper":"README.md"}[label]
            with (candidate/target).open("ab") as handle:
                handle.write(b"\n ")
        try:
            validate_saved(candidate)
        except (AssertionError,FileNotFoundError):
            pass
        else:
            raise AssertionError("accepted "+label)
    live,candidate=root/"live",root/"candidate"; live.mkdir(); candidate.mkdir()
    (live/"result").write_bytes(b"prior-success"); (candidate/"result").write_bytes(b"next-success")
    previous=digest((live/"result").read_bytes()); original=os.replace
    def fail_swap(source,destination):
        if Path(source)==candidate:
            raise OSError("injected swap failure")
        return original(source,destination)
    try:
        with patch("observe.os.replace",side_effect=fail_swap):
            publish(candidate,live)
    except OSError:
        pass
    else:
        raise AssertionError("swap failure swallowed")
    assert digest((live/"result").read_bytes())==previous and candidate.exists()
    publish(candidate,live)
    assert (live/"result").read_bytes()==b"next-success" and not candidate.exists()

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        self.links.extend(v for k,v in attrs if k in ("href","src") and v)

parser=Links(); parser.feed((HERE/"index.html").read_text()); checked=0
for path in (HERE/"index.html",HERE/"README.md",HERE/"COVERAGE.md",HERE/"skills/atlas-analytics-data-platform/SKILL.md"):
    links=parser.links if path.name=="index.html" else re.findall(r"\]\(([^)]+)\)",path.read_text())
    for link in links:
        if urlsplit(link).scheme or link.startswith("#"):
            continue
        assert (path.parent/urlsplit(link).path).is_file(), (path.name,link)
        checked+=1
raw=validate_saved()
# Author routing walkthrough, not independent Agent Eval.
assert raw["queries"][0]["metric_rows"][0][3]==380
assert raw["queries"][1]["metric_rows"][0][3]==280
assert all(raw["scope"][field] is False for field in ("warehouse_product","lake_product","bi_product","performance_benchmark"))
assert state()==before
print("PASS: read-only bytes+mtime; 4 freshness negatives; runner/oracle failure retention; atomic rollback; %d local links; normal/unsupported Skill walkthrough" % checked)
