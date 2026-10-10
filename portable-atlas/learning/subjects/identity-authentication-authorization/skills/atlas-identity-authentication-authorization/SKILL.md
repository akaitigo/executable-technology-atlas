---
name: atlas-identity-authentication-authorization
description: Use the bounded local authorization lesson to explain or verify exact scope matching, role permission inheritance, and permission-grant revocation. Do not use it as proof of authentication, OAuth/OIDC, WebAuthn, sessions, federation, or complete RBAC/ABAC/ReBAC/capability support.
---

# Authorization scope / inheritance / revocation

Use this skill for questions that can be answered by the module's fixed synthetic policy: `subject-01`, an `editor → viewer` hierarchy, exact `project-alpha` scope, `document.read`, and removal of that permission grant.

## Route

Treat the directory two levels above this file as the module root.

- Read `../../README.md` for assumptions, supported scenarios, Authority locators, and exclusions.
- Run `python3 ../../verify.py` for positive and negative model checks.
- Run `python3 ../../observe.py --check` to bind the answer to the current implementation and `../../evidence/observation.json`.
- Use `../../index.html` and `../../assets/` when a visual comparison of the graph or Decision trace helps.
- Cite `../../sources.json` for the NIST document identifier and locator; do not present the model as standards conformance.

Report the observed `result`, `reason`, Policy revision, and relevant trace steps. Keep the input assumption explicit: Identity is already authenticated, but authentication is not implemented here.

If a request needs credential issuance or validation, OAuth/OIDC/login/WebAuthn, sessions, federation, hierarchy beyond this fixed pair, hierarchical scope, ABAC, ReBAC, capabilities, distributed propagation, or a real product integration, say that the lesson does not cover it. Do not infer an answer from this bounded model or silently expand the policy.
