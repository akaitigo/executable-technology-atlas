---
name: atlas-privacy-engineering
description: Reproduce this fictional table lesson comparing direct-identifier projection, quasi-identifier generalization and grouped counts. Use for its declared-QI group sizes and utility boundaries, not real reidentification, legal approval, differential privacy or a privacy guarantee.
---

# Fictional release-projection lesson

Links are relative to this Skill. Module root is two levels above.

- Read [README](../../README.md) for the declared QI, transformations, answers and unimplemented coverage.
- Run `python3 -B verify.py` and `python3 -B observe.py --check` from module root. These do not update raw evidence. Use `--write` only when an evidence update is explicitly requested.
- For a supported query run `python3 -B runner.py --mode generalize --k 4`; modes are drop, generalize, aggregate. Compare to the independent [hand groups](../../hand-groups.json).
- Route to [UI](../../index.html), [raw output](../../evidence/observation.json), [capture/digests](../../evidence/verification.json), and [NIST locators](../../sources.json).

State released columns, source-record count, release-row count, group basis and minimum before interpreting k. Age/zone QI are assumed only for this fixture. Audit members are synthetic lineage, not release columns. Aggregate size describes underlying microdata groups, not the privacy of the count table. Empty minimum/check is undefined, null input is rejected. Changing k does not transform data.

Do not call direct-identifier removal anonymous, or k a full privacy/DP guarantee. These are fabricated records; no external auxiliary linkage or real reidentification was performed. For real individuals, production disclosure approval, l-diversity/attribute guarantees, differential privacy/noise budgets, utility optimization, consent or legal certification, say this module provides no evidence and perform no external action. This module-local Skill is not globally installed and does not certify the Subject.
