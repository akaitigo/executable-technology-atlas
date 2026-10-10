window.ATLAS_SEARCH_DATA = {
  "title": "Atlas 保存計算と画面の接続",
  "schema": 1,
  "run_id": "calculation-20261006T145534753918Z",
  "observed_at": "2026-10-06T14:55:35.073704+00:00",
  "runtime": {
    "implementation": "CPython",
    "python": "3.9.6",
    "system": "Darwin",
    "machine": "arm64"
  },
  "fixture_sha256": "52864641eb925094abfd2d51662e123569c037994bf014ba88b79353d56956c8",
  "cases": [
    {
      "mode_id": "raw-tfidf",
      "query": "alpha",
      "N": 4,
      "df": 2,
      "total_tokens": 16,
      "avgdl": 4.0,
      "idf_variant": "ln(N/df)",
      "idf": 0.6931471805599453,
      "k1": null,
      "b": null,
      "match_ids": [
        "d1",
        "d2"
      ],
      "nonmatch_ids": [
        "d3",
        "d4"
      ],
      "matched_order": [
        "d1",
        "d2"
      ],
      "tie_groups": [],
      "rows": [
        {
          "id": "d1",
          "tokens": [
            "alpha",
            "alpha",
            "x",
            "x",
            "x",
            "x",
            "x",
            "x"
          ],
          "length": 8,
          "term_frequency": 2,
          "positions": [
            0,
            1
          ],
          "matched": true,
          "numerator": 2.0,
          "denominator": 1.0,
          "coefficient": 2.0,
          "score": 1.3862943611198906,
          "rank": 1,
          "nonmatch_short_circuit": false
        },
        {
          "id": "d2",
          "tokens": [
            "alpha",
            "x"
          ],
          "length": 2,
          "term_frequency": 1,
          "positions": [
            0
          ],
          "matched": true,
          "numerator": 1.0,
          "denominator": 1.0,
          "coefficient": 1.0,
          "score": 0.6931471805599453,
          "rank": 2,
          "nonmatch_short_circuit": false
        },
        {
          "id": "d3",
          "tokens": [],
          "length": 0,
          "term_frequency": 0,
          "positions": [],
          "matched": false,
          "numerator": null,
          "denominator": null,
          "coefficient": 0.0,
          "score": 0.0,
          "rank": null,
          "nonmatch_short_circuit": true
        },
        {
          "id": "d4",
          "tokens": [
            "x",
            "y",
            "z",
            "x",
            "y",
            "z"
          ],
          "length": 6,
          "term_frequency": 0,
          "positions": [],
          "matched": false,
          "numerator": null,
          "denominator": null,
          "coefficient": 0.0,
          "score": 0.0,
          "rank": null,
          "nonmatch_short_circuit": true
        }
      ],
      "scope": "finite Python score calculation; no real search engine; usefulness unjudged"
    },
    {
      "mode_id": "bm25-b0",
      "query": "alpha",
      "N": 4,
      "df": 2,
      "total_tokens": 16,
      "avgdl": 4.0,
      "idf_variant": "ln(N/df)",
      "idf": 0.6931471805599453,
      "k1": 1,
      "b": 0.0,
      "match_ids": [
        "d1",
        "d2"
      ],
      "nonmatch_ids": [
        "d3",
        "d4"
      ],
      "matched_order": [
        "d1",
        "d2"
      ],
      "tie_groups": [],
      "rows": [
        {
          "id": "d1",
          "tokens": [
            "alpha",
            "alpha",
            "x",
            "x",
            "x",
            "x",
            "x",
            "x"
          ],
          "length": 8,
          "term_frequency": 2,
          "positions": [
            0,
            1
          ],
          "matched": true,
          "numerator": 4.0,
          "denominator": 3.0,
          "coefficient": 1.3333333333333333,
          "score": 0.9241962407465937,
          "rank": 1,
          "nonmatch_short_circuit": false
        },
        {
          "id": "d2",
          "tokens": [
            "alpha",
            "x"
          ],
          "length": 2,
          "term_frequency": 1,
          "positions": [
            0
          ],
          "matched": true,
          "numerator": 2.0,
          "denominator": 2.0,
          "coefficient": 1.0,
          "score": 0.6931471805599453,
          "rank": 2,
          "nonmatch_short_circuit": false
        },
        {
          "id": "d3",
          "tokens": [],
          "length": 0,
          "term_frequency": 0,
          "positions": [],
          "matched": false,
          "numerator": null,
          "denominator": null,
          "coefficient": 0.0,
          "score": 0.0,
          "rank": null,
          "nonmatch_short_circuit": true
        },
        {
          "id": "d4",
          "tokens": [
            "x",
            "y",
            "z",
            "x",
            "y",
            "z"
          ],
          "length": 6,
          "term_frequency": 0,
          "positions": [],
          "matched": false,
          "numerator": null,
          "denominator": null,
          "coefficient": 0.0,
          "score": 0.0,
          "rank": null,
          "nonmatch_short_circuit": true
        }
      ],
      "scope": "finite Python score calculation; no real search engine; usefulness unjudged"
    },
    {
      "mode_id": "bm25-bhalf",
      "query": "alpha",
      "N": 4,
      "df": 2,
      "total_tokens": 16,
      "avgdl": 4.0,
      "idf_variant": "ln(N/df)",
      "idf": 0.6931471805599453,
      "k1": 1,
      "b": 0.5,
      "match_ids": [
        "d1",
        "d2"
      ],
      "nonmatch_ids": [
        "d3",
        "d4"
      ],
      "matched_order": [
        "d1",
        "d2"
      ],
      "tie_groups": [
        [
          "d1",
          "d2"
        ]
      ],
      "rows": [
        {
          "id": "d1",
          "tokens": [
            "alpha",
            "alpha",
            "x",
            "x",
            "x",
            "x",
            "x",
            "x"
          ],
          "length": 8,
          "term_frequency": 2,
          "positions": [
            0,
            1
          ],
          "matched": true,
          "numerator": 4.0,
          "denominator": 3.5,
          "coefficient": 1.1428571428571428,
          "score": 0.7921682063542231,
          "rank": 1,
          "nonmatch_short_circuit": false
        },
        {
          "id": "d2",
          "tokens": [
            "alpha",
            "x"
          ],
          "length": 2,
          "term_frequency": 1,
          "positions": [
            0
          ],
          "matched": true,
          "numerator": 2.0,
          "denominator": 1.75,
          "coefficient": 1.1428571428571428,
          "score": 0.7921682063542231,
          "rank": 2,
          "nonmatch_short_circuit": false
        },
        {
          "id": "d3",
          "tokens": [],
          "length": 0,
          "term_frequency": 0,
          "positions": [],
          "matched": false,
          "numerator": null,
          "denominator": null,
          "coefficient": 0.0,
          "score": 0.0,
          "rank": null,
          "nonmatch_short_circuit": true
        },
        {
          "id": "d4",
          "tokens": [
            "x",
            "y",
            "z",
            "x",
            "y",
            "z"
          ],
          "length": 6,
          "term_frequency": 0,
          "positions": [],
          "matched": false,
          "numerator": null,
          "denominator": null,
          "coefficient": 0.0,
          "score": 0.0,
          "rank": null,
          "nonmatch_short_circuit": true
        }
      ],
      "scope": "finite Python score calculation; no real search engine; usefulness unjudged"
    },
    {
      "mode_id": "bm25-b1",
      "query": "alpha",
      "N": 4,
      "df": 2,
      "total_tokens": 16,
      "avgdl": 4.0,
      "idf_variant": "ln(N/df)",
      "idf": 0.6931471805599453,
      "k1": 1,
      "b": 1.0,
      "match_ids": [
        "d1",
        "d2"
      ],
      "nonmatch_ids": [
        "d3",
        "d4"
      ],
      "matched_order": [
        "d2",
        "d1"
      ],
      "tie_groups": [],
      "rows": [
        {
          "id": "d1",
          "tokens": [
            "alpha",
            "alpha",
            "x",
            "x",
            "x",
            "x",
            "x",
            "x"
          ],
          "length": 8,
          "term_frequency": 2,
          "positions": [
            0,
            1
          ],
          "matched": true,
          "numerator": 4.0,
          "denominator": 4.0,
          "coefficient": 1.0,
          "score": 0.6931471805599453,
          "rank": 2,
          "nonmatch_short_circuit": false
        },
        {
          "id": "d2",
          "tokens": [
            "alpha",
            "x"
          ],
          "length": 2,
          "term_frequency": 1,
          "positions": [
            0
          ],
          "matched": true,
          "numerator": 2.0,
          "denominator": 1.5,
          "coefficient": 1.3333333333333333,
          "score": 0.9241962407465937,
          "rank": 1,
          "nonmatch_short_circuit": false
        },
        {
          "id": "d3",
          "tokens": [],
          "length": 0,
          "term_frequency": 0,
          "positions": [],
          "matched": false,
          "numerator": null,
          "denominator": null,
          "coefficient": 0.0,
          "score": 0.0,
          "rank": null,
          "nonmatch_short_circuit": true
        },
        {
          "id": "d4",
          "tokens": [
            "x",
            "y",
            "z",
            "x",
            "y",
            "z"
          ],
          "length": 6,
          "term_frequency": 0,
          "positions": [],
          "matched": false,
          "numerator": null,
          "denominator": null,
          "coefficient": 0.0,
          "score": 0.0,
          "rank": null,
          "nonmatch_short_circuit": true
        }
      ],
      "scope": "finite Python score calculation; no real search engine; usefulness unjudged"
    }
  ],
  "source_result_sha256": "e5760ff1119d3469e5bcb50aee6e4841615fbedf44ec0e1667bc8bd9862e8523"
};
