"""Independent transition table and byte hash oracle. No runner import."""
import hashlib
import json

# Finite teaching cases, not an implementation of a production release policy.
TRANSITIONS = {
    "normal": [("build", "ok"), ("test", "passed"), ("candidate", "accepted"), ("promotion", "promoted")],
    "test-swap": [("build", "ok"), ("test", "passed"), ("substitution", "injected"), ("candidate", "refused")],
    "promotion-swap": [("build", "ok"), ("test", "passed"), ("candidate", "accepted"), ("substitution", "injected"), ("promotion", "refused")],
    "failed-test": [("build", "ok"), ("test", "failed"), ("candidate", "refused")],
    "missing-history": [("build", "ok"), ("test", "passed"), ("candidate", "accepted"), ("promotion", "promoted")],
}


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def check(plan, actual):
    original = bytes.fromhex(plan["previous_hex"]) if plan["previous_hex"] else None
    built = bytes.fromhex(plan["build_hex"])
    substituted = bytes.fromhex(plan["replacement_hex"])
    old, new = digest(original) if original else None, digest(built)
    expected = list(TRANSITIONS[plan["case"]])
    promoted = plan["case"] in ("normal", "missing-history")
    rollback = "not-requested" if not plan["rollback"] else ("not-attempted" if not promoted else ("rolled-back" if original else "refused"))
    expected.append(("rollback", rollback))
    transition_match = [(e["stage"], e["status"]) for e in actual["events"]] == expected
    state_match, hashes_match = True, True
    current, history = old, None
    workspace = built
    candidate = None
    # A separate parser derives the expected test result from actual bytes.
    obj = json.loads(built[len(b"ATLAS-SYNTHETIC\x00"):])
    passed = obj["ready"] is True and obj["release"] in (1, 2, 3) and obj["format"] == "atlas-synthetic-v1"
    expected_objects = {} if original is None else {old: original}
    test = None
    guards_match = True
    for index, event in enumerate(actual["events"]):
        stage, status = expected[index] if index < len(expected) else (None, None)
        if stage == "test":
            policy_raw = json.dumps({"format": "atlas-synthetic-v1", "release": "integer 1..3", "ready": True},sort_keys=True,separators=(",", ":")).encode()
            test = {"artifact_digest": new, "policy_digest": digest(policy_raw),
                    "checks": {"header": True, "schema": True, "ready": passed}, "passed": passed}
        elif stage == "substitution":
            workspace = substituted
        elif stage == "candidate":
            guards_match &= event["guards"] == {"test_passed": passed, "test_digest_matches": digest(workspace) == new}
            if status == "accepted":
                expected_objects[new] = built
                record_raw = json.dumps(test, sort_keys=True, separators=(",", ":")).encode()
                candidate = {"artifact_digest": new, "test_record_digest": digest(record_raw)}
        elif stage == "promotion":
            guards_match &= event["guards"] == {"test_passed": passed, "workspace_matches": digest(workspace) == new,
                    "test_digest_matches": True, "test_record_matches": True, "stored_bytes_match": True}
            if status == "promoted":
                history, current = current, new
        elif stage == "rollback":
            guards_match &= event["guards"] == ({"stored_bytes_match":True} if status == "rolled-back" else {})
            if status == "rolled-back": current = old
        if stage in ("build", "test", "substitution"):
            guards_match &= event["guards"] == {}
        expected_snapshot = {k: {"bytes":len(b), "hex":b.hex()} for k,b in expected_objects.items()}
        state_match &= (event["seq"] == index and event["active"] == current and event["previous"] == history
                        and event["objects"] == expected_snapshot and event["test"] == test and event["candidate"] == candidate)
        hashes_match &= event["working_digest"] == digest(workspace) and event["working_hex"] == workspace.hex()
        hashes_match &= all(digest(bytes.fromhex(v["hex"])) == k and len(bytes.fromhex(v["hex"])) == v["bytes"] for k,v in event["objects"].items())
    expected_summary = {"test_passed": passed, "candidate_accepted": candidate is not None, "promoted": promoted,
                        "rollback_status": rollback, "active": current, "original_active": old, "previous_bytes_unchanged": True,
                        "history_present_initially": original is not None, "trace_events": len(expected)}
    plan_raw = json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
    summary_match = (actual["summary"] == expected_summary and actual["final"] == actual["events"][-1]
                     and actual["plan"] == plan and actual["plan_digest"] == digest(plan_raw))
    return {"transition_matches": transition_match, "state_matches": bool(state_match), "hashes_match": bool(hashes_match),
            "guards_match": bool(guards_match), "summary_matches": summary_match,
            "all_match": bool(transition_match and state_match and hashes_match and guards_match and summary_match),
            "expected_transitions": expected, "expected_summary": expected_summary}
