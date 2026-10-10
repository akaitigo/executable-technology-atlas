#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the finite checker in a new Python process and retain its actual stdout."""
import hashlib
import html
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent


def sha(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
        staging = Path(handle.name)
    try:
        os.replace(staging, path)
    finally:
        staging.unlink(missing_ok=True)


def render_trace(document):
    model = document["models"]["split-guard"]
    sequence = [0] + [edge["to"] for edge in model["shortest_counterexample"]]
    pieces = ['<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="1000" viewBox="0 0 1040 1000" role="img" aria-labelledby="title desc">',
        '<title id="title">Mutex guard defect — shortest counterexample</title>',
        '<desc id="desc">Diagram generated from the actual Python breadth-first search trace. Six transitions reach two processes in the critical section.</desc>',
        '<rect width="1040" height="1000" rx="24" fill="#f4f1e9"/>',
        '<g font-family="-apple-system, sans-serif" fill="#202e31">',
        '<text x="48" y="58" font-size="28" font-weight="700">空き確認を分けると、6 stepで相互排他が破れる</text>',
        '<text x="48" y="91" font-size="15">実探索traceの再描画 / Python BFS / 23 states · 44 transitions · 2 violations</text>']
    for index, state_id in enumerate(sequence):
        state = model["states"][state_id]
        y = 122 + index * 116
        color = "#b33c35" if not state["invariant"] else "#24725f"
        background = "#fce0dd" if not state["invariant"] else "#fffdfa"
        owner = "∅" if state["owner"] is None else "P" + str(state["owner"])
        action = "initial" if index == 0 else "P{process}: {action}".format(**model["shortest_counterexample"][index - 1])
        pieces.extend([
            f'<rect x="48" y="{y}" width="944" height="90" rx="12" fill="{background}" stroke="{color}" stroke-width="2"/>',
            f'<text x="70" y="{y+29}" font-size="16" font-weight="700">{index} · {html.escape(action)}</text>',
            f'<text x="70" y="{y+64}" font-size="20" font-family="monospace">P0={state["pc"][0]}   P1={state["pc"][1]}   owner={owner}</text>',
            f'<text x="950" y="{y+38}" text-anchor="end" font-size="16" fill="{color}">{"VIOLATION" if not state["invariant"] else "safe"}</text>',
        ])
        if index < len(sequence) - 1:
            pieces.append(f'<path d="M520 {y+93}v17m-6-6 6 6 6-6" fill="none" stroke="#566568" stroke-width="2"/>')
    pieces.extend([f'<text x="48" y="965" font-size="14">Observed: {document["observation_finished_at"]} · Abstract model; production mutex refinement not checked</text>', '</g></svg>'])
    return "\n".join(pieces).encode()


def main():
    command = [sys.executable, "check.py"]
    start = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")
    result = subprocess.run(command, cwd=HERE, capture_output=True, text=True, timeout=10, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    payload = json.loads(result.stdout)
    if not payload["models"]["atomic"]["invariant_holds"] or payload["models"]["split-guard"]["invariant_holds"]:
        raise RuntimeError("Expected safe model / faulty model distinction was not observed")
    document = {
        "catalog_id": "formal-methods-verification",
        "observation_started_at": start,
        "observation_finished_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds"),
        "command": "python3 check.py",
        "reproduce_command": "python3 observe.py",
        "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(), "os": platform.system(), "os_version": platform.mac_ver()[0] or platform.release(), "architecture": platform.machine()},
        "process": {"exit_code": result.returncode, "attempts": 1, "retries": 0, "stdout_digest": "sha256:" + hashlib.sha256(result.stdout.encode()).hexdigest(), "stderr": result.stderr},
        "input": {"processes": 2, "owner_domain": [None, 0, 1], "initial": {"pc": ["idle", "idle"], "owner": None}, "invariant": "count(pc[i] == critical) <= 1", "fairness": "none", "memory_model": "sequentially consistent interleaving of declared atomic transitions"},
        "source_digests": {name: sha(HERE / name) for name in ("model.py", "check.py", "observe.py", "sources.json")},
        "expected_results": {"atomic": "safety invariant holds for every reachable state", "split-guard": "safety violation with shortest counterexample"},
        "observation_classification": "finite model execution; not execution or verification of a production mutex",
        **payload,
    }
    encoded = json.dumps(document, ensure_ascii=False, indent=2).encode() + b"\n"
    atomic_write(HERE / "evidence" / "run.json", encoded)
    atomic_write(HERE / "evidence" / "stdout.json", result.stdout.encode())
    atomic_write(HERE / "evidence" / "stderr.txt", result.stderr.encode())
    atomic_write(HERE / "data.js", b"window.MODEL_OBSERVATION = " + encoded.rstrip() + b";\n")
    atomic_write(HERE / "evidence" / "counterexample.svg", render_trace(document))
    for name, model in document["models"].items():
        print(f"{name}: states={model['state_count']} transitions={model['transition_count']} violations={model['violation_count']} shortest={model['shortest_counterexample_steps']}")
    print(f"Observed: {document['observation_finished_at']} Python {document['environment']['python']}")


if __name__ == "__main__":
    main()
