"""Independent ID/revision/set coverage and tuple queue oracle. No app/runner import."""
import hashlib
import json


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",", ":"),ensure_ascii=False).encode()).hexdigest()


def tuple_trace(ops, capacity, overflow=False):
    state=(); trace=[]
    for index, op in enumerate(ops):
        before=state
        if op["op"] == "enqueue":
            output=len(state)<capacity or overflow
            state=state+(op["value"],) if output else state
        else:
            output=state[0] if state else None
            state=state[1:] if state else state
        trace.append({"step":index,"operation":op,"before":list(before),"output":output,"after":list(state)})
    return trace


def declared_operations(test_id, capacity):
    values=tuple("ABC")[:capacity]
    enqueues=[{"op":"enqueue","value":v} for v in values]
    return {"T-CAP-FILL":enqueues, "T-CAP-OVER":enqueues+[{"op":"enqueue","value":"Z"}],
            "T-FIFO":enqueues+[{"op":"dequeue"} for _ in values], "T-EMPTY":[{"op":"dequeue"}]}[test_id]


def oracle_rows(requirements, proofs, binding):
    rows=[]
    for r in requirements:
        statuses=[]; details=[]
        for test_id in r["required_tests"]:
            candidates=[p for p in proofs if (p["requirement_id"],p["test_id"])==(r["id"],test_id)]
            current=[]; rejected=[]
            for p in candidates:
                reasons=[]
                checks=[("evidence-digest-mismatch",p["evidence_digest"]==digest({k:v for k,v in p.items() if k!="evidence_digest"})),
                        ("requirement-revision-stale",p["requirement_revision"]==r["revision"]),
                        ("requirement-content-stale",p["requirement_digest"]==digest(r)),
                        ("app-config-stale",p["app_digest"]==binding["app_digest"]),
                        ("harness-stale",p["harness_digest"]==binding["harness_digest"]),
                        ("test-result-inconsistent",p["passed"]==(p["actual"]==p["expected"])),
                        ("test-operations-inconsistent",p["operations"]==declared_operations(test_id,p["config"]["capacity"]))]
                reasons=[name for name, ok in checks if not ok]
                if reasons: rejected.append({"evidence_id":p["evidence_id"],"reasons":reasons})
                else: current.append(p)
            states={p["passed"] for p in current}
            s="missing" if not candidates else ("stale" if not current else ("failed" if False in states else "passed"))
            statuses.append(s); details.append({"test_id":test_id,"status":s,"current_evidence":[p["evidence_id"] for p in current],"rejected_evidence":rejected})
        unique=set(statuses)
        state="verified-local" if unique=={"passed"} else ("orphan" if unique=={"missing"} else ("failed" if "failed" in unique else ("missing-proof" if "missing" in unique else "stale")))
        rows.append({"requirement_id":r["id"],"revision":r["revision"],"statement":r["statement"],"requirement_digest":digest(r),"status":state,"checks":details})
    return rows


def check(plan, actual, current_binding):
    proofs=actual["proofs"]; ids=[p["evidence_id"] for p in proofs]
    expected_rows=oracle_rows(plan["current_requirements"],proofs,current_binding)
    pairs={(r["id"],t) for r in plan["current_requirements"] for t in r["required_tests"]}
    unmapped=[p["evidence_id"] for p in proofs if (p["requirement_id"],p["test_id"]) not in pairs]
    expected_matrix={"rows":expected_rows,"unmapped_evidence":unmapped,"verified":sum(r["status"]=="verified-local" for r in expected_rows),
                     "total":len(expected_rows),"finite_checks_complete":bool(expected_rows) and all(r["status"]=="verified-local" for r in expected_rows) and not unmapped,
                     "stakeholder_approved":False,"whole_requirements_complete":False}
    coverage_match=actual["final_matrix"]==expected_matrix and len(ids)==len(set(ids))
    raw_match=True
    for p in proofs:
        observed=tuple_trace(p["operations"],p["config"]["capacity"],p["config"]["inject_overflow_bug"])
        contract=tuple_trace(p["operations"],p["config"]["capacity"],False)
        raw_match &= (p["actual"]==observed and p["expected"]==contract and p["passed"]==(observed==contract)
                      and p["operations"]==declared_operations(p["test_id"],p["config"]["capacity"])
                      and p["app_digest"]==digest({"source":current_binding["app_source_digest"],"config":p["config"]})
                      and p["evidence_digest"]==digest({k:v for k,v in p.items() if k!="evidence_digest"}))
    b={r["id"]:r for r in plan["initial_requirements"]}; a={r["id"]:r for r in plan["current_requirements"]}
    diff={"added":[a[k] for k in sorted(set(a)-set(b))],"removed":[b[k] for k in sorted(set(b)-set(a))],
          "changed":[{"id":k,"before":b[k],"after":a[k]} for k in sorted(set(a)&set(b)) if a[k]!=b[k]]}
    diff_match=actual["diff"]==diff
    events_match=all(e["seq"]==i for i,e in enumerate(actual["events"])) and actual["events"][-1]["matrix"]==expected_matrix
    # Compare intermediate snapshots too, without calling classify.
    by_id={p["evidence_id"]:p for p in proofs}
    for e in actual["events"]:
        ep=[by_id[k] for k in e["evidence_ids"]]
        source_digest=current_binding["app_source_digest"]
        app_digest=digest({"source":source_digest,"config":e["config"]})
        eb={"app_digest":app_digest,"harness_digest":current_binding["harness_digest"]}
        rows=oracle_rows(e["requirements"],ep,eb)
        event_pairs={(r["id"],t) for r in e["requirements"] for t in r["required_tests"]}
        extras=[p["evidence_id"] for p in ep if (p["requirement_id"],p["test_id"]) not in event_pairs]
        em={"rows":rows,"unmapped_evidence":extras,"verified":sum(r["status"]=="verified-local" for r in rows),
            "total":len(rows),"finite_checks_complete":bool(rows) and all(r["status"]=="verified-local" for r in rows) and not extras,
            "stakeholder_approved":False,"whole_requirements_complete":False}
        events_match &= e["matrix"]==em
    return {"coverage_matches":coverage_match,"raw_queue_matches":bool(raw_match),"diff_matches":diff_match,"events_match":bool(events_match),
            "plan_matches":actual["plan"]==plan and actual["plan_digest"]==digest(plan),
            "all_match":bool(coverage_match and raw_match and diff_match and events_match and actual["plan"]==plan and actual["plan_digest"]==digest(plan)),
            "expected_matrix":expected_matrix,"expected_diff":diff}
