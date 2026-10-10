#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Positive and negative checks for the bounded authorization model."""

from copy import deepcopy

from model import BASE_POLICY, evaluate, revoke_viewer_read, role_closure, run_scenarios


def expect_error(operation, expected: str) -> None:
    try:
        operation()
    except ValueError as error:
        assert str(error) == expected
    else:
        raise AssertionError(f"expected ValueError: {expected}")


def main() -> int:
    observed = run_scenarios()
    assert all(observed["assertions"].values())
    assert observed["scenarios"]["role-inheritance"]["role_closure"] == ["editor", "viewer"]
    assert observed["scenarios"]["scope-crossing"]["reason"] == "scope_mismatch"
    assert observed["scenarios"]["grant-revocation"]["before"]["result"] == "allow"
    assert observed["scenarios"]["grant-revocation"]["after"]["result"] == "deny"

    unauthenticated = evaluate(
        BASE_POLICY,
        authenticated_identity=False,
        subject="subject-01",
        scope="project-alpha",
        resource="document-001",
        action="read",
    )
    assert unauthenticated["result"] == "deny" and unauthenticated["reason"] == "unauthenticated_input"

    unknown_action = evaluate(
        BASE_POLICY,
        authenticated_identity=True,
        subject="subject-01",
        scope="project-alpha",
        resource="document-001",
        action="delete",
    )
    assert unknown_action["result"] == "deny" and unknown_action["reason"] == "permission_not_granted"

    cyclic = deepcopy(BASE_POLICY)
    cyclic["role_inheritance"]["viewer"] = ["editor"]
    expect_error(lambda: role_closure(cyclic, "editor"), "role hierarchy cycle")

    revoked = revoke_viewer_read(BASE_POLICY)
    assert BASE_POLICY["role_permissions"]["viewer"] == ["document.read"]
    assert revoked["role_permissions"]["viewer"] == []
    print("authorization model: 9 assertions verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
