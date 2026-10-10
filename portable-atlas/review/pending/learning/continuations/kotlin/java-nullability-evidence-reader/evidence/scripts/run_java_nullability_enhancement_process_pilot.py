#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import tempfile
from pathlib import Path

from kotlin_compiler_distribution import verify_compiler_tree
from process_contract import ProcessBudget, ProcessOutcome, atomic_publish_json, run_process

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "labs" / "java-nullability-enhancement-process-pilot"
JAVA_SOURCES = [LAB / "java" / "org" / "jetbrains" / "annotations" / "NotNull.java", LAB / "java" / "pilot" / "JavaNulls.java"]
KOTLIN_SOURCE = LAB / "kotlin" / "JavaNullabilityBoundary.kt"
REJECTED_SOURCE = LAB / "kotlin" / "RejectedNullArgument.kt"
EXPECTED = LAB / "expected.json"
OUTPUT = ROOT / "evidence" / "diagnostics" / "java-nullability-enhancement-process-pilot.json"
DIAGNOSTIC_FLAG = "-Xrender-internal-diagnostic-names"
ENVIRONMENT_OVERRIDES = {
    "CLASSPATH", "JAVA_OPTS", "JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS",
    "KOTLIN_COMPILER", "KOTLIN_HOME", "KOTLIN_RUNNER", "KOTLIN_TOOL", "JAVACMD",
}


def sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def execute(command: list[str], budget: ProcessBudget, label: str, environment: dict[str, str]) -> ProcessOutcome:
    return run_process(
        command, cwd=ROOT, env=environment, budget=budget, label=label,
    )


def probe(executable: str, kind: str, budget: ProcessBudget, environment: dict[str, str]) -> dict:
    result = execute([executable, "-version"], budget, f"probe-{kind}-version", environment)
    combined = result.stdout + result.stderr
    patterns = {
        "kotlinc": r"kotlinc(?:-jvm)?\s+([0-9]+\.[0-9]+\.[0-9]+)",
        "java": r'version "([0-9]+(?:\.[0-9]+)+)',
        "javac": r"javac\s+([0-9]+(?:\.[0-9]+)+)",
        "javap": r"([0-9]+(?:\.[0-9]+)+)",
    }
    match = re.search(patterns[kind], combined)
    return {
        "version": match.group(1) if match else None,
        "exit_code": result.returncode,
        "stdout_digest": sha256(result.stdout.encode()),
        "stderr_digest": sha256(result.stderr.encode()),
    }


def runtime_case(java: str, classpath: str, name: str, expected: dict, budget: ProcessBudget, environment: dict[str, str]) -> dict:
    result = execute([java, "-cp", classpath, "JavaNullabilityBoundaryKt", *expected["arguments"]], budget, f"runtime-{name}", environment)
    stderr_expectations = expected.get("stderr_contains", [])
    stdout_matches = "stdout" not in expected or result.stdout == expected["stdout"]
    stderr_matches = all(value in result.stderr for value in stderr_expectations)
    return {
        "name": name,
        "arguments": expected["arguments"],
        "attempts": 1,
        "retries": 0,
        "exit_code": result.returncode,
        "exit_code_matches": result.returncode == expected["exit_code"],
        "stdout_digest": sha256(result.stdout.encode()),
        "stdout_matches": stdout_matches,
        "stderr_digest": sha256(result.stderr.encode()),
        "stderr_matches": stderr_matches,
        "oracle_matches": result.returncode == expected["exit_code"] and stdout_matches and stderr_matches,
    }


