"""One-feature OLS and two deliberately contaminated holdout evaluations."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parent
SOURCE_FILES = ("lesson.py", "oracle.py", "verify.py", "test_lesson.py", "index.html", "README.md",
                "skills/atlas-data-science-statistical-learning/SKILL.md")
MODES = ("train-only", "fit-leakage", "selection-leakage")
TRAIN = [[-2, -3], [-1, -1], [0, 2], [1, 3], [2, 4]]
HOLDOUT = [[-2, -1], [-1, 1], [0, 4], [1, 5], [2, 6]]
OOD = [[4, 17], [5, 26], [6, 37]]
PRESETS = {mode: {"train": TRAIN, "holdout": HOLDOUT, "mode": mode} for mode in MODES}
PRESETS["exact-line"] = {"train": [[-2, -3], [-1, -1], [0, 1], [1, 3], [2, 5]],
                         "holdout": [[-2, -1], [-1, 1], [0, 3], [1, 5], [2, 7]], "mode": "train-only"}
PRESETS["two-points"] = {"train": [[0, 1], [1, 3]], "holdout": [[2, 5], [3, 7]], "mode": "train-only"}


def invalid_inputs():
    edits = [
        {"train": []}, {"train": [[1, 2], [1, 4]]}, {"holdout": []},
        {"train": [[0, True], [1, 3]]}, {"train": [[0, 1.5], [1, 3]]},
        {"train": [[0, "1"], [1, 3]]}, {"train": [[0], [1, 3]]},
        {"train": [[0, 1], [21, 3]]}, {"mode": "ridge"}, {"ood": [[0, 0]]},
    ]
    return [{**copy.deepcopy(PRESETS["train-only"]), **edit} for edit in edits]


def validate_points(points, name, minimum):
    if not isinstance(points, list) or not minimum <= len(points) <= 40:
        raise ValueError(f"{name}は{minimum}〜40行の[x,y] listです")
    for point in points:
        if not isinstance(point, list) or len(point) != 2:
            raise ValueError(f"{name}の各行は[x,y]です")
        x, y = point
        if type(x) is not int or type(y) is not int or not -20 <= x <= 20 or not -200 <= y <= 200:
            raise ValueError(f"{name}: xは-20〜20、yは-200〜200の整数です（bool/小数/文字列は不可）")
    return copy.deepcopy(points)


def validate(data):
    if not isinstance(data, dict) or set(data) != {"train", "holdout", "mode"}:
        raise ValueError("train/holdout/modeのみ指定してください。OODは固定・評価専用です")
    if not isinstance(data["mode"], str) or data["mode"] not in MODES:
        raise ValueError("modeはtrain-only / fit-leakage / selection-leakageです。別の学習方式は未実装です")
    train = validate_points(data["train"], "train", 2)
    holdout = validate_points(data["holdout"], "holdout", 1)
    if len({x for x, _ in train}) < 2:
        raise ValueError("trainのxが一定では傾きと切片を一意に学習できません")
    return {"train": train, "holdout": holdout, "mode": data["mode"]}


def fit_ols(points):
    """Centered floating-point OLS. Receives only its explicit fitting subset."""
    if not points:
        raise ValueError("empty fit")
    n = len(points)
    mx = math.fsum(x for x, _ in points) / n
    my = math.fsum(y for _, y in points) / n
    sxx = math.fsum((x - mx) ** 2 for x, _ in points)
    if sxx == 0:
        raise ValueError("constant x fit")
    slope = math.fsum((x - mx) * (y - my) for x, y in points) / sxx
    intercept = my - slope * mx
    return {"intercept": intercept, "slope": slope}


def evaluate(points, model, prefix):
    rows = []
    for i, (x, y) in enumerate(points):
        prediction = model["intercept"] + model["slope"] * x
        residual = y - prediction
        rows.append({"id": f"{prefix}.{i}", "x": x, "y": y, "prediction": prediction,
                     "residual": residual, "squared_error": residual ** 2})
    return {"n": len(rows), "rows": rows,
            "mse": math.fsum(row["squared_error"] for row in rows) / len(rows)}


def calculate(raw):
    from fractions import Fraction
    from oracle import comparison as exact_comparison
    data = validate(raw)
    train, holdout = data["train"], data["holdout"]
    base = fit_ols(train)
    candidates = [{"intercept": base["intercept"] + offset, "slope": base["slope"]} for offset in (0, 1, 2)]
    candidate_scores = [{"offset": offset,
                         "train_mse": evaluate(train, model, "train")["mse"],
                         "holdout_mse": evaluate(holdout, model, "holdout")["mse"]}
                        for offset, model in enumerate(candidates)]
    best_score = min(row["holdout_mse"] for row in candidate_scores)
    selected = next(row["offset"] for row in candidate_scores
                    if math.isclose(row["holdout_mse"], best_score, rel_tol=0, abs_tol=1e-9))
    models = {"train-only": base, "fit-leakage": fit_ols(train + holdout),
              "selection-leakage": candidates[selected]}
    exact = exact_comparison(train, holdout, OOD)
    records = {}
    for name, model in models.items():
        for field in ("intercept", "slope"):
            if not math.isclose(model[field], float(Fraction(exact[name][field])), rel_tol=1e-10, abs_tol=1e-9):
                raise RuntimeError("独立Fraction係数oracleと不一致")
        scores = {label: evaluate(points, model, label)
                  for label, points in (("train", train), ("holdout", holdout), ("ood", OOD))}
        for label, evaluation in scores.items():
            if not math.isclose(evaluation["mse"], float(Fraction(exact[name]["mse"][label])), rel_tol=1e-10, abs_tol=1e-9):
                raise RuntimeError("独立Fraction MSE oracleと不一致")
        fitted_on = ["train", "holdout"] if name == "fit-leakage" else ["train"]
        fit_ids = [f"{label}.{i}" for label in fitted_on for i in range(len(data[label]))]
        records[name] = {**model, "evaluations": scores, "fit_row_ids": fit_ids,
                         "selection_row_ids": [f"holdout.{i}" for i in range(len(holdout))] if name == "selection-leakage" else [],
                         "selected_offset": selected if name == "selection-leakage" else None,
                         "holdout_independent": name == "train-only", "ood_used_for_fit_or_selection": False,
                         "exact_oracle": exact[name]}
    if selected != exact["selection-leakage"]["selected_offset"]:
        raise RuntimeError("独立Fraction selection oracleと不一致")
    dataset_digests = {label: hashlib.sha256(json.dumps(points, separators=(",", ":")).encode()).hexdigest()
                       for label, points in (("train", train), ("holdout", holdout), ("ood", OOD))}
    lo, hi = min(x for x, _ in train), max(x for x, _ in train)
    return {"input": data, "ood": copy.deepcopy(OOD), "dataset_digests": dataset_digests,
            "ood_outside_train_span": [x < lo or x > hi for x, _ in OOD],
            "models": records, "selected": data["mode"],
            "candidate_scores": candidate_scores, "candidate_policy": "train OLSの切片へ0/1/2を加える固定候補。holdout MSE最小、同率は小offset。",
            "tolerance": {"relative": 1e-10, "absolute": 1e-9},
            "warning": "holdoutをfit/選択に使った後、そのMSEは未使用testの性能評価ではありません。toy結果で現実の一般化は証明しません。"}


def source_hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCE_FILES}


def environment():
    return {"python": platform.python_version(), "implementation": platform.python_implementation(),
            "system": platform.system(), "macos": platform.mac_ver()[0], "machine": platform.machine(),
            "arithmetic": "math.fsum centered float OLS / independent Fraction normal equations",
            "data": "fixed synthetic integer points, no randomness, no external data"}


def observed(data):
    return {"observed_at": datetime.now(timezone.utc).isoformat(), "environment": environment(),
            "source_hashes": source_hashes(), **calculate(data)}


def observation_set():
    cases = {name: calculate(data) for name, data in PRESETS.items()}
    rejections = []
    for data in invalid_inputs():
        try:
            calculate(data)
        except ValueError as err:
            rejections.append({"input": data, "error": str(err)})
        else:
            raise RuntimeError("invalid input accepted")
    return {"cases": cases, "rejections": rejections}


def record():
    data = {"command": "/usr/bin/python3 -B lesson.py --record", "observed_at": datetime.now(timezone.utc).isoformat(),
            "environment": environment(), "source_hashes": source_hashes(), **observation_set()}
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
            self.reply(200, {"presets": PRESETS, "ood": OOD})
        else:
            self.reply(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/run":
            self.reply(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 8192:
                raise ValueError("JSON入力は1〜8192 bytesです")
            self.reply(200, observed(json.loads(self.rfile.read(length))))
        except (ValueError, TypeError) as err:
            self.reply(400, {"error": str(err)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--case", choices=tuple(PRESETS))
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    if args.record:
        record()
    elif args.case:
        print(json.dumps(observed(PRESETS[args.case]), ensure_ascii=False, indent=2))
    else:
        server = HTTPServer(("127.0.0.1", args.port), Handler)
        print(f"OLS lesson: http://127.0.0.1:{server.server_address[1]}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Owned OLS lesson server stopped.", flush=True)
        finally:
            server.server_close()
