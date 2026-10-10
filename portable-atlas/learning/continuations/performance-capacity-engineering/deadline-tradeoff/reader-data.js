(function(root){const data={
  "jobs": [
    {
      "id": "A",
      "service": 4,
      "deadline": 6
    },
    {
      "id": "B",
      "service": 2,
      "deadline": 3
    },
    {
      "id": "C",
      "service": 1,
      "deadline": 7
    }
  ],
  "orders": [
    "ABC",
    "ACB",
    "BAC",
    "BCA",
    "CAB",
    "CBA"
  ],
  "policies": {
    "fifo": "ABC",
    "shortest": "CBA",
    "deadline": "BAC"
  },
  "outcomes": {
    "ABC": {
      "order": "ABC",
      "slots": "AAAABBC",
      "start": [
        0,
        4,
        6
      ],
      "finish": [
        4,
        6,
        7
      ],
      "lateness": [
        -2,
        3,
        0
      ],
      "tardiness": [
        0,
        3,
        0
      ],
      "on_time": [
        true,
        false,
        true
      ],
      "missed": [
        "B"
      ],
      "equal_deadline": [
        "C"
      ],
      "sum_wait": 10,
      "mean_wait": "10/3",
      "mean_completion": "17/3",
      "max_tardiness": 3,
      "makespan": 7
    },
    "ACB": {
      "order": "ACB",
      "slots": "AAAACBB",
      "start": [
        0,
        5,
        4
      ],
      "finish": [
        4,
        7,
        5
      ],
      "lateness": [
        -2,
        4,
        -2
      ],
      "tardiness": [
        0,
        4,
        0
      ],
      "on_time": [
        true,
        false,
        true
      ],
      "missed": [
        "B"
      ],
      "equal_deadline": [],
      "sum_wait": 9,
      "mean_wait": "3",
      "mean_completion": "16/3",
      "max_tardiness": 4,
      "makespan": 7
    },
    "BAC": {
      "order": "BAC",
      "slots": "BBAAAAC",
      "start": [
        2,
        0,
        6
      ],
      "finish": [
        6,
        2,
        7
      ],
      "lateness": [
        0,
        -1,
        0
      ],
      "tardiness": [
        0,
        0,
        0
      ],
      "on_time": [
        true,
        true,
        true
      ],
      "missed": [],
      "equal_deadline": [
        "A",
        "C"
      ],
      "sum_wait": 8,
      "mean_wait": "8/3",
      "mean_completion": "5",
      "max_tardiness": 0,
      "makespan": 7
    },
    "BCA": {
      "order": "BCA",
      "slots": "BBCAAAA",
      "start": [
        3,
        0,
        2
      ],
      "finish": [
        7,
        2,
        3
      ],
      "lateness": [
        1,
        -1,
        -4
      ],
      "tardiness": [
        1,
        0,
        0
      ],
      "on_time": [
        false,
        true,
        true
      ],
      "missed": [
        "A"
      ],
      "equal_deadline": [],
      "sum_wait": 5,
      "mean_wait": "5/3",
      "mean_completion": "4",
      "max_tardiness": 1,
      "makespan": 7
    },
    "CAB": {
      "order": "CAB",
      "slots": "CAAAABB",
      "start": [
        1,
        5,
        0
      ],
      "finish": [
        5,
        7,
        1
      ],
      "lateness": [
        -1,
        4,
        -6
      ],
      "tardiness": [
        0,
        4,
        0
      ],
      "on_time": [
        true,
        false,
        true
      ],
      "missed": [
        "B"
      ],
      "equal_deadline": [],
      "sum_wait": 6,
      "mean_wait": "2",
      "mean_completion": "13/3",
      "max_tardiness": 4,
      "makespan": 7
    },
    "CBA": {
      "order": "CBA",
      "slots": "CBBAAAA",
      "start": [
        3,
        1,
        0
      ],
      "finish": [
        7,
        3,
        1
      ],
      "lateness": [
        1,
        0,
        -6
      ],
      "tardiness": [
        1,
        0,
        0
      ],
      "on_time": [
        false,
        true,
        true
      ],
      "missed": [
        "A"
      ],
      "equal_deadline": [
        "B"
      ],
      "sum_wait": 4,
      "mean_wait": "4/3",
      "mean_completion": "11/3",
      "max_tardiness": 1,
      "makespan": 7
    }
  },
  "frames": [
    {
      "order": "ABC",
      "tick": 0,
      "jobs": {
        "A": "実行中",
        "B": "待ち",
        "C": "待ち"
      }
    },
    {
      "order": "ABC",
      "tick": 1,
      "jobs": {
        "A": "実行中",
        "B": "待ち",
        "C": "待ち"
      }
    },
    {
      "order": "ABC",
      "tick": 2,
      "jobs": {
        "A": "実行中",
        "B": "待ち",
        "C": "待ち"
      }
    },
    {
      "order": "ABC",
      "tick": 3,
      "jobs": {
        "A": "実行中",
        "B": "待ち",
        "C": "待ち"
      }
    },
    {
      "order": "ABC",
      "tick": 4,
      "jobs": {
        "A": "完了",
        "B": "実行中",
        "C": "待ち"
      }
    },
    {
      "order": "ABC",
      "tick": 5,
      "jobs": {
        "A": "完了",
        "B": "実行中",
        "C": "待ち"
      }
    },
    {
      "order": "ABC",
      "tick": 6,
      "jobs": {
        "A": "完了",
        "B": "完了",
        "C": "実行中"
      }
    },
    {
      "order": "ABC",
      "tick": 7,
      "jobs": {
        "A": "完了",
        "B": "完了",
        "C": "完了"
      }
    },
    {
      "order": "ACB",
      "tick": 0,
      "jobs": {
        "A": "実行中",
        "B": "待ち",
        "C": "待ち"
      }
    },
    {
      "order": "ACB",
      "tick": 1,
      "jobs": {
        "A": "実行中",
        "B": "待ち",
        "C": "待ち"
      }
    },
    {
      "order": "ACB",
      "tick": 2,
      "jobs": {
        "A": "実行中",
        "B": "待ち",
        "C": "待ち"
      }
    },
    {
      "order": "ACB",
      "tick": 3,
      "jobs": {
        "A": "実行中",
        "B": "待ち",
        "C": "待ち"
      }
    },
    {
      "order": "ACB",
      "tick": 4,
      "jobs": {
        "A": "完了",
        "B": "待ち",
        "C": "実行中"
      }
    },
    {
      "order": "ACB",
      "tick": 5,
      "jobs": {
        "A": "完了",
        "B": "実行中",
        "C": "完了"
      }
    },
    {
      "order": "ACB",
      "tick": 6,
      "jobs": {
        "A": "完了",
        "B": "実行中",
        "C": "完了"
      }
    },
    {
      "order": "ACB",
      "tick": 7,
      "jobs": {
        "A": "完了",
        "B": "完了",
        "C": "完了"
      }
    },
    {
      "order": "BAC",
      "tick": 0,
      "jobs": {
        "A": "待ち",
        "B": "実行中",
        "C": "待ち"
      }
    },
    {
      "order": "BAC",
      "tick": 1,
      "jobs": {
        "A": "待ち",
        "B": "実行中",
        "C": "待ち"
      }
    },
    {
      "order": "BAC",
      "tick": 2,
      "jobs": {
        "A": "実行中",
        "B": "完了",
        "C": "待ち"
      }
    },
    {
      "order": "BAC",
      "tick": 3,
      "jobs": {
        "A": "実行中",
        "B": "完了",
        "C": "待ち"
      }
    },
    {
      "order": "BAC",
      "tick": 4,
      "jobs": {
        "A": "実行中",
        "B": "完了",
        "C": "待ち"
      }
    },
    {
      "order": "BAC",
      "tick": 5,
      "jobs": {
        "A": "実行中",
        "B": "完了",
        "C": "待ち"
      }
    },
    {
      "order": "BAC",
      "tick": 6,
      "jobs": {
        "A": "完了",
        "B": "完了",
        "C": "実行中"
      }
    },
    {
      "order": "BAC",
      "tick": 7,
      "jobs": {
        "A": "完了",
        "B": "完了",
        "C": "完了"
      }
    },
    {
      "order": "BCA",
      "tick": 0,
      "jobs": {
        "A": "待ち",
        "B": "実行中",
        "C": "待ち"
      }
    },
    {
      "order": "BCA",
      "tick": 1,
      "jobs": {
        "A": "待ち",
        "B": "実行中",
        "C": "待ち"
      }
    },
    {
      "order": "BCA",
      "tick": 2,
      "jobs": {
        "A": "待ち",
        "B": "完了",
        "C": "実行中"
      }
    },
    {
      "order": "BCA",
      "tick": 3,
      "jobs": {
        "A": "実行中",
        "B": "完了",
        "C": "完了"
      }
    },
    {
      "order": "BCA",
      "tick": 4,
      "jobs": {
        "A": "実行中",
        "B": "完了",
        "C": "完了"
      }
    },
    {
      "order": "BCA",
      "tick": 5,
      "jobs": {
        "A": "実行中",
        "B": "完了",
        "C": "完了"
      }
    },
    {
      "order": "BCA",
      "tick": 6,
      "jobs": {
        "A": "実行中",
        "B": "完了",
        "C": "完了"
      }
    },
    {
      "order": "BCA",
      "tick": 7,
      "jobs": {
        "A": "完了",
        "B": "完了",
        "C": "完了"
      }
    },
    {
      "order": "CAB",
      "tick": 0,
      "jobs": {
        "A": "待ち",
        "B": "待ち",
        "C": "実行中"
      }
    },
    {
      "order": "CAB",
      "tick": 1,
      "jobs": {
        "A": "実行中",
        "B": "待ち",
        "C": "完了"
      }
    },
    {
      "order": "CAB",
      "tick": 2,
      "jobs": {
        "A": "実行中",
        "B": "待ち",
        "C": "完了"
      }
    },
    {
      "order": "CAB",
      "tick": 3,
      "jobs": {
        "A": "実行中",
        "B": "待ち",
        "C": "完了"
      }
    },
    {
      "order": "CAB",
      "tick": 4,
      "jobs": {
        "A": "実行中",
        "B": "待ち",
        "C": "完了"
      }
    },
    {
      "order": "CAB",
      "tick": 5,
      "jobs": {
        "A": "完了",
        "B": "実行中",
        "C": "完了"
      }
    },
    {
      "order": "CAB",
      "tick": 6,
      "jobs": {
        "A": "完了",
        "B": "実行中",
        "C": "完了"
      }
    },
    {
      "order": "CAB",
      "tick": 7,
      "jobs": {
        "A": "完了",
        "B": "完了",
        "C": "完了"
      }
    },
    {
      "order": "CBA",
      "tick": 0,
      "jobs": {
        "A": "待ち",
        "B": "待ち",
        "C": "実行中"
      }
    },
    {
      "order": "CBA",
      "tick": 1,
      "jobs": {
        "A": "待ち",
        "B": "実行中",
        "C": "完了"
      }
    },
    {
      "order": "CBA",
      "tick": 2,
      "jobs": {
        "A": "待ち",
        "B": "実行中",
        "C": "完了"
      }
    },
    {
      "order": "CBA",
      "tick": 3,
      "jobs": {
        "A": "実行中",
        "B": "完了",
        "C": "完了"
      }
    },
    {
      "order": "CBA",
      "tick": 4,
      "jobs": {
        "A": "実行中",
        "B": "完了",
        "C": "完了"
      }
    },
    {
      "order": "CBA",
      "tick": 5,
      "jobs": {
        "A": "実行中",
        "B": "完了",
        "C": "完了"
      }
    },
    {
      "order": "CBA",
      "tick": 6,
      "jobs": {
        "A": "実行中",
        "B": "完了",
        "C": "完了"
      }
    },
    {
      "order": "CBA",
      "tick": 7,
      "jobs": {
        "A": "完了",
        "B": "完了",
        "C": "完了"
      }
    }
  ],
  "recorded_at_utc": "2026-10-06T07:42:21.498581+00:00",
  "bindings": {
    "fixtures.json": "7fc37a1ff4e596cbabce2fa47f524735af12a529cdc4688f3d7b0574d492865b",
    "hand-oracle.json": "28f30b98257e206f1361496349d69a7bf8a2fbffae6d05eb8537a1ed20e71668",
    "observations/model-check.json": "18450e116fa6cab63bd6929ffb62910bbafc1f5c25ca97ed49e4633da15173f9"
  }
};if(typeof module!=="undefined"&&module.exports)module.exports=data;else root.DeadlineData=data;})(globalThis);
