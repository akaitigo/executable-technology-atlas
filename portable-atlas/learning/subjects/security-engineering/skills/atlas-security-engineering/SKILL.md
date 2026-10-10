---
name: atlas-security-engineering
description: Reproduce this synthetic tenant/object authorization lesson with pure Python handlers, an independent permission matrix and lookup-only versus controlled responses. Use for its local actor/resource/operation and rejection cases, not real exploitation, authentication validation, penetration testing or security certification.
---

# Synthetic object-authorization lesson

Resolve links relative to this Skill; module root is two levels above.

- Read [README](../../README.md) for trusted-context assumptions, controls and unsupported scope.
- Run `python3 -B verify.py` and `python3 -B observe.py --check` at module root. Normal checks do not update evidence. `--write` requires an explicit evidence-update request.
- For the core example run `python3 -B runner.py --case actor-a/blue-report/read`; other supported cases appear in [raw observation](../../evidence/observation.json).
- Compare responses and trace to [independent oracle](../../oracle.json), [capture/digests](../../evidence/verification.json), [official locators](../../sources.json) and [UI](../../index.html).

State context actor, server-side tenant, request operation/object, expected matrix cell and actual response before interpreting. Lookup success is not permission. Controlled access requires tenant equality AND the exact operation/resource ID/type grant. Rejection must not return payload. Context identity is assumed authenticated upstream, not validated here. The static preview is not an authorization API.

All input/payload is fictional and public. Do not request credentials, query a real target, perform an attack or infer full OWASP/ASVS coverage. For authentication/token assurance, real product pentests, production policy/race/field-level enforcement, or global security/compliance guarantees, say this module has no evidence and perform no external action. This module-local Skill is not globally installed and does not certify the Subject.
