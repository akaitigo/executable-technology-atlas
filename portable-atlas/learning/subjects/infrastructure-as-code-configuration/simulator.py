"""Finite declaration simulator, no provider, network, shell or external state."""
import copy
import hashlib
import json
import re

SCOPE = "synthetic-iac-v1"


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def digest(value):
    return "sha256:" + hashlib.sha256(encoded(value)).hexdigest()


def validate(value, observed=False):
    required = {"scope", "resources", "revision"} if observed else {"scope", "resources"}
    if not isinstance(value, dict) or set(value) != required or value.get("scope") != SCOPE:
        raise ValueError("unsupported-root-schema")
    if observed and (type(value["revision"]) is not int or value["revision"] < 0):
        raise ValueError("invalid-revision")
    resources = value["resources"]
    if not isinstance(resources, dict) or len(resources) > 6:
        raise ValueError("resource-limit-or-type")
    for ident, attrs in resources.items():
        if re.fullmatch(r"(service|config)\.[a-z][a-z0-9-]{0,20}", ident) is None:
            raise ValueError("unsupported-resource-id")
        if not isinstance(attrs, dict):
            raise ValueError("unsupported-resource-attributes")
        kind = ident.split(".")[0]
        keys = {"replicas", "port", "enabled"} if kind == "service" else {"text"}
        if set(attrs) != keys:
            raise ValueError("unsupported-attribute")
        if any(v is None for v in attrs.values()):
            raise ValueError("unknown-value")
        if kind == "service":
            if type(attrs["replicas"]) is not int or not 0 <= attrs["replicas"] <= 5:
                raise ValueError("invalid-replicas")
            if type(attrs["port"]) is not int or not 1 <= attrs["port"] <= 65535 or type(attrs["enabled"]) is not bool:
                raise ValueError("invalid-service-value")
        elif not isinstance(attrs["text"], str) or len(attrs["text"]) > 80:
            raise ValueError("invalid-config-text")


def diff(desired, observed):
    changes = []
    before, after = observed["resources"], desired["resources"]
    for ident in sorted(set(before) | set(after)):
        old, new = before.get(ident), after.get(ident)
        if old == new:
            continue
        changes.append({"id": ident, "op": "create" if old is None else "delete" if new is None else "update",
                        "before": copy.deepcopy(old), "after": copy.deepcopy(new)})
    return changes


def make_plan(desired, observed):
    plan = {"schema_version": 1, "status": "planned", "scope": SCOPE,
            "desired_digest": digest(desired), "observed_digest": digest(observed),
            "observed_revision": observed.get("revision"), "actions": [], "blocked_reasons": []}
    try:
        validate(desired)
        validate(observed, True)
        plan["actions"] = diff(desired, observed)
    except ValueError as error:
        plan["status"] = "blocked"
        plan["blocked_reasons"] = [str(error)]
    return plan


def apply_plan(plan, desired, observed, trusted_plan_digest, approval=None):
    events = []
    pre = digest(observed)
    def blocked(reason):
        events.append({"event": "blocked", "reason": reason, "mutation_count": 0})
        return {"status": "blocked", "reason": reason, "events": events,
                "state": copy.deepcopy(observed), "pre_digest": pre, "post_digest": pre}
    if digest(plan) != trusted_plan_digest:
        return blocked("plan-digest-mismatch")
    events.append({"event": "plan-binding", "digest": trusted_plan_digest})
    if plan["status"] == "blocked":
        return blocked(plan["blocked_reasons"][0])
    if observed.get("revision") != plan["observed_revision"]:
        return blocked("stale-revision")
    if digest(observed) != plan["observed_digest"]:
        return blocked("stale-observed-hash")
    if digest(desired) != plan["desired_digest"]:
        return blocked("desired-changed")
    if make_plan(desired, observed) != plan:
        return blocked("plan-actions-mismatch")
    deletes = sorted(a["id"] for a in plan["actions"] if a["op"] == "delete")
    if deletes:
        if approval != {"plan_digest": trusted_plan_digest, "delete_ids": deletes}:
            return blocked("delete-approval-required")
        events.append({"event": "synthetic-delete-approval", "plan_digest": trusted_plan_digest, "delete_ids": deletes})
    result = copy.deepcopy(observed)
    for action in plan["actions"]:
        if action["op"] == "delete":
            del result["resources"][action["id"]]
        else:
            result["resources"][action["id"]] = copy.deepcopy(action["after"])
        events.append({"event": "apply", "op": action["op"], "id": action["id"]})
    if plan["actions"]:
        result["revision"] += 1
    events.append({"event": "commit" if plan["actions"] else "noop", "revision": result["revision"],
                   "mutation_count": len(plan["actions"])})
    return {"status": "applied" if plan["actions"] else "noop", "reason": None, "events": events,
            "state": result, "pre_digest": pre, "post_digest": digest(result)}
