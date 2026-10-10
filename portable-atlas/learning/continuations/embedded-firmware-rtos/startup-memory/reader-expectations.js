/* Atlas: fixed saved calculation, not a new execution. */
globalThis.AtlasStartupExpected = {
  "title": "Atlas startup memory saved calculation",
  "run_id": "calculation-20261006T214619487663Z",
  "result_sha256": "c5972ffa7864cecba8abd323b70133c88d4f69ab946272b041e9195a9af9559e",
  "result_path": "observations/calculation-20261006T214619487663Z/result.json",
  "fixture_sha256": "b1ef9b93b666981721ef569cbf561e4fa44e21f460b82b9b42d170347f30d3c3",
  "fixtures": {
    "schema": 1,
    "rom_base": 4096,
    "ram_base": 8192,
    "size": 16,
    "rom": [
      208,
      209,
      210,
      211,
      17,
      34,
      51,
      68,
      232,
      233,
      234,
      235,
      236,
      237,
      238,
      239
    ],
    "ram_initial": [
      165,
      165,
      165,
      165,
      165,
      165,
      204,
      165,
      165,
      165,
      165,
      165,
      204,
      165,
      165,
      165
    ],
    "data_source_offset": 4,
    "data_target_offset": 2,
    "bss_offset": 8,
    "guard_offsets": [
      6,
      12
    ],
    "cases": [
      {
        "id": "copy-zero-main",
        "operations": [
          "copy",
          "zero",
          "main"
        ],
        "data_length": 4,
        "bss_length": 4,
        "copy_one_past": false
      },
      {
        "id": "zero-copy-main",
        "operations": [
          "zero",
          "copy",
          "main"
        ],
        "data_length": 4,
        "bss_length": 4,
        "copy_one_past": false
      },
      {
        "id": "skip-copy",
        "operations": [
          "zero",
          "main"
        ],
        "data_length": 4,
        "bss_length": 4,
        "copy_one_past": false
      },
      {
        "id": "skip-zero",
        "operations": [
          "copy",
          "main"
        ],
        "data_length": 4,
        "bss_length": 4,
        "copy_one_past": false
      },
      {
        "id": "main-early",
        "operations": [
          "main",
          "copy",
          "zero"
        ],
        "data_length": 4,
        "bss_length": 4,
        "copy_one_past": false
      },
      {
        "id": "copy-one-past",
        "operations": [
          "copy",
          "zero",
          "main"
        ],
        "data_length": 4,
        "bss_length": 4,
        "copy_one_past": true
      },
      {
        "id": "empty-regions",
        "operations": [
          "copy",
          "zero",
          "main"
        ],
        "data_length": 0,
        "bss_length": 0,
        "copy_one_past": false
      }
    ]
  },
  "result": {
    "title": "Atlas startup memory saved calculation",
    "schema": 1,
    "status": "observed",
    "observed_at_utc": "2026-10-06T21:46:19.688255+00:00",
    "runtime": {
      "python": "3.9.6",
      "platform": "macOS-26.1-arm64-arm-64bit",
      "machine": "arm64"
    },
    "priority_observed": 10,
    "fixture_sha256": "b1ef9b93b666981721ef569cbf561e4fa44e21f460b82b9b42d170347f30d3c3",
    "cases": [
      {
        "id": "copy-zero-main",
        "classification": "NORMAL",
        "writes": [
          {
            "phase": "copy",
            "ram_offset": 2,
            "rom_offset": 4,
            "before": 165,
            "after": 17
          },
          {
            "phase": "copy",
            "ram_offset": 3,
            "rom_offset": 5,
            "before": 165,
            "after": 34
          },
          {
            "phase": "copy",
            "ram_offset": 4,
            "rom_offset": 6,
            "before": 165,
            "after": 51
          },
          {
            "phase": "copy",
            "ram_offset": 5,
            "rom_offset": 7,
            "before": 165,
            "after": 68
          },
          {
            "phase": "zero",
            "ram_offset": 8,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 9,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 10,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 11,
            "rom_offset": null,
            "before": 165,
            "after": 0
          }
        ],
        "snapshots": [
          {
            "phase": "initial",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": false,
            "zero_completed": false
          },
          {
            "phase": "copy",
            "ram": [
              165,
              165,
              17,
              34,
              51,
              68,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": false
          },
          {
            "phase": "zero",
            "ram": [
              165,
              165,
              17,
              34,
              51,
              68,
              204,
              165,
              0,
              0,
              0,
              0,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": true
          },
          {
            "phase": "main",
            "ram": [
              165,
              165,
              17,
              34,
              51,
              68,
              204,
              165,
              0,
              0,
              0,
              0,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": true
          }
        ],
        "main": {
          "data": [
            17,
            34,
            51,
            68
          ],
          "bss": [
            0,
            0,
            0,
            0
          ],
          "copy_completed": true,
          "zero_completed": true,
          "guards_intact": true,
          "values_expected": true,
          "initialized": true
        },
        "final_ram": [
          165,
          165,
          17,
          34,
          51,
          68,
          204,
          165,
          0,
          0,
          0,
          0,
          204,
          165,
          165,
          165
        ],
        "final_rom": [
          208,
          209,
          210,
          211,
          17,
          34,
          51,
          68,
          232,
          233,
          234,
          235,
          236,
          237,
          238,
          239
        ],
        "rom_unchanged": true,
        "guards_intact": true,
        "write_ranges_valid": true,
        "write_count": 8
      },
      {
        "id": "zero-copy-main",
        "classification": "NORMAL",
        "writes": [
          {
            "phase": "zero",
            "ram_offset": 8,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 9,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 10,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 11,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "copy",
            "ram_offset": 2,
            "rom_offset": 4,
            "before": 165,
            "after": 17
          },
          {
            "phase": "copy",
            "ram_offset": 3,
            "rom_offset": 5,
            "before": 165,
            "after": 34
          },
          {
            "phase": "copy",
            "ram_offset": 4,
            "rom_offset": 6,
            "before": 165,
            "after": 51
          },
          {
            "phase": "copy",
            "ram_offset": 5,
            "rom_offset": 7,
            "before": 165,
            "after": 68
          }
        ],
        "snapshots": [
          {
            "phase": "initial",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": false,
            "zero_completed": false
          },
          {
            "phase": "zero",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              0,
              0,
              0,
              0,
              204,
              165,
              165,
              165
            ],
            "copy_completed": false,
            "zero_completed": true
          },
          {
            "phase": "copy",
            "ram": [
              165,
              165,
              17,
              34,
              51,
              68,
              204,
              165,
              0,
              0,
              0,
              0,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": true
          },
          {
            "phase": "main",
            "ram": [
              165,
              165,
              17,
              34,
              51,
              68,
              204,
              165,
              0,
              0,
              0,
              0,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": true
          }
        ],
        "main": {
          "data": [
            17,
            34,
            51,
            68
          ],
          "bss": [
            0,
            0,
            0,
            0
          ],
          "copy_completed": true,
          "zero_completed": true,
          "guards_intact": true,
          "values_expected": true,
          "initialized": true
        },
        "final_ram": [
          165,
          165,
          17,
          34,
          51,
          68,
          204,
          165,
          0,
          0,
          0,
          0,
          204,
          165,
          165,
          165
        ],
        "final_rom": [
          208,
          209,
          210,
          211,
          17,
          34,
          51,
          68,
          232,
          233,
          234,
          235,
          236,
          237,
          238,
          239
        ],
        "rom_unchanged": true,
        "guards_intact": true,
        "write_ranges_valid": true,
        "write_count": 8
      },
      {
        "id": "skip-copy",
        "classification": "INTENTIONAL_FAULT",
        "writes": [
          {
            "phase": "zero",
            "ram_offset": 8,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 9,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 10,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 11,
            "rom_offset": null,
            "before": 165,
            "after": 0
          }
        ],
        "snapshots": [
          {
            "phase": "initial",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": false,
            "zero_completed": false
          },
          {
            "phase": "zero",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              0,
              0,
              0,
              0,
              204,
              165,
              165,
              165
            ],
            "copy_completed": false,
            "zero_completed": true
          },
          {
            "phase": "main",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              0,
              0,
              0,
              0,
              204,
              165,
              165,
              165
            ],
            "copy_completed": false,
            "zero_completed": true
          }
        ],
        "main": {
          "data": [
            165,
            165,
            165,
            165
          ],
          "bss": [
            0,
            0,
            0,
            0
          ],
          "copy_completed": false,
          "zero_completed": true,
          "guards_intact": true,
          "values_expected": false,
          "initialized": false
        },
        "final_ram": [
          165,
          165,
          165,
          165,
          165,
          165,
          204,
          165,
          0,
          0,
          0,
          0,
          204,
          165,
          165,
          165
        ],
        "final_rom": [
          208,
          209,
          210,
          211,
          17,
          34,
          51,
          68,
          232,
          233,
          234,
          235,
          236,
          237,
          238,
          239
        ],
        "rom_unchanged": true,
        "guards_intact": true,
        "write_ranges_valid": true,
        "write_count": 4
      },
      {
        "id": "skip-zero",
        "classification": "INTENTIONAL_FAULT",
        "writes": [
          {
            "phase": "copy",
            "ram_offset": 2,
            "rom_offset": 4,
            "before": 165,
            "after": 17
          },
          {
            "phase": "copy",
            "ram_offset": 3,
            "rom_offset": 5,
            "before": 165,
            "after": 34
          },
          {
            "phase": "copy",
            "ram_offset": 4,
            "rom_offset": 6,
            "before": 165,
            "after": 51
          },
          {
            "phase": "copy",
            "ram_offset": 5,
            "rom_offset": 7,
            "before": 165,
            "after": 68
          }
        ],
        "snapshots": [
          {
            "phase": "initial",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": false,
            "zero_completed": false
          },
          {
            "phase": "copy",
            "ram": [
              165,
              165,
              17,
              34,
              51,
              68,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": false
          },
          {
            "phase": "main",
            "ram": [
              165,
              165,
              17,
              34,
              51,
              68,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": false
          }
        ],
        "main": {
          "data": [
            17,
            34,
            51,
            68
          ],
          "bss": [
            165,
            165,
            165,
            165
          ],
          "copy_completed": true,
          "zero_completed": false,
          "guards_intact": true,
          "values_expected": false,
          "initialized": false
        },
        "final_ram": [
          165,
          165,
          17,
          34,
          51,
          68,
          204,
          165,
          165,
          165,
          165,
          165,
          204,
          165,
          165,
          165
        ],
        "final_rom": [
          208,
          209,
          210,
          211,
          17,
          34,
          51,
          68,
          232,
          233,
          234,
          235,
          236,
          237,
          238,
          239
        ],
        "rom_unchanged": true,
        "guards_intact": true,
        "write_ranges_valid": true,
        "write_count": 4
      },
      {
        "id": "main-early",
        "classification": "INTENTIONAL_FAULT",
        "writes": [
          {
            "phase": "copy",
            "ram_offset": 2,
            "rom_offset": 4,
            "before": 165,
            "after": 17
          },
          {
            "phase": "copy",
            "ram_offset": 3,
            "rom_offset": 5,
            "before": 165,
            "after": 34
          },
          {
            "phase": "copy",
            "ram_offset": 4,
            "rom_offset": 6,
            "before": 165,
            "after": 51
          },
          {
            "phase": "copy",
            "ram_offset": 5,
            "rom_offset": 7,
            "before": 165,
            "after": 68
          },
          {
            "phase": "zero",
            "ram_offset": 8,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 9,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 10,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 11,
            "rom_offset": null,
            "before": 165,
            "after": 0
          }
        ],
        "snapshots": [
          {
            "phase": "initial",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": false,
            "zero_completed": false
          },
          {
            "phase": "main",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": false,
            "zero_completed": false
          },
          {
            "phase": "copy",
            "ram": [
              165,
              165,
              17,
              34,
              51,
              68,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": false
          },
          {
            "phase": "zero",
            "ram": [
              165,
              165,
              17,
              34,
              51,
              68,
              204,
              165,
              0,
              0,
              0,
              0,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": true
          }
        ],
        "main": {
          "data": [
            165,
            165,
            165,
            165
          ],
          "bss": [
            165,
            165,
            165,
            165
          ],
          "copy_completed": false,
          "zero_completed": false,
          "guards_intact": true,
          "values_expected": false,
          "initialized": false
        },
        "final_ram": [
          165,
          165,
          17,
          34,
          51,
          68,
          204,
          165,
          0,
          0,
          0,
          0,
          204,
          165,
          165,
          165
        ],
        "final_rom": [
          208,
          209,
          210,
          211,
          17,
          34,
          51,
          68,
          232,
          233,
          234,
          235,
          236,
          237,
          238,
          239
        ],
        "rom_unchanged": true,
        "guards_intact": true,
        "write_ranges_valid": true,
        "write_count": 8
      },
      {
        "id": "copy-one-past",
        "classification": "INTENTIONAL_FAULT",
        "writes": [
          {
            "phase": "copy",
            "ram_offset": 2,
            "rom_offset": 4,
            "before": 165,
            "after": 17
          },
          {
            "phase": "copy",
            "ram_offset": 3,
            "rom_offset": 5,
            "before": 165,
            "after": 34
          },
          {
            "phase": "copy",
            "ram_offset": 4,
            "rom_offset": 6,
            "before": 165,
            "after": 51
          },
          {
            "phase": "copy",
            "ram_offset": 5,
            "rom_offset": 7,
            "before": 165,
            "after": 68
          },
          {
            "phase": "copy",
            "ram_offset": 6,
            "rom_offset": 8,
            "before": 204,
            "after": 232
          },
          {
            "phase": "zero",
            "ram_offset": 8,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 9,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 10,
            "rom_offset": null,
            "before": 165,
            "after": 0
          },
          {
            "phase": "zero",
            "ram_offset": 11,
            "rom_offset": null,
            "before": 165,
            "after": 0
          }
        ],
        "snapshots": [
          {
            "phase": "initial",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": false,
            "zero_completed": false
          },
          {
            "phase": "copy",
            "ram": [
              165,
              165,
              17,
              34,
              51,
              68,
              232,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": false
          },
          {
            "phase": "zero",
            "ram": [
              165,
              165,
              17,
              34,
              51,
              68,
              232,
              165,
              0,
              0,
              0,
              0,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": true
          },
          {
            "phase": "main",
            "ram": [
              165,
              165,
              17,
              34,
              51,
              68,
              232,
              165,
              0,
              0,
              0,
              0,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": true
          }
        ],
        "main": {
          "data": [
            17,
            34,
            51,
            68
          ],
          "bss": [
            0,
            0,
            0,
            0
          ],
          "copy_completed": true,
          "zero_completed": true,
          "guards_intact": false,
          "values_expected": true,
          "initialized": false
        },
        "final_ram": [
          165,
          165,
          17,
          34,
          51,
          68,
          232,
          165,
          0,
          0,
          0,
          0,
          204,
          165,
          165,
          165
        ],
        "final_rom": [
          208,
          209,
          210,
          211,
          17,
          34,
          51,
          68,
          232,
          233,
          234,
          235,
          236,
          237,
          238,
          239
        ],
        "rom_unchanged": true,
        "guards_intact": false,
        "write_ranges_valid": false,
        "write_count": 9
      },
      {
        "id": "empty-regions",
        "classification": "NORMAL",
        "writes": [],
        "snapshots": [
          {
            "phase": "initial",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": false,
            "zero_completed": false
          },
          {
            "phase": "copy",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": false
          },
          {
            "phase": "zero",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": true
          },
          {
            "phase": "main",
            "ram": [
              165,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165,
              165,
              165,
              204,
              165,
              165,
              165
            ],
            "copy_completed": true,
            "zero_completed": true
          }
        ],
        "main": {
          "data": [],
          "bss": [],
          "copy_completed": true,
          "zero_completed": true,
          "guards_intact": true,
          "values_expected": true,
          "initialized": true
        },
        "final_ram": [
          165,
          165,
          165,
          165,
          165,
          165,
          204,
          165,
          165,
          165,
          165,
          165,
          204,
          165,
          165,
          165
        ],
        "final_rom": [
          208,
          209,
          210,
          211,
          17,
          34,
          51,
          68,
          232,
          233,
          234,
          235,
          236,
          237,
          238,
          239
        ],
        "rom_unchanged": true,
        "guards_intact": true,
        "write_ranges_valid": true,
        "write_count": 0
      }
    ],
    "input_refusals": [
      {
        "id": "size-bool",
        "status": "INPUT_REFUSED",
        "reason": "INTEGER_REQUIRED",
        "write_count": 0,
        "main": null
      },
      {
        "id": "rom-short",
        "status": "INPUT_REFUSED",
        "reason": "MEMORY_BYTES",
        "write_count": 0,
        "main": null
      },
      {
        "id": "byte-bool",
        "status": "INPUT_REFUSED",
        "reason": "MEMORY_BYTES",
        "write_count": 0,
        "main": null
      },
      {
        "id": "byte-over",
        "status": "INPUT_REFUSED",
        "reason": "MEMORY_BYTES",
        "write_count": 0,
        "main": null
      },
      {
        "id": "rom-changed",
        "status": "INPUT_REFUSED",
        "reason": "FIXED_MEMORY",
        "write_count": 0,
        "main": null
      },
      {
        "id": "ram-changed",
        "status": "INPUT_REFUSED",
        "reason": "FIXED_MEMORY",
        "write_count": 0,
        "main": null
      },
      {
        "id": "missing-field",
        "status": "INPUT_REFUSED",
        "reason": "SCHEMA",
        "write_count": 0,
        "main": null
      },
      {
        "id": "extra-field",
        "status": "INPUT_REFUSED",
        "reason": "SCHEMA",
        "write_count": 0,
        "main": null
      },
      {
        "id": "negative-source",
        "status": "INPUT_REFUSED",
        "reason": "MAP_RANGE",
        "write_count": 0,
        "main": null
      },
      {
        "id": "overlap",
        "status": "INPUT_REFUSED",
        "reason": "OVERLAP",
        "write_count": 0,
        "main": null
      },
      {
        "id": "guard-overlap",
        "status": "INPUT_REFUSED",
        "reason": "GUARD_RANGE",
        "write_count": 0,
        "main": null
      },
      {
        "id": "bss-over",
        "status": "INPUT_REFUSED",
        "reason": "MAP_RANGE",
        "write_count": 0,
        "main": null
      },
      {
        "id": "negative-length",
        "status": "INPUT_REFUSED",
        "reason": "MAP_RANGE",
        "write_count": 0,
        "main": null
      },
      {
        "id": "float-length",
        "status": "INPUT_REFUSED",
        "reason": "INTEGER_REQUIRED",
        "write_count": 0,
        "main": null
      },
      {
        "id": "unknown-operation",
        "status": "INPUT_REFUSED",
        "reason": "CASE_SCHEMA",
        "write_count": 0,
        "main": null
      },
      {
        "id": "unapproved-overrun",
        "status": "INPUT_REFUSED",
        "reason": "CASE_SCHEMA",
        "write_count": 0,
        "main": null
      },
      {
        "id": "unknown-case",
        "status": "INPUT_REFUSED",
        "reason": "UNKNOWN_CASE",
        "write_count": 0,
        "main": null
      }
    ],
    "scope": {
      "model_only": true,
      "linker_runs": 0,
      "compiler_runs": 0,
      "device_access": 0,
      "cpu_instruction_execution": 0,
      "browser_executed": false,
      "server_started": false
    }
  }
};
