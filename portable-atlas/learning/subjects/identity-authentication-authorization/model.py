#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Small deterministic authorization model for scope, inheritance and revocation.

Authentication is an explicit input assumption. This module does not issue or
validate credentials and does not implement OAuth, OIDC, login or WebAuthn.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json


MODEL_VERSION = "authorization-scope-inheritance-revoke-v1"

BASE_POLICY = {
    "revision": "policy-v1",
    "role_inheritance": {"editor": ["viewer"], "viewer": []},
    "role_permissions": {
        "editor": ["document.write"],
        "viewer": ["document.read"],
    },
    "assignments": [
        {"subject": "subject-01", "role": "editor", "scope": "project-alpha"}
    ],
}


def role_closure(policy: dict, role: str) -> list[str]:
    """Return the role followed by inherited roles, rejecting hierarchy cycles."""
    ordered: list[str] = []
    visiting: set[str] = set()

    def visit(current: str) -> None:
        if current in visiting:
            raise ValueError("role hierarchy cycle")
        if current in ordered:
            return
        visiting.add(current)
        ordered.append(current)
        for inherited in policy["role_inheritance"].get(current, []):
            visit(inherited)
        visiting.remove(current)

    visit(role)
    return ordered


def decision_id(policy_revision: str, subject: str, scope: str, resource: str, action: str) -> str:
    material = json.dumps(
        [policy_revision, subject, scope, resource, action],
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "decision-" + hashlib.sha256(material).hexdigest()[:16]


def evaluate(
    policy: dict,
    *,
    authenticated_identity: bool,
    subject: str,
    scope: str,
    resource: str,
    action: str,
) -> dict:
    """Evaluate one fixed-policy request and return an explicit decision trace."""
    trace = [
        {
            "step": "identity-input",
            "status": "assumed-authenticated" if authenticated_identity else "missing",
            "detail": "authentication is an input assumption, not implemented here",
        }
    ]
    common = {
        "model_version": MODEL_VERSION,
        "policy_revision": policy["revision"],
        "decision_id": decision_id(policy["revision"], subject, scope, resource, action),
        "request": {"subject": subject, "scope": scope, "resource": resource, "action": action},
    }
    if not authenticated_identity:
        trace.append({"step": "decision", "status": "deny", "detail": "unauthenticated_input"})
        return {**common, "result": "deny", "reason": "unauthenticated_input", "trace": trace}

    subject_assignments = [row for row in policy["assignments"] if row["subject"] == subject]
    scoped_assignments = [row for row in subject_assignments if row["scope"] == scope]
    if not scoped_assignments:
        observed = sorted({row["scope"] for row in subject_assignments})
        trace.extend(
            [
                {"step": "scope-match", "status": "rejected", "detail": {"requested": scope, "assigned": observed}},
                {"step": "decision", "status": "deny", "detail": "scope_mismatch"},
            ]
        )
        return {**common, "result": "deny", "reason": "scope_mismatch", "trace": trace}

    trace.append({"step": "scope-match", "status": "matched", "detail": scope})
    permission = f"document.{action}"
    for assignment in scoped_assignments:
        roles = role_closure(policy, assignment["role"])
        trace.append({"step": "role-closure", "status": "resolved", "detail": roles})
        for role in roles:
            grants = policy["role_permissions"].get(role, [])
            trace.append({"step": "permission-lookup", "status": "checked", "detail": {"role": role, "grants": grants}})
            if permission in grants:
                inherited = role != assignment["role"]
                trace.append({"step": "decision", "status": "allow", "detail": "inherited_permission" if inherited else "direct_permission"})
                return {
                    **common,
                    "result": "allow",
                    "reason": "inherited_permission" if inherited else "direct_permission",
                    "matched_role": role,
                    "assigned_role": assignment["role"],
                    "role_closure": roles,
                    "trace": trace,
                }
    trace.append({"step": "decision", "status": "deny", "detail": "permission_not_granted"})
    return {**common, "result": "deny", "reason": "permission_not_granted", "trace": trace}


def revoke_viewer_read(policy: dict) -> dict:
    """Return a new policy snapshot with the viewer read grant removed."""
    updated = deepcopy(policy)
    updated["revision"] = "policy-v2-read-grant-revoked"
    updated["role_permissions"]["viewer"] = [
        grant for grant in updated["role_permissions"]["viewer"] if grant != "document.read"
    ]
    return updated


def run_scenarios() -> dict:
    request = {
        "authenticated_identity": True,
        "subject": "subject-01",
        "scope": "project-alpha",
        "resource": "document-001",
        "action": "read",
    }
    inherited = evaluate(BASE_POLICY, **request)
    scope_crossing = evaluate(
        BASE_POLICY,
        authenticated_identity=True,
        subject="subject-01",
        scope="project-beta",
        resource="document-002",
        action="read",
    )
    after_policy = revoke_viewer_read(BASE_POLICY)
    after_revoke = evaluate(after_policy, **request)
    return {
        "schema_version": 1,
        "model_version": MODEL_VERSION,
        "observation_type": "local-fixed-policy-execution",
        "authentication": {"status": "input-assumption", "implemented": False},
        "policy_before": BASE_POLICY,
        "policy_after_revoke": after_policy,
        "scenarios": {
            "role-inheritance": inherited,
            "scope-crossing": scope_crossing,
            "grant-revocation": {"before": inherited, "after": after_revoke},
        },
        "graph": {
            "nodes": ["subject-01", "assignment@project-alpha", "editor", "viewer", "document.read", "document-001"],
            "edges": [
                {"from": "subject-01", "to": "assignment@project-alpha", "kind": "assigned"},
                {"from": "assignment@project-alpha", "to": "editor", "kind": "activates"},
                {"from": "editor", "to": "viewer", "kind": "inherits"},
                {"from": "viewer", "to": "document.read", "kind": "grant-before-revoke"},
                {"from": "document.read", "to": "document-001", "kind": "requested-operation"},
            ],
        },
        "assertions": {
            "inherited_read_allowed": inherited["result"] == "allow" and inherited["reason"] == "inherited_permission",
            "scope_crossing_denied": scope_crossing["result"] == "deny" and scope_crossing["reason"] == "scope_mismatch",
            "before_revoke_allowed": inherited["result"] == "allow",
            "after_revoke_denied": after_revoke["result"] == "deny" and after_revoke["reason"] == "permission_not_granted",
            "authenticated_identity_only_assumed": all(
                row["trace"][0]["status"] == "assumed-authenticated"
                for row in (inherited, scope_crossing, after_revoke)
            ),
        },
    }
