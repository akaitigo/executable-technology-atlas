"""Read-only by default. --record explicitly creates a fresh UTC observation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SOURCES = ["calculate.py","checker.py","runner.py","contract.json",
           "oracle-contract.md","hand-table.json","expected.json"]


def bindings():
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--record",action="store_true")
    args=parser.parse_args(); before=bindings()
    raw=[]
    for case in json.loads((ROOT/"expected.json").read_text()):
        stdin=json.dumps(case["input"], ensure_ascii=False)
        p=subprocess.run([sys.executable,"-B",str(ROOT/"calculate.py")],
                         input=stdin,text=True,capture_output=True)
        result=json.loads(p.stdout)
        assert p.returncode==0 and not p.stderr
        assert all(result[k]==v for k,v in case.items() if k not in ("id","input"))
        raw.append({"id":case["id"],"input":case["input"],"stdin":stdin,
                    "stdout":p.stdout,"stderr":p.stderr,"exit_code":p.returncode,
                    "argv":["python3","-B","calculate.py"],"result":result,
                    "utc":datetime.now(timezone.utc).isoformat(),"source_sha256":before})
    assert before==bindings()
    if args.record:
        stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-loop")
        directory=ROOT/"observations"/stamp; directory.mkdir(parents=True,exist_ok=False)
        for name in SOURCES:
            (directory/name).write_bytes((ROOT/name).read_bytes())
        (directory/"raw.json").write_text(json.dumps(raw,ensure_ascii=False,indent=2)+"\n")
        (directory/"manifest.json").write_text(json.dumps(before,indent=2)+"\n")
        print(json.dumps({"status":"PASS","record":str(directory.relative_to(ROOT)),"cases":len(raw)}))
    else:
        print(json.dumps({"status":"PASS","cases":len(raw),"writes":False}))


if __name__=="__main__":
    main()
