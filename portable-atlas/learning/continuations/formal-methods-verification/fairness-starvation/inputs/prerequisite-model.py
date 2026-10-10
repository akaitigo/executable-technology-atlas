#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Two-process finite-state mutex model; one transition is one atomic step."""
from collections import deque
from dataclasses import dataclass

MODEL_VERSION = "mutex-atomic-versus-split-guard-v1"


@dataclass(frozen=True)
class State:
    pc: tuple
    owner: int

    def record(self):
        return {"pc": list(self.pc), "owner": None if self.owner == -1 else self.owner}


INITIAL = State(("idle", "idle"), -1)


def invariant(state):
    return state.pc.count("critical") <= 1


def successors(state, variant):
    if variant not in ("atomic", "split-guard"):
        raise ValueError("Unknown model variant")
    for process in range(2):
        pc = list(state.pc)
        owner = state.owner
        action = None
        if pc[process] == "idle":
            pc[process] = "waiting"
            action = "request"
        elif pc[process] == "waiting" and owner == -1:
            if variant == "atomic":
                pc[process], owner, action = "critical", process, "check-and-enter"
            else:
                pc[process], action = "ready", "check-free"
        elif pc[process] == "ready" and variant == "split-guard":
            # Intentional defect: the earlier observation of owner is stale.
            # Claim does not recheck owner, so two checked processes may enter.
            pc[process], owner, action = "critical", process, "claim-without-recheck"
        elif pc[process] == "critical":
            pc[process], owner, action = "idle", -1, "release"
        if action is not None:
            yield {"process": process, "action": action}, State(tuple(pc), owner)


def explore(variant):
    queue = deque([INITIAL])
    states = [INITIAL]
    ids = {INITIAL: 0}
    depth = {INITIAL: 0}
    parents = {}
    edges = []
    while queue:
        state = queue.popleft()
        for event, target in successors(state, variant):
            if target not in ids:
                ids[target] = len(states)
                states.append(target)
                depth[target] = depth[state] + 1
                parents[target] = (state, event)
                queue.append(target)
            edges.append({"from": ids[state], "to": ids[target], **event})
    violations = [state for state in states if not invariant(state)]
    witness = []
    if violations:
        cursor = min(violations, key=depth.get)
        reverse = []
        while cursor != INITIAL:
            previous, event = parents[cursor]
            reverse.append({"from": ids[previous], "to": ids[cursor], **event})
            cursor = previous
        witness = list(reversed(reverse))
    return {
        "variant": variant,
        "state_count": len(states),
        "transition_count": len(edges),
        "violation_count": len(violations),
        "invariant_holds": not violations,
        "search_complete": True,
        "search_method": "breadth-first reachable-state fixed point",
        "search_depth_limit": None,
        "max_shortest_distance": max(depth.values()),
        "states": [{"id": ids[state], **state.record(), "depth": depth[state], "invariant": invariant(state)} for state in states],
        "transitions": edges,
        "shortest_counterexample": witness,
        "shortest_counterexample_steps": len(witness) if violations else None,
        "liveness_checked": False,
    }
