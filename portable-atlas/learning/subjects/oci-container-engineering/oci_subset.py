"""Read OCI object bytes and apply a deliberately narrow layer subset in memory."""
import hashlib
import io
import json
import re
import tarfile

PREFIX = "application/vnd.oci.image."
MANIFEST = PREFIX + "manifest.v1+json"
CONFIG = PREFIX + "config.v1+json"
LAYER = PREFIX + "layer.v1.tar"
INDEX = PREFIX + "index.v1+json"
MAX_BLOB = 2 * 1024 * 1024


class Refusal(ValueError):
    pass


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def descriptor(data, media_type):
    return {"mediaType": media_type, "size": len(data), "digest": digest(data)}


def path_key(name):
    # Stricter than the full OCI specification: only canonical ASCII relative paths.
    if name.startswith("/"):
        raise Refusal("absolute-path")
    parts = name.split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise Refusal("noncanonical-path")
    if not re.fullmatch(r"[A-Za-z0-9_./-]{1,160}", name):
        raise Refusal("unsupported-path")
    return name


def apply_layer(lower, data):
    if len(data) > MAX_BLOB:
        raise Refusal("blob-limit")
    entries = []
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as archive:
        for member in archive:
            name = path_key(member.name)
            if name in seen:
                raise Refusal("duplicate-path")
            seen.add(name)
            if len(seen) > 128 or member.size > 65536:
                raise Refusal("member-limit")
            if not member.isfile() or member.pax_headers:
                raise Refusal("unsupported-entry-type")
            payload = archive.extractfile(member).read()  # bytes only; never extract to disk
            if len(payload) != member.size:
                raise Refusal("truncated-member")
            base = name.rsplit("/", 1)[-1]
            if base == ".wh..wh..opq":
                raise Refusal("unsupported-opaque-whiteout")
            target = None
            if base.startswith(".wh."):
                if payload:
                    raise Refusal("nonempty-whiteout")
                parent = name[:len(name) - len(base)]
                target = path_key(parent + base[4:])
            entries.append((name, payload, target))
    # Validate every entry before making a new map. Whiteouts affect lower entries only,
    # independent of their physical order relative to files in this same layer.
    result = dict(lower)
    events = []
    for name, payload, target in entries:
        if target is not None:
            removed = [p for p in lower if p == target or p.startswith(target + "/")]
            for p in removed:
                result.pop(p, None)
            events.append({"path": name, "action": "whiteout", "target": target,
                           "removed": sorted(removed), "marker_visible": False})
    for name, payload, target in entries:
        if target is None:
            # File/directory shape conflicts are outside this file-only subset.
            if any(p.startswith(name + "/") or name.startswith(p + "/") for p in result):
                raise Refusal("unsupported-path-conflict")
            events.append({"path": name, "action": "overwrite" if name in result else "add",
                           "digest": digest(payload), "size": len(payload)})
            result[name] = payload
    return result, events


def map_record(files):
    return {p: {"text": b.decode("utf-8"), "digest": digest(b), "size": len(b)}
            for p, b in sorted(files.items())}


def inspect(layout):
    trace = []
    snapshots = []
    integrity = False
    try:
        def read_local(relative):
            p = layout / relative
            if p.is_symlink() or not p.resolve().is_relative_to(layout.resolve()):
                raise Refusal("host-path-escape")
            data = p.read_bytes()
            if len(data) > MAX_BLOB:
                raise Refusal("blob-limit")
            return data

        def load(desc, media):
            if desc.get("mediaType") != media:
                raise Refusal("unsupported-media-type")
            d = desc.get("digest", "")
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", d):
                raise Refusal("invalid-descriptor-digest")
            data = read_local("blobs/sha256/" + d.split(":")[1])
            actual = descriptor(data, media)
            if actual != desc:
                raise Refusal("descriptor-mismatch")
            trace.append({"phase": "descriptor", "expected": desc, "actual": actual})
            return data

        if json.loads(read_local("oci-layout")) != {"imageLayoutVersion": "1.0.0"}:
            raise Refusal("layout-version")
        index = json.loads(read_local("index.json"))
        if index.get("schemaVersion") != 2 or index.get("mediaType") != INDEX or len(index["manifests"]) != 1:
            raise Refusal("unsupported-index")
        manifest = json.loads(load(index["manifests"][0], MANIFEST))
        if manifest.get("schemaVersion") != 2 or manifest.get("mediaType") != MANIFEST:
            raise Refusal("manifest-schema")
        config = json.loads(load(manifest["config"], CONFIG))
        if config.get("os") != "linux" or config.get("architecture") != "amd64":
            raise Refusal("unsupported-platform")
        layers = [load(d, LAYER) for d in manifest["layers"]]
        if len(layers) != 2:
            raise Refusal("subset-two-layers")
        if config.get("rootfs") != {"type": "layers", "diff_ids": [digest(b) for b in layers]}:
            raise Refusal("diff-id-mismatch")
        integrity = True
        files = {}
        for i, layer in enumerate(layers):
            files, events = apply_layer(files, layer)
            snapshots.append(map_record(files))
            trace.append({"phase": "virtual-apply", "layer": i + 1, "events": events})
        return {"accepted": True, "integrity": True, "error": None, "trace": trace,
                "snapshots": snapshots, "final_map": map_record(files), "host_extracted": False}
    except (Refusal, OSError, KeyError, ValueError, tarfile.TarError) as error:
        return {"accepted": False, "integrity": integrity, "error": str(error), "trace": trace,
                "snapshots": snapshots, "final_map": None, "host_extracted": False}
