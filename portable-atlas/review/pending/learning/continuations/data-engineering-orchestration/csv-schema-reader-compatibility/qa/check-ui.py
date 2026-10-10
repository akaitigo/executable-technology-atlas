"""Saved real UI, independent list/token oracle, literal expectations. Read-only."""
import csv
from io import StringIO
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location("independent",ROOT/"oracle.py")
independent=importlib.util.module_from_spec(spec);spec.loader.exec_module(independent)
NAMES={"accepted":"受入（意味一致は別確認）","rejected":"CSV契約で拒否","input_refused":"入力形式で拒否"}
LETTERS="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
WRITERS={"v1":"id,quantity,unit_price\na,2,7\n",
         "v2":"id,quantity,unit_price,note\na,2,7,batch\n"}


def expected(stdin):
    try:d=json.loads(stdin)
    except ValueError:return None
    if (not isinstance(d,dict) or set(d)!={"writer","reader","mode","csv"}
        or d["writer"] not in ("literal","v1","v2") or d["reader"] not in ("v1","v2")
        or d["mode"] not in ("name","position-fault") or not isinstance(d["csv"],str)
        or len(d["csv"].encode())>1024):return None
    if d["writer"]!="literal" and WRITERS[d["writer"]]!=d["csv"]:return None
    return independent.oracle(d)


def receipt(r):
    assert r["exit_code"]==0 and r["stderr"]==""
    assert r["argv"]==["python3","-B","calculate.py"] and "+00:00" in r["utc"]
    assert r["source_sha256"]==hashlib.sha256((ROOT/"calculate.py").read_bytes()).hexdigest()
    got=json.loads(r["stdout"]);want=expected(r["stdin"])
    if want is None:assert got["category"]=="input_refused";return got
    assert all(got[k]==v for k,v in want.items())
    d=json.loads(r["stdin"])
    assert got["csv"]==d["csv"] and got["csv_sha256"]==hashlib.sha256(d["csv"].encode()).hexdigest()
    assert got["writer_output"]==(None if d["writer"]=="literal" else WRITERS[d["writer"]])
    assert got["reader"]==d["reader"] and got["mode"]==d["mode"] and got["runtime"]=="3.9.6"
    # Distinct list parser path; literal hand tokens are checked separately by checker.
    scanner=csv.reader(StringIO(d["csv"],newline=""),strict=True);tokens=[];ends=[]
    try:
        for values in scanner:tokens.append(values);ends.append(scanner.line_num)
    except csv.Error:
        assert got["reason"]=="csv_syntax" and not got["mapping"] and not got["records"]
        return got
    if got["reason"]=="record_bounds":assert not got["mapping"] and not got["records"];return got
    header=tokens[0];assert got["header"]==header
    if got["reason"] in ("duplicate_header","empty_header","required_header","unknown_header"):
        assert got["error_at"]=={"record":0,"field":None,"end_line":1}
        assert not got["mapping"] and not got["records"];return got
    fields=["id","quantity","unit_price"]+(["note"] if d["reader"]=="v2" else [])
    mapping=[]
    for i,field in enumerate(fields):
        col=(header.index(field)+1 if d["mode"]=="name" else i+1) if field in header else None
        mapping.append({"field":field,"column":col,"default":"(default)" if col is None else None})
    assert got["mapping"]==mapping
    previews=[];failure=None
    for ordinal,cells in enumerate(tokens[1:],1):
        row={"record":ordinal,"end_line":ends[ordinal],"cells":cells,"mapped":{}}
        previews.append(row)
        if len(cells)!=len(header):
            failure={"record":ordinal,"field":None,"end_line":ends[ordinal]};break
        typed={}
        for m in mapping:
            field=m["field"];v=cells[m["column"]-1] if m["column"] is not None else m["default"]
            row["mapped"][field]=v
            valid=(1<=len(v)<=8 and all(c in LETTERS for c in v)) if field=="id" else (
                  bool(v) and len(v)<=2 and all(c in "0123456789" for c in v) and not (len(v)>1 and v[0]=="0")) if field in ("quantity","unit_price") else (
                  len(v)<=16 and all(ord(c)<128 for c in v))
            if not valid:failure={"record":ordinal,"field":field,"end_line":ends[ordinal]};break
            typed[field]=int(v) if field in ("quantity","unit_price") else v
        if failure:break
        row["typed"]=typed
    assert got["records"]==previews
    assert got["error_at"]==failure
    return got


