#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Calculate binary evaluation metrics for fixed synthetic predictions."""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = "binary-evaluation-threshold-v1"
THRESHOLDS = (0.30, 0.50, 0.80, 0.90)


def unit_number(value, name):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{name} must be a finite number in [0,1]")
    return float(value)


def validate_samples(samples):
    if not isinstance(samples, list) or not samples:
        raise ValueError("samples must be a nonempty list")
    seen = set()
    for sample in samples:
        if not isinstance(sample, dict) or set(sample) != {"id", "label", "score"}:
            raise ValueError("sample must contain exactly id, label, score")
        sample_id = sample["id"]
        if not isinstance(sample_id, str) or not sample_id or sample_id in seen:
            raise ValueError("sample IDs must be nonempty unique strings")
        seen.add(sample_id)
        if type(sample["label"]) is not int or sample["label"] not in (0, 1):
            raise ValueError("label must be integer 0 or 1")
        unit_number(sample["score"], "score")


def ratio(numerator, denominator):
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
        "status": "defined" if denominator else "undefined-zero-denominator",
    }


def evaluate(samples, threshold):
    threshold = unit_number(threshold, "threshold")
    validate_samples(samples)
    counts = dict.fromkeys(("TP", "FN", "FP", "TN"), 0)
    decisions = []
    for sample in samples:
        prediction = int(sample["score"] >= threshold)
        outcome = ("TP" if prediction else "FN") if sample["label"] else ("FP" if prediction else "TN")
        counts[outcome] += 1
        decisions.append({**sample, "prediction": prediction, "outcome": outcome})
    tp, fn, fp, tn = (counts[key] for key in ("TP", "FN", "FP", "TN"))
    return {
        "threshold": threshold,
        "threshold_rule": "score >= threshold predicts 1",
        "counts": counts,
        "metrics": {
            "accuracy": ratio(tp + tn, len(samples)),
            "precision": ratio(tp, tp + fp),
            "recall": ratio(tp, tp + fn),
            "fpr": ratio(fp, fp + tn),
        },
        "decisions": decisions,
    }


def observation():
    fixture = json.loads((ROOT / "predictions.json").read_text(encoding="utf-8"))
    samples = fixture["samples"]
    results = [evaluate(samples, threshold) for threshold in THRESHOLDS]
    return {
        "schema_version": 1,
        "implementation_version": VERSION,
        "observation_type": "executed-python-stdlib-metric-calculation",
        "fixture_id": fixture["id"],
        "sample_count": len(samples),
        "actual_positive_count": sum(sample["label"] for sample in samples),
        "actual_negative_count": sum(1 - sample["label"] for sample in samples),
        "score_origin": "authored synthetic fixture; no model trained or called",
        "zero_denominator_policy": "null plus undefined-zero-denominator status; never substituted with 0 or 1",
        "results": results,
        "subject_completion": "not-claimed",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float)
    args = parser.parse_args()
    if args.threshold is None:
        result = observation()
    else:
        samples = json.loads((ROOT / "predictions.json").read_text(encoding="utf-8"))["samples"]
        result = evaluate(samples, args.threshold)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
