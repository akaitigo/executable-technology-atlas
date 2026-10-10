"""教材専用canonical JSON builderと、checksum/来歴binding/baseline検査。"""
import hashlib
import json

RECIPE = "stdlib-canonical-json-v1"


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def descriptor(raw):
    return {"digest": digest(raw), "size": len(raw)}


def build(source, dependency, recipe_bytes):
    # A local synthetic dependency config, not a package resolver or downloaded code.
    config = json.loads(dependency)
    if set(config) != {"name", "version", "prefix"} or not all(isinstance(value, str) for value in config.values()):
        raise ValueError("invalid synthetic dependency config")
    text = source.decode("utf-8")
    artifact = canonical({"schema_version": 1, "recipe": RECIPE,
                          "message": config["prefix"] + text,
                          "dependency": {"name": config["name"], "version": config["version"]},
                          "input_digests": {"source": digest(source), "dependency": digest(dependency),
                                            "recipe": digest(recipe_bytes)}})
    manifest = canonical({"schema_version": 1, "format": "learning-manifest-v1", "signed": False,
                          "artifact": {"name": "artifact.json", **descriptor(artifact)},
                          "materials": {"source.txt": descriptor(source), "dependency.json": descriptor(dependency)},
                          "builder": {"recipe": RECIPE, "code": descriptor(recipe_bytes)}})
    return artifact, manifest


def baseline(source, dependency, recipe_bytes, artifact, manifest):
    return canonical({"schema_version": 1, "role": "initial-consumer-expectations",
                      "artifact": descriptor(artifact), "manifest": descriptor(manifest),
                      "materials": {"source.txt": descriptor(source), "dependency.json": descriptor(dependency)},
                      "builder": descriptor(recipe_bytes), "signed": False})


def verify(source, dependency, recipe_bytes, artifact, manifest, supplied_baseline, independent_pin):
    claims = json.loads(manifest)
    candidate = json.loads(supplied_baseline)
    expected_artifact = claims.get("artifact", {})
    materials = claims.get("materials", {})
    code = claims.get("builder", {}).get("code", {})
    checks = [
        {"id": "artifact-to-manifest", "label": "Artifact bytes ↔ Manifest申告",
         "expected": {key: expected_artifact.get(key) for key in ["digest", "size"]}, "actual": descriptor(artifact)},
        {"id": "source-to-manifest", "label": "Source bytes ↔ 来歴のinput申告",
         "expected": materials.get("source.txt"), "actual": descriptor(source)},
        {"id": "dependency-to-manifest", "label": "Dependency bytes ↔ 来歴のinput申告",
         "expected": materials.get("dependency.json"), "actual": descriptor(dependency)},
        {"id": "builder-to-manifest", "label": "Builder code ↔ 来歴のrecipe申告",
         "expected": code, "actual": descriptor(recipe_bytes)},
        {"id": "baseline-pin", "label": "受け取ったBaseline ↔ 別に保持したpin",
         "expected": independent_pin, "actual": digest(supplied_baseline)},
        {"id": "artifact-to-baseline", "label": "Artifact ↔ 初期Baseline",
         "expected": candidate.get("artifact"), "actual": descriptor(artifact)},
        {"id": "manifest-to-baseline", "label": "Manifest ↔ 初期Baseline",
         "expected": candidate.get("manifest"), "actual": descriptor(manifest)},
        {"id": "source-to-baseline", "label": "Source ↔ 初期Baseline",
         "expected": candidate.get("materials", {}).get("source.txt"), "actual": descriptor(source)},
        {"id": "dependency-to-baseline", "label": "Dependency ↔ 初期Baseline",
         "expected": candidate.get("materials", {}).get("dependency.json"), "actual": descriptor(dependency)},
        {"id": "builder-to-baseline", "label": "Builder ↔ 初期Baseline",
         "expected": candidate.get("builder"), "actual": descriptor(recipe_bytes)},
    ]
    for check in checks:
        check["pass"] = check["expected"] == check["actual"]
    checksum = checks[0]["pass"]
    inputs_bound = all(check["pass"] for check in checks[1:4])
    anchored = all(check["pass"] for check in checks)
    rebuilt, _ = build(source, dependency, recipe_bytes)
    return {"checksum_match": checksum, "input_binding_match": inputs_bound,
            "baseline_match": anchored, "checks": checks,
            "rebuild_current_inputs_matches": rebuilt == artifact,
            "signature_verified": False,
            "errors": [check["id"] for check in checks if not check["pass"]]}
