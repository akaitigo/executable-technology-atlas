#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent fixed case oracle. No server/client implementation import or network."""
import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
INPUTS=("experiment.py","client.py","cases.json","contract.json","verify.py","observe.py","test_contract.py",
        "sources.json","index.html","app.js","style.css","README.md","COVERAGE.md","skills/atlas-api-integration-contracts/SKILL.md")
EXPECTED={
    "base":(200,"application/json",'{"id":7,"name":"sample"}',"accepted",True),
    "optional":(200,"application/json; charset=utf-8",'{"id":7,"name":"sample","note":"v2","extra":true}',"accepted",True),
    "missing":(200,"application/json",'{"id":7}',"required-rejected",False),
    "type-changed":(200,"application/json",'{"id":"7","name":"sample"}',"type-rejected",False),
    "boolean-id":(200,"application/json",'{"id":true,"name":"sample"}',"type-rejected",False),
    "status-changed":(201,"application/json",'{"id":7,"name":"sample"}',"status-rejected",False),
    "media-changed":(200,"text/plain",'{"id":7,"name":"sample"}',"media-rejected",False),
    "malformed":(200,"application/json",'{"id":7,',"json-rejected",False),
    "empty-body":(200,"application/json","","json-rejected",False),
    "api-error":(422,"application/json",'{"error":{"code":"invalid_input","message":"synthetic rejection"}}',"handled-api-error",False),
    "bad-error":(422,"application/json",'{"id":7,"name":"sample"}',"error-schema-rejected",False),
    "timeout":(200,"application/json",'{"id":7,"name":"late"}',"timeout",False)}
STEPS={"accepted":[("status","pass"),("content-type","pass"),("json","pass"),("success-schema","pass")],
       "required-rejected":[("status","pass"),("content-type","pass"),("json","pass"),("success-schema","reject")],
       "type-rejected":[("status","pass"),("content-type","pass"),("json","pass"),("success-schema","reject")],
       "status-rejected":[("status","reject")],"media-rejected":[("status","pass"),("content-type","reject")],
       "json-rejected":[("status","pass"),("content-type","pass"),("json","reject")],
       "handled-api-error":[("status","pass"),("content-type","pass"),("json","pass"),("error-schema","pass")],
       "error-schema-rejected":[("status","pass"),("content-type","pass"),("json","pass"),("error-schema","reject")],
       "timeout":[("transport","timeout")]}


def digest(data):
    return "sha256:"+hashlib.sha256(data).hexdigest()


def validate(raw,root=HERE):
    assert raw["subject"]=="api-integration-contracts" and raw["schema_version"]==1
    contract=json.loads((root/"contract.json").read_text())
    cases=json.loads((root/"cases.json").read_text())
    assert raw["input"]["contract"]==contract and raw["input"]["cases"]==cases
    assert contract["success_status"]==200 and contract["error_status"]==422 and contract["media_type"]=="application/json"
    assert contract["success_schema"]=={"type":"object","required":["id","name"],"properties":{"id":{"type":"integer","minimum":1},"name":{"type":"string","minLength":1},"note":{"type":"string"}},"additionalProperties":True}
    assert contract["error_schema"]=={"type":"object","required":["error"],"properties":{"error":{"type":"object","required":["code","message"],"properties":{"code":{"type":"string","minLength":1},"message":{"type":"string","minLength":1}}}}}
    assert raw["input"]["body_budget_bytes"]==8192
    assert raw["input"]["request_schedule"]=="12 sequential GETs; no automatic retry"
    assert raw["input"]["timeout_design"]=="socket timeout 0.1s for delayed case; 2s otherwise; outer observation subprocess budget 15s"
    assert raw["endpoint"]["host"]=="127.0.0.1" and 0<raw["endpoint"]["port"]<65536
    assert raw["runtime"]["python_version"] and raw["runtime"]["http_version"]=="HTTP/1.1"
    assert raw["runtime"]["client"]=="stdlib http.client.HTTPConnection" and raw["runtime"]["server"]=="stdlib http.server.HTTPServer"
    assert raw["cleanup"]=={"server_closed":True,"thread_alive":False,"port_connection_refused":True}
    assert [x["id"] for x in raw["observations"]]==list(EXPECTED)
    assert [x["id"] for x in cases]==list(EXPECTED)
    assert len(raw["server_events"])==12
    verdicts=[]
    for observation,event,case in zip(raw["observations"],raw["server_events"],cases):
        case_id=observation["id"]; status,media,body,outcome,accepted=EXPECTED[case_id]
        assert (case["status"],case["content_type"],case["body"])==(status,media,body)
        delay=0.6 if case_id=="timeout" else 0
        assert case["delay_seconds"]==delay and event["delay_seconds"]==delay
        request={"method":"GET","path":"/cases/"+case_id,"headers":{"Accept":"application/json","Connection":"close"},"body":None}
        assert observation["request"]==request
        assert event["method"]=="GET" and event["path"]==request["path"]
        assert event["headers"]["Host"]=="127.0.0.1:"+str(raw["endpoint"]["port"])
        assert event["headers"]["Accept"]=="application/json" and event["headers"]["Connection"]=="close"
        assert event["intended_status"]==status and event["intended_body_digest"]==digest(body.encode())
        assert event["finished"] is True and event["write_result"] in ("completed","peer-closed")
        assert observation["attempts"]==1 and observation["retries"]==0
        assert observation["socket_timeout_seconds"]==(0.1 if case_id=="timeout" else 2.0)
        assert 0<=observation["elapsed_ms"]<3000
        decision=observation["decision"]
        assert decision["outcome"]==outcome and decision["accepted"] is accepted
        assert decision["item"]==({"id":7,"name":"sample"} if accepted else None)
        assert [(s["gate"],s["verdict"]) for s in decision["steps"]]==STEPS[outcome]
        assert all(type(s["detail"]) is str and s["detail"] for s in decision["steps"])
        response=observation["response"]
        if case_id=="timeout":
            assert observation["transport"]=="timeout" and response is None
            assert observation["elapsed_ms"]>=80
        else:
            assert observation["transport"]=="response" and event["write_result"]=="completed"
            assert response["status"]==status and response["headers"]["Content-Type"]==media
            assert response["headers"]["Content-Length"]==str(len(body.encode()))
            assert response["headers"]["Connection"]=="close"
            assert response["body_text"]==body and response["body_hex"]==body.encode().hex()
            assert response["body_bytes"]==len(body.encode()) and response["body_digest"]==digest(body.encode())
        verdicts.append({"id":case_id,"expected_outcome":outcome,"expected_accepted":accepted,
                         "classification":"compatible" if accepted else "handled-error" if outcome=="handled-api-error" else "expected-rejection"})
    assert raw["scope"]=={"actual":"stdlib loopback HTTP requests/responses with fixed handwritten JSON contract",
        "external_api":False,"real_auth":False,"tls":False,"full_http_spec":False,"general_json_schema":False,
        "retry_correctness":False,"production_server":False}
    return verdicts


