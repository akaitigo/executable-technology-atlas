#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Read-only hand oracle. No SQLite query execution or experiment import."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = ("experiment.py", "queries.json", "verify.py", "observe.py", "test_contract.py", "sources.json",
          "index.html", "app.js", "style.css", "README.md", "COVERAGE.md", "skills/atlas-analytics-data-platform/SKILL.md")
FIXTURE = {"customers": [[10,"north"],[20,"south"]], "orders": [[1,10,100],[2,10,100],[3,999,80],[4,None,None],[5,20,50],[6,20,0]],
           "lines": [[101,1],[102,1],[201,2],[301,3],[401,4],[601,6]]}
# Fixed hand totals: eligible orders 1/2/3/4/6; known 100+100+80+0=280.
ORDER_ROWS = [[1,10,100,"north","101,102"],[2,10,100,"north","201"],[3,999,80,"UNKNOWN_KEY","301"],
              [4,None,None,"NULL_KEY","401"],[6,20,0,"south","601"]]
LINE_ROWS = [[1,10,100,"north","101"],[1,10,100,"north","102"]] + copy.deepcopy(ORDER_ROWS[1:])
EXPECTED = {
    "naive": (LINE_ROWS, [[6,5,1,380,380.0]], "intentional-fanout"),
    "preaggregate": (ORDER_ROWS, [[5,4,1,280,280.0]], "matches-hand-oracle"),
    "semi": (ORDER_ROWS, [[5,4,1,280,280.0]], "matches-hand-oracle"),
    "distinct": (LINE_ROWS, [[6,5,1,180,180.0]], "intentional-value-collapse"),
    "dimension-left": (ORDER_ROWS, [["NULL_KEY",1,0,1,None,0.0],["UNKNOWN_KEY",1,1,0,80,80.0],["north",2,2,0,200,200.0],["south",1,1,0,0,0.0]], "matches-hand-oracle"),
    "dimension-inner": ([ORDER_ROWS[0],ORDER_ROWS[1],ORDER_ROWS[4]], [["north",2,2,0,200,200.0],["south",1,1,0,0,0.0]], "intentional-dimension-loss"),
    "null-only": ([ORDER_ROWS[3]], [[1,0,1,None,0.0]], "boundary-all-null"),
    "empty": ([], [[0,0,0,None,0.0]], "boundary-empty")}


def digest(content):
    return "sha256:" + hashlib.sha256(content).hexdigest()


