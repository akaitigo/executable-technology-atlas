"""Fictional table projection/aggregation and explicitly declared QI grouping."""
import sys
sys.dont_write_bytecode = True
import argparse
from collections import defaultdict
from copy import deepcopy
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MODES = ("drop", "generalize", "aggregate")
FIELDS = {"synthetic_id", "name", "age", "zone", "category"}
VERSION = "fictional-projection-groups-v1"


def validate(records):
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    seen = set()
    for row in records:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ValueError("unexpected or missing input fields")
        for field in ("synthetic_id", "name", "zone", "category"):
            if not isinstance(row[field], str) or not row[field].strip():
                raise ValueError("null/invalid string: " + field)
        if row["synthetic_id"] in seen:
            raise ValueError("duplicate synthetic_id")
        seen.add(row["synthetic_id"])
        if type(row["age"]) is not int or not 0 <= row["age"] <= 120:
            raise ValueError("age must be an integer 0..120; null not grouped")
        if not re.fullmatch(r"[A-Z][1-9]", row["zone"]):
            raise ValueError("zone must be a fictional letter-digit code")


def process(records, mode, k):
    validate(records)
    if mode not in MODES:
        raise ValueError("unknown projection mode")
    if type(k) is not int or k < 1:
        raise ValueError("k must be positive integer")
    release = []
    groups = defaultdict(list)
    for row in records:
        if mode == "drop":
            qi = (row["age"], row["zone"])
            release.append({"age": row["age"], "zone": row["zone"], "category": row["category"]})
        else:
            lower = (row["age"] // 10) * 10
            qi = (f"{lower}–{lower + 9}", row["zone"][0] + "*")
            release.append({"age_band": qi[0], "zone_group": qi[1], "category": row["category"]})
        groups[qi].append(row["synthetic_id"])
    audit_groups = [{"qi": list(qi), "members": sorted(members), "size": len(members)}
                    for qi, members in sorted(groups.items())]
    if mode == "aggregate":
        release = [{"age_band": g["qi"][0], "zone_group": g["qi"][1], "count": g["size"]} for g in audit_groups]
    columns = {"drop": ["age", "zone", "category"], "generalize": ["age_band", "zone_group", "category"],
               "aggregate": ["age_band", "zone_group", "count"]}[mode]
    sizes = [g["size"] for g in audit_groups]
    minimum = min(sizes) if sizes else None
    return {"mode": mode, "k": k, "release_columns": columns, "release": release,
            "declared_qi": columns[:2], "audit_groups": audit_groups,
            "audit_members_notice": "Synthetic lineage only; members are NOT columns of release output",
            "stats": {"source_records": len(records), "release_rows": len(release), "group_count": len(sizes),
                      "min_group_size": minimum, "singleton_source_records": sum(s for s in sizes if s == 1),
                      "meets_declared_qi_size_rule": minimum >= k if minimum is not None else None,
                      "criterion_status": "meets" if minimum is not None and minimum >= k else "below" if minimum is not None else "undefined-empty",
                      "check_basis": "source microdata partition on declared QI; before aggregate projection"},
            "utility": {"exact_age_retained": mode == "drop", "exact_zone_retained": mode == "drop",
                        "row_category_retained": mode != "aggregate", "individual_rows_retained": mode != "aggregate"},
            "privacy_guarantee": "not-claimed", "differential_privacy": False}


def run_lesson():
    data = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    invalid_examples = []
    for case_id, records, k in (
            ("null-age", [{**data["records"][0], "age": None}], 4),
            ("missing-zone", [{key: value for key, value in data["records"][0].items() if key != "zone"}], 4),
            ("invalid-k", data["records"][:1], 0)):
        try:
            process(records, "generalize", k)
        except ValueError as error:
            invalid_examples.append({"id": case_id, "input": {"records": records, "k": k},
                                     "accepted": False, "error": str(error)})
        else:
            raise AssertionError("invalid demonstration was accepted")
    return {"schema_version": 1, "runner_version": VERSION, "fixture_notice": data["notice"],
            "input_records": deepcopy(data["records"]),
            "runs": [process(data["records"], mode, k) for mode in MODES for k in (2, 4, 5)],
            "boundary_empty": process([], "generalize", 4),
            "invalid_examples": invalid_examples,
            "real_reidentification_performed": False, "subject_completion": "not-claimed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES)
    parser.add_argument("--k", type=int, default=4)
    args = parser.parse_args()
    if args.mode:
        result = process(json.loads((ROOT / "fixture.json").read_text())["records"], args.mode, args.k)
    else:
        result = run_lesson()
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
