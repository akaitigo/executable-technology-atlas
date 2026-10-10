window.MODEL_OBSERVATION = {
  "catalog_id": "formal-methods-verification",
  "observation_started_at": "2026-10-05T13:34:09+09:00",
  "observation_finished_at": "2026-10-05T13:34:09+09:00",
  "command": "python3 check.py",
  "reproduce_command": "python3 observe.py",
  "environment": {
    "python": "3.9.6",
    "implementation": "CPython",
    "os": "Darwin",
    "os_version": "26.1",
    "architecture": "arm64"
  },
  "process": {
    "exit_code": 0,
    "attempts": 1,
    "retries": 0,
    "stdout_digest": "sha256:f19799451d356c82cb6b42b7494047941d6a632d6ef3c6ca27df0dac0ac57594",
    "stderr": ""
  },
  "input": {
    "processes": 2,
    "owner_domain": [
      null,
      0,
      1
    ],
    "initial": {
      "pc": [
        "idle",
        "idle"
      ],
      "owner": null
    },
    "invariant": "count(pc[i] == critical) <= 1",
    "fairness": "none",
    "memory_model": "sequentially consistent interleaving of declared atomic transitions"
  },
  "source_digests": {
    "model.py": "sha256:293d29a5a5cd203b6b6b04b9e7ee67a18787924990613d53ecd058bc3feedf72",
    "check.py": "sha256:5b5eea32e1e962c4b52e25591110b6167ce8a7510d39c29feb1c1e7a6f26737e",
    "observe.py": "sha256:1aa4e5d1da675cb527970ad67287eee630ae1b311765ea5b95781f3d676977da",
    "sources.json": "sha256:50d98f6a594a369295ce2f71192519e3cb1124dafa84f1e504e114ffe1def7ba"
  },
  "expected_results": {
    "atomic": "safety invariant holds for every reachable state",
    "split-guard": "safety violation with shortest counterexample"
  },
  "observation_classification": "finite model execution; not execution or verification of a production mutex",
  "model_version": "mutex-atomic-versus-split-guard-v1",
  "models": {
    "atomic": {
      "variant": "atomic",
      "state_count": 8,
      "transition_count": 14,
      "violation_count": 0,
      "invariant_holds": true,
      "search_complete": true,
      "search_method": "breadth-first reachable-state fixed point",
      "search_depth_limit": null,
      "max_shortest_distance": 3,
      "states": [
        {
          "id": 0,
          "pc": [
            "idle",
            "idle"
          ],
          "owner": null,
          "depth": 0,
          "invariant": true
        },
        {
          "id": 1,
          "pc": [
            "waiting",
            "idle"
          ],
          "owner": null,
          "depth": 1,
          "invariant": true
        },
        {
          "id": 2,
          "pc": [
            "idle",
            "waiting"
          ],
          "owner": null,
          "depth": 1,
          "invariant": true
        },
        {
          "id": 3,
          "pc": [
            "critical",
            "idle"
          ],
          "owner": 0,
          "depth": 2,
          "invariant": true
        },
        {
          "id": 4,
          "pc": [
            "waiting",
            "waiting"
          ],
          "owner": null,
          "depth": 2,
          "invariant": true
        },
        {
          "id": 5,
          "pc": [
            "idle",
            "critical"
          ],
          "owner": 1,
          "depth": 2,
          "invariant": true
        },
        {
          "id": 6,
          "pc": [
            "critical",
            "waiting"
          ],
          "owner": 0,
          "depth": 3,
          "invariant": true
        },
        {
          "id": 7,
          "pc": [
            "waiting",
            "critical"
          ],
          "owner": 1,
          "depth": 3,
          "invariant": true
        }
      ],
      "transitions": [
        {
          "from": 0,
          "to": 1,
          "process": 0,
          "action": "request"
        },
        {
          "from": 0,
          "to": 2,
          "process": 1,
          "action": "request"
        },
        {
          "from": 1,
          "to": 3,
          "process": 0,
          "action": "check-and-enter"
        },
        {
          "from": 1,
          "to": 4,
          "process": 1,
          "action": "request"
        },
        {
          "from": 2,
          "to": 4,
          "process": 0,
          "action": "request"
        },
        {
          "from": 2,
          "to": 5,
          "process": 1,
          "action": "check-and-enter"
        },
        {
          "from": 3,
          "to": 0,
          "process": 0,
          "action": "release"
        },
        {
          "from": 3,
          "to": 6,
          "process": 1,
          "action": "request"
        },
        {
          "from": 4,
          "to": 6,
          "process": 0,
          "action": "check-and-enter"
        },
        {
          "from": 4,
          "to": 7,
          "process": 1,
          "action": "check-and-enter"
        },
        {
          "from": 5,
          "to": 7,
          "process": 0,
          "action": "request"
        },
        {
          "from": 5,
          "to": 0,
          "process": 1,
          "action": "release"
        },
        {
          "from": 6,
          "to": 2,
          "process": 0,
          "action": "release"
        },
        {
          "from": 7,
          "to": 1,
          "process": 1,
          "action": "release"
        }
      ],
      "shortest_counterexample": [],
      "shortest_counterexample_steps": null,
      "liveness_checked": false
    },
    "split-guard": {
      "variant": "split-guard",
      "state_count": 23,
      "transition_count": 44,
      "violation_count": 2,
      "invariant_holds": false,
      "search_complete": true,
      "search_method": "breadth-first reachable-state fixed point",
      "search_depth_limit": null,
      "max_shortest_distance": 9,
      "states": [
        {
          "id": 0,
          "pc": [
            "idle",
            "idle"
          ],
          "owner": null,
          "depth": 0,
          "invariant": true
        },
        {
          "id": 1,
          "pc": [
            "waiting",
            "idle"
          ],
          "owner": null,
          "depth": 1,
          "invariant": true
        },
        {
          "id": 2,
          "pc": [
            "idle",
            "waiting"
          ],
          "owner": null,
          "depth": 1,
          "invariant": true
        },
        {
          "id": 3,
          "pc": [
            "ready",
            "idle"
          ],
          "owner": null,
          "depth": 2,
          "invariant": true
        },
        {
          "id": 4,
          "pc": [
            "waiting",
            "waiting"
          ],
          "owner": null,
          "depth": 2,
          "invariant": true
        },
        {
          "id": 5,
          "pc": [
            "idle",
            "ready"
          ],
          "owner": null,
          "depth": 2,
          "invariant": true
        },
        {
          "id": 6,
          "pc": [
            "critical",
            "idle"
          ],
          "owner": 0,
          "depth": 3,
          "invariant": true
        },
        {
          "id": 7,
          "pc": [
            "ready",
            "waiting"
          ],
          "owner": null,
          "depth": 3,
          "invariant": true
        },
        {
          "id": 8,
          "pc": [
            "waiting",
            "ready"
          ],
          "owner": null,
          "depth": 3,
          "invariant": true
        },
        {
          "id": 9,
          "pc": [
            "idle",
            "critical"
          ],
          "owner": 1,
          "depth": 3,
          "invariant": true
        },
        {
          "id": 10,
          "pc": [
            "critical",
            "waiting"
          ],
          "owner": 0,
          "depth": 4,
          "invariant": true
        },
        {
          "id": 11,
          "pc": [
            "ready",
            "ready"
          ],
          "owner": null,
          "depth": 4,
          "invariant": true
        },
        {
          "id": 12,
          "pc": [
            "waiting",
            "critical"
          ],
          "owner": 1,
          "depth": 4,
          "invariant": true
        },
        {
          "id": 13,
          "pc": [
            "critical",
            "ready"
          ],
          "owner": 0,
          "depth": 5,
          "invariant": true
        },
        {
          "id": 14,
          "pc": [
            "ready",
            "critical"
          ],
          "owner": 1,
          "depth": 5,
          "invariant": true
        },
        {
          "id": 15,
          "pc": [
            "critical",
            "critical"
          ],
          "owner": 1,
          "depth": 6,
          "invariant": false
        },
        {
          "id": 16,
          "pc": [
            "critical",
            "critical"
          ],
          "owner": 0,
          "depth": 6,
          "invariant": false
        },
        {
          "id": 17,
          "pc": [
            "idle",
            "critical"
          ],
          "owner": null,
          "depth": 7,
          "invariant": true
        },
        {
          "id": 18,
          "pc": [
            "critical",
            "idle"
          ],
          "owner": null,
          "depth": 7,
          "invariant": true
        },
        {
          "id": 19,
          "pc": [
            "waiting",
            "critical"
          ],
          "owner": null,
          "depth": 8,
          "invariant": true
        },
        {
          "id": 20,
          "pc": [
            "critical",
            "waiting"
          ],
          "owner": null,
          "depth": 8,
          "invariant": true
        },
        {
          "id": 21,
          "pc": [
            "ready",
            "critical"
          ],
          "owner": null,
          "depth": 9,
          "invariant": true
        },
        {
          "id": 22,
          "pc": [
            "critical",
            "ready"
          ],
          "owner": null,
          "depth": 9,
          "invariant": true
        }
      ],
      "transitions": [
        {
          "from": 0,
          "to": 1,
          "process": 0,
          "action": "request"
        },
        {
          "from": 0,
          "to": 2,
          "process": 1,
          "action": "request"
        },
        {
          "from": 1,
          "to": 3,
          "process": 0,
          "action": "check-free"
        },
        {
          "from": 1,
          "to": 4,
          "process": 1,
          "action": "request"
        },
        {
          "from": 2,
          "to": 4,
          "process": 0,
          "action": "request"
        },
        {
          "from": 2,
          "to": 5,
          "process": 1,
          "action": "check-free"
        },
        {
          "from": 3,
          "to": 6,
          "process": 0,
          "action": "claim-without-recheck"
        },
        {
          "from": 3,
          "to": 7,
          "process": 1,
          "action": "request"
        },
        {
          "from": 4,
          "to": 7,
          "process": 0,
          "action": "check-free"
        },
        {
          "from": 4,
          "to": 8,
          "process": 1,
          "action": "check-free"
        },
        {
          "from": 5,
          "to": 8,
          "process": 0,
          "action": "request"
        },
        {
          "from": 5,
          "to": 9,
          "process": 1,
          "action": "claim-without-recheck"
        },
        {
          "from": 6,
          "to": 0,
          "process": 0,
          "action": "release"
        },
        {
          "from": 6,
          "to": 10,
          "process": 1,
          "action": "request"
        },
        {
          "from": 7,
          "to": 10,
          "process": 0,
          "action": "claim-without-recheck"
        },
        {
          "from": 7,
          "to": 11,
          "process": 1,
          "action": "check-free"
        },
        {
          "from": 8,
          "to": 11,
          "process": 0,
          "action": "check-free"
        },
        {
          "from": 8,
          "to": 12,
          "process": 1,
          "action": "claim-without-recheck"
        },
        {
          "from": 9,
          "to": 12,
          "process": 0,
          "action": "request"
        },
        {
          "from": 9,
          "to": 0,
          "process": 1,
          "action": "release"
        },
        {
          "from": 10,
          "to": 2,
          "process": 0,
          "action": "release"
        },
        {
          "from": 11,
          "to": 13,
          "process": 0,
          "action": "claim-without-recheck"
        },
        {
          "from": 11,
          "to": 14,
          "process": 1,
          "action": "claim-without-recheck"
        },
        {
          "from": 12,
          "to": 1,
          "process": 1,
          "action": "release"
        },
        {
          "from": 13,
          "to": 5,
          "process": 0,
          "action": "release"
        },
        {
          "from": 13,
          "to": 15,
          "process": 1,
          "action": "claim-without-recheck"
        },
        {
          "from": 14,
          "to": 16,
          "process": 0,
          "action": "claim-without-recheck"
        },
        {
          "from": 14,
          "to": 3,
          "process": 1,
          "action": "release"
        },
        {
          "from": 15,
          "to": 17,
          "process": 0,
          "action": "release"
        },
        {
          "from": 15,
          "to": 18,
          "process": 1,
          "action": "release"
        },
        {
          "from": 16,
          "to": 17,
          "process": 0,
          "action": "release"
        },
        {
          "from": 16,
          "to": 18,
          "process": 1,
          "action": "release"
        },
        {
          "from": 17,
          "to": 19,
          "process": 0,
          "action": "request"
        },
        {
          "from": 17,
          "to": 0,
          "process": 1,
          "action": "release"
        },
        {
          "from": 18,
          "to": 0,
          "process": 0,
          "action": "release"
        },
        {
          "from": 18,
          "to": 20,
          "process": 1,
          "action": "request"
        },
        {
          "from": 19,
          "to": 21,
          "process": 0,
          "action": "check-free"
        },
        {
          "from": 19,
          "to": 1,
          "process": 1,
          "action": "release"
        },
        {
          "from": 20,
          "to": 2,
          "process": 0,
          "action": "release"
        },
        {
          "from": 20,
          "to": 22,
          "process": 1,
          "action": "check-free"
        },
        {
          "from": 21,
          "to": 16,
          "process": 0,
          "action": "claim-without-recheck"
        },
        {
          "from": 21,
          "to": 3,
          "process": 1,
          "action": "release"
        },
        {
          "from": 22,
          "to": 5,
          "process": 0,
          "action": "release"
        },
        {
          "from": 22,
          "to": 15,
          "process": 1,
          "action": "claim-without-recheck"
        }
      ],
      "shortest_counterexample": [
        {
          "from": 0,
          "to": 1,
          "process": 0,
          "action": "request"
        },
        {
          "from": 1,
          "to": 3,
          "process": 0,
          "action": "check-free"
        },
        {
          "from": 3,
          "to": 7,
          "process": 1,
          "action": "request"
        },
        {
          "from": 7,
          "to": 11,
          "process": 1,
          "action": "check-free"
        },
        {
          "from": 11,
          "to": 13,
          "process": 0,
          "action": "claim-without-recheck"
        },
        {
          "from": 13,
          "to": 15,
          "process": 1,
          "action": "claim-without-recheck"
        }
      ],
      "shortest_counterexample_steps": 6,
      "liveness_checked": false
    }
  }
};
