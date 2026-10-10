#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import hashlib
import itertools
import json
from pathlib import Path
from model import State, INITIAL, invariant, successors

HERE = Path(__file__).resolve().parent


def validate(model):
    variant = model["variant"]
    states = {item["id"]: State(tuple(item["pc"]), -1 if item["owner"] is None else item["owner"]) for item in model["states"]}
    assert states[0] == INITIAL
    assert len(states) == len(set(states.values())) == model["state_count"]
    recorded_edges = {(e["from"], e["to"], e["process"], e["action"]) for e in model["transitions"]}
    assert len(recorded_edges) == model["transition_count"]
    ids = {state: key for key, state in states.items()}
    expected_edges = set()
    for source, state in states.items():
        assert model["states"][source]["invariant"] == invariant(state)
        for action, target in successors(state, variant):
            assert target in ids, "Missing reachable successor"
            expected_edges.add((source, ids[target], action["process"], action["action"]))
    assert recorded_edges == expected_edges, "Missing or invented transition"
    # Independent set expansion over the entire finite Cartesian state domain.
    locations = ("idle", "waiting", "critical") if variant == "atomic" else ("idle", "waiting", "ready", "critical")
    universe = [State(pc, owner) for pc in itertools.product(locations, repeat=2) for owner in (-1, 0, 1)]
    reachable = {INITIAL}
    distances = {INITIAL: 0}
    rounds = 0
    while True:
        targets = {target for state in universe if state in reachable for _, target in successors(state, variant)}
        new = targets - reachable
        if not new:
            break
        rounds += 1
        distances.update({state: rounds for state in new})
        reachable |= new
    assert reachable == set(states.values()), "Reachability fixed point mismatch"
    for record in model["states"]:
        assert record["depth"] == distances[states[record["id"]]]
    violations = [state for state in reachable if not invariant(state)]
    assert len(violations) == model["violation_count"]
    assert model["invariant_holds"] == (not violations)
    assert model["search_complete"] and model["search_depth_limit"] is None
    if violations:
        witness = model["shortest_counterexample"]
        assert len(witness) == min(distances[state] for state in violations) == model["shortest_counterexample_steps"]
        cursor = 0
        for event in witness:
            assert event["from"] == cursor
            assert (event["from"], event["to"], event["process"], event["action"]) in recorded_edges
            assert invariant(states[cursor]), "Counterexample has a shorter violating prefix"
            cursor = event["to"]
        assert not invariant(states[cursor])
    else:
        assert not model["shortest_counterexample"]
    assert model["liveness_checked"] is False


def main():
    document = json.loads((HERE / "evidence" / "run.json").read_text())
    for name, digest in document["source_digests"].items():
        assert "sha256:" + hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest
    stdout = (HERE / "evidence" / "stdout.json").read_bytes()
    assert "sha256:" + hashlib.sha256(stdout).hexdigest() == document["process"]["stdout_digest"]
    assert json.loads(stdout)["models"] == document["models"]
    js = (HERE / "data.js").read_text()
    assert json.loads(js.removeprefix("window.MODEL_OBSERVATION = ").removesuffix(";\n")) == document
    assert document["process"]["exit_code"] == 0 and document["process"]["attempts"] == 1 and document["process"]["retries"] == 0
    assert document["models"]["atomic"]["invariant_holds"]
    assert not document["models"]["split-guard"]["invariant_holds"]
    for model in document["models"].values():
        validate(model)
    for mutation in ("missing-state", "missing-edge", "fake-shortest", "promoted-liveness", "false-invariant"):
        model = json.loads(json.dumps(document["models"]["split-guard"]))
        if mutation == "missing-state":
            model["states"].pop()
        elif mutation == "missing-edge":
            model["transitions"].pop()
        elif mutation == "fake-shortest":
            model["shortest_counterexample_steps"] -= 1
        elif mutation == "promoted-liveness":
            model["liveness_checked"] = True
        else:
            model["states"][-1]["invariant"] = not model["states"][-1]["invariant"]
        try:
            validate(model)
        except (AssertionError, KeyError):
            continue
        raise AssertionError(f"Negative fixture accepted: {mutation}")
    print("Verification: reachable fixed point / all edges / shortest counterexample / raw stdout / source digests / UI data PASS; negatives=5")


if __name__ == "__main__":
    main()