def run(compiler: Path, distribution: Path) -> dict:
    expected_bytes = EXPECTED.read_bytes()
    expected = json.loads(expected_bytes)
    expected_digest = sha256(expected_bytes)
    budget = ProcessBudget()
    java = shutil.which("java")
    javac = shutil.which("javac")
    javap = shutil.which("javap")
    if not java or not javac or not javap:
        raise RuntimeError("OpenJDK java, javac, and javap are required")
    environment = {key: value for key, value in os.environ.items() if key not in ENVIRONMENT_OVERRIDES}
    environment.update({"LC_ALL": "C", "LANG": "C", "JAVACMD": java})
    distribution_binding = verify_compiler_tree(compiler, distribution, expected["compiler_distribution_digest"])
    compiler_probe = probe(str(compiler), "kotlinc", budget, environment)
    java_probe = probe(java, "java", budget, environment)
    javac_probe = probe(javac, "javac", budget, environment)
    javap_probe = probe(javap, "javap", budget, environment)
    distribution_digest = distribution_binding["archive_digest"]
    with tempfile.TemporaryDirectory(prefix="kotlin-java-nullability-pilot-") as temporary:
        temp = Path(temporary)
        classes = temp / "java-classes"
        classes.mkdir()
        app = temp / "app.jar"
        rejected = temp / "rejected.jar"
        java_compile = execute([javac, "-encoding", "UTF-8", "-d", str(classes), *map(str, JAVA_SOURCES)], budget, "compile-java-fixture", environment)
        if java_compile.returncode != 0:
            raise RuntimeError("javac did not produce the Java nullability fixture")
        kotlin_compile = execute([
            str(compiler), KOTLIN_SOURCE.relative_to(ROOT).as_posix(), "-classpath", str(classes),
            "-language-version", expected["language_version"], "-api-version", expected["api_version"],
            "-include-runtime", "-d", str(app),
        ], budget, "compile-kotlin-consumer", environment)
        if kotlin_compile.returncode != 0 or not app.is_file():
            raise RuntimeError("Locked Kotlin compiler did not produce the Java interop fixture")
        rejection = execute([
            str(compiler), REJECTED_SOURCE.relative_to(ROOT).as_posix(), "-classpath", str(classes),
            "-language-version", expected["language_version"], "-api-version", expected["api_version"],
            DIAGNOSTIC_FLAG, "-d", str(rejected),
        ], budget, "compile-rejected-null-argument", environment)
        rejection_output = rejection.stdout + rejection.stderr
        diagnostic = re.search(r"\[([A-Z][A-Z0-9_]+)]", rejection_output)
        rejected_artifact_created = rejected.exists()
        inspection = execute([javap, "-p", "-c", "-classpath", os.pathsep.join([str(app), str(classes)]), "JavaNullabilityBoundaryKt"], budget, "inspect-enhanced-bytecode", environment)
        inspection_output = inspection.stdout + inspection.stderr
        violated_call = inspection_output.find("pilot/JavaNulls.violatesContract:()Ljava/lang/String;")
        dereference = inspection_output.find("java/lang/String.length:()I", violated_call + 1)
        bytecode_oracle = {
            "exit_code": inspection.returncode,
            "attempts": 1,
            "retries": 0,
            "intrinsics_check_not_null_expression_value": "kotlin/jvm/internal/Intrinsics.checkNotNullExpressionValue" in inspection_output,
            "enhanced_return_invocation": violated_call >= 0,
            "direct_string_length_after_enhanced_return": violated_call >= 0 and dereference > violated_call,
            "output_digest": sha256(inspection_output.encode()),
        }
        classpath = os.pathsep.join([str(app), str(classes)])
        cases = [runtime_case(java, classpath, name, expected[name], budget, environment) for name in ("normal", "boundary", "failure")]
        app_digest = sha256(app.read_bytes())
        java_class_digests = {
            path.relative_to(classes).as_posix(): sha256(path.read_bytes())
            for path in sorted(classes.rglob("*.class"))
        }
    distribution_binding_after = verify_compiler_tree(compiler, distribution, expected["compiler_distribution_digest"])
    tree_stable_during_run = distribution_binding_after["tree_manifest_digest"] == distribution_binding["tree_manifest_digest"]
    compiler_matches = compiler_probe["version"] == expected["compiler_version"]
    distribution_matches = distribution_digest == expected["compiler_distribution_digest"]
    java_matches = java_probe["exit_code"] == 0 and str(java_probe["version"]).startswith("17.0")
    javac_matches = javac_probe["exit_code"] == 0 and str(javac_probe["version"]).startswith("17.0")
    javap_matches = javap_probe["exit_code"] == 0 and str(javap_probe["version"]).startswith("17.0")
    rejection_matches = (
        rejection.returncode == 1
        and diagnostic is not None
        and diagnostic.group(1) == expected["rejection_diagnostic_id"]
        and not rejected_artifact_created
    )
    bytecode_matches = all([
        bytecode_oracle["exit_code"] == 0,
        bytecode_oracle["enhanced_return_invocation"],
        bytecode_oracle["direct_string_length_after_enhanced_return"],
        bytecode_oracle["intrinsics_check_not_null_expression_value"] is False,
    ])
    oracle_matches = all([
        compiler_matches, compiler_probe["exit_code"] == 0, distribution_matches,
        distribution_binding["tree_matches_archive"], tree_stable_during_run, java_matches, javac_matches, javap_matches,
        java_compile.returncode == 0, kotlin_compile.returncode == 0,
        rejection_matches, bytecode_matches, all(item["oracle_matches"] for item in cases),
    ])
    return {
        "schema_version": 1,
        "id": "java-nullability-enhancement-process-pilot-v1",
        "status": "observed-locked-java-nullability-compiler-and-runtime-pending-authority-review" if oracle_matches else "observation-mismatch",
        "classification": "behavior-specific-jvm-java-interop-process-pilot-not-surface-scenario-closure-or-authority-promotion",
        "attempts": 1,
        "retries": 0,
        "behavior_id": "compiler.java-nullability-enhancement",
        "variant_id": "kotlin-2.4.10-jvm-openjdk17-java-consumer",
        "command": "python3 scripts/run_java_nullability_enhancement_process_pilot.py --compiler <task-cache-kotlinc> --distribution <task-cache-distribution> --require-locked",
        "inputs": {
            "expected": {"path": EXPECTED.relative_to(ROOT).as_posix(), "digest": expected_digest},
        },
        "sources": [
            {"path": path.relative_to(ROOT).as_posix(), "digest": sha256(path.read_bytes()), "license": "Apache-2.0"}
            for path in [*JAVA_SOURCES, KOTLIN_SOURCE, REJECTED_SOURCE]
        ],
        "harness": {"path": Path(__file__).relative_to(ROOT).as_posix(), "digest": sha256(Path(__file__).read_bytes())},
        "toolchain": {
            "compiler": {"identity": "task-cache:kotlin-compiler-2.4.10/bin/kotlinc", **compiler_probe},
            "compiler_distribution_digest": distribution_digest,
            "compiler_distribution_digest_matches": distribution_matches,
            "compiler_distribution_binding": distribution_binding,
            "compiler_distribution_binding_after_run": distribution_binding_after,
            "compiler_tree_stable_during_run": tree_stable_during_run,
            "compiler_launcher_invoked": True,
            "compiler_override_environment_removed": sorted(ENVIRONMENT_OVERRIDES - {"JAVACMD"}),
            "compiler_java_command": "PATH:java",
            "java": {"identity": "PATH:java", **java_probe},
            "javac": {"identity": "PATH:javac", **javac_probe},
            "javap": {"identity": "PATH:javap", **javap_probe},
            "host": {"os": platform.system(), "architecture": platform.machine()},
        },
        "compile": {
            "java": {"attempts": 1, "retries": 0, "exit_code": java_compile.returncode, "stdout_digest": sha256(java_compile.stdout.encode()), "stderr_digest": sha256(java_compile.stderr.encode())},
            "kotlin": {"attempts": 1, "retries": 0, "exit_code": kotlin_compile.returncode, "stdout_digest": sha256(kotlin_compile.stdout.encode()), "stderr_digest": sha256(kotlin_compile.stderr.encode()), "artifact_digest": app_digest},
            "rejection": {
                "attempts": 1, "retries": 0, "exit_code": rejection.returncode,
                "diagnostic_id": diagnostic.group(1) if diagnostic else None,
                "diagnostic_id_matches": diagnostic is not None and diagnostic.group(1) == expected["rejection_diagnostic_id"],
                "output_artifact_created": rejected_artifact_created,
                "stdout_digest": sha256(rejection.stdout.encode()), "stderr_digest": sha256(rejection.stderr.encode()),
            },
            "java_class_digests": java_class_digests,
        },
        "bytecode_oracle": bytecode_oracle | {"matches": bytecode_matches},
        "runtime_cases": cases,
        "trace": {
            "action_stream": ["compile-java-annotations-and-api", "compile-kotlin-consumer", "compile-rejected-null-argument", "inspect-null-check-bytecode", "launch-normal", "launch-boundary", "launch-failure"],
            "network_stream": {"expected_calls": 0, "observed_application_calls": 0, "os_level_isolation_proved": False},
            "resource_stream": {"generated_kotlin_jar_digest": app_digest, "generated_java_classes": java_class_digests, "temporary_artifacts_retained": False},
        },
        "process_contract": budget.contract(),
        "oracle": {
            "locked_compiler": compiler_matches,
            "locked_distribution": distribution_matches,
            "compiler_tree_matches_locked_archive": distribution_binding["tree_matches_archive"],
            "compiler_tree_stable_during_run": tree_stable_during_run,
            "compiler_probe_succeeded": compiler_probe["exit_code"] == 0,
            "java_17_probe_succeeded": java_matches,
            "javac_17_probe_succeeded": javac_matches,
            "javap_17_probe_succeeded": javap_matches,
            "expected_input_digest_bound": bool(expected_digest),
            "java_not_null_enhancement_rejection": rejection_matches,
            "runtime_contract_violation_observed_as_direct_jvm_npe": bytecode_matches and cases[2]["oracle_matches"],
            "generated_program_runtime_executed": True,
            "normal_boundary_failure_observed": all(item["oracle_matches"] for item in cases),
            "matches": oracle_matches,
        },
        "completion_boundary": {
            "human_decision_generated": False,
            "authority_promotion_generated": False,
            "completion_credit": False,
            "dedicated_surface_scenario_cell_closed": False,
            "reason": "This pilot exercises one real JVM Java-consumer variant, but has no human-reviewed Authority atomic binding and does not satisfy every Surface×Scenario closure cell.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compiler", required=True)
    parser.add_argument("--distribution", required=True)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--require-locked", action="store_true")
    arguments = parser.parse_args()
    compiler = Path(arguments.compiler)
    distribution = Path(arguments.distribution)
    if not compiler.is_absolute():
        compiler = ROOT / compiler
    if not distribution.is_absolute():
        distribution = ROOT / distribution
    cache_root = (ROOT / ".cache").resolve()
    for path in (compiler, distribution):
        try:
            path.resolve().relative_to(cache_root)
        except ValueError as error:
            raise RuntimeError("Pilot tools must remain in the repository-owned ignored .cache area") from error
    result = run(compiler, distribution)
    required_status = "observed-locked-java-nullability-compiler-and-runtime-pending-authority-review"
    if result["status"] != required_status:
        raise RuntimeError("Java nullability enhancement pilot did not satisfy the locked compiler/runtime oracle")
    if not arguments.no_write:
        atomic_publish_json(OUTPUT, result, required_status)
    print(
        "Java nullability enhancement process pilot: "
        f"status={result['status']} compiler={result['toolchain']['compiler']['version']} "
        f"diagnostic={result['compile']['rejection']['diagnostic_id']} cases={len(result['runtime_cases'])} credit=0"
    )
    if arguments.require_locked and result["status"] != required_status:
        raise RuntimeError("Java nullability enhancement pilot did not satisfy the locked compiler/runtime oracle")


if __name__ == "__main__":
    main()
