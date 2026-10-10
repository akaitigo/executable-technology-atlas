"""Read-only independent verification of saved real UI and child receipts."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location("independent",ROOT/"checker.py")
independent=importlib.util.module_from_spec(spec); spec.loader.exec_module(independent)
NAMES={"observed_correct":"境界を保ち guard exit","invariant_violation":"境界の不変条件違反",
       "budget_exhausted":"budget不足・事後条件未観測","input_refused":"入力拒否"}


def expected(stdin):
    try: d=json.loads(stdin)
    except ValueError: return None
    if not isinstance(d,dict) or set(d)!={"n","budget","body"}: return None
    if any(type(d[k]) is not int or not 0<=d[k]<=8 for k in ("n","budget")): return None
    if d["body"] not in ("normal","double-y"): return None
    return independent.oracle(d)


def receipt(r):
    assert r["exit_code"]==0 and r["stderr"]==""
    assert r["argv"]==["python3","-B","calculate.py"]
    assert r["source_sha256"]==hashlib.sha256((ROOT/"calculate.py").read_bytes()).hexdigest()
    assert "+00:00" in r["utc"]
    got=json.loads(r["stdout"]); want=expected(r["stdin"])
    assert got==want if want is not None else got["category"]=="input_refused"
    return got


def state(s,by_id):
    assert not s["hidden"]
    data=json.loads(s["answer"]); r=data["receipt"]
    assert r==by_id[r["request_id"]] and r["stdin"]==s["input"]
    got=receipt(r); assert data["result"]==got
    if s["prediction"]:
        assert s["comparison"]=="予測 "+NAMES[s["prediction"]]+" ／ 実際 "+NAMES[got["category"]]+" ／ "+("一致" if s["prediction"]==got["category"] else "不一致")
    else: assert s["comparison"]=="予測未選択 ／ 実際 "+NAMES[got["category"]]
    rows=got.get("trace",[])
    assert len(s["table"])==len(rows)
    for actual,row in zip(s["table"],rows):
        vals=[str(row["k"]),row["phase"],str(row["x"]),str(row["y"]),str(row["sum"]),
              str(row["equals_n"]).lower(),"● 検査点" if row["boundary"] else "○ 途中"]
        assert actual["values"]==vals
        assert actual["boundary"]==str(row["boundary"]).lower()
        assert actual["bad"]==str(row["boundary"] and not row["equals_n"]).lower()
    boundaries=[r for r in rows if r["boundary"]]
    assert len(s["circles"])==len(boundaries)
    for i,(circle,row) in enumerate(zip(s["circles"],boundaries)):
        assert int(circle["k"])==row["k"] and int(circle["x"])==row["x"]
        assert abs(float(circle["cx"])-(40+i*640/max(1,len(boundaries)-1)))<1e-8
        assert float(circle["cy"])==155-row["x"]*13
        assert circle["fill"]==("#147d77" if row["equals_n"] else "#c34b25")
    if got["category"]!="input_refused":
        expected_summary="分類："+NAMES[got["category"]]+" ｜ 終了状態："+got["completion"]+" ｜ 完了本体数："+str(got["iterations"])+" ｜ 境界I："+str(got["boundary_invariant_all"]).lower()+" ｜ 事後条件："+("未観測" if got["postcondition"] is None else str(got["postcondition"]).lower())+" ｜ 観測variant下降："+str(got["variant_decreases"]).lower()
        assert s["summary"]==expected_summary
    else: assert s["summary"]=="入力拒否："+got["error"]
    return got


def main():
    generations=sorted((ROOT/"observations").iterdir())
    assert len(generations)==2
    for generation in generations:
        manifest=json.loads((generation/"manifest.json").read_text())
        for name,sha in manifest.items():
            assert hashlib.sha256((generation/name).read_bytes()).hexdigest()==sha
        for row in json.loads((generation/"raw.json").read_text()):
            assert row["source_sha256"]==manifest
            assert row["exit_code"]==0 and row["stderr"]==""
            assert row["result"]==json.loads(row["stdout"])
            want=expected(row["stdin"])
            assert row["result"]==want if want is not None else row["result"]["category"]=="input_refused"
    assert hashlib.sha256((ROOT/"oracle-contract.md").read_bytes()).hexdigest()=="df47c2adbd26fb06d6ad268868ba3b8c5961ef009181ef5da46952674e918331"
    pointer=json.loads((ROOT/"qa/final-attempt.json").read_text())
    directory=ROOT/pointer["directory"]
    ui=json.loads((directory/"ui.json").read_text())
    receipts=json.loads((directory/"ram-receipts.json").read_text())
    assert [r["request_id"] for r in receipts]==list(range(1,len(receipts)+1))
    for r in receipts: receipt(r)
    by_id={r["request_id"]:r for r in receipts}
    cases=json.loads((ROOT/"expected.json").read_text())
    assert len(ui["matrix"])==60
    for case in cases:
        entries=[s for s in ui["matrix"] if s["id"]==case["id"]]
        assert set(s["prediction"] for s in entries)=={"",*NAMES}
        for s in entries:
            assert s["input"]==json.dumps(case["input"],ensure_ascii=False,indent=2)
            got=state(s,by_id)
            assert all(got[k]==v for k,v in case.items() if k not in ("id","input"))
    for group in ("edits","operations","captures"):
        for s in ui[group]: state(s,by_id)
    assert len(ui["edits"])==8 and len(ui["operations"])==6
    ops=ui["operations"]
    assert [json.loads(s["input"])["budget"] for s in ops[:4]]==[0,1,2,3]
    assert state(ops[4],by_id)["postcondition"] is False
    assert state(ops[5],by_id)["postcondition"] is True
    assert len(ui["stale"])==4 and all(s["hidden"] for s in ui["stale"])
    assert {s["action"] for s in ui["stale"]}=={"case","input","prediction","reset"}
    assert len(ui["resets"])==12
    for s,case in zip(ui["resets"],cases):
        assert s["hidden"] and s["prediction"]==""
        assert s["input"]==json.dumps(case["input"],ensure_ascii=False,indent=2)
    assert len(ui["captures"])==3
    for s in ui["captures"]:
        assert s["viewport"]["width"]==s["viewport"]["documentWidth"]
        raw=(directory/s["name"]).read_bytes()
        assert raw[:3]==bytes.fromhex("ffd8ff") and raw[-2:]==bytes.fromhex("ffd9")
    assert len(ui["viewers"])==10
    for viewer in ui["viewers"][:9]:
        assert viewer["heading"]==[viewer["file"]]
        assert viewer["text"]==(ROOT/viewer["file"]).read_text()
        assert viewer["url"].endswith("/"+viewer["file"])
    official=ui["viewers"][-1]
    assert official["hasWhile"] and official["hasPartial"] and official["hasTransient"]
    assert official["url"]=="https://softwarefoundations.cis.upenn.edu/plf-current/Hoare.html"
    print(json.dumps({"status":"PASS","matrix":60,"edits":8,"operations":6,"stale":4,
                      "resets":12,"captures":3,"viewers":10,"ram_receipts":len(receipts),
                      "writes":False},sort_keys=True))


if __name__=="__main__": main()
