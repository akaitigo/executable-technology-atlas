"""一次遅れplantの説明用シミュレータ。標準Pythonのみ、実機I/Oなし。"""
import argparse
import hashlib
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRESETS = {
    "stable": {"gain": 2., "dt": .1, "steps": 40, "limit": None},
    "oscillation": {"gain": 2., "dt": .5, "steps": 40, "limit": None},
    "boundary": {"gain": 2., "dt": 2/3, "steps": 40, "limit": None},
    "divergence": {"gain": 2., "dt": .8, "steps": 40, "limit": None},
    "saturation": {"gain": 2., "dt": .1, "steps": 40, "limit": .35},
}


def simulate(gain=2., dt=.1, steps=40, limit=None):
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 100:
        raise ValueError("stepsは1〜100の整数です")
    for name, value, low, high in (("gain", gain, 0., 20.), ("dt", dt, .01, 1.)):
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{name}は{low}〜{high}の有限値です")
    if limit is not None and (not math.isfinite(limit) or not .05 <= limit <= 5.):
        raise ValueError("limitは0.05〜5の有限値です")
    # tau=1, reference=1, initial=0. Euler slopeは独立のclosed-formから生成しない。
    a = 1 - dt*(1+gain)
    equilibrium = gain/(1+gain)
    y, samples = 0., []
    for n in range(steps+1):
        requested = gain*(1-y)
        u = requested if limit is None else max(-limit, min(limit, requested))
        samples.append({"n": n, "t": n*dt, "y": y, "u": u,
                        "u_requested": requested, "saturated": u != requested,
                        "continuous_unsaturated": equilibrium*(1-math.exp(-(1+gain)*n*dt))})
        if n < steps:
            y = y + dt*(-y+u)
    # 線形Oracleはclipなしの場合のみ。飽和presetは常時上限にある特殊条件。
    saturated_oracle = (limit is not None and dt <= 1 and gain*(1-limit) >= limit)
    if limit is None:
        expected = [equilibrium*(1-a**n) for n in range(steps+1)]
        oracle_name = "unsaturated-discrete-closed-form"
    elif saturated_oracle:
        expected = [limit*(1-(1-dt)**n) for n in range(steps+1)]
        oracle_name = "always-upper-saturated-discrete-closed-form"
    else:
        expected, oracle_name = None, "no-closed-form-oracle-for-this-clipped-input"
    errors = []
    if expected is not None:
        for row, value in zip(samples, expected):
            row["discrete_oracle"] = value
            errors.append(abs(row["y"]-value)/max(1., abs(value)))
    # モデルの安定性と、選択した数値schemeの安定性を別表現にする。
    if math.isclose(abs(a), 1., abs_tol=1e-12, rel_tol=0):
        classification = "boundary"
    elif abs(a) > 1:
        classification = "divergence"
    elif a < 0:
        classification = "oscillation"
    else:
        classification = "stable"
    return {
        "input": {"gain": gain, "dt": dt, "steps": steps, "limit": limit,
                  "tau": 1., "reference": 1., "initial": 0., "method": "forward-euler"},
        "summary": {"linear_factor_a": a, "unsaturated_equilibrium": equilibrium,
                    "linear_euler_class": classification,
                    "classification_applies_to": "unsaturated-Euler-only",
                    "continuous_unsaturated_stable": True, "final_y": samples[-1]["y"],
                    "final_error": 1-samples[-1]["y"],
                    "saturated_updates": sum(row["saturated"] for row in samples[:-1]),
                    "oracle": oracle_name, "max_scaled_oracle_error": max(errors) if errors else None,
                    "oracle_tolerance": 1e-12,
                    "oracle_pass": max(errors) <= 1e-12 if errors else None},
        "samples": samples,
        "boundary": "方程式のCPUシミュレーション。実機、HIL、リアルタイム制御、PID全機能、安全認証の証拠ではない。",
    }


def observe(inputs, command):
    result = simulate(**inputs)
    result["execution"] = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "implementation": platform.python_implementation(),
        "platform": platform.system() + " " + platform.machine(),
        "command": command, "source_sha256": hashlib.sha256((ROOT/"simulator.py").read_bytes()).hexdigest(),
        "cpu_only": True, "hardware_measurement": False,
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    results = {name: observe(inputs, ["python3", "simulator.py", "--record"] if args.record else ["python3", "simulator.py"]) for name, inputs in PRESETS.items()}
    payload = json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    print(payload, end="")
    if args.record:
        folder = ROOT/"observations"
        folder.mkdir(exist_ok=True)
        (folder/"presets.json").write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
