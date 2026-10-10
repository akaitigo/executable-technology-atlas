/* 固定原票を読むデータ。LIVEや新しい数値実験ではない。 */
(function(root){ const data={
  "schema": 1,
  "origin": "saved-finite-plan-model",
  "source_version": "v3.5.2",
  "source_commit": "e258ee23c3e52266d407572f4bcdfe7d9ed36cb5",
  "recorded_at_utc": "2026-10-06T06:23:10.638615+00:00",
  "bindings": {
    "fixtures.json": "5488aca73dc2d22d6b33ab196bed0c4192381adec41c44001e2f46a52014a789",
    "hand-oracle.json": "930cc9604a08f4c0a6ac906f428aa32b4c101b2bafd154b03bdd345d6c5f9a89",
    "observations/model-check.json": "038c4d5fbef7f057124c7ddac632d666482f7d7586451b7d9c22460a77ae0936"
  },
  "cases": [
    {
      "id": "ordinary",
      "title": "指定なし：通常の逆wave",
      "global_prune_last": false,
      "tasks": [
        {
          "id": "app-a",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "apply",
          "wave": 0,
          "prune_last": false
        },
        {
          "id": "app-b",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "apply",
          "wave": 5,
          "prune_last": false
        },
        {
          "id": "old-low",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "prune",
          "wave": -3,
          "prune_last": false
        },
        {
          "id": "old-high",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "prune",
          "wave": 8,
          "prune_last": false
        }
      ]
    },
    {
      "id": "global",
      "title": "全体指定：pruneを同じ終端waveへ",
      "global_prune_last": true,
      "tasks": [
        {
          "id": "app-a",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "apply",
          "wave": 0,
          "prune_last": false
        },
        {
          "id": "app-b",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "apply",
          "wave": 5,
          "prune_last": false
        },
        {
          "id": "old-low",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "prune",
          "wave": -3,
          "prune_last": false
        },
        {
          "id": "old-high",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "prune",
          "wave": 8,
          "prune_last": false
        }
      ]
    },
    {
      "id": "resource-only",
      "title": "資源単位指定：old-lowだけを終端へ",
      "global_prune_last": false,
      "tasks": [
        {
          "id": "app-a",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "apply",
          "wave": 0,
          "prune_last": false
        },
        {
          "id": "app-b",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "apply",
          "wave": 5,
          "prune_last": false
        },
        {
          "id": "old-low",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "prune",
          "wave": -3,
          "prune_last": true
        },
        {
          "id": "old-high",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "prune",
          "wave": 8,
          "prune_last": false
        }
      ]
    },
    {
      "id": "all-negative",
      "title": "全waveが負：最大値探索の初期値0",
      "global_prune_last": true,
      "tasks": [
        {
          "id": "app",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "apply",
          "wave": -4,
          "prune_last": false
        },
        {
          "id": "old-low",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "prune",
          "wave": -7,
          "prune_last": false
        },
        {
          "id": "old-high",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "prune",
          "wave": -2,
          "prune_last": false
        }
      ]
    },
    {
      "id": "presync-excluded",
      "title": "PreSyncのwave 20をSyncの最大値に含めない",
      "global_prune_last": true,
      "tasks": [
        {
          "id": "pre-check",
          "phase": "PreSync",
          "kind": "Job",
          "action": "apply",
          "wave": 20,
          "prune_last": false
        },
        {
          "id": "app",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "apply",
          "wave": 0,
          "prune_last": false
        },
        {
          "id": "old",
          "phase": "Sync",
          "kind": "ConfigMap",
          "action": "prune",
          "wave": -2,
          "prune_last": false
        }
      ]
    }
  ],
  "outcomes": {
    "ordinary": {
      "ordinary_waves": {
        "app-a": 0,
        "app-b": 5,
        "old-low": 8,
        "old-high": -3
      },
      "sync_max": 8,
      "last_wave_candidate": 9,
      "selected": [],
      "final_waves": {
        "app-a": 0,
        "app-b": 5,
        "old-low": 8,
        "old-high": -3
      },
      "phases": {
        "app-a": "Sync",
        "app-b": "Sync",
        "old-low": "Sync",
        "old-high": "Sync"
      },
      "before_groups": [
        {
          "phase": "Sync",
          "wave": -3,
          "ids": [
            "old-high"
          ]
        },
        {
          "phase": "Sync",
          "wave": 0,
          "ids": [
            "app-a"
          ]
        },
        {
          "phase": "Sync",
          "wave": 5,
          "ids": [
            "app-b"
          ]
        },
        {
          "phase": "Sync",
          "wave": 8,
          "ids": [
            "old-low"
          ]
        }
      ],
      "after_groups": [
        {
          "phase": "Sync",
          "wave": -3,
          "ids": [
            "old-high"
          ]
        },
        {
          "phase": "Sync",
          "wave": 0,
          "ids": [
            "app-a"
          ]
        },
        {
          "phase": "Sync",
          "wave": 5,
          "ids": [
            "app-b"
          ]
        },
        {
          "phase": "Sync",
          "wave": 8,
          "ids": [
            "old-low"
          ]
        }
      ]
    },
    "global": {
      "ordinary_waves": {
        "app-a": 0,
        "app-b": 5,
        "old-low": 8,
        "old-high": -3
      },
      "sync_max": 8,
      "last_wave_candidate": 9,
      "selected": [
        "old-high",
        "old-low"
      ],
      "final_waves": {
        "app-a": 0,
        "app-b": 5,
        "old-low": 9,
        "old-high": 9
      },
      "phases": {
        "app-a": "Sync",
        "app-b": "Sync",
        "old-low": "Sync",
        "old-high": "Sync"
      },
      "before_groups": [
        {
          "phase": "Sync",
          "wave": -3,
          "ids": [
            "old-high"
          ]
        },
        {
          "phase": "Sync",
          "wave": 0,
          "ids": [
            "app-a"
          ]
        },
        {
          "phase": "Sync",
          "wave": 5,
          "ids": [
            "app-b"
          ]
        },
        {
          "phase": "Sync",
          "wave": 8,
          "ids": [
            "old-low"
          ]
        }
      ],
      "after_groups": [
        {
          "phase": "Sync",
          "wave": 0,
          "ids": [
            "app-a"
          ]
        },
        {
          "phase": "Sync",
          "wave": 5,
          "ids": [
            "app-b"
          ]
        },
        {
          "phase": "Sync",
          "wave": 9,
          "ids": [
            "old-high",
            "old-low"
          ]
        }
      ]
    },
    "resource-only": {
      "ordinary_waves": {
        "app-a": 0,
        "app-b": 5,
        "old-low": 8,
        "old-high": -3
      },
      "sync_max": 8,
      "last_wave_candidate": 9,
      "selected": [
        "old-low"
      ],
      "final_waves": {
        "app-a": 0,
        "app-b": 5,
        "old-low": 9,
        "old-high": -3
      },
      "phases": {
        "app-a": "Sync",
        "app-b": "Sync",
        "old-low": "Sync",
        "old-high": "Sync"
      },
      "before_groups": [
        {
          "phase": "Sync",
          "wave": -3,
          "ids": [
            "old-high"
          ]
        },
        {
          "phase": "Sync",
          "wave": 0,
          "ids": [
            "app-a"
          ]
        },
        {
          "phase": "Sync",
          "wave": 5,
          "ids": [
            "app-b"
          ]
        },
        {
          "phase": "Sync",
          "wave": 8,
          "ids": [
            "old-low"
          ]
        }
      ],
      "after_groups": [
        {
          "phase": "Sync",
          "wave": -3,
          "ids": [
            "old-high"
          ]
        },
        {
          "phase": "Sync",
          "wave": 0,
          "ids": [
            "app-a"
          ]
        },
        {
          "phase": "Sync",
          "wave": 5,
          "ids": [
            "app-b"
          ]
        },
        {
          "phase": "Sync",
          "wave": 9,
          "ids": [
            "old-low"
          ]
        }
      ]
    },
    "all-negative": {
      "ordinary_waves": {
        "app": -4,
        "old-low": -2,
        "old-high": -7
      },
      "sync_max": 0,
      "last_wave_candidate": 1,
      "selected": [
        "old-high",
        "old-low"
      ],
      "final_waves": {
        "app": -4,
        "old-low": 1,
        "old-high": 1
      },
      "phases": {
        "app": "Sync",
        "old-low": "Sync",
        "old-high": "Sync"
      },
      "before_groups": [
        {
          "phase": "Sync",
          "wave": -7,
          "ids": [
            "old-high"
          ]
        },
        {
          "phase": "Sync",
          "wave": -4,
          "ids": [
            "app"
          ]
        },
        {
          "phase": "Sync",
          "wave": -2,
          "ids": [
            "old-low"
          ]
        }
      ],
      "after_groups": [
        {
          "phase": "Sync",
          "wave": -4,
          "ids": [
            "app"
          ]
        },
        {
          "phase": "Sync",
          "wave": 1,
          "ids": [
            "old-high",
            "old-low"
          ]
        }
      ]
    },
    "presync-excluded": {
      "ordinary_waves": {
        "pre-check": 20,
        "app": 0,
        "old": -2
      },
      "sync_max": 0,
      "last_wave_candidate": 1,
      "selected": [
        "old"
      ],
      "final_waves": {
        "pre-check": 20,
        "app": 0,
        "old": 1
      },
      "phases": {
        "pre-check": "PreSync",
        "app": "Sync",
        "old": "Sync"
      },
      "before_groups": [
        {
          "phase": "PreSync",
          "wave": 20,
          "ids": [
            "pre-check"
          ]
        },
        {
          "phase": "Sync",
          "wave": -2,
          "ids": [
            "old"
          ]
        },
        {
          "phase": "Sync",
          "wave": 0,
          "ids": [
            "app"
          ]
        }
      ],
      "after_groups": [
        {
          "phase": "PreSync",
          "wave": 20,
          "ids": [
            "pre-check"
          ]
        },
        {
          "phase": "Sync",
          "wave": 0,
          "ids": [
            "app"
          ]
        },
        {
          "phase": "Sync",
          "wave": 1,
          "ids": [
            "old"
          ]
        }
      ]
    }
  }
}; if(typeof module!=="undefined"&&module.exports)module.exports=data;else root.PruneLastData=data;})(globalThis);
