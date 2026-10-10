(function(root){const data={
  "cases": [
    {
      "id": "no-confirmation-needed",
      "title": "現在waveに確認が必要なpruneなし",
      "current_wave": 0,
      "prune_confirmed": false,
      "current_prunes": [
        {
          "id": "old-a",
          "requires_confirmation": false
        },
        {
          "id": "old-b",
          "requires_confirmation": false
        }
      ],
      "current_apply_ids": [
        "new-config"
      ],
      "later_prunes": [
        {
          "id": "old-later",
          "wave": 1,
          "requires_confirmation": false
        }
      ]
    },
    {
      "id": "needs-confirmation",
      "title": "現在waveのold-bが未確認",
      "current_wave": 0,
      "prune_confirmed": false,
      "current_prunes": [
        {
          "id": "old-a",
          "requires_confirmation": false
        },
        {
          "id": "old-b",
          "requires_confirmation": true
        }
      ],
      "current_apply_ids": [
        "new-config"
      ],
      "later_prunes": [
        {
          "id": "old-later",
          "wave": 1,
          "requires_confirmation": false
        }
      ]
    },
    {
      "id": "already-confirmed",
      "title": "同じ現在waveを確認済みで渡す",
      "current_wave": 0,
      "prune_confirmed": true,
      "current_prunes": [
        {
          "id": "old-a",
          "requires_confirmation": false
        },
        {
          "id": "old-b",
          "requires_confirmation": true
        }
      ],
      "current_apply_ids": [
        "new-config"
      ],
      "later_prunes": [
        {
          "id": "old-later",
          "wave": 1,
          "requires_confirmation": false
        }
      ]
    },
    {
      "id": "later-wave-only",
      "title": "確認が必要なのは後続waveだけ",
      "current_wave": 0,
      "prune_confirmed": false,
      "current_prunes": [
        {
          "id": "old-a",
          "requires_confirmation": false
        },
        {
          "id": "old-b",
          "requires_confirmation": false
        }
      ],
      "current_apply_ids": [
        "new-config"
      ],
      "later_prunes": [
        {
          "id": "old-later",
          "wave": 1,
          "requires_confirmation": true
        }
      ]
    }
  ],
  "outcomes": {
    "no-confirmation-needed": {
      "gate": "pass",
      "checked_current_ids": [
        "old-a",
        "old-b"
      ],
      "first_blocker": null,
      "continue_to_prune_loop": true,
      "later_prunes_checked": [],
      "current_prunes_started": [],
      "current_apply_started": [],
      "api_calls": 0
    },
    "needs-confirmation": {
      "gate": "pending",
      "checked_current_ids": [
        "old-a",
        "old-b"
      ],
      "first_blocker": "old-b",
      "continue_to_prune_loop": false,
      "later_prunes_checked": [],
      "current_prunes_started": [],
      "current_apply_started": [],
      "api_calls": 0
    },
    "already-confirmed": {
      "gate": "pass",
      "checked_current_ids": [],
      "first_blocker": null,
      "continue_to_prune_loop": true,
      "later_prunes_checked": [],
      "current_prunes_started": [],
      "current_apply_started": [],
      "api_calls": 0
    },
    "later-wave-only": {
      "gate": "pass",
      "checked_current_ids": [
        "old-a",
        "old-b"
      ],
      "first_blocker": null,
      "continue_to_prune_loop": true,
      "later_prunes_checked": [],
      "current_prunes_started": [],
      "current_apply_started": [],
      "api_calls": 0
    }
  },
  "recorded_at_utc": "2026-10-06T06:52:01.505855+00:00",
  "bindings": {
    "fixtures.json": "af7759404beb4471e0402e5e05aa17d3dbe9ff0c7815ba396edab9cfe02112f3",
    "hand-oracle.json": "15efe128f9f65e66c890244067c9c1a6f1aac8cec3eaaf2f02c5afab43f640e3",
    "observations/model-check.json": "d482f873902955e3bcbdcaedc5925e22f75589c3e13687d370e0a4a6d25c64d5"
  }
};if(typeof module!=="undefined"&&module.exports)module.exports=data;else root.ConfirmGateData=data;})(globalThis);
