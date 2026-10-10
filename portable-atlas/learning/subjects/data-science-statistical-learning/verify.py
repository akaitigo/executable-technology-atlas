"""Read-only default; explicit flags record local observations."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import re
import struct
import subprocess
import sys
import unittest
import urllib.error
import urllib.request
from urllib.parse import unquote, urlsplit
sys.dont_write_bytecode = True
from lesson import ROOT, PRESETS, calculate, invalid_inputs, observation_set, source_hashes


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jpeg_size(raw):
    if raw[:2] != b"\xff\xd8":
        raise ValueError("not JPEG")
    i = 2
    while i < len(raw):
        if raw[i] != 255:
            raise ValueError("invalid JPEG marker")
        marker = raw[i + 1]
        size = struct.unpack(">H", raw[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", raw[i + 5:i + 9])
            return w, h
        i += size + 2
    raise ValueError("JPEG dimensions missing")


def verify_saved():
    path = ROOT / "observations/python.json"
    data = json.loads(path.read_text())
    assert data["source_hashes"] == source_hashes(), "source binding drift"
    assert all(data[key] == value for key, value in observation_set().items()), "saved result drift"
    assert path.read_bytes() == (ROOT / "observations/stdout.txt").read_bytes(), "raw output drift"
    print("Saved observations: 5 cases / 10 rejections / Fraction coefficient-MSE-selection oracles OK")
    checks = ROOT / "observations/checks.json"
    if checks.exists():
        saved = json.loads(checks.read_text())
        assert saved["source_hashes"] == source_hashes(), "test source binding drift"
        assert saved["stdout_sha256"] == digest(ROOT / "observations/tests.txt"), "test output drift"
    for name in ("http.json", "media.json"):
        path = ROOT / "observations" / name
        if not path.exists():
            print(f"Not recorded: {name}")
            continue
        saved = json.loads(path.read_text())
        for relative, expected in saved["bindings"].items():
            assert digest(ROOT / relative) == expected, relative
        if name == "http.json":
            for row in saved["responses"]:
                if row["status"] == 200:
                    result = json.loads(row["raw_body"])
                    assert all(result[k] == v for k, v in calculate(row["input"]).items())
                    assert result["source_hashes"] == source_hashes()
                else:
                    try:
                        calculate(row["input"])
                    except ValueError as err:
                        assert json.loads(row["raw_body"])["error"] == str(err)
                    else:
                        raise AssertionError("HTTP rejection drift")
            print(f"Saved actual HTTP responses: {len(saved['responses'])} OK")
        else:
            assert len(saved["artifacts"]) == 6
            for artifact in saved["artifacts"]:
                path = ROOT / artifact["path"]
                assert digest(path) == artifact["sha256"]
                assert path.stat().st_size == artifact["bytes"]
                assert jpeg_size(path.read_bytes()) == (artifact["width"], artifact["height"])
            print("Actual IAB images: 6 JPEG / source-DOM binding OK")


def record_http(port):
    inputs = list(PRESETS.values()) + invalid_inputs()[:3] + [PRESETS["train-only"]]
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
            expected = calculate(data)
        except ValueError as error:
            assert status == 400 and json.loads(raw)["error"] == str(error)
        else:
            assert status == 200
            assert all(json.loads(raw)[k] == v for k, v in expected.items())
        rows.append({"observed_at": datetime.now(timezone.utc).isoformat(), "input": data,
                     "status": status, "raw_body": raw})
    saved = {"command": f"/usr/bin/python3 -B verify.py --record-http --port {port}",
             "transport": "actual loopback HTTP", "bindings": source_hashes(), "responses": rows}
    (ROOT / "observations/http.json").write_text(json.dumps(saved, ensure_ascii=False, indent=2) + "\n")
    print(f"Actual HTTP: {len(rows)} normal/boundary/rejection/recovery responses OK")


def record_media():
    rows = []
    for path in sorted((ROOT / "media").glob("*.jpg")):
        w, h = jpeg_size(path.read_bytes())
        rows.append({"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path),
                     "bytes": path.stat().st_size, "width": w, "height": h})
    assert len(rows) == 6, "six actual captures required"
    data = {"recorded_at": datetime.now(timezone.utc).isoformat(),
            "capture": "Actual background IAB screenshots via CUA; full-page JPEG",
            "bindings": {**source_hashes(), "observations/ui-dom.json": digest(ROOT / "observations/ui-dom.json")},
            "artifacts": rows,
            "visual_review": "Codex self-review: train/holdout labels, coefficients, residual plot, rejection and leakage warning readable",
            "limitations": ["browser engine version unavailable", "desktop only; no mobile QA", "still images, not video"]}
    (ROOT / "observations/media.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def record_readonly():
    def snapshot():
        return {p.relative_to(ROOT).as_posix(): digest(p) for p in ROOT.rglob("*") if p.is_file()}
    before = snapshot()
    result = subprocess.run([sys.executable, "-B", "verify.py"], cwd=ROOT, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    after = snapshot()
    assert before == after, "default checker mutated module"
    assert result.returncode == 0, result.stdout
    data = {"observed_at": datetime.now(timezone.utc).isoformat(), "command": "/usr/bin/python3 -B verify.py",
            "returncode": result.returncode, "unchanged_file_count": len(before), "before": before,
            "after": after, "raw_output": result.stdout}
    (ROOT / "observations/readonly.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Default checker read-only: {len(before)} file hashes unchanged")


def verify_local_links():
    documents = [ROOT / "README.md", ROOT / "skills/atlas-data-science-statistical-learning/SKILL.md"]
    checked = 0
    for document in documents:
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text()):
            parts = urlsplit(target)
            if parts.scheme:
                continue
            path = (document.parent / unquote(parts.path)).resolve() if parts.path else document
            path.relative_to(ROOT)
            assert path.is_file(), f"missing local link: {target}"
            if parts.fragment:
                headings = re.findall(r"^#+ (.+)$", path.read_text(), re.MULTILINE)
                slugs = {re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-") for title in headings}
                assert unquote(parts.fragment) in slugs, f"missing local anchor: {target}"
            checked += 1
    for target in re.findall(r'href="([^"]+)"', (ROOT / "index.html").read_text()):
        parts = urlsplit(target)
        if not parts.scheme and parts.path:
            assert (ROOT / unquote(parts.path)).is_file(), target
    print(f"README/Skill local links and heading anchors: {checked} OK; README/index source-bound")


def main():
    parser = argparse.ArgumentParser()
    for flag in ("checks", "http", "media", "readonly"):
        parser.add_argument(f"--record-{flag}", action="store_true")
    parser.add_argument("--port", type=int)
    parser.add_argument("--check-links", action="store_true")
    args = parser.parse_args()
    if args.record_http and (args.port is None or not 1 <= args.port <= 65535):
        parser.error("--record-httpは起動済み自分のserverの--portを指定してください")
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName("test_lesson"))
    print(output.getvalue(), end="")
    if args.record_checks:
        (ROOT / "observations/tests.txt").write_text(output.getvalue())
        saved = {"observed_at": datetime.now(timezone.utc).isoformat(),
                 "command": "/usr/bin/python3 -B verify.py --record-checks", "source_hashes": source_hashes(),
                 "tests_run": result.testsRun, "passed": result.wasSuccessful(),
                 "stdout_sha256": digest(ROOT / "observations/tests.txt")}
        (ROOT / "observations/checks.json").write_text(json.dumps(saved, ensure_ascii=False, indent=2) + "\n")
    if not result.wasSuccessful():
        return 1
    if args.record_http:
        record_http(args.port)
    if args.record_media:
        record_media()
    verify_saved()
    if args.check_links:
        verify_local_links()
    if args.record_readonly:
        record_readonly()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
