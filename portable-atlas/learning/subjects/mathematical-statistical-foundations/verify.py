"""Default checker is read-only. Recording requires explicit flags."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import struct
import unittest
import urllib.error
import urllib.request
from lesson import ROOT, calculate, source_hashes, validate


def verify_saved():
    data = json.loads((ROOT / "observations/python.json").read_text())
    assert data["source_hashes"] == source_hashes(), "source binding drift"
    assert len(data["cases"]) == 7 and len(data["rejections"]) == 7
    for case in data["cases"].values():
        assert calculate(case["counts"]) == case
    for rejected in data["rejections"]:
        try:
            validate(rejected["input"])
        except ValueError as err:
            assert str(err) == rejected["error"]
        else:
            raise AssertionError("rejection drift")
    print("Saved observations: 7 cases / 7 rejections / exact oracles / source binding OK")
    media_path = ROOT / "observations/media.json"
    if media_path.exists():
        media = json.loads(media_path.read_text())
        for path, digest in media["bindings"].items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
        assert len(media["artifacts"]) == 5
        for row in media["artifacts"]:
            content = (ROOT / row["path"]).read_bytes()
            assert hashlib.sha256(content).hexdigest() == row["sha256"]
            assert len(content) == row["bytes"]
            assert jpeg_size(content) == (row["width"], row["height"])
        print("Actual IAB images: 5 JPEG / source-DOM binding OK")


def jpeg_size(content):
    assert content[:2] == b"\xff\xd8"
    i = 2
    while i < len(content):
        assert content[i] == 255
        marker = content[i + 1]
        size = struct.unpack(">H", content[i+2:i+4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", content[i+5:i+9])
            return w, h
        i += size + 2
    raise ValueError("JPEG size not found")


def record_media():
    rows = []
    for path in sorted((ROOT / "media").glob("*.jpg")):
        content = path.read_bytes()
        w, h = jpeg_size(content)
        rows.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(content),
                     "width": w, "height": h, "sha256": hashlib.sha256(content).hexdigest()})
    assert len(rows) == 5
    paths = ["lesson.py", "index.html", "observations/ui-dom.json"]
    media = {"recorded_at": datetime.now(timezone.utc).isoformat(),
             "capture": "Actual background IAB full-page JPEG via CUA",
             "bindings": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
             "artifacts": rows, "visual_review": "Codex self review; Japanese/counts/denominators/dots/errors readable",
             "limitations": ["browser engine version not exposed", "mobile viewport not tested", "still images, not video"]}
    (ROOT / "observations/media.json").write_text(json.dumps(media, ensure_ascii=False, indent=2) + "\n")


def record_http():
    from lesson import PRESETS
    requests = [(PRESETS["rare"], 200), (PRESETS["balanced"], 200), (PRESETS["no-positive"], 200),
                ({**PRESETS["rare"], "ap": -1}, 400), (dict.fromkeys(("ap","an","bp","bn"),0), 400),
                (PRESETS["hand-count"], 200)]
    rows = []
    for counts, expected in requests:
        req = urllib.request.Request("http://127.0.0.1:18747/api/run", json.dumps(counts).encode(),
                                     {"Content-Type": "application/json"})
        try:
            response = urllib.request.urlopen(req, timeout=5)
        except urllib.error.HTTPError as err:
            response = err
        with response:
            status, raw = response.code, response.read().decode()
        assert status == expected
        body = json.loads(raw)
        if status == 200:
            assert {key:body[key] for key in calculate(counts)} == calculate(counts)
            assert body["source_hashes"] == source_hashes()
        rows.append({"input": counts, "status": status, "raw_body": raw})
    data = {"observed_at": datetime.now(timezone.utc).isoformat(),
            "command": "/usr/bin/python3 -B verify.py --record-http", "responses": rows}
    (ROOT / "observations/http.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("Actual loopback HTTP: 6 normal/boundary/rejection/recovery responses OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-checks", action="store_true")
    parser.add_argument("--record-http", action="store_true")
    parser.add_argument("--record-media", action="store_true")
    args = parser.parse_args()
    if args.record_media:
        record_media()
    verify_saved()
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromName("test_lesson")
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    output = stream.getvalue()
    print(output, end="")
    if args.record_checks:
        (ROOT / "observations/tests.txt").write_text(output)
    if not result.wasSuccessful():
        raise SystemExit(1)
    if args.record_http:
        record_http()
