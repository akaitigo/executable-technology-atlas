"""Even-parity Hamming(7,4); decoder sees only the received word."""
import argparse
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parent
SOURCE_FILES = ("lesson.py", "oracle.py", "test_lesson.py", "verify.py", "index.html")
DATA_POSITIONS = (3, 5, 6, 7)
PRESETS = {
    "no-error": {"message": "1011", "errors": []},
    "single-data": {"message": "1011", "errors": [6]},
    "single-parity": {"message": "1011", "errors": [2]},
    "double-counterexample": {"message": "0000", "errors": [1, 2]},
}
INVALID = [
    {"message": "101", "errors": []},
    {"message": "10x1", "errors": []},
    {"message": 1011, "errors": []},
    {"message": "0000", "errors": [0]},
    {"message": "0000", "errors": [8]},
    {"message": "0000", "errors": [True]},
    {"message": "0000", "errors": [1, 1]},
    {"message": "0000", "errors": [1, 2, 3]},
    {"message": "0000", "errors": "1"},
    {"message": "0000", "errors": [], "mode": "secded"},
]


def bits(value, length):
    if not isinstance(value, str) or len(value) != length or any(c not in "01" for c in value):
        raise ValueError(f"bit列は0/1のみの{length}文字にしてください")
    return [int(c) for c in value]


def encode(message):
    d1, d2, d3, d4 = bits(message, 4)
    return "".join(map(str, (d1 ^ d2 ^ d4, d1 ^ d3 ^ d4, d1,
                             d2 ^ d3 ^ d4, d2, d3, d4)))


def parity_checks(received):
    word = bits(received, 7)
    checks = []
    for mask in (1, 2, 4):
        positions = [p for p in range(1, 8) if p & mask]
        values = [word[p - 1] for p in positions]
        checks.append({"mask": mask, "positions": positions,
                       "values": values, "sum": sum(values), "bit": sum(values) % 2})
    return checks


def decode(received):
    word = bits(received, 7)
    checks = parity_checks(received)
    syndrome = sum(row["mask"] * row["bit"] for row in checks)
    if syndrome:
        word[syndrome - 1] ^= 1
    corrected = "".join(map(str, word))
    return {"checks": checks, "syndrome": syndrome, "syndrome_s4s2s1": f"{syndrome:03b}",
            "flipped_position": syndrome or None, "corrected": corrected,
            "recovered": "".join(corrected[p - 1] for p in DATA_POSITIONS),
            "post_syndrome": sum(row["mask"] * row["bit"] for row in parity_checks(corrected))}


def validate(data):
    if not isinstance(data, dict) or set(data) != {"message", "errors"}:
        raise ValueError("messageとerrorsのみを指定してください。SECDEDは未実装です")
    bits(data["message"], 4)
    errors = data["errors"]
    if not isinstance(errors, list) or len(errors) > 2:
        raise ValueError("誤り位置は0〜2個のlistにしてください。この教材は3bit以上を駆動しません")
    if any(type(p) is not int or not 1 <= p <= 7 for p in errors):
        raise ValueError("誤り位置は1〜7の整数です（bool/文字列/小数は不可）")
    if len(set(errors)) != len(errors):
        raise ValueError("同じ誤り位置の重複は指定できません")
    return {"message": data["message"], "errors": sorted(errors)}


def experiment(data):
    from oracle import matrix_encode, matrix_syndrome, nearest_codewords
    inputs = validate(data)
    encoded = encode(inputs["message"])
    received_bits = list(encoded)
    for p in inputs["errors"]:
        received_bits[p - 1] = str(1 - int(received_bits[p - 1]))
    received = "".join(received_bits)
    result = decode(received)
    oracle = {"encoded": matrix_encode(inputs["message"]),
              "syndrome": matrix_syndrome(received),
              "nearest": nearest_codewords(received)}
    if oracle["encoded"] != encoded or oracle["syndrome"] != result["syndrome"]:
        raise RuntimeError("独立matrix oracleとの不一致")
    if oracle["nearest"]["words"] != [result["corrected"]]:
        raise RuntimeError("独立nearest-codeword oracleとの不一致")
    matches = result["recovered"] == inputs["message"]
    return {"input": inputs, "encoded": encoded, "received": received, **result,
            "oracle": oracle, "ground_truth_matches": matches,
            "guarantee_applies": len(inputs["errors"]) <= 1,
            "outcome": "recovered" if matches else "miscorrected",
            "warning": "decoderは原messageと誤り数を知りません。post-syndrome 0は原messageの保証ではありません。"}


def source_hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCE_FILES}


def environment():
    return {"python": platform.python_version(), "implementation": platform.python_implementation(),
            "system": platform.system(), "macos": platform.mac_ver()[0], "machine": platform.machine(),
            "arithmetic": "integer XOR / GF(2); no packages", "channel": "deterministic bit flips, not physical channel"}


def observed(data):
    return {"observed_at": datetime.now(timezone.utc).isoformat(), "environment": environment(),
            "source_hashes": source_hashes(), **experiment(data)}


def observation_set():
    single, clean = [], []
    for n in range(16):
        message = f"{n:04b}"
        clean.append(experiment({"message": message, "errors": []}))
        for position in range(1, 8):
            row = experiment({"message": message, "errors": [position]})
            if not row["ground_truth_matches"] or row["syndrome"] != position or row["flipped_position"] != position:
                raise RuntimeError("single-bit contract failed")
            single.append(row)
    rejected = []
    for data in INVALID:
        try:
            experiment(data)
        except ValueError as err:
            rejected.append({"input": data, "error": str(err)})
        else:
            raise RuntimeError("invalid input accepted")
    return {"no_error": clean, "single_bit": single,
            "counterexample": experiment(PRESETS["double-counterexample"]), "rejections": rejected}


def record():
    data = {"command": "/usr/bin/python3 -B lesson.py --record",
            "observed_at": datetime.now(timezone.utc).isoformat(), "environment": environment(),
            "source_hashes": source_hashes(), **observation_set()}
    directory = ROOT / "observations"
    directory.mkdir(exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    (directory / "python.json").write_text(raw, encoding="utf-8")
    (directory / "stdout.txt").write_text(raw, encoding="utf-8")
    print(raw, end="")


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, payload, kind="application/json; charset=utf-8"):
        raw = json.dumps(payload, ensure_ascii=False).encode() if isinstance(payload, dict) else payload
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.reply(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/presets":
            self.reply(200, {"presets": PRESETS, "environment": environment()})
        else:
            self.reply(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/run":
            self.reply(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 2048:
                raise ValueError("入力JSONは1〜2048 bytesです")
            self.reply(200, observed(json.loads(self.rfile.read(length))))
        except (ValueError, TypeError) as err:
            self.reply(400, {"error": str(err)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--case", choices=tuple(PRESETS))
    parser.add_argument("--port", type=int, default=18748)
    args = parser.parse_args()
    if args.record:
        record()
    elif args.case:
        print(json.dumps(observed(PRESETS[args.case]), ensure_ascii=False, indent=2))
    else:
        server = HTTPServer(("127.0.0.1", args.port), Handler)
        server.timeout = 5
        print(f"Hamming lesson: http://127.0.0.1:{server.server_address[1]}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Owned lesson server stopped.", flush=True)
        finally:
            server.server_close()
