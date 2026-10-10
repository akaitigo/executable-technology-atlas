#!/usr/bin/env python3
"""Verify copied evidence only. No subprocess, network, JVM or browser is used."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
checks = []

def check(name, condition):
    checks.append({"name": name, "passed": bool(condition)})
    if not condition:
        raise AssertionError(name)

def sha(data):
    return hashlib.sha256(data).hexdigest()

provenance = json.loads((ROOT / "provenance.json").read_text())
for ref in provenance["files"]:
    file = ROOT / ref["local_path"]
    check("copy bytes: " + ref["local_path"], sha(file.read_bytes()) == ref["sha256"])

receipt_path = ROOT / "evidence/evidence/diagnostics/java-nullability-enhancement-process-pilot.json"
check("fixed existing receipt identity", sha(receipt_path.read_bytes()) == "8f24466df0e322257474ce6cf414f095aa09ddf21be0f035e9f832698ee732fb")
receipt = json.loads(receipt_path.read_text())
expected_ref = receipt["inputs"]["expected"]
expected = json.loads((ROOT / "evidence" / expected_ref["path"]).read_text())
for ref in receipt["sources"] + [expected_ref, receipt["harness"]]:
    check("original binding: " + ref["path"], "sha256:" + sha((ROOT / "evidence" / ref["path"]).read_bytes()) == ref["digest"])
check("Kotlin version", receipt["toolchain"]["compiler"]["version"] == "2.4.10")
check("JDK version", receipt["toolchain"]["java"]["version"] == "17.0.17")
check("locked distribution", receipt["toolchain"]["compiler_distribution_digest"] == "sha256:473dd66c7a3ef4b182065b3da670466c1bf2773a9dbb0ed8b33a39fe9d4f876d")
check("source compiler and Java accepted", receipt["compile"]["java"]["exit_code"] == receipt["compile"]["kotlin"]["exit_code"] == 0)
check("exact runtime set", sorted(row["name"] for row in receipt["runtime_cases"]) == ["boundary", "failure", "normal"])
for name, literal in [("normal", "RESULT=5\n"), ("boundary", "RESULT=0\n")]:
    row = next(row for row in receipt["runtime_cases"] if row["name"] == name)
    check(name + " independent expected literal", expected[name]["stdout"] == literal)
    check(name + " digest agrees with independent expected bytes", row["stdout_digest"] == "sha256:" + sha(literal.encode()))
    check(name + " recorded normal exit and matching flags", row["exit_code"] == 0 and row["stdout_matches"] and row["stderr_matches"] and row["oracle_matches"])
    check(name + " empty stderr digest", row["stderr_digest"] == "sha256:" + sha(b""))
failure = next(row for row in receipt["runtime_cases"] if row["name"] == "failure")
check("failure independent expected fragments", expected["failure"]["stderr_contains"] == ["java.lang.NullPointerException", "violatesContract()"])
check("failure recorded exit and match only", failure["exit_code"] == 1 and failure["stderr_matches"] and failure["oracle_matches"])
check("failure raw stderr absent", "stderr" not in failure)
reject = receipt["compile"]["rejection"]
check("compile refusal recorded", reject["exit_code"] == 1 and reject["diagnostic_id"] == "NULL_FOR_NONNULL_TYPE" and reject["diagnostic_id_matches"])
check("refused artifact absent", reject["output_artifact_created"] is False)
check("recorded bytecode facts", receipt["bytecode_oracle"]["intrinsics_check_not_null_expression_value"] is False and receipt["bytecode_oracle"]["direct_string_length_after_enhanced_return"] is True)
check("no stdout or stderr full logs in runtime rows", all("stdout" not in row and "stderr" not in row for row in receipt["runtime_cases"]))
check("no original timestamp claimed", not any(k in receipt for k in ["timestamp", "started_at", "finished_at", "executed_at"]))
check("generated artifacts not retained", receipt["trace"]["resource_stream"]["temporary_artifacts_retained"] is False)
check("legacy completion boundary unchanged", receipt["completion_boundary"]["completion_credit"] is False and receipt["completion_boundary"]["authority_promotion_generated"] is False)
check("local minimal annotation definition", "public @interface NotNull {}" in (ROOT / "evidence/labs/java-nullability-enhancement-process-pilot/java/org/jetbrains/annotations/NotNull.java").read_text())
check("annotation jar is not pilot dependency", provenance["existing_annotation_dependency_inspection"]["used_by_existing_pilot"] is False)
check("no new native execution", provenance["new_native_executions"] == 0)
print(json.dumps({"passed": True, "checks": checks, "check_count": len(checks), "scope": "Copied evidence consistency, not browser QA or independent acceptance", "native_executions": 0, "browser_executions": 0}, indent=2))
