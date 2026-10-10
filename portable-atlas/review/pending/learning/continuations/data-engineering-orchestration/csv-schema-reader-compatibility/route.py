import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
names=["README.md","COVERAGE.md","Skill.md","index.html","app.js","style.css",
       "calculate.py","oracle.py","checker.py","contract.json","hand-table.json","matrix-hand.json"]
assert all((ROOT/p).is_file() for p in names)
page=(ROOT/"index.html").read_text()
assert all('href="'+p+'"' in page for p in ["calculate.py","oracle.py","hand-table.json","matrix-hand.json","README.md","COVERAGE.md","Skill.md"])
print(json.dumps({"status":"PASS","files":len(names),"scope":"local route","writes":False}))
