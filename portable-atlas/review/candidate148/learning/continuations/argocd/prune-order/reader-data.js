/* 保存原票を読む教材データ。再実験やLIVE結果ではありません。 */
(function(root){ const data = {
  "schema": 1,
  "origin": "saved-finite-python-model",
  "source_version": "v3.5.2",
  "source_commit": "e258ee23c3e52266d407572f4bcdfe7d9ed36cb5",
  "recorded_at_utc": "2026-10-06T05:34:44.780996+00:00",
  "bindings": {
    "fixtures.json": "a8603254b759d508f9aa1b9ed7a6999ba2f46ffa7513c8cb2e2cf8f76b05d8cf",
    "hand-oracle.json": "8eed335ee94fda1a9c9421ddc649f782d88bc458d59f4995fc685e1ce0e8d33a",
    "observations/model-check.json": "126261ff38e6a2827682c5a6fc829bdddf6fce9b2ed2469c90d769fe8eeb6785"
  },
  "cases": [
    {
      "id": "apply-ascending",
      "title": "適用は小さいwaveから",
      "question": "high / low / midのどれを最初に適用する？",
      "tasks": [
        {
          "id": "high",
          "action": "apply",
          "wave": 8,
          "result": "Synced",
          "observation": "unobserved"
        },
        {
          "id": "low",
          "action": "apply",
          "wave": -3,
          "result": "Synced",
          "observation": "ready"
        },
        {
          "id": "mid",
          "action": "apply",
          "wave": 1,
          "result": "Synced",
          "observation": "ready"
        }
      ]
    },
    {
      "id": "prune-descending",
      "title": "削除は元の大きいwaveから",
      "question": "元waveが -3 / 1 / 8 のとき、有効waveは符号反転でよい？",
      "tasks": [
        {
          "id": "high",
          "action": "prune",
          "wave": 8,
          "result": "Pruned",
          "observation": "absent"
        },
        {
          "id": "low",
          "action": "prune",
          "wave": -3,
          "result": "Pruned",
          "observation": "unobserved"
        },
        {
          "id": "mid",
          "action": "prune",
          "wave": 1,
          "result": "Pruned",
          "observation": "absent"
        }
      ]
    },
    {
      "id": "prune-waiting",
      "title": "Prunedでも後続が待つ",
      "question": "highがPrunedでliveのdeletionTimestampがある。midへ進む？",
      "tasks": [
        {
          "id": "high",
          "action": "prune",
          "wave": 8,
          "result": "Pruned",
          "observation": "terminating"
        },
        {
          "id": "low",
          "action": "prune",
          "wave": -3,
          "result": "Pruned",
          "observation": "unobserved"
        },
        {
          "id": "mid",
          "action": "prune",
          "wave": 1,
          "result": "Pruned",
          "observation": "absent"
        }
      ]
    },
    {
      "id": "prune-failed",
      "title": "途中のprune失敗",
      "question": "high消滅を観測後、midの結果がSyncFailedならlowへ進む？",
      "tasks": [
        {
          "id": "high",
          "action": "prune",
          "wave": 8,
          "result": "Pruned",
          "observation": "absent"
        },
        {
          "id": "low",
          "action": "prune",
          "wave": -3,
          "result": "Pruned",
          "observation": "unobserved"
        },
        {
          "id": "mid",
          "action": "prune",
          "wave": 1,
          "result": "SyncFailed",
          "observation": "unobserved"
        }
      ]
    },
    {
      "id": "mixed-same-wave-failed",
      "title": "同じwave内のprune失敗でapplyも未着手",
      "question": "wave 0にoldのpruneとnewのapply。oldがSyncFailedならnewは始まる？",
      "tasks": [
        {
          "id": "old",
          "action": "prune",
          "wave": 0,
          "result": "SyncFailed",
          "observation": "unobserved"
        },
        {
          "id": "new",
          "action": "apply",
          "wave": 0,
          "result": "Synced",
          "observation": "ready"
        },
        {
          "id": "later",
          "action": "apply",
          "wave": 2,
          "result": "Synced",
          "observation": "unobserved"
        }
      ]
    }
  ],
  "outcomes": {
    "apply-ascending": {
      "declared_order": [
        "low",
        "mid",
        "high"
      ],
      "effective_waves": {
        "high": 8,
        "low": -3,
        "mid": 1
      },
      "batches": [
        {
          "wave": -3,
          "prune": [],
          "apply": [
            "low"
          ]
        },
        {
          "wave": 1,
          "prune": [],
          "apply": [
            "mid"
          ]
        },
        {
          "wave": 8,
          "prune": [],
          "apply": [
            "high"
          ]
        }
      ],
      "started": [
        "low",
        "mid",
        "high"
      ],
      "results": {
        "low": {
          "result": "Synced",
          "observation": "ready"
        },
        "mid": {
          "result": "Synced",
          "observation": "ready"
        },
        "high": {
          "result": "Synced",
          "observation": "unobserved"
        }
      },
      "unstarted": [],
      "stop": {
        "reason": "plan-consumed",
        "wave": 8
      }
    },
    "prune-descending": {
      "declared_order": [
        "low",
        "mid",
        "high"
      ],
      "effective_waves": {
        "high": -3,
        "low": 8,
        "mid": 1
      },
      "batches": [
        {
          "wave": -3,
          "prune": [
            "high"
          ],
          "apply": []
        },
        {
          "wave": 1,
          "prune": [
            "mid"
          ],
          "apply": []
        },
        {
          "wave": 8,
          "prune": [
            "low"
          ],
          "apply": []
        }
      ],
      "started": [
        "high",
        "mid",
        "low"
      ],
      "results": {
        "high": {
          "result": "Pruned",
          "observation": "absent"
        },
        "mid": {
          "result": "Pruned",
          "observation": "absent"
        },
        "low": {
          "result": "Pruned",
          "observation": "unobserved"
        }
      },
      "unstarted": [],
      "stop": {
        "reason": "plan-consumed",
        "wave": 8
      }
    },
    "prune-waiting": {
      "declared_order": [
        "low",
        "mid",
        "high"
      ],
      "effective_waves": {
        "high": -3,
        "low": 8,
        "mid": 1
      },
      "batches": [
        {
          "wave": -3,
          "prune": [
            "high"
          ],
          "apply": []
        },
        {
          "wave": 1,
          "prune": [
            "mid"
          ],
          "apply": []
        },
        {
          "wave": 8,
          "prune": [
            "low"
          ],
          "apply": []
        }
      ],
      "started": [
        "high"
      ],
      "results": {
        "high": {
          "result": "Pruned",
          "observation": "terminating"
        }
      },
      "unstarted": [
        "mid",
        "low"
      ],
      "stop": {
        "reason": "next-reconciliation-waits-for-deletion",
        "wave": -3
      }
    },
    "prune-failed": {
      "declared_order": [
        "low",
        "mid",
        "high"
      ],
      "effective_waves": {
        "high": -3,
        "low": 8,
        "mid": 1
      },
      "batches": [
        {
          "wave": -3,
          "prune": [
            "high"
          ],
          "apply": []
        },
        {
          "wave": 1,
          "prune": [
            "mid"
          ],
          "apply": []
        },
        {
          "wave": 8,
          "prune": [
            "low"
          ],
          "apply": []
        }
      ],
      "started": [
        "high",
        "mid"
      ],
      "results": {
        "high": {
          "result": "Pruned",
          "observation": "absent"
        },
        "mid": {
          "result": "SyncFailed",
          "observation": "unobserved"
        }
      },
      "unstarted": [
        "low"
      ],
      "stop": {
        "reason": "runTasks-prune-failed",
        "wave": 1
      }
    },
    "mixed-same-wave-failed": {
      "declared_order": [
        "new",
        "old",
        "later"
      ],
      "effective_waves": {
        "old": 0,
        "new": 0,
        "later": 2
      },
      "batches": [
        {
          "wave": 0,
          "prune": [
            "old"
          ],
          "apply": [
            "new"
          ]
        },
        {
          "wave": 2,
          "prune": [],
          "apply": [
            "later"
          ]
        }
      ],
      "started": [
        "old"
      ],
      "results": {
        "old": {
          "result": "SyncFailed",
          "observation": "unobserved"
        }
      },
      "unstarted": [
        "new",
        "later"
      ],
      "stop": {
        "reason": "runTasks-prune-failed",
        "wave": 0
      }
    }
  }
}; if(typeof module!=="undefined"&&module.exports) module.exports=data; else root.PruneLessonData=data; })(typeof globalThis!=="undefined"?globalThis:this);
