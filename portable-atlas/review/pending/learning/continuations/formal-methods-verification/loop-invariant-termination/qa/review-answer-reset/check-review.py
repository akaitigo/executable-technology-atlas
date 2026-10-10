import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
spec=importlib.util.spec_from_file_location("oracle",ROOT/"checker.py")
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)


def blank(s):
    return s["hidden"] and not s["open"] and all(not s[k] for k in ("answer","summary","comparison","table","diagram"))


def main():
    old=json.loads((HERE/"old-63-bindings.json").read_text())
    assert len(old)==63
    for name,binding in old.items():
        p=HERE/"old-63"/name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==binding["sha256"]
        assert p.stat().st_mtime_ns==binding["mtime_ns"]
    for name in ["artifact-index.json","qa/20261005T211831461Z-iab/verification.json"]:
        bindings=json.loads((HERE/"old-63"/name).read_text())["bindings"]
        assert all(hashlib.sha256((HERE/"old-63"/k).read_bytes()).hexdigest()==v for k,v in bindings.items())
    before=json.loads((HERE/"old-ui.json").read_text())
    assert before[1]["hidden"] and before[1]["open"] and before[1]["answer"]==before[0]["answer"]
    assert before[2]["open"] and before[2]["answer"]!=before[1]["answer"]
    ram=json.loads((HERE/"ram-receipts.json").read_text())
    assert len(ram)==162
    assert [r["request_id"] for r in ram]==list(range(1,163))
    for r in ram:
        assert r["exit_code"]==0 and r["stderr"]==""
        assert r["source_sha256"]==hashlib.sha256((ROOT/"calculate.py").read_bytes()).hexdigest()
        d=json.loads(r["stdin"]);got=json.loads(r["stdout"])
        valid=isinstance(d,dict) and set(d)=={"n","budget","body"} and all(type(d[k]) is int and 0<=d[k]<=8 for k in ("n","budget")) and d["body"] in ("normal","double-y")
        assert got==oracle.oracle(d) if valid else got["category"]=="input_refused"
    lookup={r["request_id"]:r for r in ram}
    ui=json.loads((HERE/"new-ui.json").read_text())
    def fresh(s):
        assert not s["hidden"] and not s["open"]
        result=json.loads(s["answer"])
        assert result["receipt"]==lookup[result["receipt"]["request_id"]]
        assert result["receipt"]["request_id"]>=77
        assert result["receipt"]["stdin"]==s["input"]
        assert result["result"]==json.loads(result["receipt"]["stdout"])
    assert len(ui["handlers"])==7
    assert {s["action"] for s in ui["handlers"]}=={"prediction","case","input","reset","run","step","toggle"}
    for s in ui["handlers"]:
        assert blank(s.get("changed",s.get("start")));fresh(s["fresh"])
    assert len(ui["held"])==5
    for s in ui["held"][:4]:
        assert blank(s["start"]) and blank(s["changed"]) and blank(s["after"])
    fresh(ui["held"][4]["after"])
    assert json.loads(ui["held"][4]["after"]["input"])["budget"]==2
    cases=json.loads((ROOT/"expected.json").read_text())
    assert len(ui["matrix"])==60
    for c in cases:
        rows=[s for s in ui["matrix"] if s["id"]==c["id"]]
        assert set(s["prediction"] for s in rows)=={"","observed_correct","invariant_violation","budget_exhausted","input_refused"}
        for s in rows:
            fresh(s);assert s["input"]==json.dumps(c["input"],ensure_ascii=False,indent=2)
            assert json.loads(s["answer"])["result"]["category"]==c["category"]
    fresh(ui["final"])
    image=(HERE/"closed-answer-new-result.jpg").read_bytes()
    assert image[:3]==bytes.fromhex("ffd8ff") and image[-2:]==bytes.fromhex("ffd9")
    print(json.dumps({"status":"PASS","old_63_preserved":True,"handlers":7,"held_cases":5,
                      "matrix":60,"all_ram_receipts":162,"fresh_capture_requests":86,
                      "writes":False},sort_keys=True))


if __name__=="__main__":main()
