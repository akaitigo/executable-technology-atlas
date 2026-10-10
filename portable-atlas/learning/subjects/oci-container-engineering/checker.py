"""Independent read-only oracle. Does not import the producer or layer consumer."""
import hashlib
import io
import json
import re
import tarfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def safe_name(name):
    if name.startswith("/"):
        raise ValueError("absolute-path")
    if any(x in ("", ".", "..") for x in name.split("/")):
        raise ValueError("noncanonical-path")
    if re.fullmatch(r"[A-Za-z0-9_./-]{1,160}", name) is None:
        raise ValueError("unsupported-path")
    return name


def independent_apply(lower, blob):
    incoming = {}
    deletions = []
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:") as stream:
        for entry in stream:
            key = safe_name(entry.name)
            if key in seen:
                raise ValueError("duplicate-path")
            seen.add(key)
            if not entry.isfile():
                raise ValueError("unsupported-entry-type")
            content = stream.extractfile(entry).read()
            leaf = key.split("/")[-1]
            if leaf == ".wh..wh..opq":
                raise ValueError("unsupported-opaque-whiteout")
            if leaf.startswith(".wh."):
                if content:
                    raise ValueError("nonempty-whiteout")
                deletions.append(safe_name(key[:len(key)-len(leaf)] + leaf[4:]))
            else:
                incoming[key] = content
    retained = {k: v for k, v in lower.items()
                if not any(k == d or k.startswith(d + "/") for d in deletions)}
    return {**retained, **incoming}


def oracle(folder):
    def blob(desc):
        name = desc["digest"]
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", name):
            raise ValueError("invalid-descriptor-digest")
        p = folder / "blobs/sha256" / name[7:]
        if p.is_symlink() or not p.resolve().is_relative_to(folder.resolve()):
            raise ValueError("host-path-escape")
        data = p.read_bytes()
        if sha(data) != name or len(data) != desc["size"]:
            raise ValueError("descriptor-mismatch")
        return data
    integrity = False
    try:
        header = json.loads((folder / "oci-layout").read_bytes())
        assert header == {"imageLayoutVersion": "1.0.0"}
        index = json.loads((folder / "index.json").read_bytes())
        assert index["schemaVersion"] == 2 and len(index["manifests"]) == 1
        manifest = json.loads(blob(index["manifests"][0]))
        assert manifest["schemaVersion"] == 2
        config = json.loads(blob(manifest["config"]))
        layer_bytes = [blob(d) for d in manifest["layers"]]
        if config["rootfs"]["diff_ids"] != list(map(sha, layer_bytes)):
            raise ValueError("diff-id-mismatch")
        integrity = True
        files = {}
        snapshots = []
        for b in layer_bytes:
            files = independent_apply(files, b)
            snapshots.append({p: {"text": v.decode(), "digest": sha(v), "size": len(v)}
                              for p, v in sorted(files.items())})
        return True, integrity, None, snapshots
    except ValueError as error:
        return False, integrity, str(error), []


def current():
    payload = json.loads((ROOT / "observation-data.js").read_text().removeprefix("window.OCI_OBSERVATION = ").strip().removesuffix(";"))
    relative = payload["directory"]
    if not re.fullmatch(r"observations/[0-9TZ]+-oci-layer", relative):
        raise ValueError("invalid observation path")
    return payload, ROOT / relative


class OCILessonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload, cls.folder = current()
        cls.obs = cls.payload["observation"]

    def test_all_eleven_actual_layouts(self):
        expected = {"normal": None, "same-layer": None, "absent-whiteout": None,
                    "traversal": "noncanonical-path", "absolute": "absolute-path",
                    "symlink": "unsupported-entry-type", "opaque": "unsupported-opaque-whiteout",
                    "duplicate": "duplicate-path", "metadata-tamper": "descriptor-mismatch",
                    "blob-tamper": "descriptor-mismatch", "diffid-mismatch": "diff-id-mismatch"}
        self.assertEqual(set(expected), {r["id"] for r in self.obs["scenarios"]})
        for row in self.obs["scenarios"]:
            with self.subTest(case=row["id"]):
                accepted, integrity, error, snapshots = oracle(self.folder / row["id"] / "layout")
                self.assertEqual(error, expected[row["id"]])
                self.assertEqual((accepted, integrity, error),
                                 (row["result"]["accepted"], row["result"]["integrity"], row["result"]["error"]))
                if accepted:
                    self.assertEqual(snapshots, row["result"]["snapshots"])
                    self.assertEqual(snapshots[-1], row["result"]["final_map"])

    def test_layer_order_overwrite_and_hidden_marker(self):
        _, _, _, maps = oracle(self.folder / "normal/layout")
        self.assertEqual(maps[0]["app/message.txt"]["text"], "version one\n")
        self.assertEqual(maps[1]["app/message.txt"]["text"], "version two\n")
        self.assertEqual(set(maps[1]), {"app/message.txt", "app/new.txt", "etc/stable.txt"})
        self.assertEqual(maps[1]["etc/stable.txt"], maps[0]["etc/stable.txt"])

    def test_whiteout_only_lower_layer_and_absent_target(self):
        _, _, _, maps = oracle(self.folder / "same-layer/layout")
        self.assertEqual(maps[-1]["app/obsolete.txt"]["text"], "same layer survives\n")
        _, _, _, maps = oracle(self.folder / "absent-whiteout/layout")
        self.assertEqual(maps[0], maps[1])

    def test_reproduction_bytes(self):
        def contents(p):
            return {f.relative_to(p).as_posix(): f.read_bytes() for f in p.rglob("*") if f.is_file()}
        self.assertEqual(contents(self.folder / "normal/layout"), contents(self.folder / "repeat-layout"))

    def test_new_path_negatives_and_lower_map_unchanged(self):
        for path in ("../new", "a/../new", "/new", "a//new", "./new", "a\\new"):
            with self.assertRaises(ValueError):
                safe_name(path)
        lower = {"app/old": b"original"}
        for case in ("traversal", "symlink", "opaque", "duplicate"):
            index = json.loads((self.folder / case / "layout/index.json").read_bytes())
            manifest = json.loads((self.folder / case / "layout/blobs/sha256" / index["manifests"][0]["digest"][7:]).read_bytes())
            data = (self.folder / case / "layout/blobs/sha256" / manifest["layers"][1]["digest"][7:]).read_bytes()
            with self.assertRaises(ValueError):
                independent_apply(lower, data)
            self.assertEqual(lower, {"app/old": b"original"})

    def test_raw_index_source_binding_and_no_extraction(self):
        raw = json.loads((self.folder / "observation.json").read_bytes())
        self.assertEqual(raw, self.obs)
        command = json.loads((self.folder / "command.json").read_bytes())
        self.assertEqual(command["exit_code"], 0)
        self.assertEqual(command["stderr"], "")
        self.assertEqual(json.loads(command["stdout"]), raw)
        self.assertEqual(sha(command["stdout"].encode()), command["stdout_digest"])
        index = json.loads((self.folder / "artifact-index.json").read_bytes())
        actual_paths = {p.relative_to(self.folder).as_posix() for p in self.folder.rglob("*") if p.is_file()}
        self.assertEqual(set(index) | {"artifact-index.json"}, actual_paths)
        for name, record in index.items():
            p = self.folder / name
            self.assertTrue(p.resolve().is_relative_to(self.folder.resolve()))
            data = p.read_bytes()
            self.assertEqual(record, {"digest": sha(data), "size": len(data)})
        for name, binding in raw["source_bindings"].items():
            self.assertEqual(sha((ROOT / name).read_bytes()), binding)
        for case in self.obs["scenarios"]:
            self.assertEqual(json.loads((self.folder / case["id"] / "input.json").read_bytes()), case["input"])
            self.assertFalse(case["result"]["host_extracted"])
        source = (ROOT / "oci_subset.py").read_text()
        self.assertNotIn(".extractall(", source)
        self.assertNotIn(".extract(", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
