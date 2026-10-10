---
name: atlas-ai-evaluation-safety
description: Explain and reproduce confusion matrices, precision, recall, false-positive rate, and threshold tradeoffs on the module's fixed synthetic binary predictions. Use for this bounded metric lesson, not for training, LLM safety, fairness or real-model certification.
---

# Fixed binary evaluation lesson

Resolve all links below relative to this Skill directory. The module root is two levels above.

- Read [README](../../README.md) for the four thresholds, formulas and interpretation.
- Run `python3 verify.py` from the module root to compare the actual calculator with [hand-count.json](../../hand-count.json) and reject invalid inputs.
- Run `python3 observe.py --check` from the same root for input/source/output bindings. Use `python3 evaluate.py --threshold 0.50` for a requested supported threshold calculation.
- Read [observation.json](../../evidence/observation.json) and [verification.json](../../evidence/verification.json) for values and execution conditions.
- Use [index.html](../../index.html) and [assets](../../assets/) for the matrix, score distribution and FP/FN comparison.
- Cite the official source locators in [sources.json](../../sources.json) when explaining definitions.

State the matrix counts and denominators before interpreting a percentage. Treat `null / undefined-zero-denominator` as undefined. The UI replays saved Python output; scores are authored synthetic data.

For training, real-model deployment thresholds, LLM safety, fairness, protected attributes, calibration, confidence intervals or other unsupported evaluation, report that this module supplies no evidence for the request. Do not infer safety from Accuracy or extrapolate this fixture to a real population. This Skill is a local lesson entrypoint; it is not installed globally and does not certify the Subject.
