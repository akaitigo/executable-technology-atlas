window.ATLAS_DIMENSION_DATA = {
  "schema": 1,
  "run_id": "calculation-20261006T182407405374Z",
  "result_sha256": "0df21f4583bdd17f0c4947b76a4cf99452bb418ffdf2b8bc8048c00d1b128cad",
  "observed_at_utc": "2026-10-06T18:24:07.604493+00:00",
  "runtime": {
    "python": "3.9.6",
    "sqlite": "3.51.0",
    "system": "Darwin",
    "architecture": "arm64"
  },
  "fixture": {
    "schema": 1,
    "customers": [
      [
        10,
        "north"
      ],
      [
        20,
        "south"
      ]
    ],
    "orders": [
      [
        1,
        10,
        100
      ],
      [
        2,
        10,
        100
      ],
      [
        3,
        999,
        80
      ],
      [
        4,
        null,
        null
      ],
      [
        5,
        20,
        50
      ],
      [
        6,
        20,
        0
      ]
    ],
    "lines": [
      [
        101,
        1
      ],
      [
        102,
        1
      ],
      [
        201,
        2
      ],
      [
        301,
        3
      ],
      [
        401,
        4
      ],
      [
        601,
        6
      ]
    ],
    "policies": [
      "reject-batch",
      "quarantine-row",
      "retain"
    ],
    "null_customer_policy": "allow",
    "metric": "accepted orders with at least one line; sum known amounts; report missing denominator"
  },
  "policies": [
    {
      "policy": "reject-batch",
      "batch_status": "rejected",
      "accepted_ids": [],
      "quarantined_ids": [],
      "rejected_ids": [
        1,
        2,
        3,
        4,
        5,
        6
      ],
      "metric_ids": [],
      "accepted_but_no_line_ids": [],
      "sum_amount": null,
      "input_rows": 0,
      "known_rows": 0,
      "missing_rows": 0,
      "missing_fraction": null,
      "candidate_coverage": {
        "numerator": 0,
        "denominator": 5
      },
      "candidate_ids": [
        1,
        2,
        3,
        4,
        6
      ],
      "classification_rows": [
        [
          1,
          "known",
          2
        ],
        [
          2,
          "known",
          1
        ],
        [
          3,
          "unknown",
          1
        ],
        [
          4,
          "null_key",
          1
        ],
        [
          5,
          "known",
          0
        ],
        [
          6,
          "known",
          1
        ]
      ],
      "unknown_ids": [
        3
      ],
      "null_key_ids": [
        4
      ],
      "decisions": [
        [
          1,
          "rejected",
          0
        ],
        [
          2,
          "rejected",
          0
        ],
        [
          3,
          "rejected",
          0
        ],
        [
          4,
          "rejected",
          0
        ],
        [
          5,
          "rejected",
          0
        ],
        [
          6,
          "rejected",
          0
        ]
      ],
      "quarantine_records": [],
      "rejection_records": [
        [
          1,
          "batch_rejected_unknown_key"
        ],
        [
          2,
          "batch_rejected_unknown_key"
        ],
        [
          3,
          "batch_rejected_unknown_key"
        ],
        [
          4,
          "batch_rejected_unknown_key"
        ],
        [
          5,
          "batch_rejected_unknown_key"
        ],
        [
          6,
          "batch_rejected_unknown_key"
        ]
      ],
      "foreign_keys_readback": 1,
      "database": ":memory:",
      "source_id": "2025-06-12 13:14:41 f0ca7bba1c5e232e5d279fad6338121ab55af0c8c68c84cdfb18ba5114dcaapl",
      "publish_performed": false
    },
    {
      "policy": "quarantine-row",
      "batch_status": "accepted_with_quarantine",
      "accepted_ids": [
        1,
        2,
        4,
        5,
        6
      ],
      "quarantined_ids": [
        3
      ],
      "rejected_ids": [],
      "metric_ids": [
        1,
        2,
        4,
        6
      ],
      "accepted_but_no_line_ids": [
        5
      ],
      "sum_amount": 200,
      "input_rows": 4,
      "known_rows": 3,
      "missing_rows": 1,
      "missing_fraction": {
        "numerator": 1,
        "denominator": 4
      },
      "candidate_coverage": {
        "numerator": 4,
        "denominator": 5
      },
      "candidate_ids": [
        1,
        2,
        3,
        4,
        6
      ],
      "classification_rows": [
        [
          1,
          "known",
          2
        ],
        [
          2,
          "known",
          1
        ],
        [
          3,
          "unknown",
          1
        ],
        [
          4,
          "null_key",
          1
        ],
        [
          5,
          "known",
          0
        ],
        [
          6,
          "known",
          1
        ]
      ],
      "unknown_ids": [
        3
      ],
      "null_key_ids": [
        4
      ],
      "decisions": [
        [
          1,
          "accepted",
          1
        ],
        [
          2,
          "accepted",
          1
        ],
        [
          3,
          "quarantined",
          0
        ],
        [
          4,
          "accepted",
          1
        ],
        [
          5,
          "accepted",
          0
        ],
        [
          6,
          "accepted",
          1
        ]
      ],
      "quarantine_records": [
        [
          3,
          "unknown_customer_key"
        ]
      ],
      "rejection_records": [],
      "foreign_keys_readback": 1,
      "database": ":memory:",
      "source_id": "2025-06-12 13:14:41 f0ca7bba1c5e232e5d279fad6338121ab55af0c8c68c84cdfb18ba5114dcaapl",
      "publish_performed": false
    },
    {
      "policy": "retain",
      "batch_status": "accepted",
      "accepted_ids": [
        1,
        2,
        3,
        4,
        5,
        6
      ],
      "quarantined_ids": [],
      "rejected_ids": [],
      "metric_ids": [
        1,
        2,
        3,
        4,
        6
      ],
      "accepted_but_no_line_ids": [
        5
      ],
      "sum_amount": 280,
      "input_rows": 5,
      "known_rows": 4,
      "missing_rows": 1,
      "missing_fraction": {
        "numerator": 1,
        "denominator": 5
      },
      "candidate_coverage": {
        "numerator": 5,
        "denominator": 5
      },
      "candidate_ids": [
        1,
        2,
        3,
        4,
        6
      ],
      "classification_rows": [
        [
          1,
          "known",
          2
        ],
        [
          2,
          "known",
          1
        ],
        [
          3,
          "unknown",
          1
        ],
        [
          4,
          "null_key",
          1
        ],
        [
          5,
          "known",
          0
        ],
        [
          6,
          "known",
          1
        ]
      ],
      "unknown_ids": [
        3
      ],
      "null_key_ids": [
        4
      ],
      "decisions": [
        [
          1,
          "accepted",
          1
        ],
        [
          2,
          "accepted",
          1
        ],
        [
          3,
          "accepted",
          1
        ],
        [
          4,
          "accepted",
          1
        ],
        [
          5,
          "accepted",
          0
        ],
        [
          6,
          "accepted",
          1
        ]
      ],
      "quarantine_records": [],
      "rejection_records": [],
      "foreign_keys_readback": 1,
      "database": ":memory:",
      "source_id": "2025-06-12 13:14:41 f0ca7bba1c5e232e5d279fad6338121ab55af0c8c68c84cdfb18ba5114dcaapl",
      "publish_performed": false
    }
  ],
  "foreign_key_probes": [
    {
      "foreign_keys": 0,
      "pragma_in_transaction": false,
      "outcomes": [
        "inserted",
        "inserted",
        "inserted",
        "inserted",
        "inserted",
        "inserted"
      ],
      "ids_after_each": [
        [
          1
        ],
        [
          1,
          2
        ],
        [
          1,
          2,
          3
        ],
        [
          1,
          2,
          3,
          4
        ],
        [
          1,
          2,
          3,
          4,
          5
        ],
        [
          1,
          2,
          3,
          4,
          5,
          6
        ]
      ],
      "saved_ids": [
        1,
        2,
        3,
        4,
        5,
        6
      ],
      "violations": [
        [
          "fk_orders",
          3,
          "customers",
          0
        ]
      ],
      "quarantine_rows_created": 0,
      "events": [
        {
          "order_id": 1,
          "customer_id": 10,
          "outcome": "inserted",
          "error": null,
          "in_transaction_before": false,
          "saved_ids": [
            1
          ],
          "in_transaction_after": false
        },
        {
          "order_id": 2,
          "customer_id": 10,
          "outcome": "inserted",
          "error": null,
          "in_transaction_before": false,
          "saved_ids": [
            1,
            2
          ],
          "in_transaction_after": false
        },
        {
          "order_id": 3,
          "customer_id": 999,
          "outcome": "inserted",
          "error": null,
          "in_transaction_before": false,
          "saved_ids": [
            1,
            2,
            3
          ],
          "in_transaction_after": false
        },
        {
          "order_id": 4,
          "customer_id": null,
          "outcome": "inserted",
          "error": null,
          "in_transaction_before": false,
          "saved_ids": [
            1,
            2,
            3,
            4
          ],
          "in_transaction_after": false
        },
        {
          "order_id": 5,
          "customer_id": 20,
          "outcome": "inserted",
          "error": null,
          "in_transaction_before": false,
          "saved_ids": [
            1,
            2,
            3,
            4,
            5
          ],
          "in_transaction_after": false
        },
        {
          "order_id": 6,
          "customer_id": 20,
          "outcome": "inserted",
          "error": null,
          "in_transaction_before": false,
          "saved_ids": [
            1,
            2,
            3,
            4,
            5,
            6
          ],
          "in_transaction_after": false
        }
      ],
      "schema_sql": "CREATE TABLE customers(customer_id INTEGER PRIMARY KEY, region TEXT NOT NULL); CREATE TABLE fk_orders(order_id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(customer_id), amount INTEGER);",
      "rowid_order_id_pairs": [
        [
          1,
          1
        ],
        [
          2,
          2
        ],
        [
          3,
          3
        ],
        [
          4,
          4
        ],
        [
          5,
          5
        ],
        [
          6,
          6
        ]
      ],
      "database": ":memory:",
      "isolation_level": null,
      "source_id": "2025-06-12 13:14:41 f0ca7bba1c5e232e5d279fad6338121ab55af0c8c68c84cdfb18ba5114dcaapl"
    },
    {
      "foreign_keys": 1,
      "pragma_in_transaction": false,
      "outcomes": [
        "inserted",
        "inserted",
        "foreign_key_constraint",
        "inserted",
        "inserted",
        "inserted"
      ],
      "ids_after_each": [
        [
          1
        ],
        [
          1,
          2
        ],
        [
          1,
          2
        ],
        [
          1,
          2,
          4
        ],
        [
          1,
          2,
          4,
          5
        ],
        [
          1,
          2,
          4,
          5,
          6
        ]
      ],
      "saved_ids": [
        1,
        2,
        4,
        5,
        6
      ],
      "violations": [],
      "quarantine_rows_created": 0,
      "events": [
        {
          "order_id": 1,
          "customer_id": 10,
          "outcome": "inserted",
          "error": null,
          "in_transaction_before": false,
          "saved_ids": [
            1
          ],
          "in_transaction_after": false
        },
        {
          "order_id": 2,
          "customer_id": 10,
          "outcome": "inserted",
          "error": null,
          "in_transaction_before": false,
          "saved_ids": [
            1,
            2
          ],
          "in_transaction_after": false
        },
        {
          "order_id": 3,
          "customer_id": 999,
          "outcome": "foreign_key_constraint",
          "error": {
            "type": "IntegrityError",
            "message": "FOREIGN KEY constraint failed"
          },
          "in_transaction_before": false,
          "saved_ids": [
            1,
            2
          ],
          "in_transaction_after": false
        },
        {
          "order_id": 4,
          "customer_id": null,
          "outcome": "inserted",
          "error": null,
          "in_transaction_before": false,
          "saved_ids": [
            1,
            2,
            4
          ],
          "in_transaction_after": false
        },
        {
          "order_id": 5,
          "customer_id": 20,
          "outcome": "inserted",
          "error": null,
          "in_transaction_before": false,
          "saved_ids": [
            1,
            2,
            4,
            5
          ],
          "in_transaction_after": false
        },
        {
          "order_id": 6,
          "customer_id": 20,
          "outcome": "inserted",
          "error": null,
          "in_transaction_before": false,
          "saved_ids": [
            1,
            2,
            4,
            5,
            6
          ],
          "in_transaction_after": false
        }
      ],
      "schema_sql": "CREATE TABLE customers(customer_id INTEGER PRIMARY KEY, region TEXT NOT NULL); CREATE TABLE fk_orders(order_id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(customer_id), amount INTEGER);",
      "rowid_order_id_pairs": [
        [
          1,
          1
        ],
        [
          2,
          2
        ],
        [
          4,
          4
        ],
        [
          5,
          5
        ],
        [
          6,
          6
        ]
      ],
      "database": ":memory:",
      "isolation_level": null,
      "source_id": "2025-06-12 13:14:41 f0ca7bba1c5e232e5d279fad6338121ab55af0c8c68c84cdfb18ba5114dcaapl"
    }
  ],
  "cleanup": {
    "opened": 5,
    "closed": 5,
    "complete": true
  }
};
