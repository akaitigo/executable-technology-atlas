"""合成source/dependencyから実Artifact生成。全異常を別folderで保存。"""
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import pipeline

ROOT = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def run(execution_id):
    target = ROOT / "observations" / execution_id
    target.mkdir(parents=True, exist_ok=True)
    recipe = (ROOT / "pipeline.py").read_bytes()
    source = b"Hello, supply chain!\n"
    dependency = pipeline.canonical({"name": "synthetic-prefix", "version": "1.0.0", "prefix": "v1 / "})
    artifact, manifest = pipeline.build(source, dependency, recipe)
    initial = pipeline.baseline(source, dependency, recipe, artifact, manifest)
    # Retained by consumer before any scenario mutation. Never derived from supplied replacement.
    independent_pin = pipeline.digest(initial)
    reference = {"source.txt": source, "dependency.json": dependency, "recipe.py": recipe,
                 "artifact.json": artifact, "manifest.json": manifest, "baseline.json": initial}
    rows = []
    scenarios = ["normal", "source-changed", "artifact-tampered", "manifest-only",
                 "pair-rewritten", "baseline-replaced", "source-rebuilt", "dependency-updated"]
    started = now()
    for scenario_id in scenarios:
        folder = target / scenario_id
        folder.mkdir(exist_ok=False)
        files = dict(reference)
        if scenario_id in {"source-changed", "source-rebuilt"}:
            files["source.txt"] = b"Hello, changed source!\n"
        if scenario_id == "artifact-tampered":
            files["artifact.json"] = artifact.replace(b"Hello", b"EVIL!")
        if scenario_id == "manifest-only":
            edited = json.loads(manifest)
            edited["materials"]["source.txt"]["digest"] = "sha256:" + "0" * 64
            files["manifest.json"] = pipeline.canonical(edited)
        if scenario_id in {"pair-rewritten", "baseline-replaced"}:
            # Input claims remain identical; an unsigned manifest can simply lie about the output.
            files["artifact.json"] = artifact.replace(b"Hello", b"EVIL!")
            edited = json.loads(manifest)
            edited["artifact"].update(pipeline.descriptor(files["artifact.json"]))
            files["manifest.json"] = pipeline.canonical(edited)
        if scenario_id == "dependency-updated":
            files["dependency.json"] = pipeline.canonical({"name": "synthetic-prefix", "version": "1.1.0", "prefix": "v2 / "})
        if scenario_id in {"source-rebuilt", "dependency-updated"}:
            files["artifact.json"], files["manifest.json"] = pipeline.build(files["source.txt"], files["dependency.json"], recipe)
        if scenario_id == "baseline-replaced":
            files["baseline.json"] = pipeline.baseline(files["source.txt"], files["dependency.json"], recipe,
                                                      files["artifact.json"], files["manifest.json"])
        for name, content in files.items():
            (folder / name).write_bytes(content)
        result = pipeline.verify(files["source.txt"], files["dependency.json"], recipe, files["artifact.json"],
                                 files["manifest.json"], files["baseline.json"], independent_pin)
        # Counterexample: accepting a pin freshly derived from the same supplied baseline is not independent trust.
        unsafe = pipeline.verify(files["source.txt"], files["dependency.json"], recipe, files["artifact.json"],
                                 files["manifest.json"], files["baseline.json"], pipeline.digest(files["baseline.json"]))
        row = {"id": scenario_id, "observed_at": now(), "files": {name: pipeline.descriptor(raw) for name, raw in files.items()},
               "changed_files": [name for name, raw in files.items() if raw != reference[name]],
               "result": result, "unsafe_pin_from_supplied_baseline_accepts": unsafe["baseline_match"],
               "artifact_preview": files["artifact.json"].decode("utf-8"),
               "manifest_preview": files["manifest.json"].decode("utf-8"),
               "directory": scenario_id}
        (folder / "verification.json").write_bytes(pipeline.canonical(row))
        rows.append(row)
    repeat = target / "repeat-build"
    repeat.mkdir(exist_ok=False)
    again, again_manifest = pipeline.build(source, dependency, recipe)
    (repeat / "artifact.json").write_bytes(again)
    (repeat / "manifest.json").write_bytes(again_manifest)
    expectations = {"normal": (True, True, True), "source-changed": (True, False, False),
                    "artifact-tampered": (False, True, False), "manifest-only": (True, False, False),
                    "pair-rewritten": (True, True, False), "baseline-replaced": (True, True, False),
                    "source-rebuilt": (True, True, False), "dependency-updated": (True, True, False)}
    for row in rows:
        result = row["result"]
        actual = tuple(result[key] for key in ["checksum_match", "input_binding_match", "baseline_match"])
        if actual != expectations[row["id"]]:
            raise RuntimeError("scenario oracle mismatch: " + row["id"])
    if not (artifact == again and manifest == again_manifest):
        raise RuntimeError("same-input byte reproduction failed")
    if not next(row for row in rows if row["id"] == "baseline-replaced")["unsafe_pin_from_supplied_baseline_accepts"]:
        raise RuntimeError("baseline substitution counterexample missing")
    document = {"schema_version": 1, "subject_id": "software-supply-chain", "lesson_id": "digest-provenance-baseline",
                "execution_id": execution_id, "status": "pass", "started_at": started, "completed_at": now(),
                "runtime": {"implementation": platform.python_implementation(), "python": platform.python_version(),
                            "os": platform.system(), "os_release": platform.release(), "machine": platform.machine(),
                            "attempts": 1, "retries": 0, "packages_installed": 0},
                "trusted_pin": independent_pin,
                "trust_model": "consumer retains initial baseline digest outside each mutation bundle, in process memory",
                "initial_inputs": {"source_ascii": source.decode(), "dependency_json": dependency.decode(), "recipe": pipeline.RECIPE},
                "source_bindings": {name: pipeline.digest((ROOT / name).read_bytes()) for name in ["pipeline.py", "experiment.py"]},
                "repeat_build": {"artifact_bytes_equal": artifact == again, "manifest_bytes_equal": manifest == again_manifest,
                                 "artifact_digest": pipeline.digest(again), "manifest_digest": pipeline.digest(again_manifest)},
                "scenarios": rows,
                "scope": {"synthetic_inputs": True, "actual_local_generation": True, "signed": False,
                          "slsa_level_established": False, "oci_artifact": False, "subject_completion_credit": False}}
    (target / "observation.json").write_bytes(pipeline.canonical(document))
    print(json.dumps(document, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    try:
        run(sys.argv[1])
    except Exception as error:
        print(type(error).__name__ + ": " + str(error), file=sys.stderr)
        sys.exit(1)