def state(s,lookup):
    assert not s["hidden"] and not s["open"]
    data=json.loads(s["answer"]);r=data["receipt"]
    assert lookup[r["request_id"]]==r and r["stdin"]==s["input"]
    got=receipt(r);assert data["result"]==got
    if s["prediction"]:
        assert s["comparison"]=="予想 "+NAMES[s["prediction"]]+" ／ 実際 "+NAMES[got["category"]]+" ／ "+("一致" if s["prediction"]==got["category"] else "不一致")
    else:assert s["comparison"]=="予想未選択 ／ 実際 "+NAMES[got["category"]]
    assert json.loads(s["typed"])==got.get("typed_rows",[])
    lines=got.get("csv","").split("\n")
    assert s["raw"]=="\n".join(str(i+1)+": "+("（最終改行の終端）" if i==len(lines)-1 and line=="" else line) for i,line in enumerate(lines))
    assert len(s["mapping"])==len(got.get("mapping",[]))
    for i,(actual,m) in enumerate(zip(s["mapping"],got.get("mapping",[]))):
        text=("列なし："+m["default"] if m["column"] is None else "列"+str(m["column"])+" "+got["header"][m["column"]-1])+" → "+m["field"]
        assert actual=={"field":m["field"],"column":"default" if m["column"] is None else str(m["column"]),"text":text,"x":"15","y":str(35+i*52)}
    assert len(s["records"])==len(got.get("records",[]))
    for actual,row in zip(s["records"],got.get("records",[])):
        assert actual["record"]==str(row["record"]) and actual["end_line"]==str(row["end_line"])
        values=actual["values"];assert [int(v) for v in values[:2]]==[row["record"],row["end_line"]]
        assert [json.loads(v) for v in values[2:]]==[row["cells"],row["mapped"],row.get("typed")]
    return got


def main():
    meta=json.loads((ROOT/"qa/final-attempt.json").read_text());directory=ROOT/meta["directory"]
    ui=json.loads((directory/"ui.json").read_text());ram=json.loads((directory/"ram-receipts.json").read_text())
    assert len(ram)==meta["expected_receipts"]==151
    assert [r["request_id"] for r in ram]==list(range(1,152))
    for r in ram:receipt(r)
    lookup={r["request_id"]:r for r in ram}
    cases=json.loads((ROOT/"expected.json").read_text())
    assert len(ui["matrix"])==120
    for c in cases:
        entries=[s for s in ui["matrix"] if s["id"]==c["id"]]
        assert set(s["prediction"] for s in entries)=={"",*NAMES}
        for s in entries:
            assert s["input"]==json.dumps(c["input"],ensure_ascii=False,indent=2)
            got=state(s,lookup);assert all(got[k]==v for k,v in c.items() if k not in ("id","input"))
    assert len(ui["cells"])==4
    for i,s in enumerate(ui["cells"]):
        assert s["selected"]["hidden"] and s["selected"]["case"]==str(i)
        got=state(s["result"],lookup);assert got["typed_rows"]==cases[i]["typed_rows"]
    assert len(ui["operations"])==6
    for group in ("operations","edits","captures"):
        for s in ui[group]:state(s,lookup)
    for i in (0,3):
        before=json.loads(ui["operations"][i]["typed"])[0]
        fault=json.loads(ui["operations"][i+1]["typed"])[0]
        back=json.loads(ui["operations"][i+2]["typed"])[0]
        assert (before["quantity"],before["unit_price"])==(2,7)
        assert (fault["quantity"],fault["unit_price"])==(7,2) and before==back
    assert len(ui["edits"])==10 and len(ui["stale"])==4 and len(ui["resets"])==30
    for s in ui["stale"]:
        assert s["before"]["open"]
        c=s["changed"];assert c["hidden"] and not c["open"] and not c["answer"] and not c["typed"] and not c["records"] and not c["mapping"]
        state(s["fresh"],lookup)
    for s,c in zip(ui["resets"],cases):
        assert s["hidden"] and not s["open"] and not s["prediction"]
        assert s["input"]==json.dumps(c["input"],ensure_ascii=False,indent=2)
    assert len(ui["captures"])==3
    for s in ui["captures"]:
        assert s["viewport"]["width"]==s["viewport"]["documentWidth"]
        raw=(directory/s["name"]).read_bytes();assert raw[:3]==bytes.fromhex("ffd8ff") and raw[-2:]==bytes.fromhex("ffd9")
    assert len(ui["viewers"])==10
    for s in ui["viewers"][:9]:
        assert s["headings"]==[s["file"]] and s["text"]==(ROOT/s["file"]).read_text()
        assert s["url"].endswith("/"+s["file"])
    doc=ui["viewers"][-1]
    assert all(doc[k] for k in ("dictReader","dictWriter","restkey","restval","line_num","physical_records"))
    assert "Python 3.14.8" in doc["title"]
    observation=list((ROOT/"observations").iterdir());assert len(observation)==1
    manifest=json.loads((observation[0]/"manifest.json").read_text())
    assert all(hashlib.sha256((observation[0]/k).read_bytes()).hexdigest()==v for k,v in manifest.items())
    for r in json.loads((observation[0]/"raw.json").read_text()):
        assert r["source_sha256"]==manifest and r["exit_code"]==0 and not r["stderr"]
        d=json.loads(r["stdin"]);assert r["csv_sha256"]==hashlib.sha256(d["csv"].encode()).hexdigest()
    print(json.dumps({"status":"PASS","matrix":120,"cells":4,"operations":6,"edits":10,
                      "stale":4,"resets":30,"captures":3,"viewers":10,"ram_receipts":151,
                      "literal_meaning_witness":"quantity2/unit_price7 vs quantity7/unit_price2",
                      "writes":False},sort_keys=True))


if __name__=="__main__":main()
