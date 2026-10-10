"""Verify saved observations; optionally record real loopback HTTP responses."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import struct
import sys
import urllib.error
import urllib.request
from lesson import experiment, ROOT


def verify():
    data = json.loads((ROOT / "observations/python.json").read_text())
    for name, digest in data["sources"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    assert len(data["runs"]) == 15
    for row in data["runs"]:
        assert experiment(row["input"], row["order"]) == row
    assert len(data["rejections"]) == 7
    for row in data["rejections"]:
        try:
            experiment(row["input"])
        except ValueError as err:
            assert str(err) == row["error"]
        else:
            raise AssertionError("rejection drift")
    print("Saved Python observations: 15 runs / 7 rejections / source bindings OK")
    if (ROOT / "observations/media.json").exists():
        media = json.loads((ROOT / "observations/media.json").read_text())
        for name, digest in media["source_binding"].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
        for artifact in media["artifacts"]:
            content = (ROOT / artifact["path"]).read_bytes()
            assert hashlib.sha256(content).hexdigest() == artifact["sha256"]
            assert len(content) == artifact["bytes"]
        print("Saved real UI screenshots: 6 artifacts / source and DOM bindings OK")


def http_record():
    rows = []
    for tokens, expected in [(["1", "2", "3", "4"], 200),
                             (["1e16", "1", "-1e16"], 200),
                             (["NaN"], 400), (["1e309"], 400),
                             (["1", "-1"], 200)]:
        req = urllib.request.Request("http://127.0.0.1:18746/api/run",
                                     json.dumps({"tokens": tokens}).encode(),
                                     {"Content-Type": "application/json"})
        try:
            response = urllib.request.urlopen(req, timeout=5)
        except urllib.error.HTTPError as err:
            response = err
        with response:
            status = response.code
            raw = response.read().decode()
        assert status == expected, (status, expected)
        body = json.loads(raw)
        if status == 200:
            assert body["steps"] == experiment(tokens)["steps"]
        rows.append({"input": tokens, "status": status, "raw_body": raw})
    target = ROOT / "observations/http.json"
    target.write_text(json.dumps({"observed_at": datetime.now(timezone.utc).isoformat(),
                                 "command": "/usr/bin/python3 -B verify.py --http",
                                 "responses": rows}, ensure_ascii=False, indent=2) + "\n")
    print("Real loopback HTTP: normal / cancellation / NaN rejection / range rejection / recovery OK")


def jpeg_size(content):
    assert content[:2] == b"\xff\xd8", "JPEG expected"
    offset = 2
    while offset < len(content):
        assert content[offset] == 255
        marker = content[offset + 1]
        length = struct.unpack(">H", content[offset + 2:offset + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", content[offset + 5:offset + 9])
            return width, height
        offset += 2 + length
    raise ValueError("JPEG dimensions unavailable")


def record_media():
    artifacts = []
    for path in sorted((ROOT / "media").glob("*.jpg")):
        content = path.read_bytes()
        width, height = jpeg_size(content)
        artifacts.append({"path": path.relative_to(ROOT).as_posix(), "width": width,
                          "height": height, "bytes": len(content),
                          "sha256": hashlib.sha256(content).hexdigest()})
    assert len(artifacts) == 6
    binding = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
               for name in ("index.html", "lesson.py", "observations/ui-dom.json")}
    data = {"recorded_at": datetime.now(timezone.utc).isoformat(),
            "capture": "Actual background IAB full-page JPEG via CUA screenshot API",
            "source_binding": binding, "artifacts": artifacts,
            "visual_review": {"reviewer": "Codex self review; no independent evaluator",
                              "result": "pass", "checks": ["Japanese readable", "numbers and errors readable",
                                                             "plot and step controls visible", "rejection and recovery visible"]},
            "limitations": ["browser engine version unavailable", "mobile viewport QA not run",
                            "screenshots are still images, not interaction recordings"]}
    (ROOT / "observations/media.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("Recorded 6 actual UI screenshots and source/DOM bindings")


if __name__ == "__main__":
    if "--record-media" in sys.argv:
        record_media()
    verify()
    run = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_lesson"],
                         cwd=ROOT, capture_output=True, text=True)
    (ROOT / "observations/tests.txt").write_text(run.stdout + run.stderr)
    print(run.stdout + run.stderr, end="")
    if run.returncode:
        raise SystemExit(run.returncode)
    if "--http" in sys.argv:
        http_record()
