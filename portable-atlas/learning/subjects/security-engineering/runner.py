"""Pure in-memory synthetic handlers, not an HTTP authorization service."""
import sys
sys.dont_write_bytecode = True
import argparse
from copy import deepcopy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = "tenant-object-handler-v1"


def fixture():
    return json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))


def outcome(status, reason, trace, body=None):
    public_error = {400: "invalid-request", 401: "unauthorized", 403: "forbidden", 404: "not-found"}
    return {"response": {"status": status, "body": deepcopy(body) if status == 200 else {"error": public_error[status]}},
            "decision": {"reason": reason, "trace": deepcopy(trace)}}


def precheck(context, request, data, trace):
    valid = isinstance(request, dict) and set(request) == {"object_id", "operation"}
    valid = valid and all(isinstance(request[k], str) and request[k] for k in ("object_id", "operation"))
    trace.append({"control": "request-schema", "passed": bool(valid)})
    if not valid:
        return None, outcome(400, "invalid-request", trace)
    if context is None or (isinstance(context, dict) and context == {"actor_id": None}):
        trace.append({"control": "authenticated-context", "passed": False})
        return None, outcome(401, "unauthenticated", trace)
    if not isinstance(context, dict) or set(context) != {"actor_id"} or not isinstance(context["actor_id"], str) or not context["actor_id"]:
        trace.append({"control": "context-schema", "passed": False})
        return None, outcome(400, "invalid-context", trace)
    actor = data["actors"].get(context["actor_id"])
    trace.append({"control": "authenticated-context", "passed": actor is not None})
    if actor is None:
        return None, outcome(401, "unknown-actor", trace)
    supported = request["operation"] in data["operations"]
    trace.append({"control": "supported-operation", "passed": supported})
    if not supported:
        return None, outcome(403, "unsupported-operation", trace)
    return actor, None


def handle(context, request, data, *, fixed):
    trace = []
    actor, error = precheck(context, request, data, trace)
    if error:
        return error
    record = data["records"].get(request["object_id"])
    trace.append({"control": "object-lookup", "passed": record is not None})
    if record is None:
        return outcome(404, "unknown-record", trace)
    if not fixed:
        trace.append({"control": "object-authorization", "enabled": False, "passed": None})
        return outcome(200, "lookup-only", trace, {"object_id": request["object_id"], **record})
    same_tenant = actor["tenant"] == record["tenant"]
    trace.append({"control": "tenant-boundary", "passed": same_tenant})
    if not same_tenant:
        return outcome(403, "tenant-mismatch", trace)
    expected_grant = {"operation": request["operation"], "resource_id": request["object_id"],
                      "resource_type": record["resource_type"]}
    granted = expected_grant in actor["grants"]
    trace.append({"control": "operation-resource-grant", "passed": granted})
    if not granted:
        return outcome(403, "no-grant", trace)
    return outcome(200, "allowed", trace, {"object_id": request["object_id"], **record})


def lookup_only(context, request, data):
    return handle(context, request, data, fixed=False)


def controlled(context, request, data):
    return handle(context, request, data, fixed=True)


def compare(case_id, context, request, data):
    return {"id": case_id, "context": deepcopy(context), "request": deepcopy(request),
            "lookup_only": lookup_only(context, request, data), "controlled": controlled(context, request, data)}


def run_lesson():
    data = fixture()
    oracle = json.loads((ROOT / "oracle.json").read_text(encoding="utf-8"))
    rows = []
    # Enumerate the fixture, not the expected Oracle: missing matrix entries must fail checks.
    for actor in data["actors"]:
        for resource in data["records"]:
            for operation in data["operations"]:
                rows.append(compare(f"{actor}/{resource}/{operation}", {"actor_id": actor},
                                    {"object_id": resource, "operation": operation}, data))
    base = {"object_id": "red-report", "operation": "read"}
    boundary = [
        ("unauthenticated", None, base),
        ("unknown-actor", {"actor_id": "actor-unknown"}, base),
        ("unknown-record", {"actor_id": "actor-a"}, {**base, "object_id": "not-present"}),
        ("invalid-object-type", {"actor_id": "actor-a"}, {**base, "object_id": 1}),
        ("invalid-operation-type", {"actor_id": "actor-a"}, {**base, "operation": None}),
        ("unsupported-operation", {"actor_id": "actor-a"}, {**base, "operation": "delete"}),
        ("tenant-in-request", {"actor_id": "actor-a"}, {**base, "tenant": "tenant-blue"})
    ]
    return {"schema_version": 1, "runner_version": VERSION, "fixture_notice": data["notice"],
            "fixture": data, "matrix_runs": rows,
            "permission_oracle": oracle["matrix"], "boundary_oracle": oracle["boundary_expected"],
            "boundary_runs": [compare(cid, context, request, data) for cid, context, request in boundary],
            "authentication_assumption": "trusted upstream context identifies actor; no token/password validation implemented",
            "external_attack_performed": False, "subject_completion": "not-claimed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case")
    args = parser.parse_args()
    lesson = run_lesson()
    if args.case:
        rows = lesson["matrix_runs"] + lesson["boundary_runs"]
        selected = next((r for r in rows if r["id"] == args.case), None)
        if selected is None:
            parser.error("unknown synthetic case")
        lesson = selected
    print(json.dumps(lesson, ensure_ascii=False, indent=2, allow_nan=False))
