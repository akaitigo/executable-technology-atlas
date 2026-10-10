window.AtlasQuantumExpectations={
  "fixture_sha256": "0e67d4e816a27c0248caec1d927e71d6b6f2fbe323278a815088fa4897380cad",
  "runtime": {
    "python": "3.9.6",
    "system": "Darwin",
    "architecture": "arm64",
    "arithmetic": "stdlib Fraction complex pairs"
  },
  "cases": [
    {
      "case_id": "plus@0",
      "state_id": "plus",
      "p": "0",
      "equivalent_phase_flip_q": "0",
      "before": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ],
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "1/2",
        "rho01": [
          "1/2",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_e": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ],
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "1/2",
        "rho01": [
          "1/2",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_h": {
        "density": [
          [
            [
              "1",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1",
          "0"
        ]
      },
      "branches": [
        {
          "branch": "unchanged",
          "weight": "1",
          "reachable": true,
          "conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ],
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ],
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-0",
          "weight": "0",
          "reachable": false,
          "conditional": null,
          "after_h_conditional": null,
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-1",
          "weight": "0",
          "reachable": false,
          "conditional": null,
          "after_h_conditional": null,
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        }
      ],
      "branch_sum": [
        [
          [
            "1/2",
            "0"
          ],
          [
            "1/2",
            "0"
          ]
        ],
        [
          [
            "1/2",
            "0"
          ],
          [
            "1/2",
            "0"
          ]
        ]
      ],
      "branch_sum_after_h": [
        [
          [
            "1",
            "0"
          ],
          [
            "0",
            "0"
          ]
        ],
        [
          [
            "0",
            "0"
          ],
          [
            "0",
            "0"
          ]
        ]
      ],
      "branch_weights_sum": "1",
      "paths_equal": true,
      "shots": 0,
      "quantum_hardware_used": false
    },
    {
      "case_id": "plus@1/2",
      "state_id": "plus",
      "p": "1/2",
      "equivalent_phase_flip_q": "1/4",
      "before": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ],
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "1/2",
        "rho01": [
          "1/2",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_e": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/4",
              "0"
            ]
          ],
          [
            [
              "1/4",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "3/16",
        "eigenvalues": [
          "1/4",
          "3/4"
        ],
        "coherence_z": "1/4",
        "rho01": [
          "1/4",
          "0"
        ],
        "purity": "5/8",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_h": {
        "density": [
          [
            [
              "3/4",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "1/4",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "3/16",
        "eigenvalues": [
          "1/4",
          "3/4"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "5/8",
        "probabilities_z": [
          "3/4",
          "1/4"
        ]
      },
      "branches": [
        {
          "branch": "unchanged",
          "weight": "1/2",
          "reachable": true,
          "conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ],
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "1/4",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ],
            [
              [
                "1/4",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-0",
          "weight": "1/4",
          "reachable": true,
          "conditional": [
            [
              [
                "1",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ],
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "1/4",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/8",
                "0"
              ],
              [
                "1/8",
                "0"
              ]
            ],
            [
              [
                "1/8",
                "0"
              ],
              [
                "1/8",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-1",
          "weight": "1/4",
          "reachable": true,
          "conditional": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "1",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "-1/2",
                "0"
              ]
            ],
            [
              [
                "-1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/8",
                "0"
              ],
              [
                "-1/8",
                "0"
              ]
            ],
            [
              [
                "-1/8",
                "0"
              ],
              [
                "1/8",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        }
      ],
      "branch_sum": [
        [
          [
            "1/2",
            "0"
          ],
          [
            "1/4",
            "0"
          ]
        ],
        [
          [
            "1/4",
            "0"
          ],
          [
            "1/2",
            "0"
          ]
        ]
      ],
      "branch_sum_after_h": [
        [
          [
            "3/4",
            "0"
          ],
          [
            "0",
            "0"
          ]
        ],
        [
          [
            "0",
            "0"
          ],
          [
            "1/4",
            "0"
          ]
        ]
      ],
      "branch_weights_sum": "1",
      "paths_equal": true,
      "shots": 0,
      "quantum_hardware_used": false
    },
    {
      "case_id": "plus@1",
      "state_id": "plus",
      "p": "1",
      "equivalent_phase_flip_q": "1/2",
      "before": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ],
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "1/2",
        "rho01": [
          "1/2",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_e": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "1/4",
        "eigenvalues": [
          "1/2",
          "1/2"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1/2",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_h": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "1/4",
        "eigenvalues": [
          "1/2",
          "1/2"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1/2",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "branches": [
        {
          "branch": "unchanged",
          "weight": "0",
          "reachable": false,
          "conditional": null,
          "after_h_conditional": null,
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-0",
          "weight": "1/2",
          "reachable": true,
          "conditional": [
            [
              [
                "1",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ],
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/4",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ],
            [
              [
                "1/4",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-1",
          "weight": "1/2",
          "reachable": true,
          "conditional": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "1",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "-1/2",
                "0"
              ]
            ],
            [
              [
                "-1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/4",
                "0"
              ],
              [
                "-1/4",
                "0"
              ]
            ],
            [
              [
                "-1/4",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        }
      ],
      "branch_sum": [
        [
          [
            "1/2",
            "0"
          ],
          [
            "0",
            "0"
          ]
        ],
        [
          [
            "0",
            "0"
          ],
          [
            "1/2",
            "0"
          ]
        ]
      ],
      "branch_sum_after_h": [
        [
          [
            "1/2",
            "0"
          ],
          [
            "0",
            "0"
          ]
        ],
        [
          [
            "0",
            "0"
          ],
          [
            "1/2",
            "0"
          ]
        ]
      ],
      "branch_weights_sum": "1",
      "paths_equal": true,
      "shots": 0,
      "quantum_hardware_used": false
    },
    {
      "case_id": "phase-i@0",
      "state_id": "phase-i",
      "p": "0",
      "equivalent_phase_flip_q": "0",
      "before": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "0",
              "-1/2"
            ]
          ],
          [
            [
              "0",
              "1/2"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "1/2",
        "rho01": [
          "0",
          "-1/2"
        ],
        "purity": "1",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_e": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "0",
              "-1/2"
            ]
          ],
          [
            [
              "0",
              "1/2"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "1/2",
        "rho01": [
          "0",
          "-1/2"
        ],
        "purity": "1",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_h": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "0",
              "1/2"
            ]
          ],
          [
            [
              "0",
              "-1/2"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "1/2",
        "rho01": [
          "0",
          "1/2"
        ],
        "purity": "1",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "branches": [
        {
          "branch": "unchanged",
          "weight": "1",
          "reachable": true,
          "conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "0",
                "-1/2"
              ]
            ],
            [
              [
                "0",
                "1/2"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "0",
                "1/2"
              ]
            ],
            [
              [
                "0",
                "-1/2"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "0",
                "-1/2"
              ]
            ],
            [
              [
                "0",
                "1/2"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "0",
                "1/2"
              ]
            ],
            [
              [
                "0",
                "-1/2"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-0",
          "weight": "0",
          "reachable": false,
          "conditional": null,
          "after_h_conditional": null,
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-1",
          "weight": "0",
          "reachable": false,
          "conditional": null,
          "after_h_conditional": null,
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        }
      ],
      "branch_sum": [
        [
          [
            "1/2",
            "0"
          ],
          [
            "0",
            "-1/2"
          ]
        ],
        [
          [
            "0",
            "1/2"
          ],
          [
            "1/2",
            "0"
          ]
        ]
      ],
      "branch_sum_after_h": [
        [
          [
            "1/2",
            "0"
          ],
          [
            "0",
            "1/2"
          ]
        ],
        [
          [
            "0",
            "-1/2"
          ],
          [
            "1/2",
            "0"
          ]
        ]
      ],
      "branch_weights_sum": "1",
      "paths_equal": true,
      "shots": 0,
      "quantum_hardware_used": false
    },
    {
      "case_id": "phase-i@1/2",
      "state_id": "phase-i",
      "p": "1/2",
      "equivalent_phase_flip_q": "1/4",
      "before": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "0",
              "-1/2"
            ]
          ],
          [
            [
              "0",
              "1/2"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "1/2",
        "rho01": [
          "0",
          "-1/2"
        ],
        "purity": "1",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_e": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "0",
              "-1/4"
            ]
          ],
          [
            [
              "0",
              "1/4"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "3/16",
        "eigenvalues": [
          "1/4",
          "3/4"
        ],
        "coherence_z": "1/4",
        "rho01": [
          "0",
          "-1/4"
        ],
        "purity": "5/8",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_h": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "0",
              "1/4"
            ]
          ],
          [
            [
              "0",
              "-1/4"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "3/16",
        "eigenvalues": [
          "1/4",
          "3/4"
        ],
        "coherence_z": "1/4",
        "rho01": [
          "0",
          "1/4"
        ],
        "purity": "5/8",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "branches": [
        {
          "branch": "unchanged",
          "weight": "1/2",
          "reachable": true,
          "conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "0",
                "-1/2"
              ]
            ],
            [
              [
                "0",
                "1/2"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "0",
                "1/2"
              ]
            ],
            [
              [
                "0",
                "-1/2"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "1/4",
                "0"
              ],
              [
                "0",
                "-1/4"
              ]
            ],
            [
              [
                "0",
                "1/4"
              ],
              [
                "1/4",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/4",
                "0"
              ],
              [
                "0",
                "1/4"
              ]
            ],
            [
              [
                "0",
                "-1/4"
              ],
              [
                "1/4",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-0",
          "weight": "1/4",
          "reachable": true,
          "conditional": [
            [
              [
                "1",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ],
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "1/4",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/8",
                "0"
              ],
              [
                "1/8",
                "0"
              ]
            ],
            [
              [
                "1/8",
                "0"
              ],
              [
                "1/8",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-1",
          "weight": "1/4",
          "reachable": true,
          "conditional": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "1",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "-1/2",
                "0"
              ]
            ],
            [
              [
                "-1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/8",
                "0"
              ],
              [
                "-1/8",
                "0"
              ]
            ],
            [
              [
                "-1/8",
                "0"
              ],
              [
                "1/8",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        }
      ],
      "branch_sum": [
        [
          [
            "1/2",
            "0"
          ],
          [
            "0",
            "-1/4"
          ]
        ],
        [
          [
            "0",
            "1/4"
          ],
          [
            "1/2",
            "0"
          ]
        ]
      ],
      "branch_sum_after_h": [
        [
          [
            "1/2",
            "0"
          ],
          [
            "0",
            "1/4"
          ]
        ],
        [
          [
            "0",
            "-1/4"
          ],
          [
            "1/2",
            "0"
          ]
        ]
      ],
      "branch_weights_sum": "1",
      "paths_equal": true,
      "shots": 0,
      "quantum_hardware_used": false
    },
    {
      "case_id": "phase-i@1",
      "state_id": "phase-i",
      "p": "1",
      "equivalent_phase_flip_q": "1/2",
      "before": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "0",
              "-1/2"
            ]
          ],
          [
            [
              "0",
              "1/2"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "1/2",
        "rho01": [
          "0",
          "-1/2"
        ],
        "purity": "1",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_e": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "1/4",
        "eigenvalues": [
          "1/2",
          "1/2"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1/2",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_h": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "1/4",
        "eigenvalues": [
          "1/2",
          "1/2"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1/2",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "branches": [
        {
          "branch": "unchanged",
          "weight": "0",
          "reachable": false,
          "conditional": null,
          "after_h_conditional": null,
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-0",
          "weight": "1/2",
          "reachable": true,
          "conditional": [
            [
              [
                "1",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ],
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/4",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ],
            [
              [
                "1/4",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-1",
          "weight": "1/2",
          "reachable": true,
          "conditional": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "1",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "-1/2",
                "0"
              ]
            ],
            [
              [
                "-1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/4",
                "0"
              ],
              [
                "-1/4",
                "0"
              ]
            ],
            [
              [
                "-1/4",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        }
      ],
      "branch_sum": [
        [
          [
            "1/2",
            "0"
          ],
          [
            "0",
            "0"
          ]
        ],
        [
          [
            "0",
            "0"
          ],
          [
            "1/2",
            "0"
          ]
        ]
      ],
      "branch_sum_after_h": [
        [
          [
            "1/2",
            "0"
          ],
          [
            "0",
            "0"
          ]
        ],
        [
          [
            "0",
            "0"
          ],
          [
            "1/2",
            "0"
          ]
        ]
      ],
      "branch_weights_sum": "1",
      "paths_equal": true,
      "shots": 0,
      "quantum_hardware_used": false
    },
    {
      "case_id": "zero@0",
      "state_id": "zero",
      "p": "0",
      "equivalent_phase_flip_q": "0",
      "before": {
        "density": [
          [
            [
              "1",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1",
          "0"
        ]
      },
      "after_e": {
        "density": [
          [
            [
              "1",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1",
          "0"
        ]
      },
      "after_h": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ],
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "1/2",
        "rho01": [
          "1/2",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "branches": [
        {
          "branch": "unchanged",
          "weight": "1",
          "reachable": true,
          "conditional": [
            [
              [
                "1",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ],
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "1",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ],
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-0",
          "weight": "0",
          "reachable": false,
          "conditional": null,
          "after_h_conditional": null,
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-1",
          "weight": "0",
          "reachable": false,
          "conditional": null,
          "after_h_conditional": null,
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        }
      ],
      "branch_sum": [
        [
          [
            "1",
            "0"
          ],
          [
            "0",
            "0"
          ]
        ],
        [
          [
            "0",
            "0"
          ],
          [
            "0",
            "0"
          ]
        ]
      ],
      "branch_sum_after_h": [
        [
          [
            "1/2",
            "0"
          ],
          [
            "1/2",
            "0"
          ]
        ],
        [
          [
            "1/2",
            "0"
          ],
          [
            "1/2",
            "0"
          ]
        ]
      ],
      "branch_weights_sum": "1",
      "paths_equal": true,
      "shots": 0,
      "quantum_hardware_used": false
    },
    {
      "case_id": "zero@1/2",
      "state_id": "zero",
      "p": "1/2",
      "equivalent_phase_flip_q": "1/4",
      "before": {
        "density": [
          [
            [
              "1",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1",
          "0"
        ]
      },
      "after_e": {
        "density": [
          [
            [
              "1",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1",
          "0"
        ]
      },
      "after_h": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ],
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "1/2",
        "rho01": [
          "1/2",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "branches": [
        {
          "branch": "unchanged",
          "weight": "1/2",
          "reachable": true,
          "conditional": [
            [
              [
                "1",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ],
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/4",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ],
            [
              [
                "1/4",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-0",
          "weight": "1/2",
          "reachable": true,
          "conditional": [
            [
              [
                "1",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ],
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/4",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ],
            [
              [
                "1/4",
                "0"
              ],
              [
                "1/4",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-1",
          "weight": "0",
          "reachable": false,
          "conditional": null,
          "after_h_conditional": null,
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        }
      ],
      "branch_sum": [
        [
          [
            "1",
            "0"
          ],
          [
            "0",
            "0"
          ]
        ],
        [
          [
            "0",
            "0"
          ],
          [
            "0",
            "0"
          ]
        ]
      ],
      "branch_sum_after_h": [
        [
          [
            "1/2",
            "0"
          ],
          [
            "1/2",
            "0"
          ]
        ],
        [
          [
            "1/2",
            "0"
          ],
          [
            "1/2",
            "0"
          ]
        ]
      ],
      "branch_weights_sum": "1",
      "paths_equal": true,
      "shots": 0,
      "quantum_hardware_used": false
    },
    {
      "case_id": "zero@1",
      "state_id": "zero",
      "p": "1",
      "equivalent_phase_flip_q": "1/2",
      "before": {
        "density": [
          [
            [
              "1",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1",
          "0"
        ]
      },
      "after_e": {
        "density": [
          [
            [
              "1",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1",
          "0"
        ]
      },
      "after_h": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ],
          [
            [
              "1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "1/2",
        "rho01": [
          "1/2",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "branches": [
        {
          "branch": "unchanged",
          "weight": "0",
          "reachable": false,
          "conditional": null,
          "after_h_conditional": null,
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-0",
          "weight": "1",
          "reachable": true,
          "conditional": [
            [
              [
                "1",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_conditional": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ],
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "contribution": [
            [
              [
                "1",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ],
            [
              [
                "1/2",
                "0"
              ],
              [
                "1/2",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        },
        {
          "branch": "Z-result-1",
          "weight": "0",
          "reachable": false,
          "conditional": null,
          "after_h_conditional": null,
          "contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "after_h_contribution": [
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ],
            [
              [
                "0",
                "0"
              ],
              [
                "0",
                "0"
              ]
            ]
          ],
          "observed_measurement_record": false
        }
      ],
      "branch_sum": [
        [
          [
            "1",
            "0"
          ],
          [
            "0",
            "0"
          ]
        ],
        [
          [
            "0",
            "0"
          ],
          [
            "0",
            "0"
          ]
        ]
      ],
      "branch_sum_after_h": [
        [
          [
            "1/2",
            "0"
          ],
          [
            "1/2",
            "0"
          ]
        ],
        [
          [
            "1/2",
            "0"
          ],
          [
            "1/2",
            "0"
          ]
        ]
      ],
      "branch_weights_sum": "1",
      "paths_equal": true,
      "shots": 0,
      "quantum_hardware_used": false
    }
  ],
  "wrong_phase_flip": [
    {
      "p_mistaken_as_q": "1/2",
      "meaning": "phase_flip_probability; not intended E_p",
      "after_e": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "1/4",
        "eigenvalues": [
          "1/2",
          "1/2"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1/2",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_h": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "1/4",
        "eigenvalues": [
          "1/2",
          "1/2"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1/2",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "matches_intended": false,
      "hardware_failure": false
    },
    {
      "p_mistaken_as_q": "1",
      "meaning": "phase_flip_probability; not intended E_p",
      "after_e": {
        "density": [
          [
            [
              "1/2",
              "0"
            ],
            [
              "-1/2",
              "0"
            ]
          ],
          [
            [
              "-1/2",
              "0"
            ],
            [
              "1/2",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "1/2",
        "rho01": [
          "-1/2",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "1/2",
          "1/2"
        ]
      },
      "after_h": {
        "density": [
          [
            [
              "0",
              "0"
            ],
            [
              "0",
              "0"
            ]
          ],
          [
            [
              "0",
              "0"
            ],
            [
              "1",
              "0"
            ]
          ]
        ],
        "trace": "1",
        "hermitian": true,
        "positive_semidefinite": true,
        "determinant": "0",
        "eigenvalues": [
          "0",
          "1"
        ],
        "coherence_z": "0",
        "rho01": [
          "0",
          "0"
        ],
        "purity": "1",
        "probabilities_z": [
          "0",
          "1"
        ]
      },
      "matches_intended": false,
      "hardware_failure": false
    }
  ],
  "input_refusals": [
    {
      "case": "extra_key",
      "status": "expected_refusal",
      "reason": "input_keys"
    },
    {
      "case": "bool_schema",
      "status": "expected_refusal",
      "reason": "schema"
    },
    {
      "case": "basis_reversed",
      "status": "expected_refusal",
      "reason": "basis"
    },
    {
      "case": "p_is_phase_flip",
      "status": "expected_refusal",
      "reason": "channel_semantics"
    },
    {
      "case": "bool_p",
      "status": "expected_refusal",
      "reason": "rational_type"
    },
    {
      "case": "float_p",
      "status": "expected_refusal",
      "reason": "rational_type"
    },
    {
      "case": "negative_p",
      "status": "expected_refusal",
      "reason": "p_range"
    },
    {
      "case": "p_over_one",
      "status": "expected_refusal",
      "reason": "p_range"
    },
    {
      "case": "unsupported_p",
      "status": "expected_refusal",
      "reason": "p_not_fixed"
    },
    {
      "case": "zero_denominator",
      "status": "expected_refusal",
      "reason": "rational_syntax"
    },
    {
      "case": "matrix_shape",
      "status": "expected_refusal",
      "reason": "matrix_shape"
    },
    {
      "case": "complex_shape",
      "status": "expected_refusal",
      "reason": "complex_shape"
    },
    {
      "case": "not_hermitian",
      "status": "expected_refusal",
      "reason": "not_hermitian"
    },
    {
      "case": "wrong_trace",
      "status": "expected_refusal",
      "reason": "trace_not_one"
    },
    {
      "case": "negative_eigenvalue",
      "status": "expected_refusal",
      "reason": "not_positive_semidefinite"
    },
    {
      "case": "unknown_state",
      "status": "expected_refusal",
      "reason": "state_id"
    },
    {
      "case": "shots_not_zero",
      "status": "expected_refusal",
      "reason": "shots"
    }
  ],
  "run_id": "calculation-20261006T193913941907Z",
  "result_sha256": "29f206a07bf1745b5772d7a8a9a4c435766716b9b4ab18aad5f561f4b745ed77",
  "observed_at_utc": "2026-10-06T19:39:14.316921+00:00"
};
