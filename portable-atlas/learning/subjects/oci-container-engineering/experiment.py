"""Generate task-owned synthetic OCI bytes, then actually read each layout."""
import io
import json
import platform
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from oci_subset import CONFIG, INDEX, LAYER, MANIFEST, descriptor, digest, inspect, json_bytes

ROOT = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def tar_bytes(entries):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for row in entries:
            info = tarfile.TarInfo(row["path"])
            data = row.get("text", "").encode()
            info.mode = 0o644
            info.uid = info.gid = info.mtime = 0
            if row.get("type") == "symlink":
                info.type = tarfile.SYMTYPE
                info.linkname = row["target"]
                data = b""
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return output.getvalue()


def build_layout(path, inputs, mismatch=False):
    path.mkdir()
    (path / "blobs/sha256").mkdir(parents=True)
    def put(data, media):
        desc = descriptor(data, media)
        (path / "blobs/sha256" / desc["digest"].split(":")[1]).write_bytes(data)
        return desc
    layers = [tar_bytes(rows) for rows in inputs]
    descs = [put(b, LAYER) for b in layers]
    diff_ids = [digest(b) for b in layers]
    if mismatch:
        diff_ids[1] = "sha256:" + "0" * 64
    config = {"architecture": "amd64", "os": "linux", "config": {},
              "rootfs": {"type": "layers", "diff_ids": diff_ids}}
    conf = put(json_bytes(config), CONFIG)
    manifest = {"schemaVersion": 2, "mediaType": MANIFEST, "config": conf, "layers": descs}
    man = put(json_bytes(manifest), MANIFEST)
    (path / "oci-layout").write_bytes(json_bytes({"imageLayoutVersion": "1.0.0"}))
    (path / "index.json").write_bytes(json_bytes({"schemaVersion": 2, "mediaType": INDEX, "manifests": [man]}))
    return manifest, man


def run(token):
    started = now()
    destination = ROOT / "observations" / token
    destination.mkdir(parents=True, exist_ok=False)
    base = [{"path": "app/message.txt", "text": "version one\n"},
            {"path": "app/obsolete.txt", "text": "remove me\n"},
            {"path": "etc/stable.txt", "text": "unchanged\n"}]
    upper = [{"path": "app/message.txt", "text": "version two\n"},
             {"path": "app/.wh.obsolete.txt", "text": ""},
             {"path": "app/new.txt", "text": "added\n"}]
    scenarios = [
        ("normal", upper, True, None),
        ("same-layer", [{"path": "app/obsolete.txt", "text": "same layer survives\n"},
                         {"path": "app/.wh.obsolete.txt", "text": ""}], True, None),
        ("absent-whiteout", [{"path": "app/.wh.missing.txt", "text": ""}], True, None),
        ("traversal", [{"path": "../escape.txt", "text": "unsafe\n"}], False, "noncanonical-path"),
        ("absolute", [{"path": "/escape.txt", "text": "unsafe\n"}], False, "absolute-path"),
        ("symlink", [{"path": "app/link", "type": "symlink", "target": "../../escape"}], False, "unsupported-entry-type"),
        ("opaque", [{"path": "app/.wh..wh..opq", "text": ""}], False, "unsupported-opaque-whiteout"),
        ("duplicate", [{"path": "app/same", "text": "one"}, {"path": "app/same", "text": "two"}], False, "duplicate-path"),
        ("metadata-tamper", upper, False, "descriptor-mismatch"),
        ("blob-tamper", upper, False, "descriptor-mismatch"),
        ("diffid-mismatch", upper, False, "diff-id-mismatch"),
    ]
    results = []
    for ident, rows, accepted, error in scenarios:
        folder = destination / ident
        folder.mkdir()
        inputs = [base, rows]
        (folder / "input.json").write_bytes(json_bytes(inputs))
        manifest, man = build_layout(folder / "layout", inputs, ident == "diffid-mismatch")
        mutations = []
        if ident == "metadata-tamper":
            p = folder / "layout/blobs/sha256" / man["digest"].split(":")[1]
            before = digest(p.read_bytes())
            changed = dict(manifest)
            changed["annotations"] = {"lesson.modified": "true"}
            p.write_bytes(json_bytes(changed))
            mutations.append({"file": p.relative_to(folder).as_posix(), "before": before, "after": digest(p.read_bytes())})
        if ident == "blob-tamper":
            p = folder / "layout/blobs/sha256" / manifest["layers"][1]["digest"].split(":")[1]
            b = p.read_bytes()
            p.write_bytes(b.replace(b"version two", b"version BAD", 1))
            mutations.append({"file": p.relative_to(folder).as_posix(), "before": digest(b), "after": digest(p.read_bytes())})
        result = inspect(folder / "layout")
        assert result["accepted"] == accepted, (ident, result)
        assert result["error"] == error, (ident, result)
        row = {"id": ident, "observed_at": now(), "expected": {"accepted": accepted, "error": error},
               "input": inputs, "mutations": mutations, "result": result}
        (folder / "result.json").write_bytes(json_bytes(row))
        results.append(row)
    normal = results[0]["result"]["final_map"]
    assert normal["app/message.txt"]["text"] == "version two\n"
    assert "app/obsolete.txt" not in normal and "app/.wh.obsolete.txt" not in normal
    assert results[1]["result"]["final_map"]["app/obsolete.txt"]["text"] == "same layer survives\n"
    repeat = destination / "repeat-layout"
    build_layout(repeat, [base, upper])
    normal_files = {p.relative_to(destination / "normal/layout").as_posix(): p.read_bytes()
                    for p in (destination / "normal/layout").rglob("*") if p.is_file()}
    repeat_files = {p.relative_to(repeat).as_posix(): p.read_bytes() for p in repeat.rglob("*") if p.is_file()}
    assert normal_files == repeat_files
    observation = {"schema_version": 1, "field_id": "oci-container-engineering", "lesson_id": "layer-map-subset",
                   "execution_id": token, "started_at": started, "completed_at": now(),
                   "runtime": {"python": platform.python_version(), "os": platform.system(),
                               "release": platform.release(), "machine": platform.machine(), "attempts": 1, "retries": 0},
                   "source_bindings": {f: digest((ROOT / f).read_bytes()) for f in ("oci_subset.py", "experiment.py")},
                   "repeat_layout_bytes_equal": True, "scenarios": results,
                   "scope": {"synthetic": True, "actual_tar_read": True, "virtual_map_only": True,
                             "host_extracted": False, "container_started": False, "subject_complete": False}}
    (destination / "observation.json").write_bytes(json_bytes(observation))
    print(json.dumps(observation, separators=(",", ":")))


if __name__ == "__main__":
    token = sys.argv[1]
    if not token.endswith("-oci-layer") or "/" in token or ".." in token:
        raise SystemExit("invalid run token")
    run(token)
