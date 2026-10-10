"""Conditional probabilities in a known finite synthetic population."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parent
FIELDS = ("ap", "an", "bp", "bn")
SOURCE_FILES = ("lesson.py", "test_lesson.py", "verify.py", "index.html")
PRESETS = {
    "rare": {"ap": 9, "an": 1, "bp": 99, "bn": 891},
    "balanced": {"ap": 450, "an": 50, "bp": 50, "bn": 450},
    "ten-percent": {"ap": 90, "an": 10, "bp": 90, "bn": 810},
    "no-positive": {"ap": 0, "an": 10, "bp": 0, "bn": 990},
    "no-a": {"ap": 0, "an": 0, "bp": 100, "bn": 900},
    "no-b": {"ap": 90, "an": 10, "bp": 0, "bn": 0},
    "hand-count": {"ap": 2, "an": 1, "bp": 3, "bn": 6},
}


def validate(counts):
    if not isinstance(counts, dict) or set(counts) != set(FIELDS):
        raise ValueError("ap / an / bp / bn の4セルが必要です")
    if any(type(counts[key]) is not int or not 0 <= counts[key] <= 2000 for key in FIELDS):
        raise ValueError("countsは0〜2000の整数にしてください（bool/小数/文字列は不可）")
    if not 1 <= sum(counts.values()) <= 2000:
        raise ValueError("全populationの合計は1〜2000にしてください")
    return dict(counts)


def probability(numerator, denominator):
    if denominator == 0:
        return {"fraction": None, "percent": None, "numerator": numerator,
                "denominator": denominator, "reason": "条件となる集合が空（分母0）"}
    ratio = Fraction(numerator, denominator)
    with localcontext() as ctx:
        ctx.prec = 16
        percent = format(Decimal(ratio.numerator) / Decimal(ratio.denominator) * 100, ".4f")
    return {"fraction": str(ratio), "percent": percent, "numerator": numerator,
            "denominator": denominator, "reason": None}


def enumeration_oracle(counts):
    # A separately enumerated population: each member has a class and test result.
    population = []
    for field, group, outcome in (("ap", "A", "+"), ("an", "A", "-"),
                                  ("bp", "B", "+"), ("bn", "B", "-")):
        population.extend([(group, outcome)] * counts[field])
    a = [member for member in population if member[0] == "A"]
    b = [member for member in population if member[0] == "B"]
    positive = [member for member in population if member[1] == "+"]
    intersection = [member for member in population if member == ("A", "+")]
    b_positive = [member for member in population if member == ("B", "+")]
    def ratio(n, d):
        return str(Fraction(n, d)) if d else None
    return {"prior": ratio(len(a), len(population)),
            "sensitivity": ratio(len(intersection), len(a)),
            "false_positive_rate": ratio(len(b_positive), len(b)),
            "ppv": ratio(len(intersection), len(positive)),
            "positive_rate": ratio(len(positive), len(population))}


def calculate(raw_counts):
    counts = validate(raw_counts)
    ap, an, bp, bn = (counts[key] for key in FIELDS)
    n, a, b, positive = ap + an + bp + bn, ap + an, bp + bn, ap + bp
    probabilities = {"prior": probability(a, n), "sensitivity": probability(ap, a),
                     "false_positive_rate": probability(bp, b), "ppv": probability(ap, positive),
                     "positive_rate": probability(positive, n)}
    prior = Fraction(a, n)
    joint_a = Fraction(ap, n)
    joint_b = Fraction(bp, n)
    positive_mass = joint_a + joint_b
    joint_bayes = joint_a / positive_mass if positive_mass else None
    weighted_a = Fraction(ap, a) * prior if a else Fraction(0)
    weighted_b = Fraction(bp, b) * (1 - prior) if b else Fraction(0)
    weighted_bayes = weighted_a / (weighted_a + weighted_b) if positive else None
    enumeration = enumeration_oracle(counts)
    assert all(value["fraction"] == enumeration[key] for key, value in probabilities.items())
    assert probabilities["ppv"]["fraction"] == (str(joint_bayes) if joint_bayes is not None else None)
    assert joint_bayes == weighted_bayes
    return {"counts": counts, "totals": {"population": n, "A": a, "B": b, "positive": positive},
            "probabilities": probabilities, "enumeration_oracle": enumeration,
            "bayes": {"joint_A_positive": str(joint_a), "joint_B_positive": str(joint_b),
                      "positive_mass": str(positive_mass),
                      "posterior": str(joint_bayes) if joint_bayes is not None else None,
                      "weighted_A": str(weighted_a), "weighted_B": str(weighted_b),
                      "absent_classes": [group for group, size in (("A", a), ("B", b)) if size == 0],
                      "note": "空classの確率質量は0。空classを条件とする確率自体は未定義。"},
            "inversion": {"equal": probabilities["ppv"]["fraction"] == probabilities["sensitivity"]["fraction"]
                          if a and positive else None,
                          "forward_condition_count": a, "reverse_condition_count": positive}}


def source_hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCE_FILES}


def environment():
    return {"python": platform.python_version(), "implementation": platform.python_implementation(),
            "system": platform.system(), "macos": platform.mac_ver()[0], "machine": platform.machine(),
            "arithmetic": "fractions.Fraction; Decimal percentage display only",
            "sampling": "none; all synthetic population members known, uniformly selected"}


def observed(counts):
    return {"observed_at": datetime.now(timezone.utc).isoformat(), "environment": environment(),
            "source_hashes": source_hashes(), **calculate(counts)}


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data):
        payload = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            payload = (ROOT / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
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
                raise ValueError("JSON入力は1〜2048 bytesです")
            data = json.loads(self.rfile.read(length))
            self.reply(200, observed(data))
        except (ValueError, TypeError) as err:
            self.reply(400, {"error": str(err)})


def record():
    cases = {name: calculate(counts) for name, counts in PRESETS.items()}
    invalid = [{"ap": -1, "an": 1, "bp": 1, "bn": 1},
               {"ap": 1.5, "an": 1, "bp": 1, "bn": 1},
               {"ap": True, "an": 1, "bp": 1, "bn": 1},
               {"ap": "9", "an": 1, "bp": 1, "bn": 1},
               dict.fromkeys(FIELDS, 0), dict.fromkeys(FIELDS, 1000), {"ap": 1}]
    rejections = []
    for counts in invalid:
        try:
            calculate(counts)
            raise AssertionError("expected invalid counts")
        except ValueError as err:
            rejections.append({"input": counts, "error": str(err)})
    data = {"command": "/usr/bin/python3 -B lesson.py --record", "observed_at": datetime.now(timezone.utc).isoformat(),
            "environment": environment(), "source_hashes": source_hashes(), "cases": cases, "rejections": rejections}
    out = ROOT / "observations"
    out.mkdir(exist_ok=True)
    (out / "python.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    raw = json.dumps(data, ensure_ascii=False) + "\n"
    (out / "stdout.txt").write_text(raw)
    print(raw, end="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--port", type=int, default=18747)
    args = parser.parse_args()
    if args.record:
        record()
    else:
        server = HTTPServer(("127.0.0.1", args.port), Handler)
        print(f"Conditional probability lesson: http://127.0.0.1:{args.port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Owned lesson server stopped.", flush=True)
        finally:
            server.server_close()
