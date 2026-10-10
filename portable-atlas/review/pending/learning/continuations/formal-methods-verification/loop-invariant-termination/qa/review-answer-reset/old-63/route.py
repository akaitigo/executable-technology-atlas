"""Read-only local route check; never edits global registry or index."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
names=["README.md","COVERAGE.md","Skill.md","index.html","app.js","style.css",
       "calculate.py","checker.py","contract.json","hand-table.json","expected.json"]
assert all((ROOT/name).is_file() for name in names)
html=(ROOT/"index.html").read_text()
assert all('href="'+name+'"' in html for name in ["calculate.py","checker.py",
           "hand-table.json","contract.json","expected.json","README.md","COVERAGE.md","Skill.md"])
assert "部分正当性" in html and "未観測" in html and "紙上" in html
print(json.dumps({"status":"PASS","scope":"local route only","files":len(names),"writes":False}))
