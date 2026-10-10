"""Default is read-only. Observation writes require an explicit record flag."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import struct
import subprocess
import sys
import unittest
import urllib.error
import urllib.request
from lesson import ROOT, PRESETS, experiment, observation_set, source_hashes


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jpeg_size(content):
    if content[:2] != b"\xff\xd8":
        raise ValueError("not JPEG")
    i = 2
    while i < len(content):
        if content[i] != 255:
            raise ValueError("invalid JPEG marker")
        marker = content[i + 1]
        size = struct.unpack(">H", content[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", content[i + 5:i + 9])
            return w, h
        i += size + 2
    raise ValueError("JPEG dimensions missing")


def verify_saved():
    path = ROOT / "observations/python.json"
    data = json.loads(path.read_text())
    assert data["source_hashes"] == source_hashes(), "source binding drift"
    expected = observation_set()
    assert all(data[key] == value for key, value in expected.items()), "saved result drift"
    assert path.read_bytes() == (ROOT / "observations/stdout.txt").read_bytes(), "raw output drift"
    print("Saved observations: 16 no-error / 112 single-bit / double-bit counterexample / 10 rejections OK")
    checks = ROOT / "observations/checks.json"
    if checks.exists():
        saved = json.loads(checks.read_text())
        assert saved["source_hashes"] == source_hashes(), "test source binding drift"
        assert saved["stdout_sha256"] == digest(ROOT / "observations/tests.txt"), "test output drift"
    for name in ("http.json", "media.json"):
        optional = ROOT / "observations" / name
        if not optional.exists():
            print(f"Not recorded: {name}")
            continue
        record = json.loads(optional.read_text())
        for relative, expected_digest in record["bindings"].items():
            assert digest(ROOT / relative) == expected_digest, relative
        if name == "http.json":
            for row in record["responses"]:
                if row["status"] == 200:
                    result = json.loads(row["raw_body"])
                    assert all(result[k] == v for k, v in experiment(row["input"]).items())
                    assert result["source_hashes"] == source_hashes()
                else:
                    try:
                        experiment(row["input"])
                    except ValueError as err:
                        assert json.loads(row["raw_body"])["error"] == str(err)
                    else:
                        raise AssertionError("saved HTTP rejection drift")
            print(f"Saved actual HTTP responses: {len(record['responses'])} OK")
        else:
            assert len(record["artifacts"]) == 6
            for row in record["artifacts"]:
                raw = (ROOT / row["path"]).read_bytes()
                assert digest(ROOT / row["path"]) == row["sha256"]
                assert len(raw) == row["bytes"]
                assert jpeg_size(raw) == (row["width"], row["height"])
            print("Actual IAB images: 6 JPEG / source-DOM binding OK")


def record_http(port):
    inputs = list(PRESETS.values()) + [
        {"message": "xxxx", "errors": []}, {"message": "0000", "errors": [1, 2, 3]},
        {"message": "0000", "errors": [7]},
    ]
    rows = []
    for data in inputs:
        request = urllib.request.Request(f"http://127.0.0.1:{port}/api/run", json.dumps(data).encode(),
                                         {"Content-Type": "application/json"})
        try:
            response = urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            status, raw = response.code, response.read().decode()
        try:
            expected = experiment(data)
        except ValueError as error:
            assert status == 400 and json.loads(raw)["error"] == str(error)
        else:
            assert status == 200
            assert all(json.loads(raw)[k] == v for k, v in expected.items())
        rows.append({"observed_at": datetime.now(timezone.utc).isoformat(), "input": data,
                     "status": status, "raw_body": raw})
    data = {"command": f"/usr/bin/python3 -B verify.py --record-http --port {port}", "transport": "actual loopback HTTP",
            "bindings": source_hashes(), "responses": rows}
    (ROOT / "observations/http.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("Actual HTTP: 7 normal/boundary/rejection/recovery responses OK")


def record_media():
    rows = []
    for path in sorted((ROOT / "media").glob("*.jpg")):
        raw = path.read_bytes()
        w, h = jpeg_size(raw)
        rows.append({"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path),
                     "bytes": len(raw), "width": w, "height": h})
    assert len(rows) == 6, "six actual captures required"
    data = {"recorded_at": datetime.now(timezone.utc).isoformat(),
            "capture": "Actual background IAB screenshots via CUA; full-page JPEG",
            "bindings": {**source_hashes(), "observations/ui-dom.json": digest(ROOT / "observations/ui-dom.json")},
            "artifacts": rows,
            "visual_review": "Codex self-review: bit positions, parity rows, warning, Japanese and errors readable",
            "limitations": ["browser engine version unavailable", "desktop only; no mobile QA", "stills, not video"]}
    (ROOT / "observations/media.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def record_readonly():
    def snapshot():
        return {p.relative_to(ROOT).as_posix(): digest(p) for p in ROOT.rglob("*") if p.is_file()}
    before = snapshot()
    completed = subprocess.run([sys.executable, "-B", "verify.py"], cwd=ROOT,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
    after = snapshot()
    assert before == after, "default checker mutated module"
    assert completed.returncode == 0, completed.stdout
    data = {"observed_at": datetime.now(timezone.utc).isoformat(),
            "command": "/usr/bin/python3 -B verify.py", "returncode": completed.returncode,
            "unchanged_file_count": len(before), "before": before, "after": after,
            "raw_output": completed.stdout}
    (ROOT / "observations/readonly.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Default checker read-only: {len(before)} file hashes unchanged")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-checks", action="store_true")
    parser.add_argument("--record-http", action="store_true")
    parser.add_argument("--record-media", action="store_true")
    parser.add_argument("--record-readonly", action="store_true")
    parser.add_argument("--port", type=int, default=18748)
    args = parser.parse_args()
    if args.record_media:
        record_media()
    verify_saved()
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName("test_lesson"))
    print(output.getvalue(), end="")
    if args.record_checks:
        (ROOT / "observations/tests.txt").write_text(output.getvalue())
        checks = {"observed_at": datetime.now(timezone.utc).isoformat(),
                  "command": "/usr/bin/python3 -B verify.py --record-checks",
                  "source_hashes": source_hashes(), "tests_run": result.testsRun,
                  "passed": result.wasSuccessful(), "stdout_sha256": digest(ROOT / "observations/tests.txt")}
        (ROOT / "observations/checks.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n")
    if not result.wasSuccessful():
        return 1
    if args.record_http:
        record_http(args.port)
    if args.record_readonly:
        record_readonly()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
