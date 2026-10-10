import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
SOURCES=["calculate.py","oracle.py","checker.py","runner.py","contract.json",
         "hand-table.json","expected.json","matrix-hand.json","contract-bindings.json"]


def main():
    p=argparse.ArgumentParser();p.add_argument("--record",action="store_true");args=p.parse_args()
    sources={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in SOURCES}
    raw=[]
    for case in json.loads((ROOT/"expected.json").read_text()):
        stdin=json.dumps(case["input"],ensure_ascii=False)
        process=subprocess.run([sys.executable,"-B",str(ROOT/"calculate.py")],input=stdin,
                               text=True,capture_output=True)
        got=json.loads(process.stdout)
        assert process.returncode==0 and not process.stderr
        assert all(got[k]==v for k,v in case.items() if k not in ("id","input"))
        raw.append({"id":case["id"],"stdin":stdin,"stdout":process.stdout,"stderr":process.stderr,
                    "exit_code":process.returncode,"argv":["python3","-B","calculate.py"],
                    "utc":datetime.now(timezone.utc).isoformat(),"source_sha256":sources,
                    "csv_sha256":hashlib.sha256(case["input"]["csv"].encode()).hexdigest()})
    assert sources=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in SOURCES}
    if args.record:
        d=ROOT/"observations"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-csv")
        d.mkdir(parents=True,exist_ok=False)
        for s in SOURCES:(d/s).write_bytes((ROOT/s).read_bytes())
        (d/"raw.json").write_text(json.dumps(raw,ensure_ascii=False,indent=2)+"\n")
        (d/"manifest.json").write_text(json.dumps(sources,indent=2)+"\n")
        print(json.dumps({"status":"PASS","record":str(d.relative_to(ROOT)),"cases":len(raw)}))
    else:print(json.dumps({"status":"PASS","cases":len(raw),"writes":False}))


if __name__=="__main__":main()