def validate_saved(root=HERE):
    folder=root/"evidence"; inventory=json.loads((folder/"artifacts.json").read_text())
    assert set(inventory)=={"stdout.json","stderr.txt","run.json","verification.json","data.js"}
    assert {p.name for p in folder.iterdir()}==set(inventory)|{"artifacts.json"}
    for name,binding in inventory.items():
        data=(folder/name).read_bytes()
        assert binding=={"digest":digest(data),"bytes":len(data)},"artifact mismatch: "+name
    raw=json.loads((folder/"stdout.json").read_text()); report=json.loads((folder/"run.json").read_text())
    verdicts=validate(raw,root)
    assert report["subject"]==raw["subject"] and report["status"]=="passed-with-demonstrated-rejections"
    assert report["runtime"]==raw["runtime"] and report["input"]==raw["input"]
    assert report["process"]=={"attempts":1,"retries":0,"exit_code":0,"timeout_seconds":15}
    assert datetime.fromisoformat(report["started_at"])<=datetime.fromisoformat(report["finished_at"])
    assert report["stdout_digest"]==digest((folder/"stdout.json").read_bytes())
    assert set(report["source_digests"])==set(INPUTS)
    for name in INPUTS:
        assert report["source_digests"][name]==digest((root/name).read_bytes()),"stale source: "+name
    assert json.loads((folder/"verification.json").read_text())=={"oracle":"independent-fixed-wire-and-contract-cases","verdicts":verdicts}
    expected="window.API_LESSON = "+json.dumps({"raw":raw,"run":report,"verdicts":verdicts},sort_keys=True,ensure_ascii=False,separators=(",", ":"))+";\n"
    assert (folder/"data.js").read_text()==expected
    assert json.loads((root/"sources.json").read_text())["third_party_body_saved"] is False
    return raw


def negatives(raw):
    mutations={"missing-accepted":lambda x:x["observations"][2]["decision"].__setitem__("accepted",True),
        "type-coerced":lambda x:x["observations"][3]["decision"].__setitem__("outcome","accepted"),
        "bool-as-int":lambda x:x["observations"][4]["decision"].__setitem__("outcome","accepted"),
        "any-2xx":lambda x:x["observations"][5]["decision"].__setitem__("outcome","accepted"),
        "mime-ignored":lambda x:x["observations"][6]["decision"].__setitem__("outcome","accepted"),
        "invalid-json-hidden":lambda x:x["observations"][7]["response"].__setitem__("body_text",'{}'),
        "empty-success":lambda x:x["observations"][8]["decision"].__setitem__("accepted",True),
        "error-as-success":lambda x:x["observations"][9]["decision"].__setitem__("accepted",True),
        "bad-error-accepted":lambda x:x["observations"][10]["decision"].__setitem__("outcome","handled-api-error"),
        "timeout-response-invented":lambda x:x["observations"][11].__setitem__("response",{}),
        "retry-hidden":lambda x:x["observations"][11].__setitem__("retries",1),
        "missing-request":lambda x:x["server_events"].pop(),
        "gate-skipped":lambda x:x["observations"][0]["decision"]["steps"].pop(),
        "cleanup-leak":lambda x:x["cleanup"].__setitem__("thread_alive",True),
        "external-overclaim":lambda x:x["scope"].__setitem__("external_api",True)}
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
    print("PASS: 12 real HTTP cases; independent wire/contract oracle; negative=%d; read-only" % negatives(raw))
