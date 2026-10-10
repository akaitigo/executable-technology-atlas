window.ATLAS_MULTI_DATA = {
  "schema": 1,
  "run_id": "calculation-20261006T170209712712Z",
  "result_sha256": "bf31965aaf96b70dd05cae20f5a3852abfa0673e6c9fb0d6567dac6270976c7e",
  "observed_at_utc": "2026-10-06T17:02:10.094107+00:00",
  "runtime": {
    "python": "3.9.6",
    "implementation": "CPython",
    "system": "Darwin",
    "machine": "arm64"
  },
  "fixture_sha256": "29c0d97004546fec30db7af9137114ea94c38aac21c84679b5b186392435ce3b",
  "cases": [
    {
      "request_id": "alpha-only",
      "query": "alpha",
      "status": "calculated",
      "query_tokens": [
        "alpha"
      ],
      "canonical_terms": [
        "alpha"
      ],
      "removed_duplicates": 0,
      "N": 4,
      "total_tokens": 16,
      "avgdl": 4.0,
      "k1": 1,
      "b": 0,
      "idf_variant": "ln(N/df)",
      "df": {
        "alpha": 3
      },
      "idf": {
        "alpha": 0.28768207245178085
      },
      "matches": [
        "d1",
        "d3",
        "d4"
      ],
      "weighted_order": [
        "d1",
        "d3",
        "d4"
      ],
      "weighted_ties": [
        [
          "d1",
          "d3",
          "d4"
        ]
      ],
      "unit_order": [
        "d1",
        "d3",
        "d4"
      ],
      "unit_ties": [
        [
          "d1",
          "d3",
          "d4"
        ]
      ],
      "rows": [
        {
          "id": "d1",
          "tokens": [
            "alpha",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 1.0,
              "weighted_contribution": 0.28768207245178085,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            }
          ],
          "matched": true,
          "weighted_score": 0.28768207245178085,
          "unit_score": 1.0,
          "weighted_rank": 1,
          "unit_rank": 1
        },
        {
          "id": "d2",
          "tokens": [
            "beta",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [],
              "tf": 0,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 0.0,
              "weighted_contribution": 0.0,
              "unit_contribution": 0.0,
              "nonmatch_short_circuit": true
            }
          ],
          "matched": false,
          "weighted_score": 0.0,
          "unit_score": 0.0,
          "weighted_rank": null,
          "unit_rank": null
        },
        {
          "id": "d3",
          "tokens": [
            "alpha",
            "beta",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 1.0,
              "weighted_contribution": 0.28768207245178085,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            }
          ],
          "matched": true,
          "weighted_score": 0.28768207245178085,
          "unit_score": 1.0,
          "weighted_rank": 2,
          "unit_rank": 2
        },
        {
          "id": "d4",
          "tokens": [
            "alpha",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 1.0,
              "weighted_contribution": 0.28768207245178085,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            }
          ],
          "matched": true,
          "weighted_score": 0.28768207245178085,
          "unit_score": 1.0,
          "weighted_rank": 3,
          "unit_rank": 3
        }
      ],
      "search_engine_executed": false,
      "user_relevance_evaluated": false
    },
    {
      "request_id": "beta-only",
      "query": "beta",
      "status": "calculated",
      "query_tokens": [
        "beta"
      ],
      "canonical_terms": [
        "beta"
      ],
      "removed_duplicates": 0,
      "N": 4,
      "total_tokens": 16,
      "avgdl": 4.0,
      "k1": 1,
      "b": 0,
      "idf_variant": "ln(N/df)",
      "df": {
        "beta": 2
      },
      "idf": {
        "beta": 0.6931471805599453
      },
      "matches": [
        "d2",
        "d3"
      ],
      "weighted_order": [
        "d2",
        "d3"
      ],
      "weighted_ties": [
        [
          "d2",
          "d3"
        ]
      ],
      "unit_order": [
        "d2",
        "d3"
      ],
      "unit_ties": [
        [
          "d2",
          "d3"
        ]
      ],
      "rows": [
        {
          "id": "d1",
          "tokens": [
            "alpha",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "beta",
              "positions": [],
              "tf": 0,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 0.0,
              "weighted_contribution": 0.0,
              "unit_contribution": 0.0,
              "nonmatch_short_circuit": true
            }
          ],
          "matched": false,
          "weighted_score": 0.0,
          "unit_score": 0.0,
          "weighted_rank": null,
          "unit_rank": null
        },
        {
          "id": "d2",
          "tokens": [
            "beta",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "beta",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 1.0,
              "weighted_contribution": 0.6931471805599453,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            }
          ],
          "matched": true,
          "weighted_score": 0.6931471805599453,
          "unit_score": 1.0,
          "weighted_rank": 1,
          "unit_rank": 1
        },
        {
          "id": "d3",
          "tokens": [
            "alpha",
            "beta",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "beta",
              "positions": [
                1
              ],
              "tf": 1,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 1.0,
              "weighted_contribution": 0.6931471805599453,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            }
          ],
          "matched": true,
          "weighted_score": 0.6931471805599453,
          "unit_score": 1.0,
          "weighted_rank": 2,
          "unit_rank": 2
        },
        {
          "id": "d4",
          "tokens": [
            "alpha",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "beta",
              "positions": [],
              "tf": 0,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 0.0,
              "weighted_contribution": 0.0,
              "unit_contribution": 0.0,
              "nonmatch_short_circuit": true
            }
          ],
          "matched": false,
          "weighted_score": 0.0,
          "unit_score": 0.0,
          "weighted_rank": null,
          "unit_rank": null
        }
      ],
      "search_engine_executed": false,
      "user_relevance_evaluated": false
    },
    {
      "request_id": "two-terms",
      "query": "alpha beta",
      "status": "calculated",
      "query_tokens": [
        "alpha",
        "beta"
      ],
      "canonical_terms": [
        "alpha",
        "beta"
      ],
      "removed_duplicates": 0,
      "N": 4,
      "total_tokens": 16,
      "avgdl": 4.0,
      "k1": 1,
      "b": 0,
      "idf_variant": "ln(N/df)",
      "df": {
        "alpha": 3,
        "beta": 2
      },
      "idf": {
        "alpha": 0.28768207245178085,
        "beta": 0.6931471805599453
      },
      "matches": [
        "d1",
        "d2",
        "d3",
        "d4"
      ],
      "weighted_order": [
        "d3",
        "d2",
        "d1",
        "d4"
      ],
      "weighted_ties": [
        [
          "d1",
          "d4"
        ]
      ],
      "unit_order": [
        "d3",
        "d1",
        "d2",
        "d4"
      ],
      "unit_ties": [
        [
          "d1",
          "d2",
          "d4"
        ]
      ],
      "rows": [
        {
          "id": "d1",
          "tokens": [
            "alpha",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 1.0,
              "weighted_contribution": 0.28768207245178085,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            },
            {
              "term": "beta",
              "positions": [],
              "tf": 0,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 0.0,
              "weighted_contribution": 0.0,
              "unit_contribution": 0.0,
              "nonmatch_short_circuit": true
            }
          ],
          "matched": true,
          "weighted_score": 0.28768207245178085,
          "unit_score": 1.0,
          "weighted_rank": 3,
          "unit_rank": 2
        },
        {
          "id": "d2",
          "tokens": [
            "beta",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [],
              "tf": 0,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 0.0,
              "weighted_contribution": 0.0,
              "unit_contribution": 0.0,
              "nonmatch_short_circuit": true
            },
            {
              "term": "beta",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 1.0,
              "weighted_contribution": 0.6931471805599453,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            }
          ],
          "matched": true,
          "weighted_score": 0.6931471805599453,
          "unit_score": 1.0,
          "weighted_rank": 2,
          "unit_rank": 3
        },
        {
          "id": "d3",
          "tokens": [
            "alpha",
            "beta",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 1.0,
              "weighted_contribution": 0.28768207245178085,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            },
            {
              "term": "beta",
              "positions": [
                1
              ],
              "tf": 1,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 1.0,
              "weighted_contribution": 0.6931471805599453,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            }
          ],
          "matched": true,
          "weighted_score": 0.9808292530117262,
          "unit_score": 2.0,
          "weighted_rank": 1,
          "unit_rank": 1
        },
        {
          "id": "d4",
          "tokens": [
            "alpha",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 1.0,
              "weighted_contribution": 0.28768207245178085,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            },
            {
              "term": "beta",
              "positions": [],
              "tf": 0,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 0.0,
              "weighted_contribution": 0.0,
              "unit_contribution": 0.0,
              "nonmatch_short_circuit": true
            }
          ],
          "matched": true,
          "weighted_score": 0.28768207245178085,
          "unit_score": 1.0,
          "weighted_rank": 4,
          "unit_rank": 4
        }
      ],
      "search_engine_executed": false,
      "user_relevance_evaluated": false
    },
    {
      "request_id": "reversed-terms",
      "query": "beta alpha",
      "status": "calculated",
      "query_tokens": [
        "beta",
        "alpha"
      ],
      "canonical_terms": [
        "alpha",
        "beta"
      ],
      "removed_duplicates": 0,
      "N": 4,
      "total_tokens": 16,
      "avgdl": 4.0,
      "k1": 1,
      "b": 0,
      "idf_variant": "ln(N/df)",
      "df": {
        "alpha": 3,
        "beta": 2
      },
      "idf": {
        "alpha": 0.28768207245178085,
        "beta": 0.6931471805599453
      },
      "matches": [
        "d1",
        "d2",
        "d3",
        "d4"
      ],
      "weighted_order": [
        "d3",
        "d2",
        "d1",
        "d4"
      ],
      "weighted_ties": [
        [
          "d1",
          "d4"
        ]
      ],
      "unit_order": [
        "d3",
        "d1",
        "d2",
        "d4"
      ],
      "unit_ties": [
        [
          "d1",
          "d2",
          "d4"
        ]
      ],
      "rows": [
        {
          "id": "d1",
          "tokens": [
            "alpha",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 1.0,
              "weighted_contribution": 0.28768207245178085,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            },
            {
              "term": "beta",
              "positions": [],
              "tf": 0,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 0.0,
              "weighted_contribution": 0.0,
              "unit_contribution": 0.0,
              "nonmatch_short_circuit": true
            }
          ],
          "matched": true,
          "weighted_score": 0.28768207245178085,
          "unit_score": 1.0,
          "weighted_rank": 3,
          "unit_rank": 2
        },
        {
          "id": "d2",
          "tokens": [
            "beta",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [],
              "tf": 0,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 0.0,
              "weighted_contribution": 0.0,
              "unit_contribution": 0.0,
              "nonmatch_short_circuit": true
            },
            {
              "term": "beta",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 1.0,
              "weighted_contribution": 0.6931471805599453,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            }
          ],
          "matched": true,
          "weighted_score": 0.6931471805599453,
          "unit_score": 1.0,
          "weighted_rank": 2,
          "unit_rank": 3
        },
        {
          "id": "d3",
          "tokens": [
            "alpha",
            "beta",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 1.0,
              "weighted_contribution": 0.28768207245178085,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            },
            {
              "term": "beta",
              "positions": [
                1
              ],
              "tf": 1,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 1.0,
              "weighted_contribution": 0.6931471805599453,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            }
          ],
          "matched": true,
          "weighted_score": 0.9808292530117262,
          "unit_score": 2.0,
          "weighted_rank": 1,
          "unit_rank": 1
        },
        {
          "id": "d4",
          "tokens": [
            "alpha",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 1.0,
              "weighted_contribution": 0.28768207245178085,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            },
            {
              "term": "beta",
              "positions": [],
              "tf": 0,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 0.0,
              "weighted_contribution": 0.0,
              "unit_contribution": 0.0,
              "nonmatch_short_circuit": true
            }
          ],
          "matched": true,
          "weighted_score": 0.28768207245178085,
          "unit_score": 1.0,
          "weighted_rank": 4,
          "unit_rank": 4
        }
      ],
      "search_engine_executed": false,
      "user_relevance_evaluated": false
    },
    {
      "request_id": "repeated-terms",
      "query": "alpha alpha beta",
      "status": "calculated",
      "query_tokens": [
        "alpha",
        "alpha",
        "beta"
      ],
      "canonical_terms": [
        "alpha",
        "beta"
      ],
      "removed_duplicates": 1,
      "N": 4,
      "total_tokens": 16,
      "avgdl": 4.0,
      "k1": 1,
      "b": 0,
      "idf_variant": "ln(N/df)",
      "df": {
        "alpha": 3,
        "beta": 2
      },
      "idf": {
        "alpha": 0.28768207245178085,
        "beta": 0.6931471805599453
      },
      "matches": [
        "d1",
        "d2",
        "d3",
        "d4"
      ],
      "weighted_order": [
        "d3",
        "d2",
        "d1",
        "d4"
      ],
      "weighted_ties": [
        [
          "d1",
          "d4"
        ]
      ],
      "unit_order": [
        "d3",
        "d1",
        "d2",
        "d4"
      ],
      "unit_ties": [
        [
          "d1",
          "d2",
          "d4"
        ]
      ],
      "rows": [
        {
          "id": "d1",
          "tokens": [
            "alpha",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 1.0,
              "weighted_contribution": 0.28768207245178085,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            },
            {
              "term": "beta",
              "positions": [],
              "tf": 0,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 0.0,
              "weighted_contribution": 0.0,
              "unit_contribution": 0.0,
              "nonmatch_short_circuit": true
            }
          ],
          "matched": true,
          "weighted_score": 0.28768207245178085,
          "unit_score": 1.0,
          "weighted_rank": 3,
          "unit_rank": 2
        },
        {
          "id": "d2",
          "tokens": [
            "beta",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [],
              "tf": 0,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 0.0,
              "weighted_contribution": 0.0,
              "unit_contribution": 0.0,
              "nonmatch_short_circuit": true
            },
            {
              "term": "beta",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 1.0,
              "weighted_contribution": 0.6931471805599453,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            }
          ],
          "matched": true,
          "weighted_score": 0.6931471805599453,
          "unit_score": 1.0,
          "weighted_rank": 2,
          "unit_rank": 3
        },
        {
          "id": "d3",
          "tokens": [
            "alpha",
            "beta",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 1.0,
              "weighted_contribution": 0.28768207245178085,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            },
            {
              "term": "beta",
              "positions": [
                1
              ],
              "tf": 1,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 1.0,
              "weighted_contribution": 0.6931471805599453,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            }
          ],
          "matched": true,
          "weighted_score": 0.9808292530117262,
          "unit_score": 2.0,
          "weighted_rank": 1,
          "unit_rank": 1
        },
        {
          "id": "d4",
          "tokens": [
            "alpha",
            "x",
            "x",
            "x"
          ],
          "length": 4,
          "contributions": [
            {
              "term": "alpha",
              "positions": [
                0
              ],
              "tf": 1,
              "df": 3,
              "idf": 0.28768207245178085,
              "tf_factor": 1.0,
              "weighted_contribution": 0.28768207245178085,
              "unit_contribution": 1.0,
              "nonmatch_short_circuit": false
            },
            {
              "term": "beta",
              "positions": [],
              "tf": 0,
              "df": 2,
              "idf": 0.6931471805599453,
              "tf_factor": 0.0,
              "weighted_contribution": 0.0,
              "unit_contribution": 0.0,
              "nonmatch_short_circuit": true
            }
          ],
          "matched": true,
          "weighted_score": 0.28768207245178085,
          "unit_score": 1.0,
          "weighted_rank": 4,
          "unit_rank": 4
        }
      ],
      "search_engine_executed": false,
      "user_relevance_evaluated": false
    },
    {
      "request_id": "unknown-term",
      "query": "alpha gamma",
      "status": "expected_query_refusal",
      "code": "unknown_query_term",
      "missing_terms": [
        "gamma"
      ],
      "rows": null,
      "scores_returned": false
    }
  ]
};
