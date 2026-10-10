---
name: atlas-cryptography-engineering
description: Reproduce and explain this HMAC-SHA256 lesson with publicly disclosed synthetic keys, tampering rejection and the separate local replay-state boundary. Use for the module's MAC comparisons, not production key management, encryption, public-key signatures or cryptography certification.
---

# Local HMAC and replay-state lesson

All links are relative to this Skill. Module root is two levels above.

- Read [README](../../README.md) for the prediction questions, results and unimplemented scope.
- Run `python3 -B verify.py` and `python3 -B observe.py --check` at module root. These are read-only; do not regenerate evidence unless an update is requested explicitly.
- For a supported condition run `python3 -B runner.py --scenario replay` (or valid, message-tamper, wrong-key, tag-tamper, truncated-tag, malformed-tag).
- Bind answers to [raw observation](../../evidence/observation.json), [capture/digests](../../evidence/verification.json), [RFC oracle](../../oracle.json), and [official locators](../../sources.json).
- Use [UI](../../index.html) to compare raw bytes, actual tag and MAC vs authenticated-ID memory. It displays saved outputs, not live crypto computation.

Call HMAC a shared-key MAC, not a public-key digital signature. Keys here are publicly disclosed synthetic fixture material; never request real keys or recommend their production use. A valid replay passes MAC but the seeded local guard rejects duplicate authenticated message_id. Resetting the guard loses that memory. Do not extrapolate this single-process guard to durable/distributed freshness.

`compare_digest` use is not timing evidence. No constant-time benchmark or proof exists in this lesson. For encryption, certificates, production rotation/KMS, nonrepudiation, key generation, LLM safety or other unsupported requests, say this module has no evidence and route no external action. This module-local Skill is not globally installed and does not certify the Subject.
