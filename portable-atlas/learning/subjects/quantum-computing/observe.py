# SPDX-License-Identifier: Apache-2.0
"""Run the actual simulator subprocess, retain raw complex output and identity."""
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def atomic_write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as file:
        file.write(raw)
        temporary = file.name
    os.replace(temporary, path)


def time_now():
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def render_comparison(run):
    cards = []
    for index, key in enumerate(("coherent", "dephased")):
        stages = run["result"]["circuits"][key]["stages"]
        x = 24 + index * 488
        cards.append(f'<rect x="{x}" y="88" width="464" height="332" rx="18" fill="#fff" stroke="#536a71"/>')
        cards.append(f'<text x="{x+24}" y="125" font-size="24">{ "H → H / coherence保持" if key == "coherent" else "H → D → H / coherence消失"}</text>')
        for j, stage in enumerate(stages):
            y = 168 + j * 56
            p = stage["probabilities"]
            cards.append(f'<text x="{x+24}" y="{y}" font-size="16">{stage["operation"].replace("|0>", "|0⟩")} : P(0)={p[0]:.3f}, P(1)={p[1]:.3f}</text>')
            cards.append(f'<text x="{x+24}" y="{y+22}" font-size="14" fill="#59646b">|ρ01|={stage["coherence_magnitude"]:.3f} / purity={stage["purity"]:.3f}</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="496" viewBox="0 0 1000 496" role="img" aria-labelledby="title desc">'
            '<title id="title">Interference and nonselective dephasing comparison</title><desc id="desc">Diagram redrawn from actual Python complex-state simulation, not quantum hardware or a screenshot.</desc>'
            '<rect width="1000" height="496" rx="22" fill="#eef2f4"/><g font-family="sans-serif" fill="#173945">'
            '<text x="24" y="40" font-size="26">同じ50/50でも、次のHの結果は同じではない</text><text x="24" y="67" font-size="15">実Python simulationの再描画 / D = Z基底の測定結果を読まないdephasing</text>'
            + ''.join(cards) + f'<text x="24" y="454" font-size="14">Observed: {run["finished_at"]} / 1 qubit ideal model / no quantum hardware</text></g></svg>')


def main():
    started = time_now()
    completed = subprocess.run([sys.executable, "-B", "check.py"], cwd=HERE, capture_output=True, timeout=10)
    if completed.returncode:
        raise RuntimeError("simulator failed; prior successful evidence retained")
    result = json.loads(completed.stdout)
    run = {"schema_version": 1, "classification": "actual-classical-simulation-not-quantum-device",
           "started_at": started, "finished_at": time_now(), "command": "python3 -B check.py",
           "reproduce": "python3 -B observe.py", "attempts": 1, "retries": 0,
           "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                           "os": platform.system(), "release": platform.release(), "architecture": platform.machine()},
           "input": {"initial_state": [[1, 0], [0, 0]], "qubits": 1, "circuits": {k: x["operations"] for k, x in result["circuits"].items()},
                     "shots_each": 4096, "seed_each": 20261005, "dephasing": "nonselective Z-basis measurement; outcome forgotten"},
           "source_version": result["model_version"],
           "source_hashes": {name: digest((HERE/name).read_bytes()) for name in ("simulator.py", "check.py", "observe.py", "sources.json")},
           "raw_stdout": {"path": "evidence/stdout.json", "digest": digest(completed.stdout)},
           "raw_stderr": {"path": "evidence/stderr.txt", "digest": digest(completed.stderr)},
           "exit_code": completed.returncode, "result": result}
    raw = (json.dumps(run, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    atomic_write(HERE/"evidence/stdout.json", completed.stdout)
    atomic_write(HERE/"evidence/stderr.txt", completed.stderr)
    atomic_write(HERE/"evidence/run.json", raw)
    atomic_write(HERE/"data.js", b"window.QUANTUM_OBSERVATION = " + raw.rstrip() + b";\n")
    atomic_write(HERE/"evidence/interference.svg", render_comparison(run).encode())
    print("Observed:", run["finished_at"], run["environment"])
    for name, circuit in result["circuits"].items():
        print(name, "Born=", circuit["stages"][-1]["probabilities"], "sample_counts=", circuit["sampling"]["counts"])


if __name__ == "__main__":
    main()
