"""Builderをimportせず、保存済みfile bytesを直接hash/rebuildして独立検算。"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def desc(raw):
    return {"digest": sha(raw), "size": len(raw)}


def canon(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def oracle(files, pin):
    manifest = json.loads(files["manifest.json"])
    baseline = json.loads(files["baseline.json"])
    checks = {
        "artifact-to-manifest": desc(files["artifact.json"]) == {key: manifest["artifact"][key] for key in ["digest", "size"]},
        "source-to-manifest": desc(files["source.txt"]) == manifest["materials"]["source.txt"],
        "dependency-to-manifest": desc(files["dependency.json"]) == manifest["materials"]["dependency.json"],
        "builder-to-manifest": desc(files["recipe.py"]) == manifest["builder"]["code"],
        "baseline-pin": sha(files["baseline.json"]) == pin,
        "artifact-to-baseline": desc(files["artifact.json"]) == baseline["artifact"],
        "manifest-to-baseline": desc(files["manifest.json"]) == baseline["manifest"],
        "source-to-baseline": desc(files["source.txt"]) == baseline["materials"]["source.txt"],
        "dependency-to-baseline": desc(files["dependency.json"]) == baseline["materials"]["dependency.json"],
        "builder-to-baseline": desc(files["recipe.py"]) == baseline["builder"],
    }
    return {"checksum_match": checks["artifact-to-manifest"],
            "input_binding_match": all(checks[key] for key in ["source-to-manifest", "dependency-to-manifest", "builder-to-manifest"]),
            "baseline_match": all(checks.values()), "checks": checks}


def rebuild_oracle(files):
    dependency = json.loads(files["dependency.json"])
    return canon({"schema_version": 1, "recipe": "stdlib-canonical-json-v1",
                  "message": dependency["prefix"] + files["source.txt"].decode(),
                  "dependency": {"name": dependency["name"], "version": dependency["version"]},
                  "input_digests": {"source": sha(files["source.txt"]), "dependency": sha(files["dependency.json"]),
                                    "recipe": sha(files["recipe.py"])}})


def load():
    data = json.loads((ROOT / "observation-data.js").read_text().removeprefix("window.SUPPLY_CHAIN_OBSERVATION = ").removesuffix(";\n"))
    directory = ROOT / data["directory"]
    return data, directory


class SupplyChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.directory = load()
        cls.observation = cls.data["observation"]
        cls.names = ["source.txt", "dependency.json", "recipe.py", "artifact.json", "manifest.json", "baseline.json"]
        cls.files = {row["id"]: {name: (cls.directory / row["id"] / name).read_bytes() for name in cls.names}
                     for row in cls.observation["scenarios"]}
        cls.pin = sha(cls.files["normal"]["baseline.json"])

    def test_independent_hash_and_all_eight_outcomes(self):
        expected = {"normal": (True, True, True), "source-changed": (True, False, False),
                    "artifact-tampered": (False, True, False), "manifest-only": (True, False, False),
                    "pair-rewritten": (True, True, False), "baseline-replaced": (True, True, False),
                    "source-rebuilt": (True, True, False), "dependency-updated": (True, True, False)}
        self.assertEqual(set(self.files), set(expected))
        self.assertEqual(self.pin, self.observation["trusted_pin"])
        for row in self.observation["scenarios"]:
            files = self.files[row["id"]]
            result = oracle(files, self.pin)
            with self.subTest(scenario=row["id"]):
                actual = tuple(result[key] for key in ["checksum_match", "input_binding_match", "baseline_match"])
                self.assertEqual(actual, expected[row["id"]])
                self.assertEqual({key: row["result"][key] for key in ["checksum_match", "input_binding_match", "baseline_match"]},
                                 {key: result[key] for key in ["checksum_match", "input_binding_match", "baseline_match"]})
                self.assertEqual({check["id"]: check["pass"] for check in row["result"]["checks"]}, result["checks"])
                self.assertEqual(row["files"], {name: desc(raw) for name, raw in files.items()})
                self.assertEqual(row["result"]["rebuild_current_inputs_matches"], rebuild_oracle(files) == files["artifact.json"])
                self.assertFalse(row["result"]["signature_verified"])

    def test_byte_reproduction_and_dependency_change(self):
        normal = self.files["normal"]
        self.assertEqual(normal["artifact.json"], (self.directory / "repeat-build/artifact.json").read_bytes())
        self.assertEqual(normal["manifest.json"], (self.directory / "repeat-build/manifest.json").read_bytes())
        self.assertEqual(rebuild_oracle(normal), normal["artifact.json"])
        for changed in ["source-rebuilt", "dependency-updated"]:
            self.assertNotEqual(sha(normal["artifact.json"]), sha(self.files[changed]["artifact.json"]))
            self.assertEqual(rebuild_oracle(self.files[changed]), self.files[changed]["artifact.json"])

    def test_pair_and_baseline_substitution_counterexamples(self):
        pair = oracle(self.files["pair-rewritten"], self.pin)
        self.assertTrue(pair["checksum_match"] and pair["input_binding_match"])
        self.assertFalse(pair["baseline_match"])
        replaced = self.files["baseline-replaced"]
        self.assertFalse(oracle(replaced, self.pin)["baseline_match"])
        self.assertTrue(oracle(replaced, sha(replaced["baseline.json"]))["baseline_match"])
        self.assertNotEqual(self.pin, sha(replaced["baseline.json"]))
        row = next(row for row in self.observation["scenarios"] if row["id"] == "baseline-replaced")
        self.assertTrue(row["unsafe_pin_from_supplied_baseline_accepts"])

    def test_independent_oracle_rejects_new_mutations(self):
        normal = self.files["normal"]
        changed = dict(normal, **{"artifact.json": normal["artifact.json"] + b"!"})
        self.assertFalse(oracle(changed, self.pin)["checksum_match"])
        changed = dict(normal)
        altered_manifest = json.loads(normal["manifest.json"])
        altered_manifest["artifact"]["size"] += 1
        changed["manifest.json"] = canon(altered_manifest)
        self.assertFalse(oracle(changed, self.pin)["checksum_match"])
        self.assertFalse(oracle(normal, "sha256:" + "0" * 64)["baseline_match"])

    def test_command_raw_artifact_index_and_source_bindings(self):
        observation = self.observation
        command = json.loads((self.directory / "command.json").read_text())
        self.assertEqual(command["exit_code"], 0)
        self.assertEqual(command["stderr"], "")
        self.assertEqual(sha(command["stdout"].encode()), command["stdout_digest"])
        self.assertEqual(json.loads(command["stdout"]), observation)
        self.assertEqual(json.loads((self.directory / "observation.json").read_text()), observation)
        self.assertEqual(set(observation["source_bindings"]), {"pipeline.py", "experiment.py"})
        for name, digest in observation["source_bindings"].items():
            self.assertEqual(digest, sha((ROOT / name).read_bytes()))
        self.assertEqual(self.files["normal"]["recipe.py"], (ROOT / "pipeline.py").read_bytes())
        index = self.data["artifact_index"]
        indexed = set()
        for item in index["artifacts"]:
            path = (self.directory / item["path"]).resolve()
            self.assertTrue(path.is_relative_to(self.directory.resolve()))
            raw = path.read_bytes()
            self.assertEqual(desc(raw), {"digest": item["digest"], "size": item["size"]})
            indexed.add(item["path"])
        self.assertEqual(indexed, {str(path.relative_to(self.directory)) for path in self.directory.rglob("*")
                                   if path.is_file() and path.name != "artifact-index.json"})
        self.assertFalse(observation["scope"]["signed"])
        self.assertFalse(observation["scope"]["slsa_level_established"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
