"""Finite summation experiment. Python stdlib only; browser renders strings."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
from pathlib import Path
import platform
import re
import sys

ROOT = Path(__file__).resolve().parent
PRESETS = {
    "integers": ["1", "2", "3", "4"],
    "cancellation": ["1e16", "1", "-1e16"],
    "compensation": ["1e16", "1", "1", "-1e16"],
    "decimal": ["0.1"] * 10,
    "zero": ["1", "-1"],
}


def decimal_text(value):
    with localcontext() as ctx:
        ctx.prec = 70
        return str(Decimal(value.numerator) / Decimal(value.denominator))


def exact_text(value):
    return str(value.numerator) if value.denominator == 1 else str(value)


def parse(tokens):
    if not isinstance(tokens, list) or not 1 <= len(tokens) <= 32:
        raise ValueError("入力は1〜32個の十進数文字列にしてください")
    values = []
    for token in tokens:
        if not isinstance(token, str) or len(token) > 40 or not re.fullmatch(
            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", token
        ):
            raise ValueError("有限の十進数を入力してください（NaN/Infinityは対象外）")
        exponent = re.search(r"[eE]([+-]?\d+)$", token)
        if exponent and abs(int(exponent.group(1))) > 100:
            raise ValueError("十進指数は-100〜100にしてください")
        x = float(token)
        if not math.isfinite(x) or abs(x) > 1e100 or (x == 0 and Fraction(token) != 0):
            raise ValueError("範囲外です: |x| ≤ 1e100、underflowなし")
        if Fraction(token) and abs(Fraction(token)) < Fraction("1e-100"):
            raise ValueError("非ゼロ入力は |x| ≥ 1e-100 にしてください")
        values.append(x)
    return values


def experiment(tokens, order="original"):
    values = parse(tokens)
    pairs = list(zip(tokens, values))
    if order == "reverse":
        pairs.reverse()
    elif order == "small-first":
        pairs.sort(key=lambda item: abs(item[1]))
    elif order != "original":
        raise ValueError("未知の順序です")
    s = {"naive": 0.0, "kahan": 0.0, "neumaier": 0.0}
    kc = nc = 0.0
    exact_input = exact_binary = Fraction(0)
    rows = []
    prefix = []
    for i, (token, x) in enumerate(pairs, 1):
        prefix.append(x)
        exact_input += Fraction(token)
        exact_binary += Fraction.from_float(x)
        s["naive"] += x
        y = x - kc
        t = s["kahan"] + y
        kc = (t - s["kahan"]) - y
        s["kahan"] = t
        old = s["neumaier"]
        t = old + x
        branch = "|s| >= |x|" if abs(old) >= abs(x) else "|s| < |x|"
        nc += (old - t) + x if abs(old) >= abs(x) else (x - t) + old
        s["neumaier"] = t
        results = {**s, "neumaier": s["neumaier"] + nc, "fsum": math.fsum(prefix)}
        methods = {}
        for name, result in results.items():
            err = Fraction.from_float(result) - exact_binary
            total_err = Fraction.from_float(result) - exact_input
            methods[name] = {
                "result": repr(result), "hex": result.hex(),
                "arithmetic_error_exact": exact_text(err),
                "arithmetic_error": decimal_text(err),
                "total_error": decimal_text(total_err),
                "total_error_exact": exact_text(total_err),
                "relative_error": None if exact_input == 0 else decimal_text(abs(total_err / exact_input)),
                "plot_error": float(abs(err)),
            }
        rows.append({"step": i, "input": token, "float": repr(x), "hex": x.hex(),
                     "oracle_decimal": decimal_text(exact_input),
                     "oracle_exact": exact_text(exact_input),
                     "binary_oracle_exact": exact_text(exact_binary),
                     "conversion_error": decimal_text(exact_binary - exact_input),
                     "kahan_c": repr(kc), "neumaier_c": repr(nc),
                     "neumaier_branch": branch, "methods": methods})
    return {"input": tokens, "order": order, "ordered_input": [p[0] for p in pairs], "steps": rows}


def environment():
    return {"python": platform.python_version(), "implementation": platform.python_implementation(),
            "os": platform.system(), "os_release": platform.release(), "machine": platform.machine(),
            "float_radix": sys.float_info.radix, "mantissa_bits": sys.float_info.mant_dig,
            "rounds": sys.float_info.rounds, "javascript_arithmetic": "not measured; rendering only"}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        payload = json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/api/presets":
            self.send_json(200, {"presets": PRESETS, "environment": environment()})
        elif self.path in ("/", "/index.html"):
            payload = (ROOT / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        try:
            if self.path != "/api/run":
                self.send_json(404, {"error": "not found"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("入力サイズは1〜4096 bytesです")
            request = json.loads(self.rfile.read(length))
            if not isinstance(request, dict):
                raise ValueError("JSON objectが必要です")
            data = experiment(request.get("tokens"), request.get("order", "original"))
            data["observed_at"] = datetime.now(timezone.utc).isoformat()
            data["environment"] = environment()
            self.send_json(200, data)
        except (ValueError, TypeError, OverflowError) as err:
            self.send_json(400, {"error": str(err)})


def record():
    runs = [experiment(tokens, order) for tokens in PRESETS.values()
            for order in ("original", "reverse", "small-first")]
    rejected = []
    for tokens in (["NaN"], ["Infinity"], ["1e309"], ["1e-400"], ["0e99999999"], [], ["1"] * 33):
        try:
            experiment(tokens)
            raise AssertionError("rejection expected")
        except ValueError as err:
            rejected.append({"input": tokens, "error": str(err)})
    data = {"observed_at": datetime.now(timezone.utc).isoformat(), "environment": environment(),
            "command": "/usr/bin/python3 lesson.py --record", "runs": runs, "rejections": rejected,
            "sources": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                        for name in ("lesson.py", "index.html", "test_lesson.py")}}
    target = ROOT / "observations" / "python.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    lines = [json.dumps({"environment": environment(), "observed_at": data["observed_at"]})]
    for run in runs:
        last = run["steps"][-1]
        lines.append(json.dumps({"input": run["ordered_input"], "order": run["order"],
                                 "oracle": last["oracle_exact"], "methods": last["methods"]}))
    for row in rejected:
        lines.append(json.dumps({"rejected": row}, ensure_ascii=False))
    output = "\n".join(lines) + "\n"
    (ROOT / "observations" / "stdout.txt").write_text(output)
    print(output, end="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--port", type=int, default=18746)
    args = parser.parse_args()
    if args.record:
        record()
    else:
        print(f"Numerical lesson: http://127.0.0.1:{args.port}", flush=True)
        HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
