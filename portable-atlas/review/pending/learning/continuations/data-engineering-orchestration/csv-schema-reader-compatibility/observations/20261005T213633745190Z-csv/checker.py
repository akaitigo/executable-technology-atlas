import csv
from io import StringIO
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
from oracle import oracle

ROOT=Path(__file__).resolve().parent


def execute(d):
    p=subprocess.run([sys.executable,"-B",str(ROOT/"calculate.py")],input=json.dumps(d),
                     text=True,capture_output=True)
    assert p.returncode==0 and p.stderr==""
    return json.loads(p.stdout)


def check(d):
    got=execute(d);want=oracle(d)
    assert all(got[k]==v for k,v in want.items()),(d,got,want)
    return got


def main():
    bindings=json.loads((ROOT/"contract-bindings.json").read_text())
    assert all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in bindings.items())
    hand=json.loads((ROOT/"hand-table.json").read_text())
    for fixture in hand:
        scan=csv.reader(StringIO(fixture["csv"],newline=""),strict=True);rows=[];ends=[]
        for cells in scan:rows.append(cells);ends.append(scan.line_num)
        assert rows==fixture["tokens"] and ends[1:]==fixture["end_lines"]
    cases=json.loads((ROOT/"expected.json").read_text())
    for c in cases:
        got=check(c["input"])
        assert all(got[k]==v for k,v in c.items() if k not in ("id","input"))
    # All known header permutations: independent expected typed semantics, fault witness separate.
    permutations=0
    for reader in ("v1","v2"):
        fields=["id","quantity","unit_price"]+(["note"] if reader=="v2" else [])
        for order in itertools.permutations(fields):
            values={"id":"a","quantity":"2","unit_price":"7","note":"batch"}
            raw=",".join(order)+"\n"+",".join(values[k] for k in order)+"\n"
            check({"writer":"literal","reader":reader,"mode":"name","csv":raw});permutations+=1
    lexical=0
    for value in ("0","99","100","-1","01","+2"," 2","2 ","2.0","", "NaN"):
        for reader in ("v1","v2"):
            raw="id,quantity,unit_price\na,"+value+",7\n"
            check({"writer":"literal","reader":reader,"mode":"name","csv":raw});lexical+=1
    for d in [None,{},{"writer":"v1","reader":"v1","mode":"name","csv":"wrong"},
              {"writer":"literal","reader":"v1","mode":"name","csv":"x"*1025}]:
        assert execute(d)["category"]=="input_refused"
    print(json.dumps({"status":"PASS","fixed_cases":30,"literal_fixtures":14,
                      "header_permutations":permutations,"lexical_checks":lexical,
                      "input_refusals":4,"writes":False},sort_keys=True))


if __name__=="__main__":main()