def object_hash(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def validate(raw, root=HERE):
    assert raw["subject"] == "analytics-data-platform" and raw["schema_version"] == 1
    assert raw["input"] == FIXTURE and raw["input_digest"] == object_hash(FIXTURE)
    assert raw["runtime"]["sqlite_version"] and raw["runtime"]["sqlite_source_id"]
    assert raw["runtime"]["database"] == "in-memory" and raw["runtime"]["foreign_keys"] == 1
    assert raw["metric_definition"] == {"id":"eligible-order-known-amount","grain":"one row per order_id",
        "eligibility":"at least one line exists","amount_unit":"synthetic integer units",
        "null_policy":"SUM known amount; preserve NULL when none known; report missing count",
        "dimension_policy":"retain NULL_KEY and UNKNOWN_KEY separately; no actual customer data"}
    specs = json.loads((root/"queries.json").read_text())
    assert [entry["id"] for entry in raw["queries"]] == list(EXPECTED)
    assert len(specs) == len(EXPECTED)
    verdicts=[]
    for entry,spec in zip(raw["queries"],specs):
        for key,value in spec.items():
            assert entry[key] == value, "SQL/source binding changed: " + key
        relation,metric,classification=EXPECTED[entry["id"]]
        assert entry["classification"] == classification
        assert entry["relation_columns"] == ["order_id","customer_id","amount","bucket","line_refs"]
        columns=["input_rows","known_rows","missing_rows","amount_sum","amount_total"]
        assert entry["metric_columns"] == (["bucket"]+columns if entry["id"].startswith("dimension-") else columns)
        assert entry["relation_rows"] == relation, "grain/lineage differs: " + entry["id"]
        assert entry["metric_rows"] == metric, "hand metric differs: " + entry["id"]
        verdicts.append({"id":entry["id"],"classification":classification,"hand_oracle_rows":metric,
                         "order_reference_known_amount":280,"order_reference_missing":1})
    assert raw["scope"] == {"actual":"SQLite order/line grain SQL on synthetic data","warehouse_product":False,
        "lake_product":False,"bi_product":False,"performance_benchmark":False,"distributed_pipeline":False,"financial_accounting":False}
    return verdicts


def validate_saved(root=HERE):
    folder=root/"evidence"
    inventory=json.loads((folder/"artifacts.json").read_text())
    assert set(inventory)=={"stdout.json","stderr.txt","run.json","verification.json","data.js"}
    assert {p.name for p in folder.iterdir()}==set(inventory)|{"artifacts.json"}
    for name,binding in inventory.items():
        data=(folder/name).read_bytes()
        assert binding=={"digest":digest(data),"bytes":len(data)}, "artifact mismatch: " + name
    raw=json.loads((folder/"stdout.json").read_text())
    report=json.loads((folder/"run.json").read_text())
    verdicts=validate(raw,root)
    assert report["subject"]==raw["subject"] and report["status"]=="passed-with-demonstrated-anomalies"
    assert report["runtime"]==raw["runtime"] and report["input"]==raw["input"]
    assert report["process"]=={"attempts":1,"retries":0,"exit_code":0}
    assert report["started_at"] and report["finished_at"]
    assert report["stdout_digest"]==digest((folder/"stdout.json").read_bytes())
    assert set(report["source_digests"])==set(INPUTS)
    for name in INPUTS:
        assert report["source_digests"][name]==digest((root/name).read_bytes()), "stale source: " + name
    assert json.loads((folder/"verification.json").read_text())=={"oracle":"fixed-hand-grain-and-metric","verdicts":verdicts}
    expected="window.ANALYTICS_LESSON = "+json.dumps({"raw":raw,"run":report,"verdicts":verdicts},sort_keys=True,ensure_ascii=False,separators=(",", ":"))+";\n"
    assert (folder/"data.js").read_text()==expected
    assert json.loads((root/"sources.json").read_text())["third_party_body_saved"] is False
    return raw


def negatives(raw):
    mutations={
        "fanout-hidden":lambda x:x["queries"][0]["metric_rows"][0].__setitem__(3,280),
        "preaggregate-regression":lambda x:x["queries"][1]["metric_rows"][0].__setitem__(3,380),
        "distinct-claimed-correct":lambda x:x["queries"][3]["metric_rows"][0].__setitem__(3,280),
        "unknown-bucket-dropped":lambda x:x["queries"][4]["metric_rows"].pop(1),
        "null-as-zero":lambda x:x["queries"][6]["metric_rows"][0].__setitem__(3,0),
        "empty-as-null-only":lambda x:x["queries"][7]["metric_rows"][0].__setitem__(0,1),
        "lineage-missing":lambda x:x["queries"][1]["relation_rows"][0].__setitem__(4,"101"),
        "same-amount-order-removed":lambda x:x["input"]["orders"].pop(1),
        "missing-query":lambda x:x["queries"].pop(),
        "sql-spoof":lambda x:x["queries"][2].__setitem__("metric_sql","SELECT 280"),
        "grain-spoof":lambda x:x["queries"][0].__setitem__("grain","one row per order_id"),
        "warehouse-overclaim":lambda x:x["scope"].__setitem__("warehouse_product",True)}
    for label,mutate in mutations.items():
        candidate=copy.deepcopy(raw); mutate(candidate)
        try:
            validate(candidate)
        except (AssertionError,KeyError,TypeError):
            continue
        raise AssertionError("negative accepted: "+label)
    return len(mutations)


if __name__=="__main__":
    raw=validate_saved()
    print("PASS: 8 SQL comparisons; independent hand totals/grain/lineage; negative=%d; read-only" % negatives(raw))
